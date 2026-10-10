"""Student-scoped state: dashboard aggregate, profile, graph and roadmap.

All computed numbers come from ``engine.state.recalculate`` — the routers never
invent mastery, readiness or gap values.
"""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, ConfigDict, field_validator

from ..db import col
from ..config import settings
from ..engine import state as state_engine
from ..security import StudentId, iso_now, sanitize_text

router = APIRouter(tags=["student"])


class ProfileUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    priorExperience: Optional[str] = Field(default=None, max_length=3000)
    academicDetails: Optional[str] = Field(default=None, max_length=3000)
    readinessDisplayCareerId: Optional[str] = Field(default=None, max_length=100)
    name: Optional[str] = Field(default=None, max_length=120)
    headline: Optional[str] = Field(default=None, max_length=200)
    bio: Optional[str] = Field(default=None, max_length=2000)
    location: Optional[str] = Field(default=None, max_length=120)
    degree: Optional[str] = Field(default=None, max_length=120)
    institution: Optional[str] = Field(default=None, max_length=160)
    gradYear: Optional[str] = Field(default=None, max_length=10)
    gpa: Optional[str] = Field(default=None, max_length=8)
    githubHandle: Optional[str] = Field(default=None, max_length=80)
    weeklyAvailabilityHours: Optional[int] = Field(default=None, ge=0, le=80)
    learningPreferences: Optional[list[str]] = Field(default=None, max_length=12)

    @field_validator('name')
    @classmethod
    def nonempty_name(cls, value):
        if value is not None and not value.strip(): raise ValueError('Name is required.')
        return value

    @field_validator('learningPreferences')
    @classmethod
    def preferences(cls, value):
        if value is None: return value
        cleaned=list(dict.fromkeys(sanitize_text(v,max_length=80,allow_newlines=False).strip() for v in value))
        return [v for v in cleaned if v]



def _clean_links(doc: Any) -> Any:
    """Remove the Mongo/epoch cruft the frontend must not depend on."""
    if isinstance(doc, list):
        return [_clean_links(item) for item in doc]
    if isinstance(doc, dict):
        return {k: _clean_links(v) for k, v in doc.items() if k not in {"_id", "studentId"}}
    return doc


async def _profile(student_id: str) -> dict[str, Any]:
    profile = await col("profiles").find_one({"studentId": student_id})
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found. Try the demo login again.")
    return profile


# --------------------------------------------------------------------------
# Dashboard aggregate — one call powering the whole UI after sign-in
# --------------------------------------------------------------------------
@router.get("/state")
async def full_state(student_id: str = StudentId) -> dict[str, Any]:
    profile = await _profile(student_id)
    result = await state_engine.recalculate(student_id, profile=profile, persist=False)
    career = await state_engine.load_career(student_id, profile)
    careers = [doc async for doc in col("careers").find({})]
    resources = [doc async for doc in col("resources").find({}).sort("id", 1)]
    from ..ml.inference.ranker import rank, rank_projects
    resources = rank(resources, result.competencies, profile.get("weeklyAvailabilityHours", 10))
    assessments_cursor = col("assessments").find({})
    assessments = []
    async for doc in assessments_cursor:
        questions = [
            {k: v for k, v in q.items() if k not in {"correctAnswers", "correct", "explanation"}}
            for q in doc.get("questions", [])
        ]
        assessments.append({**doc, "questions": questions})

    node_index = {n.id:n for n in result.nodes}
    assessments.sort(key=lambda a:(abs({'Beginner':20,'Intermediate':55,'Advanced':80}.get(a.get('difficulty'),50)-getattr(node_index.get(a.get('skillId')),'mastery',0)), -next((c['priority'] for c in result.competencies if c['id']==a.get('skillId')),0)))
    attempts = [a async for a in col('attempts').find({'studentId':student_id}).sort('createdAt',-1)]
    from ..engine.graph import concept_observations, project_graph
    concepts = concept_observations(attempts)
    notifications = [
        doc async for doc in col("notifications").find({"studentId": student_id}).sort("createdAt", -1).limit(50)
    ]
    events = [
        doc async for doc in col("events").find({"studentId": student_id}).sort("createdAt", -1).limit(50)
    ]

    submissions = [s async for s in col('submissions').find({'studentId':student_id}).sort('createdAt',-1)]
    projected_projects = []
    for project in result.projects:
        sub = next((s for s in submissions if s['projectId']==project['id']), None)
        review = (sub or {}).get('rubricResult') or {}
        if not isinstance(review,dict): review={}
        projected_projects.append({**project, 'verified':bool(sub and sub['verificationState']=='Verified'), 'submittedAt':(sub or {}).get('createdAt'), 'submissionDetails':{'githubUrl':(sub or {}).get('githubUrl',''),'description':(sub or {}).get('description',''),'evaluationScore':review.get('score',0),'feedback':review.get('feedback','Pending authorized rubric review.'),'skillsVerified':project['skillsValidated'] if sub and sub['verificationState']=='Verified' else []}})
    from ..ml.inference.advisory import summarize
    intelligence = summarize(result.competencies, result.evidence, profile, attempts)
    relationships = project_graph([n.to_doc() for n in result.nodes], career, result.evidence, assessments, resources, result.projects, submissions)
    return _clean_links(
        {
            "intelligence": intelligence,
            "profile": {"priorExperience":"", "academicDetails":"", "readinessDisplayCareerId":"", **profile, "isDemo": profile.get("email", "").lower() == settings.demo_email.lower(), "readiness": result.readiness, "canReview": profile.get("email", "").lower() in settings.reviewer_emails},
            "nodes": [node.to_doc() for node in result.nodes],
            "competencies": result.competencies,
            "readiness": result.readiness,
            "previousReadiness": result.previous_readiness,
            "mission": result.mission,
            "milestones": result.milestones,
            "evidence": result.evidence,
            "resume": result.resume,
            "career": career,
            "careers": [{**c, "requiredCompetencies": c.get("requirements", []), "currentReadiness": __import__("app.engine.competency", fromlist=["analyse_career"]).analyse_career(result.nodes, c.get("requirements", []), state_engine.evidence_index(result.evidence))["readiness"]} for c in careers],
            "resources": [{**r, "bookmarked": False, "completed": False, **profile.get("resourceProgress", {}).get(r["id"], {}), "reasonRecommended": r["reasonRecommended"]} for r in resources],
            "assessments": assessments,
            "projects": rank_projects(projected_projects, result.competencies, profile.get("weeklyAvailabilityHours",10)),
            "notifications": notifications,
            "events": events,
            "generatedAt": iso_now(),
            "stateVersion": profile.get("stateVersion", 0),
            "baselineNodes": profile.get("baselineNodes", []),
            "concepts": concepts,
            "relationships": relationships,
            "attempts": attempts,
        }
    )


