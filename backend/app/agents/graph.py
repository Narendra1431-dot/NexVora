"""Bounded read-only agent DAGs; mutations remain separately approved."""
import asyncio,importlib,json,time
from typing import Literal
from pydantic import Field
from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError
from ..db import col
from ..security import new_id
from ..providers.router import structured
from ..providers.base import ProviderError
from ..brain.schemas import Advisory
from ..brain.orchestrator import validate_citations
from ..runtime.redaction import redact
from .models import StrictModel
from .state import snapshot
from .proof import now,event,summary,execution_context

AgentName=Literal['profile','resume','evidence','competency','career','gap','roadmap','resources','assessment','projects','certificates','coding','rag','analytics']
MODULES=set(AgentName.__args__)
DEPENDENCIES={'profile':[],'resume':['profile'],'evidence':['profile'],'competency':['profile'],
    'career':['profile'],'gap':['competency','career','evidence'],'rag':['career'],
    'roadmap':['gap'],'resources':['gap'],'assessment':['gap'],'projects':['gap'],
    'certificates':['gap'],'coding':['profile'],'analytics':['competency']}

class StartRun(StrictModel):
    message:str=Field(min_length=3,max_length=3000)
    requestId:str=Field(min_length=8,max_length=100)

class Plan(StrictModel):
    intent:str=Field(min_length=1,max_length=80)
    agents:list[AgentName]=Field(min_length=1,max_length=14)

async def recorded_model(run,phase,prompt,schema,context):
    data,result,attempts=await structured(prompt,schema,context)
    await col('intelligence_traces').insert_one({'requestId':new_id('brain'),'runId':run['id'],'studentId':run['studentId'],
        'kind':'agent_model_call','phase':phase,'provider':result.provider,'model':result.model,'latency':result.latency,
        'tokens':result.tokens,'status':'Completed','createdAt':now()})
    return data,result,attempts

async def owned(run_id,sid):
    row=await col('agent_runs').find_one({'id':run_id,'studentId':sid,'kind':'execution_graph'})
    if not row:raise HTTPException(404,'Agent run not found.')
    return row

def public(row):return summary({k:v for k,v in row.items() if k not in {'_id','studentId','requestId','lease','rawInput'}})

async def create(payload,sid):
    if redact(payload.message)!=payload.message:raise HTTPException(422,'Remove credentials from the request.')
    existing=await col('agent_runs').find_one({'studentId':sid,'requestId':payload.requestId})
    if existing:
        if existing.get('kind')!='execution_graph' or existing.get('userRequest')!=payload.message:raise HTTPException(409,'Request ID belongs to different input.')
        return public(existing)
    s=await snapshot(sid)
    run={'id':new_id('agt'),'runId':None,'kind':'execution_graph','studentId':sid,'requestId':payload.requestId,
        'userRequest':payload.message,'status':'QUEUED','createdAt':now(),'stateVersionBefore':s.stateVersion,
        'stateVersionAfter':s.stateVersion,'selectedAgents':[],'executionGraph':[],'cancelRequested':False}
    run['runId']=run['id']
    try:await col('agent_runs').insert_one(run)
    except DuplicateKeyError:
        other=await col('agent_runs').find_one({'studentId':sid,'requestId':payload.requestId})
        if other.get('userRequest')!=payload.message:raise HTTPException(409,'Request ID belongs to different input.')
        return public(other)
    await event(run,'run.created','Workflow saved; waiting for worker.')
    from ..workers.queue import enqueue
    job=await enqueue(sid,'agent_workflow',[run['id']],'dag-'+run['id'],state_version=s.stateVersion)
    await col('agent_runs').update_one({'id':run['id']},{'$set':{'jobId':job['jobId']}})
    return public(await owned(run['id'],sid))

def graph_for(names):
    selected=set(names)
    def add(n):
        for parent in DEPENDENCIES[n]:
            if parent not in selected:selected.add(parent);add(parent)
    for n in list(selected):add(n)
    return [{'id':n,'agentName':n,'dependencyIds':DEPENDENCIES[n],'task':TASKS[n]} for n in DEPENDENCIES if n in selected]

TASKS={
 'profile':'Inspect the current owned student profile',
 'resume':'Inspect the stored resume analysis; identify unsupported claims',
 'evidence':'Read owned evidence; preserve verification state',
 'competency':'Read canonical mastery and confidence',
 'career':'Read selected target career and deterministic readiness',
 'gap':'Read deterministic skill, prerequisite and evidence gaps',
 'roadmap':'Prepare a learning proposal from current roadmap and gaps',
 'resources':'Rank existing resources for current learning priorities',
 'assessment':'Inspect available assessments and owned attempts',
 'projects':'Recommend existing projects for current gaps',
 'certificates':'Check deterministic eligibility and certification options',
 'coding':'Inspect coding progress and rank; no code execution',
 'rag':'Retrieve trusted knowledge and owned course material',
 'analytics':'Summarize measured progress; no fabricated forecasts'}

