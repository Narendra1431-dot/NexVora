"""Owned external credentials. Uploads never establish mastery or verification."""
import json
from datetime import date, datetime, timezone
from typing import Literal
from fastapi import APIRouter, Form, File, UploadFile, HTTPException, Response
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator
from pymongo.errors import DuplicateKeyError
from ..db import col
from ..security import StudentId, new_id, iso_now, sanitize_url
from ..config import settings
from ..seed.external_certifications import CATALOG, BY_ID

router = APIRouter(prefix='/external-certifications', tags=['external-credentials'])
MAX_PROOF = 5 * 1024 * 1024

class CredentialIn(BaseModel):
    model_config = ConfigDict(extra='forbid')
    certificationId: str = Field(max_length=100)
    credentialId: str = Field(default='', max_length=200)
    credentialUrl: str = Field(default='', max_length=2000)
    issueDate: date
    expiryDate: date | None = None

    @field_validator('credentialId', 'credentialUrl')
    @classmethod
    def trim(cls, value): return value.strip()

    @model_validator(mode='after')
    def valid(self):
        if self.certificationId not in BY_ID: raise ValueError('Unknown certification.')
        self.credentialUrl = sanitize_url(self.credentialUrl)
        if self.issueDate > datetime.now(timezone.utc).date(): raise ValueError('Issue date cannot be in the future.')
        if self.expiryDate and self.expiryDate < self.issueDate: raise ValueError('Expiry date must follow issue date.')
        return self

def status(doc):
    if doc.get('expiryDate') and doc['expiryDate'] < datetime.now(timezone.utc).date().isoformat(): return 'Expired'
    return 'Verified' if doc.get('review', {}).get('decision') == 'Verified' else 'Added'

def safe(doc):
    return {**{k: doc.get(k) for k in ('id','certificationId','credentialId','credentialUrl','issueDate','expiryDate','createdAt','updatedAt','proofName')},
            'status': status(doc), 'reviewNote': doc.get('review', {}).get('note'), 'hasProof': bool(doc.get('proofName'))}

async def reference(doc):
    c = BY_ID[doc['certificationId']]
    state = 'Verified' if status(doc) == 'Verified' else 'Unverified'
    record = {'id': 'external-'+doc['id'], 'studentId': doc['studentId'], 'title': c['name'],
              'type': 'Certificate', 'verificationState': state, 'externalCredentialId': doc['id'],
              'source': doc['credentialUrl'] or c['officialUrl'], 'date': doc['issueDate'],
              'summary': f"External credential from {c['provider']}. Status: {status(doc)}. No automatic skill mastery credit.",
              'provenance': 'User-added external credential; verification requires an authorized independent review.',
              'quality': 'High' if state == 'Verified' else 'Low', 'confidenceScore': 0, 'updatedAt': iso_now()}
    await col('evidence').update_one({'studentId': doc['studentId'], 'id': record['id']}, {'$set': record}, upsert=True)

@router.get('')
async def listing(student_id: str = StudentId):
    records = [d async for d in col('external_credentials').find({'studentId': student_id}, {'proofBytes': 0}).sort('updatedAt', -1)]
    for doc in records: await reference(doc)
    return {'catalog': CATALOG, 'credentials': [safe(d) for d in records]}

async def proof_data(proof):
    if not proof or not proof.filename: return {}
    blob = await proof.read(MAX_PROOF + 1)
    if len(blob) > MAX_PROOF: raise HTTPException(413, 'Proof must be 5 MB or smaller.')
    mime = 'application/pdf' if blob.startswith(b'%PDF-') else 'image/png' if blob.startswith(b'\x89PNG\r\n\x1a\n') else 'image/jpeg' if blob.startswith(b'\xff\xd8\xff') else None
    if not mime: raise HTTPException(422, 'Upload a valid PDF, PNG or JPEG proof.')
    import pymupdf
    try:
        with pymupdf.open(stream=blob, filetype={'application/pdf':'pdf','image/png':'png','image/jpeg':'jpeg'}[mime]) as document:
            if not document.page_count or document.needs_pass: raise ValueError()
    except Exception: raise HTTPException(422, 'Proof is unreadable or password protected.')
    extension = {'application/pdf':'pdf','image/png':'png','image/jpeg':'jpg'}[mime]
    return {'proofBytes': blob, 'proofMime': mime, 'proofName': 'certificate-proof.'+extension}

