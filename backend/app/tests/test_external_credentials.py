import asyncio
import json
from io import BytesIO
from uuid import uuid4
from fastapi.testclient import TestClient
from pymongo import MongoClient
from reportlab.pdfgen.canvas import Canvas
from app.main import app
from app.config import settings
from app.seed.external_certifications import CATALOG

def test_external_credentials_persistence_permissions_and_review(monkeypatch):
    assert settings.mongodb_db.endswith('_qa')
    db = MongoClient(settings.mongodb_uri)[settings.mongodb_db]
    base='/api/v1/external-certifications'
    with TestClient(app,backend_options={'loop_factory':asyncio.SelectorEventLoop}) as c:
        def register():
            email=f'external-{uuid4().hex}@example.com'
            r=c.post('/api/v1/auth/register',json={'name':'External QA','email':email,'password':'qa-secure-pass'})
            assert r.status_code==201
            d=r.json();return {'Authorization':'Bearer '+d['token']},d['student']['studentId'],email
        auth,sid,_=register();other,_,review_email=register()
        from dataclasses import replace
        from app.routers import external_credentials
        monkeypatch.setattr(external_credentials,'settings',replace(settings,reviewer_emails=[review_email]))
        assert c.get(base).status_code==401
        listing=c.get(base,headers=auth).json();assert len(listing['catalog'])==13 and not listing['credentials']
        assert all(x['officialUrl'].startswith('https://') for x in listing['catalog'])
        original=c.get('/api/v1/state',headers=auth).json()['competencies']
        body={'certificationId':CATALOG[0]['id'],'credentialId':'AWS-QA-123','credentialUrl':'https://www.credly.com/badges/qa-test','issueDate':'2025-01-01','expiryDate':'2099-01-01'}
        stream=BytesIO();pdf=Canvas(stream);pdf.drawString(20,20,'QA external proof');pdf.save()
        def save(data=body,files=None,method='post',suffix='/credentials',headers=auth):
            return getattr(c,method)(base+suffix,data={'payload':json.dumps(data)},files=files,headers=headers)
        assert save({**body,'status':'Verified'}).status_code==422
        assert save({**body,'credentialUrl':'javascript:alert(1)'}).status_code==422
        assert save({**body,'issueDate':'2099-01-01','expiryDate':None}).status_code==422
        assert save({**body,'expiryDate':'2024-01-01'}).status_code==422
        assert save(files={'proof':('fake.pdf',b'<html>fake</html>','application/pdf')}).status_code==422
        assert save(files={'proof':('huge.pdf',b'%PDF-'+b'x'*(5*1024*1024),'application/pdf')}).status_code==413
        added=save(files={'proof':('proof.pdf',stream.getvalue(),'application/pdf')})
        assert added.status_code==201,added.text
        doc=added.json();id=doc['id'];assert doc['status']=='Added' and doc['hasProof']
        assert not {'proofBytes','studentId','review'}&doc.keys()
        assert save().status_code==409
        assert db.externalCredentials.count_documents({'studentId':sid})==1
        assert c.get(base+'/credentials/'+id+'/proof',headers=auth).content==stream.getvalue()
        assert c.get(base+'/credentials/'+id+'/proof',headers=other).status_code==404
        assert save(method='put',suffix='/credentials/'+id,headers=other).status_code==404
        review_url=base+'/credentials/'+id+'/review'
        payload={'decision':'Verified','note':'Checked the official provider credential registry and identity.'}
        assert c.post(review_url,json=payload,headers=auth).status_code==403
        assert c.post(review_url,json=payload,headers=other).json()['status']=='Verified'
        assert c.get(base,headers=auth).json()['credentials'][0]['status']=='Verified'
        updated=save({**body,'expiryDate':'2025-02-01'},method='put',suffix='/credentials/'+id)
        assert updated.status_code==200 and updated.json()['status']=='Expired'
        assert updated.json()['hasProof']
        assert c.post(review_url,json=payload,headers=other).json()['status']=='Expired'
        renewed=save(body,method='put',suffix='/credentials/'+id).json()
        assert renewed['status']=='Added' and renewed['id']==id
        refs=list(db.evidence.find({'studentId':sid,'externalCredentialId':id}))
        assert len(refs)==1 and refs[0]['verificationState']=='Unverified' and not refs[0].get('skillId')
        assert c.get('/api/v1/state',headers=auth).json()['competencies']==original
        assert not c.get(base,headers=other).json()['credentials']
        # New client proves registry persistence, with the same owner's credentials.
    with TestClient(app,backend_options={'loop_factory':asyncio.SelectorEventLoop}) as c:
        assert c.get(base,headers=auth).json()['credentials'][0]['id']==id
    db.client.close()
