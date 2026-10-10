"""JWT-scoped run snapshots and resumable SSE; no bearer tokens in URLs."""
import asyncio,json
from fastapi import APIRouter,Request,HTTPException,Query
from fastapi.responses import StreamingResponse,Response
from bson import ObjectId
from ..security import StudentId
from ..db import col
from ..agents import graph
from ..agents.proof import event,now,summary

router=APIRouter(prefix='/agent/runs',tags=['agent-execution-proof'])

@router.get('/run/tools')
async def tool_catalog(student_id:str=StudentId):
    from ..runtime.gateway import READ_TOOLS,MUTATIONS,WORKSPACE,definition,WorkspaceInput,ResumeExportInput,ReportInput,EmptyInput,Result
    from ..agents.models import ToolInput,ToolOutput,ExecuteInput
    schemas={c.__name__:c.model_json_schema() for c in (WorkspaceInput,ResumeExportInput,ReportInput,EmptyInput,Result,ExecuteInput)}
    reads=[{'toolName':name,'description':'Read owned canonical state or trusted knowledge through '+name,
        'riskLevel':'READ_ONLY','permissions':['student:self'],'inputSchema':ToolInput.model_json_schema(),
        'outputSchema':ToolOutput.model_json_schema(),'timeout':60,'auditRequired':True} for name in sorted(READ_TOOLS)]
    writes=[]
    for name in sorted(MUTATIONS|WORKSPACE|{'workspace.exportResume','workspace.exportAgentReport','generate_resume'}):
        d=definition(name)
        writes.append({'toolName':name,'description':'Propose '+name+'; approval and state-version validation are required.',
            'riskLevel':d['riskLevel'],'permissions':[d['requiredPermission']], 'inputSchema':schemas[d['inputSchema']],
            'outputSchema':Result.model_json_schema(),'timeout':60,'auditRequired':True})
    return {'tools':reads+writes,'unregisteredTools':'BLOCKED','computer':'disabled'}

@router.post('/run',status_code=202)
async def create_run(payload:graph.StartRun,student_id:str=StudentId):return await graph.create(payload,student_id)

@router.get('/run')
async def list_runs(student_id:str=StudentId):
    rows=[graph.public(r) async for r in col('agent_runs').find({'studentId':student_id,'kind':'execution_graph'}).sort('createdAt',-1).limit(50)]
    return rows

@router.get('/run/{run_id}')
async def run_detail(run_id:str,student_id:str=StudentId):
    run=await graph.owned(run_id,student_id)
    data=graph.public(run)
    for key,collection in [('steps','agent_steps'),('toolCalls','agent_tool_calls'),('artifacts','agent_artifacts')]:
        data[key]=[summary({k:v for k,v in r.items() if k not in {'_id','studentId'}}) async for r in col(collection).find({'runId':run_id,'studentId':student_id})]
    data['proof']={'agentsExecuted':sum(s['status']=='COMPLETED' for s in data['steps']),
        'toolCalls':len(data['toolCalls']),'sourcesRetrieved':len({ref for t in data['toolCalls'] for ref in t.get('sourceRefs',[])}),
        'approvals':await col('runtime_actions').count_documents({'runId':run_id,'studentId':student_id}),
        'durationMs':run.get('durationMs'),'stateVersionBefore':run['stateVersionBefore'],'stateVersionAfter':run.get('stateVersionAfter')}
    return data

@router.post('/run/{run_id}/retry',status_code=202)
async def retry_run(run_id:str,payload:graph.StartRun,student_id:str=StudentId):
    previous=await graph.owned(run_id,student_id)
    if previous['status'] not in ('FAILED','CANCELLED'):raise HTTPException(409,'Only failed or cancelled analysis can be retried.')
    if payload.message!=previous['userRequest']:raise HTTPException(422,'A retry must use the original request.')
    if previous.get('retryCount',0)>=2:raise HTTPException(409,'Retry limit reached; inspect the recorded failure.')
    result=await graph.create(payload,student_id)
    if result['id']==run_id:raise HTTPException(409,'Use a new request ID for retry.')
    await col('agent_runs').update_one({'id':result['id']},{'$set':{'retryOf':run_id,'retryCount':previous.get('retryCount',0)+1}})
    return result

@router.post('/run/{run_id}/cancel')
async def cancel_run(run_id:str,student_id:str=StudentId):
    run=await graph.owned(run_id,student_id)
    if run['status'] in ('COMPLETED','FAILED','CANCELLED'):raise HTTPException(409,'Run has already finished.')
    await col('agent_runs').update_one({'id':run_id,'status':{'$in':['QUEUED','RUNNING']}},{'$set':{'cancelRequested':True}})
    if run['status']=='QUEUED':
        changed=await col('agent_runs').update_one({'id':run_id,'status':'QUEUED'},{'$set':{'status':'CANCELLED','completedAt':now()}})
        if changed.modified_count:await event(run,'run.cancelled','Queued workflow cancelled.')
    await event(run,'run.cancel_requested','Cancellation requested; running tools stop at the next safe boundary.')
    return graph.public(await graph.owned(run_id,student_id))