async def execute(run_id,sid):
    run=await owned(run_id,sid)
    if run['status'] in ('COMPLETED','FAILED','CANCELLED'):return {'runId':run_id,'status':run['status']}
    # A worker restart must not silently re-execute a partially dispatched run.
    if run['status']=='RUNNING':
        await fail(run,'WORKER_INTERRUPTED','Worker stopped before confirming completion.')
        return {'runId':run_id,'status':'FAILED'}
    changed=await col('agent_runs').update_one({'id':run_id,'status':'QUEUED','cancelRequested':False},{'$set':{'status':'RUNNING','startedAt':now()}})
    if not changed.modified_count:return {'runId':run_id,'status':(await owned(run_id,sid))['status']}
    started=time.monotonic()
    try:
        s=await snapshot(sid)
        await col('agent_runs').update_one({'id':run_id},{'$set':{'stateVersionBefore':s.stateVersion}})
        await event(run,'supervisor.started','Selecting permitted specialist agents.')
        plan,generation,attempts=await recorded_model(run,'planning','Select specialist agents for this request. Return intent and agents only. You cannot grant privileges or change student state. Include profile, competency, career, gap, roadmap, resources and rag for career planning. Include resume and evidence for resume requests.',Plan,
            json.dumps({'request':run['userRequest'],'selectedCareer':s.targetCareer.get('title'),'hasResume':bool(s.resume)}))
        names=set(plan.agents)
        # Required coverage cannot be omitted by the model.
        from .supervisor import route
        names.update(route(run['userRequest'])[1])
        if any(w in run['userRequest'].lower() for w in ('plan','career','resume')):names.update(['profile','career','competency','evidence','gap','roadmap','resources','rag'])
        graph=graph_for(names)
        await col('agent_runs').update_one({'id':run_id},{'$set':{'intent':plan.intent,'selectedAgents':[n['id'] for n in graph],
            'executionGraph':graph,'supervisorDecision':'Selected allowlisted specialists with server-enforced dependencies.',
            'modelUsage':[{'phase':'planning','provider':generation.provider,'model':generation.model,'totalTokens':generation.tokens,'latency':generation.latency,'requestCount':1,'fallbackAttempts':attempts}]}})
        await event(run,'supervisor.completed','Dependency graph validated; specialist work queued.')
        for node in graph:
            await col('agent_steps').insert_one({**node,'stepId':run_id+'-'+node['id'],'runId':run_id,'studentId':sid,
                'status':'QUEUED' if not node['dependencyIds'] else 'WAITING','retryCount':0,'inputSummary':{'stateVersion':s.stateVersion}})
            await event(run,'agent.queued',node['task'],run_id+'-'+node['id'])
        completed=set();results={};passages=[]
        async def step(node):
            step_id=run_id+'-'+node['id'];clock=time.monotonic()
            context={**run,'stepId':step_id,'agentName':node['id']}
            token=execution_context.set(context)
            await col('agent_steps').update_one({'stepId':step_id},{'$set':{'status':'RUNNING','startedAt':now(),
                'inputSummary':{'stateVersion':s.stateVersion,'dependenciesCompleted':node['dependencyIds']}}})
            await event(run,'agent.started',node['task'],step_id)
            try:
                specialist=importlib.import_module('app.agents.'+node['id'])
                focus=s.recommendations.get('skillId') if node['id']=='resources' else None
                outputs=await asyncio.wait_for(specialist.run(s,run['userRequest'],focus),60)
                values={o.name:o.data for o in outputs}
                await col('agent_steps').update_one({'stepId':step_id},{'$set':{'status':'COMPLETED','completedAt':now(),
                    'durationMs':round((time.monotonic()-clock)*1000),'outputSummary':summary(values),'toolsUsed':[o.name for o in outputs]}})
                await event(run,'agent.completed',node['id']+' completed',step_id)
                return node['id'],values
            except BaseException as exc:
                status='CANCELLED' if isinstance(exc,asyncio.CancelledError) else 'FAILED'
                await col('agent_steps').update_one({'stepId':step_id},{'$set':{'status':status,'completedAt':now(),
                    'durationMs':round((time.monotonic()-clock)*1000),'errorCode':type(exc).__name__,'errorSummary':'Specialist could not complete its task.'}})
                await event(run,'agent.failed',node['id']+' could not complete',step_id)
                raise
            finally:execution_context.reset(token)
        while len(completed)<len(graph):
            if (await owned(run_id,sid))['cancelRequested']:raise asyncio.CancelledError()
            ready=[n for n in graph if n['id'] not in completed and set(n['dependencyIds'])<=completed]
            if not ready:raise ValueError('Invalid execution graph')
            outcomes=await asyncio.gather(*(step(n) for n in ready[:4]),return_exceptions=True)
            for outcome in outcomes:
                if isinstance(outcome,BaseException):raise outcome
                name,values=outcome;results[name]=values;completed.add(name)
        if (await owned(run_id,sid))['cancelRequested']:raise asyncio.CancelledError()
        # Only retrieved source chunks may be cited by the synthesis model.
        for values in results.values():passages.extend(values.get('retrieveRAG',[]))
        cited_passages=[{'id':p.get('id') or p.get('documentId'),'text':p.get('text') or p.get('content',''),**p} for p in passages]
        evidence=[{'id':e['id']} for e in s.evidence]
        compact={name:{key:summary(value) for key,value in values.items()} for name,values in results.items()}
        # Per-agent excerpts are bounded, while source quotes remain intact.
        excerpts={name:json.dumps(value,default=str)[:650] for name,value in compact.items()}
        prompt='Synthesize the actual specialist results into actionable learning advice. Excerpts may be truncated; do not infer omitted data. Never claim state changed or evidence verified. Distinguish stored resume analysis from a fresh parse. evidenceRefs may only use provided evidence IDs. citations must use source IDs and exact quotes; return [] if none. Do not invent external URLs. Do not expose private reasoning.'
        prompt+=' Each citations.chunkId MUST equal a sources.id (not documentId). Each quote must be a literal substring of that source text.'
        context=json.dumps({'request':run['userRequest'],'results':excerpts,'evidence':evidence,'sources':cited_passages},default=str)
        for attempt in range(2):
            answer,generation,attempts=await recorded_model(run,'synthesis',prompt,Advisory,context)
            await col('agent_runs').update_one({'id':run_id},{'$push':{'modelUsage':{'phase':'synthesis','provider':generation.provider,
                'model':generation.model,'totalTokens':generation.tokens,'latency':generation.latency,'requestCount':1,'fallbackAttempts':attempts}}})
            try:validate_citations(answer,cited_passages,evidence);break
            except ProviderError as exc:
                if attempt:raise
                await event(run,'synthesis.retrying','Source validation failed; requesting one corrected response.')
                prompt+=' Repair provenance error '+exc.code+'. Use only the exact source IDs and quotes supplied. If no source supports a statement, omit its citation rather than inventing one.'
        latest=await snapshot(sid)
        if (await owned(run_id,sid))['cancelRequested']:raise asyncio.CancelledError()
        await col('agent_runs').update_one({'id':run_id},{'$set':{'status':'COMPLETED','completedAt':now(),'durationMs':round((time.monotonic()-started)*1000),
            'stateVersionAfter':latest.stateVersion,'finalResultSummary':answer.summary,'result':answer.model_dump(),
            'sources':summary(cited_passages),'changes':[],'proposal':summary(results.get('roadmap',{}))}})
        await event(run,'run.completed','Analysis ready. Proposals have not changed student state.')
        return {'runId':run_id,'status':'COMPLETED'}
    except asyncio.CancelledError:
        await fail(run,'CANCELLED','Cancellation confirmed at a safe boundary.',status='CANCELLED')
        return {'runId':run_id,'status':'CANCELLED'}
    except Exception as exc:
        code=exc.code if isinstance(exc,ProviderError) else 'TIMEOUT' if isinstance(exc,TimeoutError) else 'TOOL_ERROR'
        await fail(run,code,'Workflow could not complete. Completed steps remain available for inspection.')
        return {'runId':run_id,'status':'FAILED'}

async def fail(run,code,message,status='FAILED'):
    from datetime import datetime
    latest=await col('agent_runs').find_one({'id':run['id']})
    finished=now();duration=round((datetime.fromisoformat(finished.replace('Z','+00:00'))-datetime.fromisoformat((latest.get('startedAt') or latest['createdAt']).replace('Z','+00:00'))).total_seconds()*1000)
    await col('agent_runs').update_one({'id':run['id']},{'$set':{'status':status,'completedAt':finished,'durationMs':duration,'error':{'code':code,'message':message}}})
    await col('agent_steps').update_many({'runId':run['id'],'status':{'$in':['QUEUED','WAITING','RUNNING']}},{'$set':{'status':'CANCELLED','completedAt':now(),'errorSummary':'Workflow stopped before completion.'}})
    await event(run,'run.'+status.lower(),message)
