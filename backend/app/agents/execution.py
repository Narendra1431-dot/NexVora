"""Explicit actions delegate to domain services, with durable request deduplication."""
import hashlib,json
from ..runtime.redaction import redact
from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError
from ..db import col
from ..security import new_id,iso_now
from .models import ExecuteInput,safe
from .state import snapshot

async def claim(student_id,request_id,payload,kind):
    fingerprint=hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest()
    run={'id':new_id('run'),'studentId':student_id,'requestId':request_id,'fingerprint':fingerprint,'kind':kind,
         'intent':redact(payload.get('action',payload.get('message','')))[:160],'status':'running','createdAt':iso_now(),
         'agentsUsed':[],'toolsUsed':[],'actions':[],'citations':[],'reasonCodes':[]}
    run['agentRunId']=run['id']
    try:await col('agent_runs').insert_one(run)
    except DuplicateKeyError:
        existing=await col('agent_runs').find_one({'studentId':student_id,'requestId':request_id})
        if not existing or existing['fingerprint']!=fingerprint:raise HTTPException(409,'Request ID already belongs to a different action.')
        if existing['status']=='completed':return existing,existing.get('response')
        raise HTTPException(409,'This request is running or previously failed. Inspect activity before submitting a new action.')
    return run,None

async def finish(run,response,**fields):
    await col('agent_runs').update_one({'id':run['id'],'studentId':run['studentId']},
        {'$set':{**fields,'status':'completed','response':response,'completedAt':iso_now()}})

async def fail(run,exc):
    await col('agent_runs').update_one({'id':run['id'],'studentId':run['studentId']},
        {'$set':{'status':'failed','errorCode':f'HTTP_{exc.status_code}' if isinstance(exc,HTTPException) else type(exc).__name__,'completedAt':iso_now()}})

async def execute_action(payload:ExecuteInput,student_id):
    from ..runtime.gateway import propose,ToolRequest
    row=await propose(student_id,ToolRequest(toolName=payload.action,requestId=payload.requestId,
        expectedStateVersion=payload.expectedStateVersion,
        arguments=payload.model_dump(exclude={'action','requestId','expectedStateVersion'})))
    if row['status']=='completed':return row['result']
    return {'action':payload.action,'status':row['status'],'approval':row,'stateVersion':row['stateVersion'],'result':{}}

async def _execute_domain_action(payload:ExecuteInput,student_id):
    run,replay=await claim(student_id,payload.requestId,payload.model_dump(),'action')
    if replay is not None:return replay
    try:
        s=await snapshot(student_id)
        if payload.expectedStateVersion!=s.stateVersion:raise HTTPException(409,'State changed. Refresh before applying this action.')
        from ..routers import student,workflow,mutations,documents
        action=payload.action
        if action=='recomputeRoadmap':data=await student.force_recalculate(student_id)
        elif action=='startAssessment':data=await workflow.start(workflow.DiagnosticStart(skillId=payload.skillId,assessmentId=payload.assessmentId),student_id)
        elif action=='evaluateAssessment':
            if not payload.attemptId or payload.answers is None:raise HTTPException(422,'An owned diagnostic attempt and answers are required.')
            data=await workflow.submit(payload.attemptId,mutations.AttemptIn(answers=payload.answers),student_id)
        elif action=='analyzeResume':
            if not payload.resumeText:raise HTTPException(422,'Resume text is required; it is treated as data.')
            data=await documents.ingest(payload.resumeText,'Copilot pasted resume',student_id)
        elif action=='planWeek':
            from ..intelligence.recommendations import weekly_plan
            data=weekly_plan(s)
            await col('agent_memory').update_one({'studentId':student_id},{'$set':{'weeklyPlan':data,'updatedAt':iso_now()},'$push':{'recentGoals':{'$each':[{'goal':'Weekly learning plan','stateVersion':s.stateVersion,'at':iso_now()}],'$slice':-10}}},upsert=True)
        new_profile=await col('profiles').find_one({'studentId':student_id},{'stateVersion':1}) or {}
        response={'agentRunId':run['id'],'action':action,'status':'completed','stateVersion':new_profile.get('stateVersion',0),'result':safe(data)}
        await finish(run,response,stateVersion=response['stateVersion'],toolsUsed=[action],agentsUsed=['Supervisor',{'recomputeRoadmap':'Roadmap','startAssessment':'Assessment','evaluateAssessment':'Assessment','analyzeResume':'Resume','planWeek':'Roadmap'}[action]],
            actions=[{'label':action,'status':'completed'}],reasonCodes=['EXPLICIT_USER_ACTION','DOMAIN_SERVICE_ONLY'])
        return response
    except Exception as exc:
        await fail(run,exc)
        raise
