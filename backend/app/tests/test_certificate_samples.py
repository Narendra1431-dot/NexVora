"""Samples use the production template without registry/evidence access."""
from io import BytesIO
from pathlib import Path
from fastapi.testclient import TestClient
from pypdf import PdfReader
from app.main import app
from app.routers import certificates

def test_sample_certificates_are_read_only(monkeypatch):
    def forbidden(*args,**kwargs): raise AssertionError('Sample preview must not access MongoDB')
    monkeypatch.setattr(certificates,'col',forbidden)
    client=TestClient(app)
    output=Path('tmp/pdfs');output.mkdir(parents=True,exist_ok=True)
    for tier in ('free','premium'):
        response=client.get('/api/v1/certificates/demo/'+tier+'/pdf')
        assert response.status_code==200
        assert 'DEMO-SAMPLE.pdf' in response.headers['content-disposition']
        pdf=PdfReader(BytesIO(response.content));assert len(pdf.pages)==1
        text=pdf.pages[0].extract_text()
        for expected in ('Alex Rivera','Machine Learning Foundations','DEMO-CERT-001','Sample Date','DEMO / SAMPLE','NexVora','Demo verification QR'):
            assert expected in text
        if tier=='premium':
            for expected in ('PREMIUM VERIFIED CERTIFICATE','88%','Python, ML, Model Evaluation'):assert expected in text
        else: assert 'STANDARD CERTIFICATE' in text
        assert any('/api/v1/certificates/demo/info' in str(ref.get_object()) for ref in pdf.pages[0]['/Annots'])
        image=client.get('/api/v1/certificates/demo/'+tier+'/preview.png')
        assert image.status_code==200 and image.content.startswith(b'\x89PNG')
        (output/('demo-'+tier+'.png')).write_bytes(image.content)
        (output/('demo-'+tier+'.pdf')).write_bytes(response.content)
    assert client.get('/api/v1/certificates/demo/info').json()['verificationStatus']=='sample_only'
    assert client.get('/api/v1/certificates/verify/DEMO-CERT-001').status_code==404
    assert client.get('/api/v1/certificates/demo/unknown/pdf').status_code==422
