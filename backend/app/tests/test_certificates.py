"""Real MongoDB issuance and public verification, isolated QA database only."""
import asyncio
from uuid import uuid4
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from pathlib import Path
from fastapi.testclient import TestClient
from pypdf import PdfReader
from pymongo import MongoClient
from app.main import app
from app.config import settings
from app.seed.assessments import ASSESSMENTS
from app.engine.state import evidence_index


def test_certificate_journey(monkeypatch):
    monkeypatch.setenv('CERTIFICATE_PAYMENT_MODE','demo')
    monkeypatch.setenv('PUBLIC_APP_URL','http://localhost:5000')
    assert settings.mongodb_db.endswith('_qa')
    db=MongoClient(settings.mongodb_uri)[settings.mongodb_db]
    with TestClient(app, backend_options={'loop_factory': asyncio.SelectorEventLoop}) as client:
        register=client.post('/api/v1/auth/register',json={'name':'Certificate QA Learner','email':f'certificate-{uuid4().hex}@example.com','password':'qa-secure-pass'})
        assert register.status_code==201,register.text
        auth={'Authorization':'Bearer '+register.json()['token']}
        sid=register.json()['student']['studentId']
        cid='res-python-typing';base='/api/v1/certificates'
        assert client.get(base).status_code==401
        check=lambda:client.get(base+'/eligibility/'+cid,headers=auth).json()
        assert not check()['eligible']
        assert client.post(base+'/generate',json={'courseId':cid},headers=auth).status_code==409
        assert client.post('/api/v1/resources/'+cid+'/action',json={'completed':True},headers=auth).status_code==200
        required=check()['assessments'][0]['id'];a=next(a for a in ASSESSMENTS if a['id']==required)
        assert client.post('/api/v1/assessments/'+required+'/attempts',json={'answers':{}},headers=auth).status_code==201
        assert not check()['eligible']
        answers={q['id']:q['correctAnswers'] for q in a['questions']}
        assert client.post('/api/v1/assessments/'+required+'/attempts',json={'answers':answers},headers=auth).status_code==201
        assert check()['eligible']
        counts=(db.certificates.count_documents({'studentId':sid}),db.evidence.count_documents({'studentId':sid}))
        preview=client.post(base+'/preview',json={'courseId':cid,'type':'premium','displayName':'Alex QA','displaySubtitle':'Learning journey'},headers=auth)
        assert preview.status_code==200 and preview.content.startswith(b'\x89PNG')
        assert counts==(db.certificates.count_documents({'studentId':sid}),db.evidence.count_documents({'studentId':sid}))
        for field,value in {'assessmentScore':100,'skills':['Fake'],'issuedAt':'2020-01-01','verificationStatus':'valid','courseName':'Fake','certificateId':'Fake'}.items():
            for endpoint in ('/preview','/generate'):
                assert client.post(base+endpoint,json={'courseId':cid,field:value},headers=auth).status_code==422
        before=client.get('/api/v1/state',headers=auth).json()['competencies']
        assert client.post(base+'/generate',json={'courseId':cid,'type':'premium'},headers=auth).status_code==402
        assert client.post(base+'/generate',json={'courseId':cid,'studentName':'Spoof'},headers=auth).status_code==422
        response=client.post(base+'/generate',json={'courseId':cid},headers=auth)
        assert response.status_code==200,response.text
        free=response.json(); certid=free['certificateId']
        assert free['publicUrl']=='http://localhost:5000/certificate/'+certid
        assert not set(free)&{'studentId','pdfBytes','evidenceIds','orderId','_id'}
        assert client.get(base+'/verify/'+certid).json()==free
        assert client.get(base+'/'+certid).json()==free
        pdf=client.get(free['pdfUrl']);assert pdf.status_code==200 and pdf.content.startswith(b'%PDF')
        reader=PdfReader(BytesIO(pdf.content));assert len(reader.pages)==1
        assert float(reader.pages[0].mediabox.width)>float(reader.pages[0].mediabox.height)
        assert 'Certificate QA Learner' in reader.pages[0].extract_text()
        assert b'<svg' in client.get(free['qrUrl']).content
        assert client.get(base+'/verify/invalid').status_code==404
        assert client.get(base+'/CIQ-'+'0'*32+'/pdf').status_code==404
        assert db.certificates.count_documents({'certificateId':certid})==1
        refs=list(db.evidence.find({'studentId':sid,'certificateId':certid}));assert len(refs)==1
        assert evidence_index(refs)=={} # no double-counted assessment or mastery credit
        after=client.get('/api/v1/state',headers=auth).json()['competencies']
        assert [(n['id'],n['mastery'],n['confidence']) for n in before]==[(n['id'],n['mastery'],n['confidence']) for n in after]
        with ThreadPoolExecutor(max_workers=3) as pool:
            duplicates=list(pool.map(lambda _:client.post(base+'/generate',json={'courseId':cid},headers=auth).json()['certificateId'],range(3)))
        assert duplicates==[certid]*3
        order=client.post(base+'/premium/create-order',json={'courseId':cid},headers=auth).json()
        assert order['mode']=='DEMO' and order['amount']==19900
        assert client.post(base+'/premium/confirm',json={'orderId':order['orderId']},headers=auth).status_code==422
        stranger=client.post('/api/v1/auth/register',json={'name':'Other learner','email':f'other-{uuid4().hex}@example.com','password':'qa-secure-pass'}).json()
        other={'Authorization':'Bearer '+stranger['token']}
        assert client.post(base+'/premium/confirm',json={'orderId':order['orderId'],'confirmDemo':True},headers=other).status_code==404
        assert client.post(base+'/generate',json={'courseId':cid,'type':'premium','orderId':order['orderId']},headers=other).status_code==409
        assert client.post(base+'/premium/confirm',json={'orderId':order['orderId'],'confirmDemo':True},headers=auth).status_code==200
        premium=client.post(base+'/generate',json={'courseId':cid,'type':'premium','orderId':order['orderId'],'displayName':'Alex QA','displaySubtitle':'Learning journey'},headers=auth).json()
        assert premium['type']=='premium' and premium['paymentStatus']=='demo_confirmed'
        assert premium['assessmentScore']==100
        blob=client.get(premium['pdfUrl']).content
        text=PdfReader(BytesIO(blob)).pages[0].extract_text()
        assert 'Alex QA' in text and 'Learning journey' in text
        assert premium['templateVersion']=='nexvora-premium-locked-v1'
        for disclaimer in ('DEMO / SAMPLE','DEMO PURCHASE','Sample issuer','sample only'):
            assert disclaimer not in text
        from app.services.certificate_pdf import pdf_preview
        assert client.get(base+'/'+premium['certificateId']+'/preview.png').content==pdf_preview(blob)
        Path('tmp/pdfs').mkdir(parents=True,exist_ok=True)
        Path('tmp/pdfs/premium-certificate-qa.png').write_bytes(pdf_preview(blob))
        assert len(client.get(base,headers=auth).json()['certificates'])==2
        assert not client.get(base,headers=other).json()['certificates']
        assert db.certificateOrders.find_one({'orderId':order['orderId']})['status']=='demo_confirmed'
        output=Path('tmp/pdfs');output.mkdir(parents=True,exist_ok=True)
        (output/'premium-certificate-qa.pdf').write_bytes(blob)
        (output/'free-certificate-qa.pdf').write_bytes(pdf.content)
        # A new unauthenticated client can resolve the persistent public ID.
    with TestClient(app, backend_options={'loop_factory': asyncio.SelectorEventLoop}) as public:
        assert public.get(base+'/verify/'+certid).json()['certificateId']==certid
    db.client.close()

