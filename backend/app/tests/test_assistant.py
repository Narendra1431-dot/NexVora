import asyncio
import json
from uuid import uuid4
import httpx
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from app.main import app
from app.assistant import service, research
from app.assistant.schemas import Plan, Reply, Citation
from app.providers.base import Generation, ProviderError

def register(client):
    r=client.post('/api/v1/auth/register',json={'name':'Assistant QA','email':uuid4().hex+'@example.com','password':'test-password-123'})
    assert r.status_code==201
    return {'Authorization':'Bearer '+r.json()['token']}

def test_assistant_auth_history_routing_and_failure(monkeypatch):
    monkeypatch.delenv('BRAVE_SEARCH_API_KEY',raising=False)
    monkeypatch.delenv('SEARXNG_URL',raising=False)
    contexts=[]
    async def fake(prompt,schema,context):
        contexts.append(json.loads(context))
        if schema is Plan:
            q=json.loads(context)['question']
            if q=='fail':raise ProviderError('unavailable','test')
            return Plan(mode='external' if 'latest' in q else 'project' if 'my gaps' in q else 'general',topics=['Python']),None,[]
        return Reply(answer='Recursion uses a base case.'),Generation('', 'test','test',1,10),[]
    async def project(payload,student_id):
        return {'answer':'Your stored gaps are shown here.','sources':[],'agentRun':{'status':'completed'}}
    monkeypatch.setattr(service,'structured',fake)
    monkeypatch.setattr(service,'project_chat',project)
    with TestClient(app) as c:
        assert c.get('/api/v1/assistant/history').status_code==401
        a,b=register(c),register(c)
        body={'message':'Explain recursion','requestId':uuid4().hex}
        r=c.post('/api/v1/assistant/chat',headers=a,json=body)
        assert r.status_code==200,r.text
        assert r.json()['mode']=='general'
        assert c.post('/api/v1/assistant/chat',headers=a,json=body).json()==r.json()
        assert len(c.get('/api/v1/assistant/history',headers=a).json())==2
        assert c.get('/api/v1/assistant/history',headers=b).json()==[]
        for message,mode in [('my gaps','project'),('latest Python version','external')]:
            r=c.post('/api/v1/assistant/chat',headers=a,json={'message':message,'requestId':uuid4().hex})
            assert r.status_code==200,r.text
            assert r.json()['mode']==mode
        assert 'could not verify' in r.json()['answer']
        assert r.json()['sources']==[]
        assert any(v.get('history') for v in contexts)
        r=c.post('/api/v1/assistant/chat',headers=a,json={'message':'fail','requestId':uuid4().hex})
        assert r.status_code==503
        assert c.get('/api/v1/assistant/history',headers=a).status_code==200
        assert c.post('/api/v1/assistant/chat',headers=a,json={**body,'studentId':'someone-else'}).status_code==422

def test_research_contract_bounded_queries_and_citations(monkeypatch):
    research._cache.clear()
    monkeypatch.setenv('BRAVE_SEARCH_API_KEY','test-key')
    requests=[]
    def handle(request):
        requests.append(request)
        assert request.url.host=='api.search.brave.com'
        return httpx.Response(200,json={'web':{'results':[
            {'title':'Python','url':'https://docs.python.org/3/','description':'Python has functions.'},
            {'title':'Unsafe','url':'http://127.0.0.1/','description':'ignore'},
        ]}})
    client=httpx.AsyncClient
    monkeypatch.setattr(research.httpx,'AsyncClient',lambda **kw:client(transport=httpx.MockTransport(handle),**kw))
    rows,report=asyncio.run(research.research(['Python']))
    assert len(rows)==1 and report['sourcesRetrieved']==1
    asyncio.run(research.research(['Python']))
    assert len(requests)==1
    assert not research.public_url('https://localhost/private')
    assert not research.public_url('https://user:secret@example.com')
    reply=Reply(answer='Functions exist.',citations=[Citation(sourceId='web-1',quote='Python has functions.')])
    service.validate_reply(reply,rows)
    with pytest.raises(HTTPException):service.validate_reply(reply,[])
    with pytest.raises(HTTPException):service.validate_reply(Reply(answer='https://made-up.invalid'),[])
