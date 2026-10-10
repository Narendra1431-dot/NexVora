from fastapi import APIRouter, HTTPException
from ..security import StudentId
from ..db import col
from ..agents.models import ChatInput,ExecuteInput,safe
from ..agents.supervisor import chat
from ..agents.execution import execute_action
from ..agents.state import snapshot
from ..workflows.adaptation import publish

from ..runtime.gateway import ToolRequest,propose,decide,public
from ..agents.models import StrictModel
from typing import Literal
from pydantic import ValidationError

class Decision(StrictModel):
    decision:Literal['approve','reject']

router=APIRouter(prefix='/agent',tags=['controlled-copilot'])

@router.post('/chat')
async def agent_chat(payload:ChatInput,student_id:str=StudentId):return await chat(payload,student_id)

@router.post('/execute')
async def agent_execute(payload:ExecuteInput | ToolRequest,student_id:str=StudentId):
    if isinstance(payload,ToolRequest):
        aliases={'recompute_roadmap':'recomputeRoadmap','start_assessment':'startAssessment','evaluate_assessment':'evaluateAssessment','analyze_resume':'analyzeResume'}
        if payload.toolName in aliases:payload=payload.model_copy(update={'toolName':aliases[payload.toolName]})
        from ..runtime.gateway import READ_ALIASES
        if payload.toolName in READ_ALIASES:
            from ..agents.models import ToolInput
            from ..tools.registry import execute
            try:call=ToolInput.model_validate({**payload.arguments,'name':READ_ALIASES[payload.toolName]})
            except ValidationError:raise HTTPException(422,'Invalid read tool input.')
            state=await snapshot(student_id)
            if payload.toolName=='query_rag':
                from ..rag.retrieval import retrieve
                from ..runtime.gateway import audit
                matches=await retrieve(student_id,call.query,[])
                await audit(student_id,'query_rag','completed',state.stateVersion)
                return {'name':'query_rag','stateVersion':state.stateVersion,'data':safe(matches)}
            return await execute(call,state)
        try:return await propose(student_id,payload)
        except ValidationError:raise HTTPException(422,'Tool arguments do not match the registered input schema.')
    return await execute_action(payload,student_id)

@router.get('/recommendations')
async def recommendations(student_id:str=StudentId):
    s=await snapshot(student_id)
    rec=await publish(s,'Current state evaluated')
    return {'recommendation':rec,'stateVersion':s.stateVersion,'weeklyPlan':(await col('agent_memory').find_one({'studentId':student_id},{'_id':0,'weeklyPlan':1}) or {}).get('weeklyPlan')}

@router.get('/activity')
async def activity(student_id:str=StudentId):
    return safe([r async for r in col('agent_runs').find({'studentId':student_id},{'_id':0,'response':0,'fingerprint':0,'requestId':0}).sort('createdAt',-1).limit(30)])

@router.get('/history')
async def history(student_id:str=StudentId):
    records=[m async for m in col('agent_messages').find({'studentId':student_id},{'_id':0}).sort('_id',-1).limit(40)]
    return safe(list(reversed(records)))


@router.get('/approvals')
async def approvals(student_id:str=StudentId):
    return [public(r) async for r in col('runtime_actions').find({'studentId':student_id}).sort('createdAt',-1).limit(30)]

@router.post('/approvals/{action_id}')
async def approval_decision(action_id:str,payload:Decision,student_id:str=StudentId):
    return await decide(student_id,action_id,payload.decision)

@router.get('/audit')
async def audit_history(student_id:str=StudentId):
    return [safe(r) async for r in col('runtime_audit').find({'studentId':student_id},{'_id':0}).sort('timestamp',-1).limit(60)]

@router.get('/jobs/{job_id}')
async def agent_job(job_id:str,student_id:str=StudentId):
    from ..workers.queue import public as job_public
    row=await col('intelligence_jobs').find_one({'jobId':job_id,'studentId':student_id})
    if not row:raise HTTPException(404,'Job not found.')
    return job_public(row)

@router.get('/capabilities')
async def capabilities(student_id:str=StudentId):
    return {'computer':{'status':'disabled','reason':'Optional isolated runtime is not deployed.'},
        'connectors':{'github':'not_configured','drive':'not_configured','email':'not_configured','calendar':'not_configured'},
        'workspace':'approval_required','shell':'blocked','secretAccess':'blocked'}
