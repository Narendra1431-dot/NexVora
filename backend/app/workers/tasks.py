"""Finite typed workflows. Model output is stored as advice, never domain writes."""
import asyncio
import json
from contextvars import ContextVar
from datetime import datetime,timezone,timedelta
from fastapi.concurrency import run_in_threadpool
from pymongo import ReturnDocument
from ..db import col,ensure_database,ensure_indexes,close
from ..security import iso_now,new_id
from ..brain.schemas import ResumeExtraction
from ..brain.prompts import SYSTEM
from ..providers.router import structured
from ..providers.base import ProviderError
from ..rag import ingestion,chunking,embeddings
from ..rag.store import store
from .queue import recover,QUEUE,redis_settings,serialize,deserialize

IN_WORKER=ContextVar('intelligence_worker',default=False)

class Cancelled(Exception):pass

async def checkpoint(job,progress,stage,**values):
    current=await col('intelligence_jobs').find_one({'jobId':job['jobId']})
    if not current or current['status']=='Cancelled':raise Cancelled()
    await col('intelligence_jobs').update_one({'jobId':job['jobId'],'lease':job['lease'],'status':'Processing'},
        {'$set':{'progress':progress,'stage':stage,**values}})

async def index_document(job,doc):
    if doc.get('status')=='Ready':return doc
    await checkpoint(job,5,'Reading document')
    pages=doc.get('pages') or await run_in_threadpool(ingestion.parse,bytes(doc['data']),doc['extension'])
    await col('intelligence_documents').update_one({'id':doc['id'],'studentId':doc['studentId']},
        {'$set':{'pages':pages,'status':'Indexing'}})
    parts=chunking.chunks(pages,doc)
    if not parts:raise ValueError('No usable document text to index.')
    for offset in range(0,len(parts),32):
        batch=parts[offset:offset+32]
        await checkpoint(job,10+int(55*offset/len(parts)),f'Indexing material: {offset} / {len(parts)} chunks',chunksDone=offset,chunksTotal=len(parts))
        vectors=await run_in_threadpool(embeddings.embed,[c['text'] for c in batch])
        await run_in_threadpool(lambda:store().upsert(batch,vectors))
        for part in batch:
            await col('intelligence_chunks').update_one({'id':part['id']},{'$set':part},upsert=True)
    await checkpoint(job,68,'Material indexed',chunksDone=len(parts),chunksTotal=len(parts))
    await col('intelligence_documents').update_one({'id':doc['id'],'studentId':doc['studentId']},
        {'$set':{'status':'Ready','chunkCount':len(parts),'indexedAt':iso_now()}})
    return {**doc,'pages':pages,'status':'Ready'}

