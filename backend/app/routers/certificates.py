"""Server-owned eligibility and idempotent certificate issuance."""
import os
import secrets
from datetime import datetime, timezone, timedelta
from io import BytesIO
from typing import Literal
from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, ConfigDict, Field, field_validator
from pymongo.errors import DuplicateKeyError
import qrcode
import qrcode.image.svg
from ..db import col
from ..security import StudentId, iso_now
from ..engine import state as state_engine
from ..services.certificate_agent import prepare
from ..services.certificate_payment import payment_service
from ..services.certificate_pdf import render_certificate, pdf_preview

router=APIRouter(prefix='/certificates',tags=['certificates'])
SAFE=('certificateId','studentName','displaySubtitle','courseId','courseName','type','skills','assessmentScore','completedAt','issuedAt','verificationStatus','templateVersion','paymentStatus','issuer','achievementDescription','publicUrl','pdfUrl','qrUrl')
def public(doc):
    return {key:doc.get(key) for key in SAFE}
def base_url():
    return os.getenv('PUBLIC_APP_URL','http://localhost:5000').rstrip('/')

async def eligibility(student_id, course_id):
    course=await col('resources').find_one({'id':course_id,'type':'Course'})
    if not course: raise HTTPException(404,'Course not found.')
    profile=await col('profiles').find_one({'studentId':student_id})
    if not profile: raise HTTPException(404,'Student profile not found.')
    policy=course.get('certificatePolicy',{})
    modules=policy.get('moduleIds') or [course_id]
    assessment_ids=policy.get('assessmentIds')
    if assessment_ids is None:
        matching=[a async for a in col('assessments').find({'skillId':course.get('skillId')}).sort('id',1)]
        assessment_ids=[matching[0]['id']] if matching else []
    missing=[m for m in modules if not profile.get('resourceProgress',{}).get(m,{}).get('completed')]
    reasons=[]
    if missing: reasons.append('Complete all required modules.')
    if not assessment_ids: reasons.append('No qualifying assessment is configured for this course.')
    if policy.get('completionRule','all_modules_and_assessments')!='all_modules_and_assessments': reasons.append('Course completion rule is not supported.')
    completion_dates=[profile.get('resourceProgress',{}).get(m,{}).get('completedAt') or profile.get('resourceProgress',{}).get(m,{}).get('updatedAt','') for m in modules]
    proofs=[]; scores=[]; assessments=[]
    for aid in assessment_ids:
        assessment=await col('assessments').find_one({'id':aid})
        threshold=max(80,assessment.get('passingScore',80)) if assessment else 100
        attempt=await col('attempts').find_one({'studentId':student_id,'assessmentId':aid,'passed':True,'score':{'$gte':threshold}},sort=[('score',-1)])
        proof=await col('evidence').find_one({'studentId':student_id,'type':'Assessment','attemptId':attempt['id'],'verificationState':'Verified','superseded':{'$ne':True}}) if attempt else None
        passed=bool(assessment and attempt and proof)
        assessments.append({'id':aid,'title':assessment.get('title',aid) if assessment else aid,'passed':passed,'passingScore':threshold})
        if not passed: reasons.append('Pass the required assessment: '+assessments[-1]['title'])
        else:
            proofs.append(proof); scores.append(attempt['score']); completion_dates.append(attempt['createdAt'])
    derived=await state_engine.recalculate(student_id,profile=profile,persist=False)
    skill_ids={p['skillId'] for p in proofs}
    skills=[n['name'] for n in derived.competencies if n['id'] in skill_ids and n['state']=='Verified']
    projects=[e async for e in col('evidence').find({'studentId':student_id,'skillId':{'$in':list(skill_ids)},'type':'Project','verificationState':'Verified','superseded':{'$ne':True}})]
    return {'completedAt':max(completion_dates,default=''),'courseId':course_id,'courseName':course['title'],'eligible':not reasons,'reasons':reasons,'requiredModuleIds':modules,'completedModules':len(modules)-len(missing),'assessments':assessments,'completionRule':'all_modules_and_assessments','completionNote':'Course completion is recorded learning activity; only scored assessments and reviewed evidence verify skills.','skills':skills,'assessmentScore':round(sum(scores)/len(scores),1) if scores else None,'evidenceIds':[e['id'] for e in proofs+projects],'studentName':profile['name'],'skillId':course.get('skillId',''),'skillName':course.get('skillName','')}

class Personalization(BaseModel):
    displayName:str|None=Field(default=None,min_length=1,max_length=120)
    displaySubtitle:str=Field(default='',max_length=80)

    @field_validator('displayName','displaySubtitle')
    @classmethod
    def clean_display(cls,value,info):
        if value is None:return value
        value=' '.join(value.split())
        if info.field_name=='displayName' and not value:raise ValueError('Display name cannot be blank.')
        return value

