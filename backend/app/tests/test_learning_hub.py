import asyncio,json
from io import BytesIO
from pathlib import Path
from uuid import uuid4
from fastapi.testclient import TestClient
from pypdf import PdfReader
from pymongo import MongoClient
from app.main import app
from app.config import settings
from app.seed.catalog import SKILLS,CAREERS
from app.services.learning_pdf import clean

TARGETS=['career-ai-engineer','career-ml-engineer','career-data-scientist','career-backend-engineer','career-cloud-engineer']

def test_five_target_objectives_complete_notes_and_cache():
    assert settings.mongodb_db.endswith('_qa')
    db=MongoClient(settings.mongodb_uri)[settings.mongodb_db]
    with TestClient(app,backend_options={'loop_factory':asyncio.SelectorEventLoop}) as c:
        r=c.post('/api/v1/auth/register',json={'name':'Learning QA','email':f'learning-{uuid4().hex}@example.com','password':'qa-secure-pass'})
        assert r.status_code==201
        auth={'Authorization':'Bearer '+r.json()['token']};sid=r.json()['student']['studentId'];base='/api/v1/learning-hub/'
        assert c.get(base+TARGETS[0]).status_code==401
        assert c.get(base+'unknown',headers=auth).status_code==404
        initial=c.get('/api/v1/state',headers=auth).json()['competencies']
        topic_sets=[]
        for career in TARGETS:
            r=c.get(base+career,headers=auth);assert r.status_code==200,r.text
            hub=r.json();ids={t['id'] for t in hub['topics']};topic_sets.append(ids)
            assert hub['notesReady'],hub['missingNotes']
            catalog=next(x for x in CAREERS if x['id']==career)
            assert {r[0] for r in catalog['requirements']}<=ids
            assert hub['coverage']['totalTopics']==len(ids)==hub['coverage']['readyTopics']
            assert sum(t['status']=='Recommended Next' for t in hub['topics'])==1
            for topic in hub['topics']:
                skill=next(x for x in SKILLS if x['id']==topic['id'])
                assert set(skill['prerequisites'])<=ids
                assert 2<=len(topic['textbooks'])<=4
                assert topic['videos'],topic['name']
                assert len({v['id'] for v in topic['videos']})==len(topic['videos'])
                for video in topic['videos']:
                    assert video['language']=='en' and 'YouTube' in video['source']
                    assert video['url']=='https://www.youtube.com/watch?v='+video['id']
                    assert video['views'] is None or isinstance(video['views'],int)
            notes=c.get(base+career+'/notes',headers=auth).json()
            assert {ch['id'] for ch in notes['chapters']}==ids
            for chapter in notes['chapters']:
                n=chapter['notes'];assert len(json.dumps(n).split())>=1300
                assert len(n['practice'])>=6 and len(n['interview'])>=4 and len(n['examples'])>=2
                assert all(isinstance(step,str) for step in n['flow'])
                assert set(chapter['concepts'])<={x['title'] for x in n['concepts']}
            response=c.get(base+career+'/pdf',headers=auth);assert response.status_code==200,response.text[:200]
            assert response.headers['content-type']=='application/pdf'
            pdf=PdfReader(BytesIO(response.content));assert len(pdf.pages)>=len(ids)*3
            text='\n'.join(page.extract_text() for page in pdf.pages)
            for topic in hub['topics']:assert clean(topic['name']) in text
            assert 'Practice solutions' in text and 'Contents' in text
            assert c.get(base+career+'/pdf',headers=auth).content==response.content
            out=Path('tmp/pdfs/learning');out.mkdir(parents=True,exist_ok=True);(out/(career+'.pdf')).write_bytes(response.content)
            print(career,len(ids),'topics',len(pdf.pages),'pages')
        assert len({frozenset(x) for x in topic_sets})==5
        assert c.get('/api/v1/state',headers=auth).json()['competencies']==initial
        topic=c.get(base+TARGETS[0]+'/pdf?topic_id=prog-python-advanced',headers=auth)
        assert topic.status_code==200 and len(PdfReader(BytesIO(topic.content)).pages)>=5
        assert c.get(base+TARGETS[2]+'/notes?topic_id=ops-iac',headers=auth).status_code==404
        assert db.learningPdfs.count_documents({'career':{'$in':TARGETS}})>=5
        assert db.learningTopics.count_documents({})>=len(set.union(*topic_sets))
        assert not db.evidence.find_one({'studentId':sid,'type':'Learning Notes'})
    db.client.close()

