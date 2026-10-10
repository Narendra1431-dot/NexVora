"""Controlled domain agents: typed read-only dispatch, no mutation or shell tools."""
from typing import Literal
from pydantic import BaseModel
from ..db import col
from ..engine.state import recalculate, load_career
from ..security import new_id, iso_now
from ..observability import log
from . import rag

class ToolCall(BaseModel):
    name: Literal['Profile', 'Evidence', 'Competency', 'Career', 'Roadmap', 'Resource', 'Assessment', 'Project', 'Resume', 'RAG']

def clean(value):
    if isinstance(value, list): return [clean(v) for v in value]
    if isinstance(value, dict): return {k:clean(v) for k,v in value.items() if k not in {'_id','studentId','correctAnswers','correct','explanation'}}
    return value

async def execute_tool(call: ToolCall, *, student_id, query, state, profile, career):
    name=call.name
    if name=='Profile': return {k:profile.get(k) for k in ('name','weeklyAvailabilityHours','learningPreferences')}
    if name=='Evidence': return clean(state.evidence)
    if name=='Competency': return clean(state.competencies)
    if name=='Career': return clean({'title':(career or {}).get('title'),'readiness':state.readiness,'requirements':(career or {}).get('requirements',[])})
    if name=='Roadmap': return clean({'milestones':state.milestones,'nextAction':state.mission})
    if name=='Resource':
        from ..ml.inference.ranker import rank
        resources=[r async for r in col('resources').find({})]
        return clean(rank(resources,state.competencies,profile.get('weeklyAvailabilityHours',10))[:10])
    if name=='Assessment':
        bank=[a async for a in col('assessments').find({}, {'questions':0}).limit(30)]
        attempts=[a async for a in col('attempts').find({'studentId':student_id},{'answers':0}).sort('createdAt',-1).limit(10)]
        return clean({'available':bank,'recentAttempts':attempts})
    if name=='Project': return clean(state.projects)
    if name=='Resume': return clean(state.resume)
    if name=='RAG': return await rag.retrieve(query)
    raise ValueError('Tool not allowed')

async def supervise(student_id: str, query: str):
    state=await recalculate(student_id,persist=False)
    career=await load_career(student_id)
    profile=await col('profiles').find_one({'studentId':student_id},{'_id':0}) or {}
    names=['Profile','Evidence','Competency','Career','Roadmap','Resource','RAG']
    for word,name in [('assessment','Assessment'),('project','Project'),('resume','Resume')]:
        if word in query.lower(): names.append(name)
    run_id=new_id('run')
    results={}
    errors=[]
    executed=[]
    for name in names:
        try:
            results[name]=await execute_tool(ToolCall(name=name),student_id=student_id,query=query,state=state,profile=profile,career=career)
            executed.append(name)
            log('agent_tool_completed',agent=name,agentRunId=run_id,stateVersion=profile.get('stateVersion',0))
        except Exception as exc:
            errors.append({'agent':name,'error':type(exc).__name__})
            log('agent_tool_failed',agent=name,agentRunId=run_id,error=type(exc).__name__)
    passages=results.get('RAG',[])
    context={'targetCareer':results.get('Career',{}).get('title'),'readiness':state.readiness,'skills':results.get('Competency',[]),'nextAction':state.mission,'roadmap':results.get('Roadmap',{}).get('milestones',[]),'stateVersion':profile.get('stateVersion',0),'evidence':results.get('Evidence',[]),'profile':results.get('Profile',{}),'resources':results.get('Resource',[])}
    for name in ['Assessment','Project','Resume']:
        if name in results: context[name.lower()]=results[name]
    run={'id':run_id,'agentRunId':run_id,'studentId':student_id,'tools':executed,'toolsUsed':executed,'reasonCodes':['READ_ONLY_STUDENT_CONTEXT','HYBRID_RETRIEVAL'],'stateVersion':profile.get('stateVersion',0),'citations':[p['id'] for p in passages],'proposedActions':[state.mission],'errors':errors,'createdAt':iso_now()}
    await col('agent_runs').insert_one(run)
    return context,passages,clean(run)