@router.post('/run/{run_id}/roadmap-proposal')
async def propose_roadmap(run_id:str,student_id:str=StudentId):
    run=await graph.owned(run_id,student_id)
    if run['status']!='COMPLETED' or 'roadmap' not in run['selectedAgents']:raise HTTPException(409,'Complete the roadmap analysis first.')
    from ..runtime.gateway import propose,ToolRequest
    action=await propose(student_id,ToolRequest(toolName='planWeek',requestId='plan-'+run_id,expectedStateVersion=run['stateVersionAfter']))
    await col('runtime_actions').update_one({'id':action['id'],'studentId':student_id},{'$set':{'runId':run_id}})
    await col('agent_tool_calls').update_one({'toolCallId':action['id']},{'$setOnInsert':{'toolCallId':action['id'],
        'runId':run_id,'studentId':student_id,'agentName':'roadmap','stepId':run_id+'-roadmap','toolName':'planWeek',
        'riskLevel':'REQUIRES_APPROVAL','status':'WAITING_APPROVAL','approvalId':action['id'],'sourceRefs':[],
        'inputSummary':{'stateVersion':run['stateVersionAfter']}}},upsert=True)
    await event(run,'approval.required','Review the deterministic weekly-plan action in Approvals.')
    return action

@router.post('/run/{run_id}/report-proposal')
async def propose_report(run_id:str,student_id:str=StudentId):
    run=await graph.owned(run_id,student_id)
    from ..runtime.gateway import propose,ToolRequest
    from ..agents.state import snapshot
    state=await snapshot(student_id)
    action=await propose(student_id,ToolRequest(toolName='workspace.exportAgentReport',requestId='export-'+run_id,
        expectedStateVersion=state.stateVersion,arguments={'runId':run_id,'fileName':run_id+'.md'}))
    await col('runtime_actions').update_one({'id':action['id'],'studentId':student_id},{'$set':{'runId':run_id}})
    await event(run,'approval.required','Review the report export in Approvals.')
    await col('agent_tool_calls').update_one({'toolCallId':action['id']},{'$setOnInsert':{'toolCallId':action['id'],
        'runId':run_id,'studentId':student_id,'agentName':'Supervisor','stepId':None,'toolName':'workspace.exportAgentReport',
        'riskLevel':'REQUIRES_APPROVAL','status':'WAITING_APPROVAL','approvalId':action['id'],'sourceRefs':[],
        'inputSummary':{'runId':run_id}}},upsert=True)
    return action

@router.get('/run/{run_id}/artifacts/{artifact_id}/download')
async def download_artifact(run_id:str,artifact_id:str,student_id:str=StudentId):
    await graph.owned(run_id,student_id)
    artifact=await col('agent_artifacts').find_one({'artifactId':artifact_id,'runId':run_id,'studentId':student_id})
    if not artifact:raise HTTPException(404,'Artifact not found.')
    from ..runtime.workspace import read
    from fastapi.concurrency import run_in_threadpool
    content=await run_in_threadpool(read,student_id,artifact['storageRef'])
    return Response(content,media_type='text/markdown',headers={'Content-Disposition':'attachment; filename="'+artifact['name']+'"','Cache-Control':'no-store'})

@router.get('/run/{run_id}/events')
async def run_events(run_id:str,request:Request,after:str=Query(default='',max_length=24),student_id:str=StudentId):
    await graph.owned(run_id,student_id)
    cursor=request.headers.get('Last-Event-ID') or after
    if cursor and not ObjectId.is_valid(cursor):raise HTTPException(422,'Invalid event cursor.')
    async def stream():
        nonlocal cursor
        # Reconnect periodically so authentication is rechecked; no open-ended
        # connection with an expired session. Stored event IDs support replay.
        for _ in range(55):
            if await request.is_disconnected():return
            query={'runId':run_id,'studentId':student_id}
            if cursor:query['_id']={'$gt':ObjectId(cursor)}
            rows=[r async for r in col('agent_events').find(query).sort('_id',1).limit(100)]
            for row in rows:
                cursor=str(row.pop('_id'));row.pop('studentId',None)
                yield 'id: '+cursor+'\nevent: agent-event\ndata: '+json.dumps(summary(row))+'\n\n'
            state=await graph.owned(run_id,student_id)
            if state['status'] in ('COMPLETED','FAILED','CANCELLED') and len(rows)<100:
                yield 'event: stream-end\ndata: {}\n\n';return
            yield ': heartbeat\n\n'
            await asyncio.sleep(1)
    return StreamingResponse(stream(),media_type='text/event-stream',headers={'Cache-Control':'no-cache','X-Accel-Buffering':'no'})

@router.post('/approvals/{approval_id}/approve')
async def approve(approval_id:str,student_id:str=StudentId):
    from ..runtime.gateway import decide
    return await decide(student_id,approval_id,'approve')

@router.post('/approvals/{approval_id}/reject')
async def reject(approval_id:str,student_id:str=StudentId):
    from ..runtime.gateway import decide
    return await decide(student_id,approval_id,'reject')