async def save(payload, proof, student_id, existing=None):
    try: data = CredentialIn.model_validate_json(payload)
    except ValidationError: raise HTTPException(422, 'Check certification, credential URL, issue date and expiry date. Only credential details are editable.')
    upload = await proof_data(proof)
    if not (data.credentialId or data.credentialUrl or upload or (existing and existing.get('proofName'))):
        raise HTTPException(422, 'Provide a credential ID, credential URL or proof.')
    if existing and existing['certificationId'] != data.certificationId: raise HTTPException(422, 'Certification cannot be changed.')
    doc = {**(existing or {}), **data.model_dump(mode='json'), **upload,
           'id': existing['id'] if existing else new_id('credential'), 'studentId': student_id,
           'createdAt': existing['createdAt'] if existing else iso_now(), 'updatedAt': iso_now(), 'review': {}}
    try:
        if existing:
            await col('external_credentials').replace_one({'id': existing['id'], 'studentId': student_id}, doc)
        else: await col('external_credentials').insert_one(doc)
    except DuplicateKeyError: raise HTTPException(409, 'This certification is already added. Edit your saved credential to update or renew it.')
    await reference(doc)
    return safe(doc)

@router.post('/credentials', status_code=201)
async def create(payload: str = Form(..., max_length=5000), proof: UploadFile | None = File(None), student_id: str = StudentId):
    return await save(payload, proof, student_id)

async def owned(id, student_id):
    doc = await col('external_credentials').find_one({'id': id, 'studentId': student_id})
    if not doc: raise HTTPException(404, 'Credential not found.')
    return doc

@router.put('/credentials/{id}')
async def edit(id: str, payload: str = Form(..., max_length=5000), proof: UploadFile | None = File(None), student_id: str = StudentId):
    return await save(payload, proof, student_id, await owned(id, student_id))

@router.get('/credentials/{id}/proof')
async def download(id: str, student_id: str = StudentId):
    doc = await owned(id, student_id)
    if not doc.get('proofBytes'): raise HTTPException(404, 'No proof uploaded.')
    return Response(bytes(doc['proofBytes']), media_type=doc['proofMime'], headers={
        'Content-Disposition': 'attachment; filename="'+doc['proofName']+'"', 'X-Content-Type-Options':'nosniff', 'Cache-Control':'no-store'})

class ReviewIn(BaseModel):
    model_config = ConfigDict(extra='forbid')
    decision: Literal['Verified','Unverified']
    note: str = Field(min_length=10, max_length=2000)

@router.post('/credentials/{id}/review')
async def review(id: str, payload: ReviewIn, reviewer: str = StudentId):
    user = await col('users').find_one({'studentId': reviewer})
    if not user or user['email'].lower() not in settings.reviewer_emails: raise HTTPException(403, 'Authorized reviewer required.')
    doc = await col('external_credentials').find_one({'id': id})
    if not doc: raise HTTPException(404, 'Credential not found.')
    if doc['studentId'] == reviewer: raise HTTPException(403, 'You cannot verify your own credential.')
    doc['review'] = {**payload.model_dump(), 'reviewerId': reviewer, 'reviewedAt': iso_now()}
    result = await col('external_credentials').update_one({'id': id, 'updatedAt': doc['updatedAt']}, {'$set': {'review': doc['review'], 'updatedAt': iso_now()}})
    if not result.matched_count: raise HTTPException(409, 'Credential changed; review its latest details.')
    await reference(doc)
    return safe(doc)
