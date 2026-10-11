"""Document ingestion and student-owned lifecycle operations."""
import io
import asyncio
from weakref import WeakValueDictionary
import re
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from pypdf import PdfReader
from ..config import settings
from ..db import col
from ..security import StudentId, new_id, iso_now
from ..engine import state
from .student import full_state
router = APIRouter(tags=['documents'])
class ResumeText(BaseModel):
    text: str = Field(min_length=1, max_length=100000)
    fileName: str = Field(default='Pasted resume.txt', max_length=200)
    background: bool = False

_upload_locks = WeakValueDictionary()

async def ingest(text, filename, student_id, document_id=None):
    lock = _upload_locks.setdefault(student_id, asyncio.Lock())
    async with lock:
        return await _ingest(text, filename, student_id, document_id)

async def _ingest(text, filename, student_id, document_id=None):
    if not text.strip(): raise HTTPException(422, 'No extractable text. Upload a text-based PDF or paste text.')
    text = text[:100000]
    from ..services.resume_parser import extract_sections
    parsed_sections = extract_sections(text)
    doc_id = document_id or new_id('doc')
    current = await col('resume_analysis').find_one({'studentId':student_id,'documentId':doc_id})
    if current:
        return {'documentId':doc_id,'state':await full_state(student_id)}
    await col('documents').update_one({'id':doc_id,'studentId':student_id},{'$setOnInsert':{'id': doc_id, 'studentId': student_id, 'fileName': filename, 'text': text, 'sections': parsed_sections, 'createdAt': iso_now()}},upsert=True)
    skills = [s async for s in col('skills').find({})]
    aliases = {'prog-python-advanced':['Python'],'data-sql-querying':['SQL'],'dl-pytorch':['PyTorch'],'data-numpy-pandas':['NumPy','Pandas'],'dl-rag-systems':['RAG'],'math-prob-stats':['Statistics','Probability'],'dl-transformers':['Transformers'],'prog-docker-containers':['Docker']}
    aliases.update({'prog-rest-apis':['REST API','REST APIs'],'prog-data-structures':['Data Structures'],'web-html-css':['HTML','CSS'],'web-typescript':['JavaScript','TypeScript'],'ml-model-evaluation':['model evaluation'],'ml-supervised':['supervised learning'],'ml-unsupervised':['unsupervised learning']})
    matched = [s for s in skills if any(re.search(r'(?<!\w)' + re.escape(name) + r'(?!\w)', text, re.I) for name in [s['name']] + aliases.get(s['id'], []))]
    for skill in matched:
        if await col('evidence').find_one({'studentId':student_id,'documentId':doc_id,'skillId':skill['id']}):continue
        names = [skill['name']] + aliases.get(skill['id'], [])
        source_section = next((section['name'] for section in parsed_sections if any(re.search(r'(?<!\w)' + re.escape(name) + r'(?!\w)',section['text'],re.I) for name in names)), 'unclassified')
        await state.add_evidence(student_id, {'id': new_id('ev'), 'title': f"Resume claim: {skill['name']}", 'documentId': doc_id, 'sourceSection': source_section, 'type': 'Resume Claim', 'skillId': skill['id'], 'skillName': skill['name'], 'verificationState': 'Unverified', 'quality': 'Low', 'confidenceScore': 35, 'date': iso_now()[:10], 'source': filename, 'provenance': f'Document {doc_id}; deterministic skill-name matching, not verification.', 'summary': next((line.strip()[:500] for line in text.splitlines() if any(re.search(r'(?<!\w)'+re.escape(name)+r'(?!\w)',line,re.I) for name in names)), skill['name'])})
    sections = list(dict.fromkeys(section['name'] for section in parsed_sections if section['name']!='unclassified'))
    await col('resume_analysis').update_one({'studentId': student_id}, {'$set': {'documentId': doc_id, 'fileName': filename, 'uploadedAt': iso_now(), 'uploadedAtRaw': iso_now(), 'parsedSections': parsed_sections, 'sectionsDetected': sections, 'extractedSkillsCount': len(matched), 'suggestedImprovements': ['Support each skill claim with an assessment or reviewed project.', 'ATS score is an explainable platform heuristic, not a third-party ATS result.']}, '$setOnInsert': {'createdAt': iso_now()}}, upsert=True)
    await state.recalculate(student_id)
    return {'documentId': doc_id, 'extractedSkills': [s['name'] for s in matched], 'sections': parsed_sections, 'state': await full_state(student_id)}

@router.post('/resume/analyze')
async def analyze(payload: ResumeText, student_id: str = StudentId):
    if payload.background:
        from ..workers.queue import enqueue
        id=new_id('material')
        await col('intelligence_documents').insert_one({'id':id,'studentId':student_id,'fileName':payload.fileName,'documentType':'resume','extension':'txt','data':payload.text.encode('utf-8'),'createdAt':iso_now(),'status':'Queued'})
        return await enqueue(student_id,'resume_analysis',[id],id)
    return await ingest(payload.text, payload.fileName, student_id)