def test_required_modules_and_unconfigured_payment(monkeypatch):
    monkeypatch.setenv('CERTIFICATE_PAYMENT_MODE','demo')
    assert settings.mongodb_db.endswith('_qa')
    db=MongoClient(settings.mongodb_uri)[settings.mongodb_db]
    course_id='certificate-qa-'+uuid4().hex
    with TestClient(app,backend_options={'loop_factory':asyncio.SelectorEventLoop}) as c:
        a=next(a for a in ASSESSMENTS if a['id']=='assess-python-baseline')
        db.resources.insert_one({'id':course_id,'title':'Module gated QA course','type':'Course','skillId':a['skillId'],'skillName':a['skillName'],'certificatePolicy':{'moduleIds':[course_id,'res-python-typing'],'assessmentIds':[a['id']],'completionRule':'all_modules_and_assessments'}})
        try:
            registered=c.post('/api/v1/auth/register',json={'name':'Module QA','email':f'module-{uuid4().hex}@example.com','password':'qa-secure-pass'}).json()
            headers={'Authorization':'Bearer '+registered['token']}
            check=lambda:c.get('/api/v1/certificates/eligibility/'+course_id,headers=headers).json()
            c.post('/api/v1/resources/'+course_id+'/action',json={'completed':True},headers=headers)
            c.post('/api/v1/assessments/'+a['id']+'/attempts',json={'answers':{q['id']:q['correctAnswers'] for q in a['questions']}},headers=headers)
            assert check()['completedModules']==1 and not check()['eligible']
            c.post('/api/v1/resources/res-python-typing/action',json={'completed':True},headers=headers)
            assert check()['eligible'] and check()['completedAt']
            db.resources.update_one({'id':course_id},{'$set':{'certificatePolicy.completionRule':'unknown_rule'}})
            assert not check()['eligible']
            db.resources.update_one({'id':course_id},{'$set':{'certificatePolicy.completionRule':'all_modules_and_assessments'}})
            monkeypatch.setenv('CERTIFICATE_PAYMENT_MODE','live')
            assert c.post('/api/v1/certificates/premium/create-order',json={'courseId':course_id},headers=headers).status_code==503
            monkeypatch.setenv('CERTIFICATE_PAYMENT_MODE','demo')
            order=c.post('/api/v1/certificates/premium/create-order',json={'courseId':course_id},headers=headers).json()
            db.certificateOrders.update_one({'orderId':order['orderId']},{'$set':{'expiresAt':'2000-01-01T00:00:00+00:00'}})
            assert c.post('/api/v1/certificates/premium/confirm',json={'orderId':order['orderId'],'confirmDemo':True},headers=headers).status_code==409
        finally: db.resources.delete_one({'id':course_id})
    db.client.close()

