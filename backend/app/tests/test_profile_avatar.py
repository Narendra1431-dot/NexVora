import asyncio,base64,io
from uuid import uuid4
from fastapi.testclient import TestClient
from PIL import Image
from pymongo import MongoClient
from app.main import app
from app.config import settings
from app.agents.models import safe

def register(c):
    r=c.post('/api/v1/auth/register',json={'name':'Avatar QA','email':f'avatar-{uuid4().hex}@example.com','password':'qa-profile-password'});assert r.status_code==201
    return {'Authorization':'Bearer '+r.json()['token']},r.json()['student']['studentId']

def test_profile_fields_avatar_upload_and_persistence():
    assert settings.mongodb_db.endswith('_qa')
    with TestClient(app,backend_options={'loop_factory':asyncio.SelectorEventLoop}) as c:
        auth,sid=register(c);other,_=register(c)
        fields={'name':'Edited Learner','headline':'ML student','degree':'B.Tech','institution':'QA College','gpa':'8.6/10','gradYear':'2027','weeklyAvailabilityHours':12,'bio':'Learning applied ML','priorExperience':'Summer internship','academicDetails':'Computer science, year 3','learningPreferences':['Videos','Labs'],'readinessDisplayCareerId':'career-backend-engineer'}
        before=c.get('/api/v1/state',headers=auth).json()
        saved=c.patch('/api/v1/profile',headers=auth,json=fields);assert saved.status_code==200,saved.text
        state=c.get('/api/v1/state',headers=auth).json()
        assert all(state['profile'][key]==value for key,value in fields.items())
        assert state['profile']['targetCareerId']==before['profile']['targetCareerId']
        assert state['readiness']==before['readiness']
        for preset in ['student-1','student-2','coder-1','ai-2','hero-1','minimal-2','initials-1','scholar-2','explorer-2']:
            assert c.put('/api/v1/profile/avatar',headers=auth,json={'presetId':preset}).status_code==200
            assert c.get('/api/v1/state',headers=auth).json()['profile']['avatar']['presetId']==preset
        assert not c.get('/api/v1/state',headers=other).json()['profile'].get('avatar')
        for fmt,mime in [('JPEG','image/jpeg'),('PNG','image/png'),('WEBP','image/webp')]:
            image=Image.new('RGB',(600,400),'teal');output=io.BytesIO();image.save(output,fmt)
            r=c.post('/api/v1/profile/photo',headers=auth,files={'file':('photo',output.getvalue(),mime)});assert r.status_code==200,r.text
            avatar=r.json()['avatar'];assert avatar['kind']=='photo'
            normalized=Image.open(io.BytesIO(base64.b64decode(avatar['dataUrl'].split(',')[1])))
            assert normalized.size==(384,384) and normalized.format=='WEBP'
        db=MongoClient(settings.mongodb_uri)[settings.mongodb_db]
        assert db.profiles.find_one({'studentId':sid})['avatar']==avatar
        assert 'avatar' not in safe({'avatar':avatar,'name':'Safe'})
        assert c.delete('/api/v1/profile/avatar',headers=auth).status_code==200
        assert db.profiles.find_one({'studentId':sid})['avatar'] is None
        db.client.close()
        assert c.get('/api/v1/state',headers=auth).json()['profile']['avatar'] is None

def test_profile_avatar_validation_and_ownership():
    with TestClient(app,backend_options={'loop_factory':asyncio.SelectorEventLoop}) as c:
        auth,_=register(c)
        assert c.put('/api/v1/profile/avatar',json={'presetId':'student-1'}).status_code==401
        for payload in [{'name':'  '},{'weeklyAvailabilityHours':81},{'readiness':100},{'studentId':'other'},{'readinessDisplayCareerId':'fake'},{'learningPreferences':['a']*13}]:
            assert c.patch('/api/v1/profile',headers=auth,json=payload).status_code==422
        assert c.put('/api/v1/profile/avatar',headers=auth,json={'presetId':'untrusted-url'}).status_code==422
        assert c.patch('/api/v1/profile',headers=auth,json={'avatar':{'kind':'photo','dataUrl':'https://fake'}}).status_code==422
        assert c.post('/api/v1/profile/photo',headers=auth,files={'file':('bad.svg',b'<svg/>','image/svg+xml')}).status_code==415
        assert c.post('/api/v1/profile/photo',headers=auth,files={'file':('bad.png',b'not an image','image/png')}).status_code==422
        assert c.post('/api/v1/profile/photo',headers=auth,files={'file':('big.png',b'x'*(5*1024*1024+1),'image/png')}).status_code==413
