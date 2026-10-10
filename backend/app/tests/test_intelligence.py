"""Real Mongo/Chroma tests; Redis transport and provider responses are explicit doubles."""
import asyncio
import io
import json
from uuid import uuid4
from contextlib import asynccontextmanager
import pytest
from pydantic import ValidationError
from fastapi.testclient import TestClient
from pymongo import MongoClient
from reportlab.pdfgen import canvas
from app.main import app
from app.config import settings
from app.services import llm,openrouter
from app.workers import queue,tasks
from app.providers.base import Generation,ProviderError
from app.brain.schemas import Advisory,ResumeExtraction,JobRequest
from app.brain.orchestrator import validate_citations
from app.rag.ingestion import parse,validate_file
from app.rag.store import store


class LockTransportDouble:
    @asynccontextmanager
    async def lock(self,*args,**kwargs):yield


def test_brain_repairs_fabricated_citations_without_changing_facts(monkeypatch):
    from types import SimpleNamespace
    from app.brain import orchestrator
    state=SimpleNamespace(readiness=42,mastery={},confidence={},careerGaps=[],xp=10,rank=2,
        stateVersion=3,profile={},targetCareer={'title':'AI Engineer'},competencies=[],
        evidence=[],roadmap=[],recommendations=[],resources=[])
    async def snapshot(_):return state
    async def retrieve(*_):return []
    prompts=[]
    async def model(prompt,*args,**kwargs):
        prompts.append(prompt)
        citations=[{'chunkId':'invented','quote':'Invented quote'}] if len(prompts)==1 else []
        return Advisory(intent='explain',summary='Review your next learning priority.',
            confidence=.5,citations=citations),Generation('','test','test-model',1,5),[]
    class Traces:
        async def insert_one(self,value):self.value=value
    traces=Traces()
    monkeypatch.setattr(orchestrator,'snapshot',snapshot)
    monkeypatch.setattr(orchestrator,'retrieve',retrieve)
    monkeypatch.setattr(orchestrator,'structured',model)
    monkeypatch.setattr(orchestrator,'col',lambda _:traces)
    result=asyncio.run(orchestrator.query('qa','What next?'))
    assert len(prompts)==2 and 'Repair failed provenance validation' in prompts[1]
    assert result['answer']['citations']==[] and result['sources']==[]
    assert result['facts']['readiness']==42 and result['facts']['xp']==10
    assert state.readiness==42 and state.xp==10


def test_parsing_and_schema_boundaries():
    # A retrieved document is not competency evidence. Never accept its chunk
    # identifier as a verified evidence reference, even with a valid quote.
    source={'id':'chunk-qa','text':'Attention combines value vectors.'}
    answer=Advisory(intent='explain',summary='Attention combines values.',confidence=.8,
        evidenceRefs=['chunk-qa'],citations=[{'chunkId':'chunk-qa','quote':source['text']}])
    with pytest.raises(ProviderError,match='invalid_evidence_reference'):
        validate_citations(answer,[source],[])
    answer.evidenceRefs=[]
    validate_citations(answer,[source],[])
    stream=io.BytesIO();pdf=canvas.Canvas(stream)
    pdf.drawString(40,740,'Transformers use attention to relate tokens in a sequence.');pdf.showPage()
    pdf.drawString(40,740,'Scaled dot-product attention divides logits by the square root of dimension.');pdf.save()
    assert validate_file('notes.pdf','application/pdf',stream.getvalue())=='pdf'
    pages=parse(stream.getvalue(),'pdf')
    assert len(pages)==2 and pages[1]['page']==2 and 'Scaled' in pages[1]['text']
    with pytest.raises(Exception):validate_file('bad.pdf','application/pdf',b'not a pdf')
    with pytest.raises(ValidationError):JobRequest(type='shell',requestId='12345678')
    with pytest.raises(ValidationError):Advisory(intent='gap',summary='a',confidence=.7,mastery=100)
    a=Advisory(intent='explain',summary='A',confidence=.8,citations=[{'chunkId':'owned','quote':'Attention computes values.'}])
    validate_citations(a,[{'id':'owned','text':'Attention computes values.'}],[])
    with pytest.raises(ProviderError):validate_citations(a,[{'id':'owned','text':'Unrelated text.'}],[])


