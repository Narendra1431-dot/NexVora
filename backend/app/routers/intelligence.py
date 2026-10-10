import hashlib
from typing import Literal
from fastapi import APIRouter,UploadFile,File,Form,HTTPException
from fastapi.concurrency import run_in_threadpool
from ..db import col,database
from ..security import StudentId,new_id,iso_now
from ..brain.schemas import JobRequest,Query
from ..brain.orchestrator import query
from ..providers.base import ProviderError
from ..providers.router import health as provider_health
from ..workers import queue
from ..rag.ingestion import validate_file

router=APIRouter(tags=['background-intelligence'])

async def owned_job(id,sid):
    job=await col('intelligence_jobs').find_one({'jobId':id,'studentId':sid})
    if not job:raise HTTPException(404,'Job not found.')
    return job

@router.post('/documents/upload',status_code=202)
async def upload(file:UploadFile=File(...),documentType:Literal['resume','textbook','manual','course','roadmap','certification','project']=Form('textbook'),
                 title:str=Form(''),subject:str=Form(''),student_id:str=StudentId):
    data=await file.read(8*1024*1024+1)
    name=(file.filename or 'document')[:200]
    extension=validate_file(name,file.content_type or 'application/octet-stream',data)
    id=new_id('material')
    await col('intelligence_documents').insert_one({'id':id,'studentId':student_id,'fileName':name,'documentType':documentType,
        'title':title[:200] or name,'subject':subject[:160],'extension':extension,'data':data,
        'sha256':hashlib.sha256(data).hexdigest(),'createdAt':iso_now(),'status':'Queued'})
    return await queue.enqueue(student_id,'resume_analysis' if documentType=='resume' else 'document_ingestion',[id],id)

@router.get('/documents/library')
async def library(student_id:str=StudentId):
    return [d async for d in col('intelligence_documents').find({'studentId':student_id},{'_id':0,'studentId':0,'data':0,'pages':0}).sort('createdAt',-1).limit(100)]

@router.post('/jobs',status_code=202)
async def submit(payload:JobRequest,student_id:str=StudentId):
    if payload.type=='agent_workflow':raise HTTPException(422,'Create governed workflows through /agent/runs.')
    for ref in payload.inputRefs:
        if not await col('intelligence_documents').find_one({'id':ref,'studentId':student_id}):raise HTTPException(404,'Owned document not found.')
    if payload.type in ('resume_analysis','document_ingestion','embedding_generation','rag_index_update') and len(payload.inputRefs)!=1:
        raise HTTPException(422,'This job requires one document reference.')
    profile=await col('profiles').find_one({'studentId':student_id}) or {}
    return await queue.enqueue(student_id,payload.type,payload.inputRefs,payload.requestId,state_version=profile.get('stateVersion',0))

@router.get('/jobs')
async def jobs(student_id:str=StudentId):
    return [queue.public(j) async for j in col('intelligence_jobs').find({'studentId':student_id}).sort('createdAt',-1).limit(30)]

@router.get('/jobs/{id}')
async def job(id:str,student_id:str=StudentId):return queue.public(await owned_job(id,student_id))

@router.get('/jobs/{id}/result')
async def result(id:str,student_id:str=StudentId):
    job=await owned_job(id,student_id)
    if job['status']!='Completed':raise HTTPException(409,'This job has no completed result.')
    value=await col('intelligence_results').find_one({'jobId':id,'studentId':student_id},{'_id':0,'studentId':0})
    if not value:raise HTTPException(404,'Result not found.')
    return value

@router.post('/jobs/{id}/cancel')
async def cancel(id:str,student_id:str=StudentId):
    await owned_job(id,student_id)
    changed=await col('intelligence_jobs').update_one({'jobId':id,'studentId':student_id,'status':'Queued'},
        {'$set':{'status':'Cancelled','stage':'Cancelled before processing','completedAt':iso_now()}})
    if not changed.modified_count:raise HTTPException(409,'Only queued work can be cancelled safely.')
    return queue.public(await owned_job(id,student_id))

@router.post('/jobs/{id}/retry',status_code=202)
async def retry(id:str,student_id:str=StudentId):
    await owned_job(id,student_id)
    changed=await col('intelligence_jobs').update_one({'jobId':id,'studentId':student_id,'status':'Failed','retryCount':{'$lt':3}},
        {'$set':{'status':'Queued','progress':0,'completedAt':None,'error':None},'$inc':{'retryCount':1}})
    if not changed.modified_count:raise HTTPException(409,'Only failed jobs with fewer than three retries can be retried.')
    value=await owned_job(id,student_id);await queue.dispatch(value)
    return queue.public(await owned_job(id,student_id))

@router.post('/brain/query')
async def brain(payload:Query,student_id:str=StudentId):
    try:return await query(student_id,payload.question,payload.documentIds)
    except ProviderError as exc:raise HTTPException(503,'AI reasoning unavailable: '+exc.code)
    except RuntimeError:raise HTTPException(503,'Knowledge retrieval is unavailable.')

async def rag(payload:Query,student_id:str=StudentId):
    try:return await query(student_id,payload.question,payload.documentIds,require_sources=True)
    except ProviderError as exc:raise HTTPException(503,'Grounded answer unavailable: '+exc.code)
    except RuntimeError:raise HTTPException(503,'Knowledge retrieval is unavailable.')

@router.get('/recommendations')
async def recommendations(student_id:str=StudentId):
    from .agent import recommendations as existing
    return await existing(student_id)

async def intelligence_health():
    providers=provider_health()
    for name in providers:
        latest=await col('intelligence_traces').find_one({'provider':name},sort=[('createdAt',-1)])
        if latest:
            providers[name]={**providers[name],'status':'healthy' if latest['status']=='Completed' else 'unavailable',
                'model':latest.get('model'),'errorCode':latest.get('errorCode')}
    transport=await queue.health()
    try:await database().command('ping');mongo='healthy'
    except Exception:mongo='unavailable'
    try:
        from ..rag.store import store
        vector=await run_in_threadpool(lambda:store().health())
    except Exception:vector={'status':'unavailable'}
    from ..providers.router import adapters
    selected=adapters()
    working=next((providers[p.name] for p in selected if providers.get(p.name,{}).get('status')=='healthy'),None)
    llama=bool(working and 'llama' in (working.get('model') or '').lower() and 'guard' not in working['model'].lower())
    brain_status=('healthy' if llama else 'degraded_non_llama_fallback') if working else 'unverified'
    return {'centralBrain':brain_status,'metaProvider':'disabled',
        'fallbackProvider':providers['groq']['status'],**transport,'rag':vector['status'] if vector.get('chunks') else 'no_indexed_material','vectorDb':vector['status'],
        'mongodb':mongo,'providers':providers,'vector':vector,'scores':'deterministic'}

@router.get('/intelligence/status')
async def runtime_status(student_id:str=StudentId):
    return await intelligence_health()