async def resume_workflow(job,doc):
    text='\n'.join(p['text'] for p in doc['pages'])
    if len(text)>100000:raise ValueError('Resume exceeds 100,000 characters. Use learning-material upload for books.')
    skills=[{'id':s['id'],'name':s['name']} async for s in col('skills').find({})]
    await checkpoint(job,72,'Identifying resume claims')
    extraction,model,attempts=await structured(SYSTEM+' Extract resume claims and project names. Each claim must contain a verbatim quote and a skillId from the catalog. Extracted claims are NOT verified.',
        ResumeExtraction,json.dumps({'resume':text,'skills':skills}),background=True)
    valid_ids={s['id'] for s in skills}
    if any(c.quote not in text or c.skillId not in valid_ids for c in extraction.claims):
        raise ProviderError('invalid_resume_provenance','validator')
    await checkpoint(job,80,'Cross-checking evidence',provider=model.provider,model=model.model,fallbackAttempts=attempts)
    from ..agents.state import snapshot
    s=await snapshot(job['studentId'])
    claims=[]
    for claim in extraction.claims:
        matches=[e for e in s.evidence if e.get('skillId')==claim.skillId and e.get('type')!='Resume Claim']
        verified=[e for e in matches if e.get('verificationState')=='Verified']
        claims.append({**claim.model_dump(),'classification':'Supported' if verified else 'Self-Reported',
            'evidenceRefs':[e['id'] for e in verified],
            'note':'Independent evidence supports this skill; this resume statement itself is not verified.' if verified else 'Resume assertion only; assessment or project proof needed.'})
    # Only the existing domain service computes ATS, gaps, readiness and roadmap.
    from ..routers.documents import ingest
    await checkpoint(job,86,'Updating resume analysis and roadmap')
    current=await col('resume_analysis').find_one({'studentId':job['studentId']}) or {}
    newest=await col('intelligence_documents').find_one({'studentId':job['studentId'],'documentType':'resume'},sort=[('createdAt',-1)])
    if ((newest and newest['id']!=doc['id'] and newest['createdAt']>doc['createdAt']) or
        (current.get('documentId')!=doc['id'] and current.get('uploadedAtRaw','')>job['createdAt'])):
        await col('intelligence_jobs').update_one({'jobId':job['jobId'],'lease':job['lease']},
            {'$set':{'status':'Cancelled','stage':'Superseded by a newer resume','completedAt':iso_now()}})
        raise Cancelled()
    result=await ingest(text,doc['fileName'],job['studentId'],document_id=doc['id'])
    await col('intelligence_traces').insert_one({'requestId':job['requestId'],'jobId':job['jobId'],'studentId':job['studentId'],
        'provider':model.provider,'model':model.model,'latency':model.latency,'tokens':model.tokens,
        'status':'Completed','createdAt':iso_now(),'agent':'Resume Agent','stateVersion':s.stateVersion,
        'retrievedDocumentIds':[doc['id']]})
    return {'documentId':doc['id'],'domainDocumentId':result['documentId'],'claims':claims,
        'summary':extraction.summary,'projects':extraction.projects,'advisoryOnly':True,
        'provider':model.provider,'model':model.model}

PROMPTS={
 'career_gap_explanation':'Explain the current direct, prerequisite and evidence gaps using authoritative numeric facts.',
 'roadmap_generation':'Propose learning strategy and sequencing rationale for the deterministic roadmap. Do not alter its requirements.',
 'resource_enrichment':'Explain why the existing trusted resources match this student. Do not invent resources or links.',
 'assessment_generation':'Propose practice questions with explanations aligned to the weakest competencies. Label these practice only, not graded assessment items.',
 'project_recommendation':'Explain which existing projects address the most important evidence gaps and suggest a rubric.',
 'resume_generation':'Propose resume improvements using existing verified evidence, and distinguish self-reported statements. Do not invent achievements.',
 'certificate_description':'Draft an achievement description using existing certificate and evidence facts. Do not assert eligibility or issue a certificate.',
 'student_intelligence_refresh':'Summarize the latest learning priorities, gaps, and next action. Explain the deterministic roadmap.'}

async def perform(job):
    if job['type']=='agent_workflow':
        from ..agents.graph import execute
        await checkpoint(job,10,'Executing governed specialist graph')
        result=await execute(job['inputRefs'][0],job['studentId'])
        if result['status']=='FAILED':raise ProviderError('agent_workflow_failed','supervisor')
        if result['status']=='CANCELLED':
            await col('intelligence_jobs').update_one({'jobId':job['jobId']},{'$set':{'status':'Cancelled','stage':'Workflow cancelled','completedAt':iso_now()}})
            raise Cancelled()
        return result
    if job['type']=='resume_generation':
        from ..routers.resume_generator import Generate,generate
        profile=await col('profiles').find_one({'studentId':job['studentId']}) or {}
        await checkpoint(job,20,'Preparing evidence-backed resume draft')
        # Reuse the existing provenance validator and immutable draft versions.
        draft=await generate(Generate(targetRole=profile.get('targetCareerId','')),job['studentId'])
        await checkpoint(job,90,'Resume draft saved')
        return {'draftId':draft['draftId'],'summary':'Resume draft saved. Open Resume Intelligence to review it.',
                'version':draft['version'],'advisoryOnly':True}
    if job['type'] in ('resume_analysis','document_ingestion','embedding_generation','rag_index_update'):
        if not job['inputRefs']:raise ValueError('A document reference is required.')
        doc=await col('intelligence_documents').find_one({'id':job['inputRefs'][0],'studentId':job['studentId']})
        if not doc:raise ValueError('Owned document not found.')
        doc=await index_document(job,doc)
        if job['type']=='resume_analysis':return await resume_workflow(job,doc)
        return {'documentId':doc['id'],'status':'Ready','source':doc['fileName']}
    from ..brain.orchestrator import query
    await checkpoint(job,20,'Preparing your current learning context')
    result=await query(job['studentId'],PROMPTS[job['type']],job['inputRefs'],background=True,job_id=job['jobId'])
    await checkpoint(job,85,'Validating recommendations',provider=result.get('provider'),model=result.get('model'))
    return result