def test_job_pipeline_isolation_and_failures(monkeypatch,tmp_path):
    monkeypatch.delenv('CHROMA_HOST',raising=False)
    monkeypatch.setenv('CHROMA_PATH',str(tmp_path/'chroma'));store.cache_clear()
    monkeypatch.setenv('ENABLE_CENTRAL_BRAIN','false')
    async def available():return True
    async def no_redis():raise ConnectionError('test transport unavailable')
    monkeypatch.setattr(llm,'is_available',available);monkeypatch.setattr(openrouter,'is_available',available)
    monkeypatch.setattr(queue,'connection',no_redis)
    assert settings.mongodb_db.endswith('_qa')
    db=MongoClient(settings.mongodb_uri)[settings.mongodb_db]
    with TestClient(app,backend_options={'loop_factory':asyncio.SelectorEventLoop}) as c:
        def user():return c.post('/api/v1/auth/register',json={'name':'Intelligence QA','email':uuid4().hex+'@example.com','password':'qa-secure-pass'}).json()
        u,v=user(),user();sid=u['student']['studentId'];h={'Authorization':'Bearer '+u['token']};other={'Authorization':'Bearer '+v['token']}
        assert c.get('/api/v1/jobs').status_code==401
        text=b'Transformers use self-attention to relate tokens. Attention computes a weighted sum of value vectors. The softmax normalizes attention weights. Positional encodings represent token order.'
        r=c.post('/api/v1/documents/upload',headers=h,data={'documentType':'textbook'},files={'file':('Transformers.txt',text,'text/plain')})
        assert r.status_code==202,r.text
        job=r.json();id=job['jobId'];assert job['status']=='Queued' and job['queueStatus']=='unavailable'
        assert c.get('/api/v1/jobs/'+id,headers=other).status_code==404
        assert c.post('/api/v1/jobs',headers=other,json={'type':'document_ingestion','inputRefs':job['inputRefs'],'requestId':uuid4().hex}).status_code==404
        c.portal.call(tasks.process_job,{'redis':LockTransportDouble()},id)
        done=c.get('/api/v1/jobs/'+id,headers=h).json();assert done['status']=='Completed',done
        assert done['progress']==100 and done['chunksDone']>0
        result=c.get('/api/v1/jobs/'+id+'/result',headers=h);assert result.status_code==200
        assert c.get('/api/v1/jobs/'+id+'/result',headers=other).status_code==404
        before=db.intelligenceResults.count_documents({'jobId':id})
        c.portal.call(tasks.process_job,{'redis':LockTransportDouble()},id)
        assert db.intelligenceResults.count_documents({'jobId':id})==before==1
        from app.rag.retrieval import retrieve
        matches=c.portal.call(retrieve,sid,'How do transformers use attention?',[])
        assert matches and all(m['studentId']==sid and m['page']==1 for m in matches)
        assert not c.portal.call(retrieve,v['student']['studentId'],'How do transformers use attention?',[])
        from app.brain import orchestrator
        async def grounded(prompt,schema,context,**kwargs):
            data=json.loads(context);source=data['sources'][0]
            answer=Advisory(intent='explain',summary='Attention relates tokens.',recommendations=[],evidenceRefs=[],
                citations=[{'chunkId':source['id'],'quote':source['text'][:70]}],confidence=.8)
            return answer,Generation('', 'test','test-model',1,10),[]
        monkeypatch.setattr(orchestrator,'structured',grounded)
        c.portal.call(orchestrator.query,sid,'Explain transformers and attention.',[])
        response=c.post('/api/v1/rag/query',headers=h,json={'question':'Explain transformers and attention.'})
        assert response.status_code==200,response.text
        assert response.json()['sources'][0]['documentId']==job['inputRefs'][0]
        absent=c.post('/api/v1/rag/query',headers=other,json={'question':'Explain transformers and attention.'}).json()
        assert absent['abstained'] and not absent['sources']
        # Model assertions never become skill verification or numeric mastery.
        nodes_before=c.get('/api/v1/state',headers=h).json()['competencies']
        async def resume_model(prompt,schema,context,**kwargs):
            return ResumeExtraction(summary='Python claim',claims=[{'text':'Python','quote':'Python developer','skillId':'prog-python-advanced'}],projects=[]),Generation('','test','test-model',1,10),[]
        monkeypatch.setattr(tasks,'structured',resume_model)
        resume=c.post('/api/v1/resume/analyze',headers=h,json={'text':'Summary\nPython developer\nEducation\nStudent','background':True}).json()
        c.portal.call(tasks.process_job,{'redis':LockTransportDouble()},resume['jobId'])
        outcome=c.get('/api/v1/jobs/'+resume['jobId'],headers=h).json();assert outcome['status']=='Completed',outcome
        ev=list(db.evidence.find({'studentId':sid,'documentId':resume['inputRefs'][0]}))
        assert ev and all(e['verificationState']=='Unverified' for e in ev)
        after=c.get('/api/v1/state',headers=h).json()
        # Preserve the existing deterministic self-report policy exactly; it can
        # display claimed familiarity, but never a Verified competency.
        plain=c.post('/api/v1/resume/analyze',headers=other,json={'text':'Summary\nPython developer\nEducation\nStudent'}).json()['state']
        assert [n['mastery'] for n in after['competencies']]==[n['mastery'] for n in plain['competencies']]
        assert all(n['state']!='Verified' for n in after['competencies'])
        # A parsing failure stays failed, is retriable, and has no completed result.
        bad=c.post('/api/v1/documents/upload',headers=h,files={'file':('bad.pdf',b'%PDF-1.4\ninvalid','application/pdf')}).json()
        c.portal.call(tasks.process_job,{'redis':LockTransportDouble()},bad['jobId'])
        assert c.get('/api/v1/jobs/'+bad['jobId'],headers=h).json()['status']=='Failed'
        assert c.get('/api/v1/jobs/'+bad['jobId']+'/result',headers=h).status_code==409
        retried=c.post('/api/v1/jobs/'+bad['jobId']+'/retry',headers=h).json();assert retried['retryCount']==1 and retried['status']=='Queued'
        assert c.post('/api/v1/jobs/'+bad['jobId']+'/cancel',headers=h).json()['status']=='Cancelled'
        c.portal.call(tasks.process_job,{'redis':LockTransportDouble()},bad['jobId'])
        assert c.get('/api/v1/jobs/'+bad['jobId'],headers=h).json()['status']=='Cancelled'
        assert c.get('/health/intelligence').json()['workers']=='unavailable'
    db.client.close();store.cache_clear()


def test_worker_and_dispatch_share_queue_configuration(monkeypatch):
    monkeypatch.setenv('REDIS_URL','redis://127.0.0.1:6379/0')
    redis=queue.redis_settings()
    assert (redis.host,redis.port,redis.database)==('127.0.0.1',6379,0)
    assert tasks.WorkerSettings.queue_name==queue.QUEUE=='nexvora:intelligence'
    assert tasks.WorkerSettings.functions==[tasks.process_job]
