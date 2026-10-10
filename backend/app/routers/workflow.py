"""Versioned workflow API aliases and adaptive diagnostic sessions."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..security import StudentId, new_id, iso_now
from ..db import col
from ..engine import state
from . import auth, student, mutations
router=APIRouter(tags=['workflow'])
router.add_api_route('/me',auth.me,methods=['GET'])
router.add_api_route('/careers/select',student.set_target_career,methods=['POST'])
router.add_api_route('/roadmap/recompute',student.force_recalculate,methods=['POST'])
router.add_api_route('/evidence/ingest',mutations.create_evidence,methods=['POST'])
router.add_api_route('/projects/{project_id}/submit',mutations.submit_project,methods=['POST'])

@router.get('/resources/recommendations')
async def resources(student_id: str = StudentId):
    return (await student.full_state(student_id))['resources']

@router.get('/projects/recommendations')
async def projects(student_id: str = StudentId):
    data=await student.full_state(student_id)
    return data['projects']

class DiagnosticStart(BaseModel):
    skillId: str | None = None
    assessmentId: str | None = None

@router.post('/diagnostic/start')
async def start(payload: DiagnosticStart, student_id: str = StudentId):
    result=await state.recalculate(student_id,persist=False)
    nodes={n.id:n for n in result.nodes}
    bank=[a async for a in col('assessments').find({})]
    if payload.skillId: bank=[a for a in bank if a['skillId']==payload.skillId]
    if payload.assessmentId: bank=[a for a in bank if a['id']==payload.assessmentId]
    if not bank: raise HTTPException(404,'No scored assessment is available for this skill yet.')
    from ..engine.diagnostic import select_bank
    assessment=select_bank(bank,nodes)
    if assessment is None: raise HTTPException(404,'No assessment maps to this competency state.')
    attempt_id=new_id('diagnostic')
    await col('diagnostics').insert_one({'id':attempt_id,'studentId':student_id,'assessmentId':assessment['id'],'status':'started','createdAt':iso_now()})
    public={k:v for k,v in assessment.items() if k!='_id'}
    public['questions']=[{k:v for k,v in q.items() if k not in {'correctAnswers','correct','explanation'}} for q in assessment['questions']]
    return {'id':attempt_id,'assessment':public,'reason':'Selected nearest available difficulty to evidenced mastery; the item bank may not cover every level.'}

@router.post('/attempts/{attempt_id}/submit')
async def submit(attempt_id: str, payload: mutations.AttemptIn, student_id: str = StudentId):
    from pymongo import ReturnDocument
    attempt=await col('diagnostics').find_one_and_update({'id':attempt_id,'studentId':student_id,'status':'started'},{'$set':{'status':'submitting'}},return_document=ReturnDocument.BEFORE)
    if not attempt: raise HTTPException(409,'Attempt does not exist or has already been submitted.')
    try:
        result=await mutations.submit_attempt(attempt['assessmentId'],payload,student_id)
    except HTTPException as exc:
        # These errors occur before any attempt/evidence writes in submit_attempt.
        if exc.status_code in {404,413}:
            await col('diagnostics').update_one({'id':attempt_id,'studentId':student_id,'status':'submitting'},{'$set':{'status':'started'}})
        raise
    await col('diagnostics').update_one({'id':attempt_id,'studentId':student_id},{'$set':{'status':'completed','resultId':result['attempt']['id']}})
    return result
