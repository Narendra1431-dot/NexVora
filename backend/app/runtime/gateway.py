"""Open Dots action lifecycle adapted for JWT ownership and durable Mongo CAS.

MIT attribution: OPEN_DOTS_LICENSE.txt. No owner auth, SQLite, shell or host runtime.
"""
import hashlib
import asyncio
import json
from datetime import datetime,timezone,timedelta
from typing import Any,Literal
from pydantic import Field
from fastapi import HTTPException
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError
from ..agents.models import StrictModel,ExecuteInput,safe
from ..db import col
from ..security import iso_now,new_id
from .redaction import redact

class ToolRequest(StrictModel):
    toolName: str = Field(min_length=1,max_length=80)
    requestId: str = Field(min_length=8,max_length=100)
    expectedStateVersion: int = Field(ge=0)
    arguments: dict[str,Any] = Field(default_factory=dict)

class WorkspaceInput(StrictModel):
    fileName: str = Field(max_length=100)
    content: str = Field(default='',max_length=100000)

class EmptyInput(StrictModel):pass

class ReportInput(StrictModel):
    runId:str=Field(min_length=8,max_length=80)
    fileName:str=Field(min_length=1,max_length=100)

class ResumeExportInput(StrictModel):
    draftId: str = Field(min_length=1,max_length=80)
    version: int = Field(ge=1)
    fileName: str = Field(max_length=100)

class Result(StrictModel):
    status: Literal['completed','pending_approval','rejected','expired','failed','executing']
    actionId: str
    toolName: str
    result: dict[str,Any] = Field(default_factory=dict)

READ_TOOLS={'getStudentProfile','getCompetencies','getEvidence','calculateCareerGap','calculateReadiness','getRoadmap','searchResources','retrieveRAG','getAssessments','recommendProject','analyzeResume','checkCertificateEligibility','getAnalytics','getCodingProgress','getRank'}
MUTATIONS={'recomputeRoadmap','startAssessment','evaluateAssessment','analyzeResume','planWeek'}
WORKSPACE={'workspace.write','workspace.read','workspace.exportRoadmap'}
READ_ALIASES={'get_profile':'getStudentProfile','get_competencies':'getCompetencies','get_evidence':'getEvidence',
    'get_student_profile':'getStudentProfile','get_target_career':'calculateReadiness','get_skill_gap':'calculateCareerGap',
    'get_assessment_history':'getAssessments','get_projects':'recommendProject','get_learning_stats':'getAnalytics',
    'get_career_requirements':'calculateReadiness','calculate_gap':'calculateCareerGap','get_roadmap':'getRoadmap',
    'search_resources':'searchResources','query_rag':'retrieveRAG','recommend_project':'recommendProject',
    'check_certificate_eligibility':'checkCertificateEligibility','get_coding_progress':'getCodingProgress','get_rank':'getRank'}

def definition(name):
    if name=='workspace.exportAgentReport':return {'riskLevel':'REQUIRES_APPROVAL','requiredPermission':'workspace:propose','inputSchema':'ReportInput','outputSchema':'Result'}
    if name=='workspace.exportResume':return {'riskLevel':'REQUIRES_APPROVAL','requiredPermission':'workspace:propose','inputSchema':'ResumeExportInput','outputSchema':'Result'}
    if name=='generate_resume':return {'riskLevel':'REQUIRES_APPROVAL','requiredPermission':'domain:propose','inputSchema':'EmptyInput','outputSchema':'Result'}
    if name in MUTATIONS:return {'riskLevel':'REQUIRES_APPROVAL','requiredPermission':'domain:propose','inputSchema':'ExecuteInput','outputSchema':'Result'}
    if name in WORKSPACE:return {'riskLevel':'REQUIRES_APPROVAL','requiredPermission':'workspace:propose','inputSchema':'WorkspaceInput','outputSchema':'Result'}
    raise HTTPException(403,'Tool is not registered. External connectors, computer, shell, secrets and direct database tools are disabled.')