def test_incomplete_curriculum_never_publishes_complete_pdf(monkeypatch,tmp_path):
    from app.routers import learning_hub
    monkeypatch.setattr(learning_hub,'ASSETS',tmp_path)
    with TestClient(app,backend_options={'loop_factory':asyncio.SelectorEventLoop}) as c:
        r=c.post('/api/v1/auth/register',json={'name':'Missing Notes QA','email':f'missing-{uuid4().hex}@example.com','password':'qa-secure-pass'}).json()
        auth={'Authorization':'Bearer '+r['token']}
        hub=c.get('/api/v1/learning-hub/career-ai-engineer',headers=auth).json()
        assert not hub['notesReady'] and hub['missingNotes']
        assert c.get('/api/v1/learning-hub/career-ai-engineer/pdf',headers=auth).status_code==503


def test_live_mastery_status_and_video_cache(monkeypatch):
    from types import SimpleNamespace
    from app.routers import learning_hub
    from app.services import learning_videos
    from datetime import datetime,timezone,timedelta
    async def recalculate(*args,**kwargs):
        assert kwargs['persist'] is False
        return SimpleNamespace(readiness=67,competencies=[
            {'id':'math-linear-algebra','mastery':90,'targetLevel':80,'state':'Verified'},
            {'id':'prog-python-advanced','mastery':78,'targetLevel':90,'state':'In Progress'},
            {'id':'math-prob-stats','mastery':45,'targetLevel':80,'state':'In Progress'},
            {'id':'dl-transformers','mastery':20,'targetLevel':80,'state':'Prerequisite Gap','unmetPrerequisites':['dl-neural-networks']},
        ],milestones=[{'skillId':'prog-python-advanced','masteryTarget':90,'order':1,'reason':'Python is the next roadmap step.'}])
    async def no_network(ids):raise AssertionError('Fresh video cache must not fetch YouTube')
    monkeypatch.setattr(learning_videos,'refresh',no_network)
    db=MongoClient(settings.mongodb_uri)[settings.mongodb_db]
    db.learningVideos.update_many({},{'$set':{'lastCheckedAt':datetime.now(timezone.utc).isoformat()}})
    with TestClient(app,backend_options={'loop_factory':asyncio.SelectorEventLoop}) as c:
        registration=c.post('/api/v1/auth/register',json={'name':'Personalized QA','email':f'personalized-{uuid4().hex}@example.com','password':'qa-secure-pass'}).json()
        auth={'Authorization':'Bearer '+registration['token']}
        monkeypatch.setattr(learning_hub.state,'recalculate',recalculate)
        for _ in range(2):
            hub=c.get('/api/v1/learning-hub/career-ai-engineer',headers=auth).json()
            topics={t['id']:t for t in hub['topics']}
            assert hub['readiness']==67
            assert topics['math-linear-algebra']['status']=='Completed'
            assert topics['prog-python-advanced']['status']=='Recommended Next'
            assert topics['prog-python-advanced']['difficulty']=='Advanced'
            assert topics['math-prob-stats']['status']=='In Progress'
            assert topics['math-prob-stats']['difficulty']=='Intermediate'
            assert topics['dl-transformers']['status']=='Locked/Prerequisite'
            assert topics['dl-transformers']['difficulty']=='Beginner'
    assert learning_videos.expired({'lastCheckedAt':(datetime.now(timezone.utc)-timedelta(days=8)).isoformat()})
    assert not learning_videos.expired({'lastCheckedAt':datetime.now(timezone.utc).isoformat()})
    db.client.close()


def test_curriculum_rejects_cycles_and_incomplete_content():
    import pytest
    from fastapi import HTTPException
    from app.routers.learning_hub import closure
    from app.services.learning_content import valid_chapter
    with pytest.raises(HTTPException):closure([{'skillId':'a'}],{'a':{'prerequisites':['b']},'b':{'prerequisites':['a']}})
    with pytest.raises(HTTPException):closure([{'skillId':'missing'}],{})
    assert not valid_chapter({'concepts':[{'title':'A'}]},['A'])