class Generate(Personalization):
    model_config=ConfigDict(extra='forbid')
    courseId:str=Field(min_length=1,max_length=160)
    type:Literal['free','premium']='free'
    orderId:str|None=Field(default=None,max_length=160)
class Confirm(BaseModel):
    model_config=ConfigDict(extra='forbid')
    orderId:str=Field(min_length=1,max_length=160)
    confirmDemo:bool=False
class OrderIn(BaseModel):
    model_config=ConfigDict(extra='forbid')
    courseId:str=Field(min_length=1,max_length=160)

async def add_reference(doc):
    # Intentionally no skillId: this record references the already-counted proof,
    # rather than being another input to a skill's mastery/confidence formula.
    evidence={'id':'cert-'+doc['certificateId'],'studentId':doc['studentId'],'certificateId':doc['certificateId'],'courseId':doc['courseId'],'title':doc['courseName']+' certificate','type':'Certificate','skillId':'','skillName':'Course completion record','verificationState':'Verified','quality':'High','confidenceScore':0,'date':doc['issuedAt'][:10],'source':doc['issuer'],'provenance':'Registry-issued course certificate; underlying proof is linked, not counted again.','url':doc['publicUrl'],'summary':'Course completion and passing assessments recorded. No additional mastery awarded.','evidenceIds':doc['evidenceIds'],'assessmentIds':doc.get('assessmentIds',[])}
    await col('evidence').update_one({'studentId':doc['studentId'],'id':evidence['id']},{'$setOnInsert':evidence},upsert=True)

class PreviewIn(Personalization):
    model_config=ConfigDict(extra='forbid')
    courseId:str=Field(min_length=1,max_length=160)
    type:Literal['free','premium']='premium'

@router.post('/preview')
async def preview(payload:PreviewIn,student_id:str=StudentId):
    e=await eligibility(student_id,payload.courseId)
    if not e['eligible']:raise HTTPException(409,'; '.join(e['reasons']))
    doc={'certificateId':'Assigned on issuance','studentName':payload.displayName or e['studentName'],
         'displaySubtitle':payload.displaySubtitle,'courseName':e['courseName'],'type':payload.type,
         'assessmentScore':e['assessmentScore'],'issuedAt':'Assigned on issuance','completedAt':e['completedAt'],
         'paymentStatus':'preview','evidenceIds':e['evidenceIds'],**prepare(e,payload.type),
         'publicUrl':base_url()+'/api/v1/certificates/demo/info'}
    return Response(pdf_preview(render_certificate(doc,draft=True)),media_type='image/png',headers={'Cache-Control':'no-store','X-Content-Type-Options':'nosniff'})

@router.get('/demo/info')
async def sample_info():
    return {'demo':True,'verificationStatus':'sample_only','message':'DEMO / SAMPLE certificate. This is not an issued credential and has no verification or evidence record.'}

@router.get('/demo/{tier}/pdf')
async def sample_download(tier:Literal['free','premium']):
    from ..services.certificate_samples import sample_pdf
    return Response(sample_pdf(tier,base_url()),media_type='application/pdf',headers={'Content-Disposition':f'attachment; filename="NexVora-{tier}-DEMO-SAMPLE.pdf"','X-Content-Type-Options':'nosniff','Cache-Control':'no-store'})

@router.get('/demo/{tier}/preview.png')
async def sample_preview(tier:Literal['free','premium']):
    from ..services.certificate_samples import sample_png
    return Response(sample_png(tier,base_url()),media_type='image/png',headers={'X-Content-Type-Options':'nosniff','Cache-Control':'no-store'})

@router.get('')
async def listing(student_id:str=StudentId):
    docs=[d async for d in col('certificates').find({'studentId':student_id}).sort('issuedAt',-1)]
    for doc in docs: await add_reference(doc) # repairs an interrupted post-issuance reference write
    courses=[c async for c in col('resources').find({'type':'Course'}).sort('id',1)]
    entries=[]
    for course in courses:
        e=await eligibility(student_id,course['id'])
        entries.append({k:v for k,v in e.items() if k not in {'studentName','evidenceIds','skillId','skillName'}})
    return {'certificates':[public(d) for d in docs],'courses':entries,'payment':payment_service().create()}

@router.get('/eligibility/{course_id}')
async def check(course_id:str,student_id:str=StudentId):
    return await eligibility(student_id,course_id)

@router.post('/premium/create-order')
async def create_order(payload:OrderIn,student_id:str=StudentId):
    e=await eligibility(student_id,payload.courseId)
    if not e['eligible']: raise HTTPException(409, '; '.join(e['reasons']))
    if await col('certificates').find_one({'studentId':student_id,'courseId':payload.courseId,'type':'premium'}): raise HTTPException(409,'Premium certificate already issued.')
    order={'orderId':secrets.token_urlsafe(24),'studentId':student_id,'courseId':payload.courseId,'createdAt':iso_now(),'expiresAt':(datetime.now(timezone.utc)+timedelta(minutes=30)).isoformat(),**payment_service().create()}
    await col('certificate_orders').insert_one(order)
    return {k:v for k,v in order.items() if k not in {'_id','studentId'}}