async def audit(sid,tool,status,version,*,action_id=None,approval='not_required',risk='READ_ONLY',agent='Supervisor'):
    from ..agents.proof import execution_context
    context=execution_context.get() or {}
    await col('runtime_audit').insert_one({'auditId':new_id('audit'),'studentId':sid,'agent':agent,
        'tool':tool,'action':tool,'riskLevel':risk,'approvalStatus':approval,'stateVersion':version,
        'timestamp':iso_now(),'resultStatus':status,'actionId':action_id,'runId':context.get('id'),'stepId':context.get('stepId')})

async def read_tool(call,state,executor):
    if call.name not in READ_TOOLS:raise HTTPException(403,'Unregistered read tool.')
    try:
        from ..agents.proof import traced_tool
        output=await asyncio.wait_for(traced_tool(call,state,executor),timeout=60)
        await audit(state.studentId,call.name,'completed',state.stateVersion)
        return output
    except Exception:
        await audit(state.studentId,call.name,'failed',state.stateVersion)
        raise

def public(row):
    # Do not return raw arguments, documents, secrets or internal execution payload.
    return redact({k:row.get(k) for k in ('id','requestId','toolName','riskLevel','status','stateVersion','createdAt','expiresAt','preview','reason','result','errorCode')})

async def propose(sid,request:ToolRequest):
    from ..agents.state import snapshot
    s=await snapshot(sid)
    if redact(request.arguments)!=request.arguments:raise HTTPException(422,'Credentials are not allowed in tool arguments.')
    try:d=definition(request.toolName)
    except HTTPException:
        await audit(sid,'blocked_tool','blocked',s.stateVersion,risk='BLOCKED');raise
    permissions={'domain:propose','workspace:propose'} # Server policy, never model/request fields.
    if d['requiredPermission'] not in permissions:raise HTTPException(403,'Permission denied.')
    if request.toolName=='workspace.exportAgentReport':
        args=ReportInput.model_validate(request.arguments).model_dump()
        from ..agents.graph import owned
        from .workspace import resolve
        report=await owned(args['runId'],sid)
        if report['status']!='COMPLETED':raise HTTPException(409,'Only completed analysis can be exported.')
        resolve(sid,args['fileName'])
        if not args['fileName'].endswith('.md'):raise HTTPException(422,'Agent reports use Markdown.')
        preview={'action':'Save agent analysis report','runId':args['runId'],'fileName':args['fileName']}
    elif request.toolName=='workspace.exportResume':
        args=ResumeExportInput.model_validate(request.arguments).model_dump()
        from .workspace import resolve
        from ..routers.resume_generator import owned
        resolve(sid,args['fileName'])
        if not args['fileName'].endswith('.pdf'):raise HTTPException(422,'Resume export requires a PDF filename.')
        draft=await owned(args['draftId'],sid)
        if draft['version']!=args['version']:raise HTTPException(409,'Resume draft changed; preview its current version.')
        preview={'action':'Create resume PDF','draftId':args['draftId'],'version':args['version'],'fileName':args['fileName']}
    elif request.toolName=='generate_resume':
        args=EmptyInput.model_validate(request.arguments).model_dump();preview={'action':'Generate a resume draft in background; review it before export.'}
    elif request.toolName in MUTATIONS:
        args=ExecuteInput.model_validate({**request.arguments,'action':request.toolName,'requestId':request.requestId,'expectedStateVersion':request.expectedStateVersion}).model_dump()
        preview={'action':request.toolName,'skillId':args.get('skillId'),'assessmentId':args.get('assessmentId'),'attemptId':args.get('attemptId')}
    else:
        parsed=WorkspaceInput.model_validate(request.arguments)
        from .workspace import resolve
        resolve(sid,parsed.fileName)
        if request.toolName=='workspace.write' and not parsed.fileName.endswith(('.txt','.md')):raise HTTPException(422,'Notes must be text or Markdown.')
        args=parsed.model_dump()
        preview={'fileName':parsed.fileName,'content':parsed.content if request.toolName=='workspace.write' else None}
    fingerprint=hashlib.sha256(json.dumps({'tool':request.toolName,'args':args},sort_keys=True).encode()).hexdigest()
    prior=await col('runtime_actions').find_one({'studentId':sid,'requestId':request.requestId})
    if prior:
        if prior['fingerprint']!=fingerprint:raise HTTPException(409,'Request ID belongs to different input.')
        return public(prior)
    if request.expectedStateVersion!=s.stateVersion:raise HTTPException(409,'Student state changed. Refresh before proposing this action.')
    row={'id':new_id('action'),'studentId':sid,'requestId':request.requestId,'toolName':request.toolName,
        **d,'status':'pending_approval','stateVersion':s.stateVersion,'createdAt':iso_now(),
        'expiresAt':(datetime.now(timezone.utc)+timedelta(minutes=15)).isoformat(),
        'preview':preview,'reason':'Proposed action; review before execution.','arguments':args,'fingerprint':fingerprint}
    try:await col('runtime_actions').insert_one(row)
    except DuplicateKeyError:
        row=await col('runtime_actions').find_one({'studentId':sid,'requestId':request.requestId})
        if row['fingerprint']!=fingerprint:raise HTTPException(409,'Request ID belongs to different input.')
        return public(row)
    await audit(sid,request.toolName,'pending',s.stateVersion,action_id=row['id'],approval='pending',risk=d['riskLevel'])
    return public(row)

