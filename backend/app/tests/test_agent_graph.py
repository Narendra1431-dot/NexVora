"""Real Mongo + domain tools, with explicit model/queue transport doubles."""
import asyncio,json
from uuid import uuid4
import pytest,httpx
from fastapi.testclient import TestClient
from app.main import app
from app.agents import graph
from app.brain.schemas import Advisory
from app.providers.base import Generation,ProviderError
from app.workers import queue

def login(c):
    r=c.post('/api/v1/auth/register',json={'name':'Agent Graph QA','email':uuid4().hex+'@example.com','password':uuid4().hex})
    assert r.status_code==201
    return {'Authorization':'Bearer '+r.json()['token']},r.json()['student']['studentId']

def test_graph_proof_isolation_sse_and_approvals(monkeypatch,tmp_path):
    monkeypatch.setenv('NEXVORA_WORKSPACE',str(tmp_path))
    async def no_dispatch(*args,**kwargs):pass
    monkeypatch.setattr(queue,'dispatch',no_dispatch)
    async def model(prompt,schema,context,**kwargs):
        value=graph.Plan(intent='career_plan',agents=['profile','resume','career','rag','roadmap','resources']) if schema is graph.Plan else Advisory(intent='career_plan',summary='Review the recorded gaps and weekly proposal.',confidence=.8)
        return value,Generation('','test','test-model',1,10),[]
    monkeypatch.setattr(graph,'structured',model)
    with TestClient(app,backend_options={'loop_factory':asyncio.SelectorEventLoop}) as c:
        h,sid=login(c);other,_=login(c)
        payload={'message':'Analyze my resume and create my next learning plan.','requestId':uuid4().hex}
        r=c.post('/api/v1/agent/runs/run',headers=h,json=payload);assert r.status_code==202,r.text
        id=r.json()['id']
        assert c.post('/api/v1/agent/runs/run',headers=h,json=payload).json()['id']==id
        assert c.get('/api/v1/agent/runs/run/'+id,headers=other).status_code==404
        assert c.get('/api/v1/agent/runs/run/'+id+'/events',headers=other).status_code==404
        assert c.post('/api/v1/agent/runs/run/'+id+'/cancel',headers=other).status_code==404
        before=c.get('/api/v1/state',headers=h).json()
        c.portal.call(graph.execute,id,sid)
        detail=c.get('/api/v1/agent/runs/run/'+id,headers=h).json()
        assert detail['status']=='COMPLETED',detail
        assert detail['proof']['agentsExecuted']>=6 and detail['proof']['toolCalls']>=6
        assert all(t['status']=='COMPLETED' for t in detail['toolCalls'])
        assert all(s['startedAt']<=s['completedAt'] for s in detail['steps'])
        steps={s['id']:s for s in detail['steps']}
        for s in steps.values():
            for dep in s['dependencyIds']:assert steps[dep]['completedAt']<=s['startedAt']
        assert c.get('/api/v1/state',headers=h).json()['competencies']==before['competencies']
        events=c.get('/api/v1/agent/runs/run/'+id+'/events',headers=h)
        assert events.status_code==200 and 'tool.completed' in events.text and 'run.completed' in events.text
        assert 'text/event-stream' in events.headers['content-type']
        assert c.get('/api/v1/agent/runs/run/'+id+'/events?after=bad',headers=h).status_code==422
        action=c.post('/api/v1/agent/runs/run/'+id+'/roadmap-proposal',headers=h,json={}).json()
        assert action['status']=='pending_approval'
        rejected=c.post('/api/v1/agent/approvals/'+action['id'],headers=h,json={'decision':'reject'})
        assert rejected.json()['status']=='rejected'
        assert c.post('/api/v1/agent/approvals/'+action['id'],headers=h,json={'decision':'approve'}).status_code==409
        assert c.get('/api/v1/state',headers=h).json()['stateVersion']==before['stateVersion']
        report=c.post('/api/v1/agent/runs/run/'+id+'/report-proposal',headers=h,json={})
        assert report.status_code==200,report.text
        exported=c.post('/api/v1/agent/approvals/'+report.json()['id'],headers=h,json={'decision':'approve'})
        assert exported.json()['status']=='completed',exported.text
        artifacts=c.get('/api/v1/agent/runs/run/'+id,headers=h).json()['artifacts']
        assert len(artifacts)==1
        url='/api/v1/agent/runs/run/'+id+'/artifacts/'+artifacts[0]['artifactId']+'/download'
        assert c.get(url,headers=other).status_code==404
        download=c.get(url,headers=h)
        assert download.status_code==200 and '# NexVora learning analysis' in download.text
        assert c.post('/api/v1/agent/approvals/'+report.json()['id'],headers=h,json={'decision':'approve'}).status_code==409
        again=c.post('/api/v1/agent/runs/run',headers=h,json={**payload,'requestId':uuid4().hex}).json()
        cancelled=c.post('/api/v1/agent/runs/run/'+again['id']+'/cancel',headers=h,json={}).json()
        assert cancelled['status']=='CANCELLED'
        result=c.portal.call(graph.execute,again['id'],sid);assert result['status']=='CANCELLED'
        async def unavailable(*args,**kwargs):raise ProviderError('all_configured_providers_failed','test')
        monkeypatch.setattr(graph,'structured',unavailable)
        failed=c.post('/api/v1/agent/runs/run',headers=h,json={**payload,'requestId':uuid4().hex}).json()
        c.portal.call(graph.execute,failed['id'],sid)
        detail=c.get('/api/v1/agent/runs/run/'+failed['id'],headers=h).json()
        assert detail['status']=='FAILED' and detail['proof']['agentsExecuted']==0
        retry=c.post('/api/v1/agent/runs/run/'+failed['id']+'/retry',headers=h,json={**payload,'requestId':uuid4().hex})
        assert retry.status_code==202 and retry.json()['id']!=failed['id']

def test_agent_zero_boundary_and_contract(monkeypatch):
    from app.integrations.agent_zero.client import AgentZeroClient
    from app.integrations.agent_zero.security import public_url,require_isolation
    from app.integrations.agent_zero.result_parser import parse_result
    from fastapi import HTTPException
    monkeypatch.setenv('AGENT_ZERO_BASE_URL','http://127.0.0.1:5080')
    monkeypatch.setenv('AGENT_ZERO_API_KEY','test-only-credential')
    monkeypatch.delenv('AGENT_ZERO_EXECUTION_ENABLED',raising=False)
    with pytest.raises(HTTPException):require_isolation()
    for url in ['http://127.0.0.1/.env','https://169.254.169.254/','file:///etc/passwd','https://docs.python.org/?token=x','https://evil.example/']:
        with pytest.raises(HTTPException):public_url(url)
    def transport(request):
        assert request.headers['X-API-KEY']=='test-only-credential'
        assert request.url.path=='/api_message'
        body=json.loads(request.content);assert 'attachments' not in body and 'studentId' not in body
        return httpx.Response(200,json={'context_id':'owned-context','response':json.dumps({'title':'Python','summary':'Official documentation.','sourceUrl':'https://docs.python.org/','available':True})})
    result=asyncio.run(AgentZeroClient(httpx.MockTransport(transport)).submit('Read documentation.'))
    assert parse_result(result.response,'https://docs.python.org/').available
    with pytest.raises(HTTPException):parse_result(result.response,'https://aws.amazon.com/')