@router.post('/premium/confirm')
async def confirm(payload:Confirm,student_id:str=StudentId):
    order=await col('certificate_orders').find_one({'orderId':payload.orderId,'studentId':student_id})
    if not order: raise HTTPException(404,'Order not found.')
    if datetime.fromisoformat(order['expiresAt'])<datetime.now(timezone.utc): raise HTTPException(409,'Order expired. Create another order.')
    e=await eligibility(student_id,order['courseId'])
    if not e['eligible']: raise HTTPException(409,'Certificate eligibility changed.')
    status=payment_service().confirm(order,payload.confirmDemo)
    await col('certificate_orders').update_one({'orderId':order['orderId'],'studentId':student_id},{'$set':{'status':status,'confirmedAt':iso_now()}})
    return {'orderId':order['orderId'],'status':status,'mode':'DEMO','notice':'DEMO payment confirmed. No money charged. Generate your certificate separately.'}

@router.post('/generate')
async def generate(payload:Generate,student_id:str=StudentId):
    existing=await col('certificates').find_one({'studentId':student_id,'courseId':payload.courseId,'type':payload.type})
    if existing:
        await add_reference(existing)
        return public(existing)
    e=await eligibility(student_id,payload.courseId)
    if not e['eligible']: raise HTTPException(409,'; '.join(e['reasons']))
    payment='not_required'
    if payload.type=='premium':
        order=await col('certificate_orders').find_one({'orderId':payload.orderId,'studentId':student_id,'courseId':payload.courseId,'status':'demo_confirmed'})
        if not order: raise HTTPException(402,'Confirmed premium order required.')
        if datetime.fromisoformat(order['expiresAt'])<datetime.now(timezone.utc): raise HTTPException(409,'Order expired.')
        payment='demo_confirmed'
    cid='CIQ-'+secrets.token_hex(16)
    doc={'certificateId':cid,'studentId':student_id,'studentName':payload.displayName or e['studentName'],'displaySubtitle':payload.displaySubtitle,'courseId':e['courseId'],'courseName':e['courseName'],'type':payload.type,'assessmentScore':e['assessmentScore'],'evidenceIds':e['evidenceIds'],'assessmentIds':[a['id'] for a in e['assessments']],'completedAt':e['completedAt'],'issuedAt':iso_now(),'verificationStatus':'valid','paymentStatus':payment,'orderId':payload.orderId,**prepare(e,payload.type)}
    doc.update(publicUrl=base_url()+'/certificate/'+cid,pdfUrl='/api/v1/certificates/'+cid+'/pdf',qrUrl='/api/v1/certificates/'+cid+'/qr')
    doc['pdfBytes']=render_certificate(doc)
    try: await col('certificates').insert_one(doc)
    except DuplicateKeyError:
        doc=await col('certificates').find_one({'studentId':student_id,'courseId':payload.courseId,'type':payload.type})
        if not doc: raise HTTPException(409,'Please retry issuance.')
    await add_reference(doc)
    return public(doc)

async def issued(cid):
    if len(cid)!=36 or not cid.startswith('CIQ-'): raise HTTPException(404,'Certificate not found or invalid.')
    doc=await col('certificates').find_one({'certificateId':cid,'verificationStatus':'valid'})
    if not doc: raise HTTPException(404,'Certificate not found or invalid.')
    return doc

@router.get('/verify/{certificateId}')
async def verify(certificateId:str): return public(await issued(certificateId))
@router.get('/{id}/preview.png')
async def issued_preview(id:str):
    doc=await issued(id)
    return Response(pdf_preview(bytes(doc['pdfBytes'])),media_type='image/png',headers={'Cache-Control':'no-store','X-Content-Type-Options':'nosniff'})

@router.get('/{id}/pdf')
async def pdf(id:str):
    doc=await issued(id)
    return Response(bytes(doc['pdfBytes']),media_type='application/pdf',headers={'Content-Disposition':f'inline; filename="{id}.pdf"','X-Content-Type-Options':'nosniff','Cache-Control':'no-store'})
@router.get('/{id}/qr')
async def qr_image(id:str):
    doc=await issued(id); image=qrcode.make(doc['publicUrl'],image_factory=qrcode.image.svg.SvgPathImage)
    buffer=BytesIO();image.save(buffer)
    return Response(buffer.getvalue(),media_type='image/svg+xml',headers={'X-Content-Type-Options':'nosniff'})
@router.get('/{id}')
async def get(id:str): return public(await issued(id))