# --------------------------------------------------------------------------
# Profile
# --------------------------------------------------------------------------
@router.get("/profile")
async def get_profile(student_id: str = StudentId) -> dict[str, Any]:
    return _clean_links(await _profile(student_id))


@router.patch("/profile")
async def update_profile(payload: ProfileUpdate, student_id: str = StudentId) -> dict[str, Any]:
    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    if "name" in updates:
        updates["name"] = sanitize_text(updates["name"], max_length=120, allow_newlines=False)
    if "headline" in updates:
        updates["headline"] = sanitize_text(updates["headline"], max_length=200, allow_newlines=False)
    if "bio" in updates:
        updates["bio"] = sanitize_text(updates["bio"], max_length=2000)
    if not updates:
        return _clean_links(await _profile(student_id))

    if updates.get('readinessDisplayCareerId') and not await col('careers').find_one({'id':updates['readinessDisplayCareerId']}):
        raise HTTPException(422, 'Choose an existing career for the readiness display.')
    for key in ('priorExperience','academicDetails'):
        if key in updates: updates[key]=sanitize_text(updates[key],max_length=3000)
    if 'name' in updates and not updates['name'].strip(): raise HTTPException(422, 'Name is required.')
    updates["updatedAt"] = iso_now()
    await col("profiles").update_one({"studentId": student_id}, {"$set": updates})
    await state_engine.recalculate(student_id)
    return _clean_links(await _profile(student_id))


# --------------------------------------------------------------------------
# Career targeting — changing this re-derives the graph and roadmap
# --------------------------------------------------------------------------
class CareerTarget(BaseModel):
    careerId: str


@router.post("/career/target")
async def set_target_career(payload: CareerTarget, student_id: str = StudentId) -> dict[str, Any]:
    career = await col("careers").find_one({"id": payload.careerId})
    if not career:
        raise HTTPException(status_code=404, detail="Unknown career id.")

    profile = await _profile(student_id)
    previous = profile.get("targetCareerId")
    await col("profiles").update_one(
        {"studentId": student_id},
        {"$set": {"targetCareerId": payload.careerId, "updatedAt": iso_now()}},
    )

    result = await state_engine.recalculate(student_id)
    await state_engine.persist_events(
        student_id,
        [
            state_engine.build_event(
                "Career Target Changed",
                f"Target career set to {career['title']}",
                "Gap analysis and roadmap generation aligned to the new requirement set.",
                delta=payload.careerId,
                link_tab="careers",
            )
        ]
        if previous != payload.careerId
        else [],
    )
    return _clean_links({"readiness": result.readiness, "mission": result.mission, "career": career})


# --------------------------------------------------------------------------
# Graph + roadmap reads (cheap, no recompute)
# --------------------------------------------------------------------------
@router.get("/competencies")
async def get_competencies(student_id: str = StudentId) -> dict[str, Any]:
    result = await state_engine.recalculate(student_id, persist=False)
    return {'nodes':result.competencies,'competencies':result.competencies,'readiness':result.readiness}



@router.get("/roadmap")
async def get_roadmap(student_id: str = StudentId) -> dict[str, Any]:
    doc = await col("roadmaps").find_one({"studentId": student_id})
    if not doc:
        result = await state_engine.recalculate(student_id)
        return {"milestones": result.milestones, "summary": ""}
    return _clean_links(doc)


@router.post("/recalculate")
async def force_recalculate(student_id: str = StudentId) -> dict[str, Any]:
    """Re-derive everything from evidence (used by the UI's sync button)."""
    result = await state_engine.recalculate(student_id)
    return {"readiness": result.readiness, "mission": result.mission}


@router.get('/competencies/relationships')
async def relationships(student_id: str = StudentId):
    snapshot = await full_state(student_id)
    return {**snapshot['relationships'], 'stateVersion': snapshot['stateVersion']}

@router.get('/competencies/concepts')
async def concepts(student_id: str = StudentId):
    attempts = [a async for a in col('attempts').find({'studentId':student_id})]
    from ..engine.graph import concept_observations
    return concept_observations(attempts)