async def decide(sid,action_id,decision):
    row=await col('runtime_actions').find_one({'id':action_id,'studentId':sid})
    if not row:raise HTTPException(404,'Approval not found.')
    if row['status']!='pending_approval':raise HTTPException(409,'Approval was already consumed; inspect its result.')
    expired=datetime.fromisoformat(row['expiresAt'])<=datetime.now(timezone.utc)
    status='expired' if expired else 'rejected' if decision=='reject' else 'executing'
    claimed=await col('runtime_actions').find_one_and_update({'id':action_id,'studentId':sid,'status':'pending_approval'},
        {'$set':{'status':status,'decidedAt':iso_now()}},return_document=ReturnDocument.AFTER)
    if not claimed:raise HTTPException(409,'Approval already consumed.')
    await audit(sid,row['toolName'],status,row['stateVersion'],action_id=action_id,approval=status,risk=row['riskLevel'])
    if status!='executing':
        await record_run_decision(claimed)
        return public(claimed)
    try:
        async with asyncio.timeout(60):
            from ..agents.state import snapshot
            current=await snapshot(sid)
            if current.stateVersion!=row['stateVersion']:raise HTTPException(409,'State changed after proposal; submit a fresh action.')
            definition(row['toolName']) # Recheck policy after approval.
            if row['toolName']=='workspace.exportAgentReport':
                from ..agents.graph import owned
                from .workspace import write
                from fastapi.concurrency import run_in_threadpool
                report=await owned(row['arguments']['runId'],sid)
                if report['status']!='COMPLETED':raise HTTPException(409,'Analysis is not complete.')
                text='# NexVora learning analysis\n\nRun: '+report['id']+'\n\n'+report['finalResultSummary']+'\n\n'
                text+='\n'.join('- '+v for v in report.get('result',{}).get('recommendations',[]))
                text+='\n\nAnalysis only. Verification and scoring remain controlled by domain services.\n'
                result=await run_in_threadpool(write,sid,row['arguments']['fileName'],text.encode('utf-8'))
                artifact={'artifactId':new_id('artifact'),'runId':report['id'],'studentId':sid,'type':'markdown','name':row['arguments']['fileName'],
                    'storageRef':row['arguments']['fileName'],'createdAt':iso_now(),'sha256':hashlib.sha256(text.encode('utf-8')).hexdigest()}
                await col('agent_artifacts').insert_one(artifact)
                result={**result,'artifactId':artifact['artifactId']}
            elif row['toolName']=='workspace.exportResume':
                from ..routers.resume_generator import owned,Draft,export_draft
                from .workspace import write
                from fastapi.concurrency import run_in_threadpool
                args=row['arguments'];draft=await owned(args['draftId'],sid)
                if draft['version']!=args['version']:raise HTTPException(409,'Resume changed since approval was proposed.')
                pdf=await export_draft('pdf',Draft.model_validate(draft),sid)
                result=await run_in_threadpool(write,sid,args['fileName'],pdf.body)
            elif row['toolName']=='generate_resume':
                from ..workers.queue import enqueue
                result=await enqueue(sid,'resume_generation',[],'approved-'+action_id,state_version=current.stateVersion)
            elif row['toolName'] in MUTATIONS:
                from ..agents.execution import _execute_domain_action
                args={**row['arguments'],'requestId':'approved-'+action_id}
                result=await _execute_domain_action(ExecuteInput.model_validate(args),sid)
            else:
                from . import workspace
                from fastapi.concurrency import run_in_threadpool
                args=row['arguments'];name=args['fileName']
                if row['toolName']=='workspace.read':
                    raw=await run_in_threadpool(workspace.read,sid,name)
                    if not name.endswith(('.md','.txt','.json')):raise HTTPException(422,'Use certificate/resume PDF downloads for binary files.')
                    result={'fileName':name,'content':raw.decode('utf-8')}
                else:
                    content=json.dumps(safe(current.roadmap),ensure_ascii=False,indent=2) if row['toolName']=='workspace.exportRoadmap' else args['content']
                    result=await run_in_threadpool(workspace.write,sid,name,content.encode('utf-8'))
            validated=Result(status='completed',actionId=action_id,toolName=row['toolName'],result=safe(result))
            await col('runtime_actions').update_one({'id':action_id,'studentId':sid},{'$set':{'status':'completed','result':validated.result,'completedAt':iso_now()}})
            await audit(sid,row['toolName'],'completed',current.stateVersion,action_id=action_id,approval='approved',risk=row['riskLevel'])
    except Exception as exc:
        # Consume before dispatch: never replay an uncertain side effect after a crash.
        await col('runtime_actions').update_one({'id':action_id,'studentId':sid},{'$set':{'status':'failed','errorCode':f'HTTP_{exc.status_code}' if isinstance(exc,HTTPException) else type(exc).__name__}})
        await audit(sid,row['toolName'],'failed',row['stateVersion'],action_id=action_id,approval='approved',risk=row['riskLevel'])
    completed=await col('runtime_actions').find_one({'id':action_id,'studentId':sid})
    await record_run_decision(completed)
    return public(completed)

async def record_run_decision(row):
    if not row.get('runId'):return
    from ..agents.proof import event,now,summary
    from ..agents.state import snapshot
    run=await col('agent_runs').find_one({'id':row['runId'],'studentId':row['studentId']})
    if not run:return
    await col('agent_tool_calls').update_one({'toolCallId':row['id']},{'$set':{'status':row['status'].upper(),
        'completedAt':now(),'resultSummary':summary(row.get('result',{})),'error':row.get('errorCode')}})
    await event(run,'approval.'+row['status'],'Approved action '+row['status']+'.')
    if row['status']=='completed':
        state=await snapshot(row['studentId'])
        await col('agent_runs').update_one({'id':run['id']},{'$set':{'stateVersionAfter':state.stateVersion},'$addToSet':{'changes':'Approved '+row['toolName']+' executed by the deterministic service.'}})
        await event(run,'state.updated','Approved action saved; current state version '+str(state.stateVersion)+'.')
