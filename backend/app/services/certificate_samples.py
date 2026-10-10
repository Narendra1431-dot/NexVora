"""Read-only sample documents: no persistence or eligibility side effects."""
from functools import lru_cache
import pymupdf
from .certificate_pdf import render_certificate

@lru_cache(maxsize=8)
def sample_pdf(tier: str, origin: str) -> bytes:
    return render_certificate({
        'certificateId':'DEMO-CERT-001','studentName':'Alex Rivera',
        'courseName':'Machine Learning Foundations','type':tier,
        'assessmentScore':88,'skills':['Python','ML','Model Evaluation'],
        'issuedAt':'Sample Date','completedAt':'Sample Date',
        'issuer':'NexVora Learning Platform','evidenceIds':[],
        'paymentStatus':'sample','publicUrl':origin+'/api/v1/certificates/demo/info',
        'achievementDescription':'Demonstration of the final certificate design. All displayed names, scores and skills are sample data.',
    },sample=True)

@lru_cache(maxsize=8)
def sample_png(tier: str, origin: str) -> bytes:
    with pymupdf.open(stream=sample_pdf(tier,origin),filetype='pdf') as doc:
        return doc[0].get_pixmap(matrix=pymupdf.Matrix(2,2)).tobytes('png')