async def process_job(ctx,job_id):
    lease=new_id('lease')
    job=await col('intelligence_jobs').find_one_and_update({'jobId':job_id,'status':'Queued'},
        {'$set':{'status':'Processing','startedAt':iso_now(),'lease':lease,
                  'leaseUntil':(datetime.now(timezone.utc)+timedelta(minutes=31)).isoformat().replace('+00:00','Z')}},return_document=ReturnDocument.AFTER)
    if not job:return
    token=IN_WORKER.set(True)
    try:
        # Serialize jobs per student across processes, with a lease longer than
        # the worker timeout. ARQ is the only execution transport.
        async with ctx['redis'].lock('nexvora:student:'+job['studentId'],timeout=1860,blocking_timeout=5):
            result=await perform(job)
            await checkpoint(job,95,'Saving results')
            output_id='result-'+job_id
            await col('intelligence_results').update_one({'id':output_id,'studentId':job['studentId']},
                {'$set':{'jobId':job_id,'type':job['type'],'data':result,'createdAt':iso_now()}},upsert=True)
            updated=await col('intelligence_jobs').update_one({'jobId':job_id,'lease':lease,'status':'Processing'},
                {'$set':{'status':'Completed','progress':100,'stage':'Ready','completedAt':iso_now(),'outputRefs':[output_id],'error':None},'$unset':{'lease':''}})
            if updated.modified_count:
                await col('notifications').update_one({'studentId':job['studentId'],'id':'notification-'+job_id},
                    {'$setOnInsert':{'title':'Your resume analysis is ready' if job['type']=='resume_analysis' else 'Your learning intelligence is ready',
                        'description':'Open the background activity panel to view the result.','type':'success','read':False,
                        'createdAt':iso_now(),'linkTab':'resume' if job['type']=='resume_analysis' else 'resources'}},upsert=True)
    except Cancelled:pass
    except asyncio.CancelledError:
        await col('intelligence_jobs').update_one({'jobId':job_id,'status':'Processing','lease':lease},
            {'$set':{'status':'Queued','stage':'Interrupted; waiting to retry'},'$unset':{'lease':''}})
        raise
    except Exception as exc:
        # Exception messages may contain document contents or transport URLs.
        code=exc.code if isinstance(exc,ProviderError) else type(exc).__name__
        await col('intelligence_jobs').update_one({'jobId':job_id,'status':'Processing','lease':lease},
            {'$set':{'status':'Failed','stage':'Could not complete analysis','error':code,'completedAt':iso_now()},'$unset':{'lease':''}})
    finally:IN_WORKER.reset(token)

async def startup(ctx):
    await ensure_database();await ensure_indexes();await recover(ctx)

async def shutdown(ctx):await close()

from arq import cron
class WorkerSettings:
    job_serializer=staticmethod(serialize)
    job_deserializer=staticmethod(deserialize)
    functions=[process_job]
    cron_jobs=[cron(recover,second={0,20,40},run_at_startup=True)]
    on_startup=startup
    on_shutdown=shutdown
    redis_settings=redis_settings()
    queue_name=QUEUE
    max_jobs=3
    job_timeout=1800
    keep_result=0
    health_check_interval=15
    health_check_key=QUEUE+':health-check'
    log_results=False

if __name__=='__main__':
    from arq.worker import Worker
    # Windows event loops do not implement add_signal_handler.
    async def main():
        worker=Worker(**{k:getattr(WorkerSettings,k) for k in vars(WorkerSettings) if not k.startswith('_')},handle_signals=False)
        try:await worker.async_run()
        finally:await worker.close()
    asyncio.run(main())