@router.post('/documents/upload')
async def documents_upload(file: UploadFile = File(...), student_id: str = StudentId):
    """Upload and process a document for resume analysis (background job queue)."""
    suffix = (file.filename or '').lower().rsplit('.',1)[-1]
    if suffix not in {'pdf','txt','md'}: raise HTTPException(415, 'Upload PDF or UTF-8 TXT.')
    if file.content_type not in settings.allowed_upload_types and file.content_type not in {'application/octet-stream',''}: raise HTTPException(415, 'Upload PDF or plain text.')
    data = await file.read(settings.max_upload_bytes + 1)
    if len(data) > settings.max_upload_bytes: raise HTTPException(413, 'Upload exceeds 8 MB.')
    try:
        if suffix == 'pdf':
            if not data.startswith(b'%PDF-'): raise ValueError('Invalid PDF')
            reader = PdfReader(io.BytesIO(data))
            if len(reader.pages) > 100: raise ValueError('Too many pages')
            text = '\n'.join(p.extract_text() or '' for p in reader.pages)
        else: text = data.decode('utf-8')
    except Exception:
        raise HTTPException(422, 'Could not parse this document; upload a text-based PDF or UTF-8 text.')
    from ..workers.queue import enqueue
    id=new_id('material')
    await col('intelligence_documents').insert_one({'id':id,'studentId':student_id,'fileName':file.filename or 'resume','documentType':'resume','extension':suffix,'data':data,'createdAt':iso_now(),'status':'Queued'})
    job = await enqueue(student_id,'resume_analysis',[id],id)
    return JSONResponse(status_code=202, content=job)

@router.post('/documents')
async def documents(file: UploadFile = File(...), student_id: str = StudentId):
    suffix = (file.filename or '').lower().rsplit('.',1)[-1]
    if suffix not in {'pdf','txt','md'}: raise HTTPException(415, 'Upload PDF or UTF-8 TXT.')
    if file.content_type not in settings.allowed_upload_types and file.content_type not in {'application/octet-stream',''}: raise HTTPException(415, 'Upload PDF or plain text.')
    data = await file.read(settings.max_upload_bytes + 1)
    if len(data) > settings.max_upload_bytes: raise HTTPException(413, 'Upload exceeds 8 MB.')
    try:
        if suffix == 'pdf':
            if not data.startswith(b'%PDF-'): raise ValueError('Invalid PDF')
            reader = PdfReader(io.BytesIO(data))
            if len(reader.pages) > 100: raise ValueError('Too many pages')
            text = '\n'.join(p.extract_text() or '' for p in reader.pages)
        else: text = data.decode('utf-8')
    except Exception:
        raise HTTPException(422, 'Could not parse this document; upload a text-based PDF or UTF-8 text.')
    return await ingest(text, (file.filename or 'resume')[:200], student_id)

@router.post('/demo/reset')
async def reset(student_id: str = StudentId):
    user = await col('users').find_one({'studentId': student_id})
    if user['email'] != settings.demo_email: raise HTTPException(403, 'Reset is limited to the demo account.')
    for key in ['profiles', 'competencies', 'evidence', 'roadmaps', 'attempts', 'submissions', 'resume_analysis', 'documents', 'notifications', 'events', 'analytics', 'agent_runs']:
        await col(key).delete_many({'studentId': student_id})
    from ..seed.run import _seed_demo_student
    await _seed_demo_student()
    await state.recalculate(student_id)
    return {'ok': True}

@router.patch('/evidence/{evidence_id}')
async def edit_evidence(evidence_id: str, payload: ResumeText, student_id: str = StudentId):
    result = await col('evidence').update_one({'studentId': student_id, 'id': evidence_id, 'verificationState': 'Unverified'}, {'$set': {'summary': payload.text[:1000], 'updatedAt': iso_now()}})
    if not result.matched_count: raise HTTPException(404, 'Editable unverified evidence not found.')
    await state.recalculate(student_id)
    return {'ok': True}

@router.get('/analytics/overview')
async def analytics(student_id: str = StudentId):
    result = await state.recalculate(student_id, persist=False)
    return {'readiness': result.readiness, 'verifiedSkills': sum(c['state']=='Verified' for c in result.competencies), 'evidenceCount': len(result.evidence), 'nextAction': result.mission}


@router.get('/analytics/intelligence')
async def intelligence(student_id: str = StudentId):
    from ..ml.inference.advisory import summarize
    result = await state.recalculate(student_id, persist=False)
    profile = await col('profiles').find_one({'studentId':student_id}) or {}
    attempts = [a async for a in col('attempts').find({'studentId':student_id})]
    return summarize(result.competencies, result.evidence, profile, attempts)
