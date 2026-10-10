import asyncio
from uuid import uuid4
from fastapi.testclient import TestClient
from app.main import app

def test_approval_ownership_rejection_execution_and_confinement(monkeypatch,tmp_path):
    monkeypatch.setenv('NEXVORA_WORKSPACE',str(tmp_path))
    from app.services import llm,openrouter
    async def available():return True
    monkeypatch.setattr(llm,'is_available',available)
    monkeypatch.setattr(openrouter,'is_available',available)
    with TestClient(app,backend_options={'loop_factory':asyncio.SelectorEventLoop}) as c:
        def user():
            r=c.post('/api/v1/auth/register',json={'name':'Runtime QA','email':uuid4().hex+'@example.com','password':'qa-secure-pass'})
            assert r.status_code==201,r.text
            return {'Authorization':'Bearer '+r.json()['token']}
        h,o=user(),user()
        state=c.get('/api/v1/state',headers=h).json();version=state['stateVersion']
        def propose(tool,args={}):
            return c.post('/api/v1/agent/execute',headers=h,json={'toolName':tool,'requestId':uuid4().hex,'expectedStateVersion':version,'arguments':args})
        assert c.get('/api/v1/agent/approvals').status_code==401
        for bad in ('shell','read_secrets','connector.github_create_issue','computer.navigate','setMastery'):
            assert propose(bad).status_code==403
        for path in ('../outside.txt','.env','credentials.txt','C:\\secret.txt','notes.txt:stream','CON.txt','api-key.txt'):
            assert propose('workspace.write',{'fileName':path,'content':'no'}).status_code in (403,422)
        r=propose('workspace.write',{'fileName':'study.txt','content':'A reviewed study plan.'})
        assert r.status_code==200,r.text
        row=r.json();assert row['status']=='pending_approval'
        assert not list(tmp_path.rglob('*.txt'))
        url='/api/v1/agent/approvals/'+row['id']
        assert c.post(url,headers=o,json={'decision':'approve'}).status_code==404
        assert c.post(url,headers=h,json={'decision':'reject'}).json()['status']=='rejected'
        assert not list(tmp_path.rglob('*.txt'))
        assert c.post(url,headers=h,json={'decision':'approve'}).status_code==409
        row=propose('workspace.write',{'fileName':'study.txt','content':'A reviewed study plan.'}).json()
        url='/api/v1/agent/approvals/'+row['id']
        approved=c.post(url,headers=h,json={'decision':'approve'})
        assert approved.json()['status']=='completed',approved.text
        assert len(list(tmp_path.rglob('study.txt')))==1
        assert c.post(url,headers=h,json={'decision':'approve'}).status_code==409
        assert c.get('/api/v1/agent/approvals',headers=o).json()==[]
        events=c.get('/api/v1/agent/audit',headers=h).json()
        assert any(e['resultStatus']=='completed' and e['approvalStatus']=='approved' for e in events)
        assert not any('arguments' in e or 'studentId' in e for e in events)
        # Agent roadmap writes are now proposals; a rejection preserves domain truth.
        action={'action':'recomputeRoadmap','requestId':uuid4().hex,'expectedStateVersion':version}
        proposal=c.post('/api/v1/agent/execute',headers=h,json=action).json()
        assert proposal['status']=='pending_approval',proposal
        assert c.get('/api/v1/state',headers=h).json()['competencies']==state['competencies']
        c.post('/api/v1/agent/approvals/'+proposal['approval']['id'],headers=h,json={'decision':'reject'})
        assert c.get('/api/v1/state',headers=h).json()['stateVersion']==version
        # Copilot proposals are valid chat responses and support the single-line composer.
        chat=c.post('/api/v1/agent/chat',headers=h,json={'message':'/workspace write chat-note.txt "Study SQL"','requestId':uuid4().hex})
        assert chat.status_code==200,chat.text
        assert chat.json()['agentRun']['agentsUsed']==['Supervisor']
        assert chat.json()['approval']['status']=='pending_approval'
        assert not list(tmp_path.rglob('chat-note.txt'))
        approved=c.post('/api/v1/agent/approvals/'+chat.json()['approval']['id'],headers=h,json={'decision':'approve'})
        assert approved.json()['status']=='completed',approved.text
        assert list(tmp_path.rglob('chat-note.txt'))[0].read_text()=='Study SQL'
        health=c.get('/api/v1/health/agentic').json()
        assert health['computer']=='disabled' and health['meta']=='disabled'

def test_provider_policy_excludes_meta(monkeypatch):
    from app.providers.router import adapters
    monkeypatch.setenv('PRIMARY_LLM_PROVIDER','openrouter')
    monkeypatch.setenv('BACKGROUND_LLM_PROVIDER','openrouter')
    monkeypatch.setenv('FALLBACK_LLM_PROVIDER','meta,groq,ollama')
    assert [p.name for p in adapters()]==['openrouter','groq']
    assert [p.name for p in adapters(background=True)]==['openrouter','groq']
