import asyncio
from copy import deepcopy
from io import BytesIO
from pathlib import Path
from uuid import uuid4
from zipfile import ZipFile
from xml.etree import ElementTree as ET
from fastapi.testclient import TestClient
from pymongo import MongoClient
from pypdf import PdfReader
from app.main import app
from app.config import settings
from app.services import llm, openrouter
from app.services.resume_generator import factual_rewrite


def test_resume_workspace(monkeypatch):
    async def available():return True
    async def plan(*args,**kwargs):return {'rewrites':{'profile:education':'Invented NASA internship 99%'},'text':'Invented Google employee 99%'}
    monkeypatch.setattr(llm,'is_available',available)
    monkeypatch.setattr(openrouter,'is_available',available)
    monkeypatch.setattr(llm,'extract_json',plan)
    assert settings.mongodb_db.endswith('_qa')
    db=MongoClient(settings.mongodb_uri)[settings.mongodb_db]
    with TestClient(app,backend_options={'loop_factory':asyncio.SelectorEventLoop}) as c:
        def register():return c.post('/api/v1/auth/register',json={'name':'Resume QA Student','email':uuid4().hex+'@example.com','password':'qa-secure-pass'}).json()
        user=register();sid=user['student']['studentId'];auth={'Authorization':'Bearer '+user['token']}
        db.profiles.update_one({'studentId':sid},{'$set':{'degree':'BSc Computer Science','institution':'Example University','priorExperience':'Unsupported employer'}})
        base='/api/v1/resume'
        assert c.get(base+'/drafts').status_code==401
        ctx=c.get(base+'/generator/context',headers=auth).json()
        r=c.post(base+'/generate',headers=auth,json={'targetRole':ctx['careerId'],'studentContext':{'name':'Spoof','skills':['FakeSkill']}})
        assert r.status_code==200,r.text
        d=r.json();assert d['name']=='Resume QA Student'
        assert 'Invented' not in str(d) and 'FakeSkill' not in str(d) and 'Unsupported employer' not in str(d)
        assert d['exportReady'] and db.resumeDrafts.find_one({'draftId':d['draftId'],'studentId':sid})
        other=register();assert c.get(base+'/drafts/'+d['draftId'],headers={'Authorization':'Bearer '+other['token']}).status_code==404
        original=deepcopy(d)
        d['sections'][0]['blocks'][0]['text']='Senior Google employee with 99% improvement'
        checked=c.post(base+'/validate',headers=auth,json=d).json()
        assert checked['unsupportedClaims'] and not checked['exportReady']
        assert c.post(base+'/export/pdf',headers=auth,json=d).status_code==422
        d['sections'][0]['blocks'][0]['keepSelfReported']=True
        assert c.post(base+'/validate',headers=auth,json=d).json()['exportReady']
        d['headline']='Google CEO';assert not c.post(base+'/validate',headers=auth,json=d).json()['exportReady']
        d['headlineSelfReported']=True
        saved=c.post(base+'/drafts/save',headers=auth,json=d);assert saved.status_code==200,saved.text
        d=saved.json();assert d['version']==2
        assert c.post(base+'/drafts/save',headers=auth,json=original).status_code==409
        assert len(c.get(base+'/drafts/'+d['draftId']+'/versions',headers=auth).json())==2
        assert c.get(base+'/drafts/'+d['draftId'],headers=auth).json()['headline']=='Google CEO'
        out=Path('tmp/resume-qa');out.mkdir(parents=True,exist_ok=True)
        for template in ['Modern Professional','ATS Minimal','Technical Engineer']:
            d['template']=template
            pdf=c.post(base+'/export/pdf',headers=auth,json=d);assert pdf.status_code==200,pdf.text[:100] if not pdf.content.startswith(b'%PDF') else ''
            text=''.join(p.extract_text() for p in PdfReader(BytesIO(pdf.content)).pages)
            assert '[Self-reported]' in text and 'Resume QA Student' in text
            word=c.post(base+'/export/docx',headers=auth,json=d);assert word.status_code==200
            with ZipFile(BytesIO(word.content)) as z:
                xml=ET.fromstring(z.read('word/document.xml'));assert 'Google CEO' in ''.join(xml.itertext())
            (out/(template+'.pdf')).write_bytes(pdf.content);(out/(template+'.docx')).write_bytes(word.content)
        preview=c.post(base+'/export/preview',headers=auth,json=d);assert preview.status_code==200,preview.text[:200]
        (out/'preview.png').write_bytes(preview.content)
        edu=next(b for s in original['sections'] if s['id']=='education' for b in s['blocks'])
        improved=c.post(base+'/improve',headers=auth,json={**original,'blockId':edu['id']});assert improved.status_code==200,improved.text
        assert improved.json()['block']['text']==edu['text']
        regenerated=c.post(base+'/regenerate',headers=auth,json={**d,'sectionId':'education'});assert regenerated.status_code==200
        assert 'Invented' not in str(regenerated.json())
        assert db.evidence.count_documents({'studentId':sid})==0
    db.client.close()


def test_rewrite_cannot_invent_or_remove_qualifiers():
    for source,candidate in [('Python project','Python project with 99% accuracy'),('Assisted Python project','Led Python project'),('Learning Python','Python expert')]:
        assert factual_rewrite(source,candidate)==source

def test_evidence_revocation_and_role_scoring():
    from app.services.resume_generator import validate, fingerprint
    fact={'id':'skill:python','text':'Python','state':'VERIFIED','evidenceIds':['assessment-1']};fact['hash']=fingerprint(fact)
    block={'id':fact['id'],'text':'Python','state':'VERIFIED','sourceIds':[fact['id']],'keepSelfReported':False}
    doc={'headline':'AI Engineer candidate','sections':[{'id':'skills','blocks':[block]}]}
    base={**doc,'generatedContent':doc['sections'],'sourceHashes':{fact['id']:fact['hash']}}
    ctx={'targetRole':'AI Engineer','facts':[fact],'requirements':[{'name':'Python','weight':3}]}
    assert validate(doc,ctx,base)['evidenceCoverage']==100
    assert validate(doc,ctx,base)['targetRoleMatch']==100
    ctx['requirements']=[{'name':'Docker','weight':3}]
    assert validate(doc,ctx,base)['targetRoleMatch']==0
    ctx['facts']=[]
    checked=validate(doc,ctx,base)
    assert checked['evidenceCoverage']==0 and not checked['exportReady']
