"""Evidence vault, assessment attempts, project submissions and resources.

These are the only three ways the deterministic competency model is allowed to
change (plus resume parsing). Every mutation lands as an ``evidence`` record and
then flows through ``engine.state.recalculate``.
"""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..db import col
from ..engine import competency as engine
from ..engine import state as state_engine
from ..security import StudentId, clamp_int, iso_now, new_id, sanitize_text, sanitize_url

router = APIRouter(tags=["mutations"])


async def _apply_and_return(student_id: str, events: list[dict[str, Any]]) -> dict[str, Any]:
    result = await state_engine.recalculate(student_id, events=events)
    return {"readiness": result.readiness, "mission": result.mission}


# --------------------------------------------------------------------------
# Evidence
# --------------------------------------------------------------------------
class EvidenceIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    type: str
    skillId: str
    verificationState: str = "Unverified"
    quality: str = "Low"
    confidenceScore: int = Field(default=40, ge=0, le=100)
    source: str = ""
    provenance: str = ""
    url: str = ""
    summary: str = ""


@router.get("/evidence")
async def list_evidence(student_id: str = StudentId) -> list[dict[str, Any]]:
    records = await state_engine.load_evidence(student_id)
    return [{k: v for k, v in record.items() if k != "_id"} for record in records]


@router.post("/evidence", status_code=201)
async def create_evidence(payload: EvidenceIn, student_id: str = StudentId) -> dict[str, Any]:
    if payload.type not in engine.EVIDENCE_TYPES:
        raise HTTPException(status_code=422, detail=f"type must be one of: {', '.join(engine.EVIDENCE_TYPES)}")
    if payload.verificationState not in engine.VERIFICATION_STATES:
        raise HTTPException(status_code=422, detail="Unknown verificationState.")

    skill = await col("skills").find_one({"id": payload.skillId})
    if not skill:
        raise HTTPException(status_code=404, detail="Unknown skillId.")

    record = await state_engine.add_evidence(
        student_id,
        {
            "id": new_id("ev"),
            "title": sanitize_text(payload.title, max_length=200, allow_newlines=False),
            "type": payload.type,
            "skillId": payload.skillId,
            "skillName": skill["name"],
            "verificationState": "Unverified",
            "quality": "Low",
            "confidenceScore": min(payload.confidenceScore, 40),
            "date": iso_now()[:10],
            "source": sanitize_text(payload.source, max_length=200, allow_newlines=False),
            "provenance": sanitize_text(payload.provenance, max_length=1000),
            "url": sanitize_url(payload.url),
            "summary": sanitize_text(payload.summary, max_length=1000),
        },
    )
    nodes = await state_engine.load_nodes(student_id)
    await state_engine.apply_evidence_to_nodes(
        nodes, state_engine.evidence_index(await state_engine.load_evidence(student_id)), [payload.skillId], "Evidence Added"
    )
    await col("competencies").update_one(
        {"studentId": student_id},
        {"$set": {"nodes": [node.to_doc() for node in nodes], "updatedAt": iso_now()}},
    )
    return {"evidence": {k: v for k, v in record.items() if k != "_id"}, **await _apply_and_return(student_id, [])}


@router.delete("/evidence/{evidence_id}")
async def delete_evidence(evidence_id: str, student_id: str = StudentId) -> dict[str, Any]:
    removed = await state_engine.remove_evidence(student_id, evidence_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Evidence record not found.")
    return await _apply_and_return(student_id, [])


# --------------------------------------------------------------------------
# Assessments
# --------------------------------------------------------------------------
class AttemptIn(BaseModel):
    answers: dict[str, Any] = Field(max_length=100)


@router.post("/assessments/{assessment_id}/attempts", status_code=201)
async def submit_attempt(assessment_id: str, payload: AttemptIn, student_id: str = StudentId) -> dict[str, Any]:
    assessment = await col("assessments").find_one({"id": assessment_id})
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found.")

    if len(str(payload.answers)) > 50000:
        raise HTTPException(413, 'Assessment answer payload is too large.')
    graded = engine.score_attempt(assessment.get("questions", []), payload.answers)
    score = clamp_int(graded["accuracy"], 0, 100)
    passing_score = clamp_int(assessment.get("passingScore",80), 0, 100)

    before = await state_engine.recalculate(student_id, persist=False)
    await col('profiles').update_one({'studentId':student_id},{'$set':{'baselineNodes':before.competencies,'baselineReadiness':before.readiness,'baselineAt':iso_now()}})
    attempt = {
        "id": new_id("att"),
        "studentId": student_id,
        "assessmentId": assessment_id,
        "skillId": assessment.get("skillId", ""),
        "skillName": assessment.get("skillName", ""),
        "score": score,
        "accuracy": graded["accuracy"],
        "passingScore": passing_score,
        "passed": score >= passing_score,
        "breakdown": graded["breakdown"],
        "beforeMastery": next((n.mastery for n in before.nodes if n.id==assessment.get("skillId")), 0),
        "beforeReadiness": before.readiness,
        "createdAt": iso_now(),
    }
    await col("attempts").insert_one(attempt)

    # A passing attempt is verifier evidence; a weak one still records practice.
    evidence = await state_engine.add_evidence(
        student_id,
        {
            "id": new_id("ev"),
            "title": f"{assessment.get('title', 'Assessment')} — scored {score}%",
            "type": "Assessment",
            "skillId": attempt["skillId"],
            "skillName": attempt["skillName"],
            "verificationState": "Verified" if score >= passing_score else "Needs Review",
            "score": score,
            "attemptId": attempt["id"],
            "quality": "High" if score >= 85 else "Medium",
            "confidenceScore": score,
            "date": iso_now()[:10],
            "source": "Platform Assessment Engine",
            "provenance": f"Graded server-side: {graded['correct']}/{graded['total']} correct.",
            "summary": graded.get("explanation", ""),
        },
    )
    events = [
        state_engine.build_event(
            "Assessment Completed",
            f"{attempt['skillName']} assessment",
            f"Scored {score}% ({graded['correct']}/{graded['total']} correct).",
            delta=f"{score}% accuracy",
            link_tab="assessments",
        )
    ]
    return {
        "attempt": {k: v for k, v in attempt.items() if k != "_id"},
        "evidenceId": evidence["id"],
        **await _apply_and_return(student_id, events),
    }


# --------------------------------------------------------------------------
# Projects
# --------------------------------------------------------------------------
class SubmissionIn(BaseModel):
    githubUrl: str = ""
    description: str = Field(min_length=1, max_length=4000)


@router.post("/projects/{project_id}/submissions", status_code=201)
async def submit_project(project_id: str, payload: SubmissionIn, student_id: str = StudentId) -> dict[str, Any]:
    project = await col("projects").find_one({"id": project_id})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    url = sanitize_url(payload.githubUrl)
    description = sanitize_text(payload.description, max_length=4000)

    # Rubric: deterministic, URL presence gates the "Verified" bar.
    verified = False  # Repository presence is not proof of correctness. Review required.
    submission = {
        "id": new_id("sub"),
        "studentId": student_id,
        "rubricResult": [{"criterion": r["criterion"], "status": "Pending review", "score": None} for r in project.get("rubric", [])],
        "projectId": project_id,
        "githubUrl": url,
        "description": description,
        "verificationState": "Verified" if verified else "Needs Review",
        "skillsValidated": project.get("skillsValidated", []),
        "createdAt": iso_now(),
    }
    await col("submissions").insert_one(submission)

    skill_ids = [s for s in project.get("skillsValidated", [])]
    for skill_id in skill_ids:
        skill = await col("skills").find_one({"id": skill_id})
        if not skill:
            continue
        await state_engine.add_evidence(
            student_id,
            {
                "id": new_id("ev"),
                "title": f"Project submission: {project.get('title', project_id)}",
                "submissionId": submission["id"],
                "type": "Project",
                "skillId": skill_id,
                "skillName": skill["name"],
                "verificationState": "Verified" if verified else "Needs Review",
                "quality": "High" if verified else "Medium",
                "confidenceScore": 88 if verified else 60,
                "date": iso_now()[:10],
                "source": url or "Submitted repository",
                "provenance": "Unreviewed student submission; no rubric verification has occurred.",
                "summary": description[:400],
            },
        )

    events = [
        state_engine.build_event(
            "Project Submitted",
            project.get("title", project_id),
            "Submission recorded. Rubric review is pending; skills are not verified.",
            delta="Verified" if verified else "Needs Review",
            link_tab="projects",
        )
    ]
    return {
        "submission": {k: v for k, v in submission.items() if k != "_id"},
        **await _apply_and_return(student_id, events),
    }


# --------------------------------------------------------------------------
# Resources (practice credit — can never verify a skill on its own)
# --------------------------------------------------------------------------
class ResourceAction(BaseModel):
    completed: Optional[bool] = None
    bookmarked: Optional[bool] = None


@router.post("/resources/{resource_id}/action")
async def resource_action(resource_id: str, payload: ResourceAction, student_id: str = StudentId) -> dict[str, Any]:
    resource = await col("resources").find_one({"id": resource_id})
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found.")

    skill_id = resource.get("skillId", "")
    update: dict[str, Any] = {"updatedAt": iso_now()}
    if payload.completed is not None:
        update["completed"] = payload.completed
        profile = await col('profiles').find_one({'studentId':student_id}) or {}
        previous = profile.get('resourceProgress',{}).get(resource_id,{})
        if payload.completed and not previous.get('completed'):
            update['completedAt'] = iso_now()
    if payload.bookmarked is not None:
        update["bookmarked"] = payload.bookmarked

    await col("profiles").update_one({"studentId": student_id}, {"$set": {f"resourceProgress.{resource_id}.{key}":value for key,value in update.items()}})

    events: list[dict[str, Any]] = []
    if payload.completed and skill_id:
        evidence_id = f"resource-{resource_id}"
        existing = await col('evidence').find_one({'studentId':student_id,'id':evidence_id})
        if not existing:
            await state_engine.add_evidence(student_id, {'id':evidence_id,'title':resource['title'],'type':'Course Record','skillId':skill_id,'skillName':resource.get('skillName',''),'verificationState':'Unverified','quality':'Low','confidenceScore':40,'date':iso_now()[:10],'source':resource.get('url',''),'provenance':'Self-reported resource completion; not independently verified.','summary':'Learning activity recorded. Assessment required.'})
            events.append(state_engine.build_event('Resource Completed',resource['title'],'Self-reported practice recorded. No skill verification granted.',link_tab='resources'))
    return await _apply_and_return(student_id, events)


# --------------------------------------------------------------------------
# Roadmap milestone advance (manual override for demo flow)
# --------------------------------------------------------------------------
class MilestoneAdvance(BaseModel):
    note: str = ""


@router.post("/roadmap/{milestone_id}/advance")
async def advance_milestone(milestone_id: str, payload: MilestoneAdvance, student_id: str = StudentId) -> dict[str, Any]:
    doc = await col("roadmaps").find_one({"studentId": student_id})
    if not doc:
        raise HTTPException(status_code=404, detail="No roadmap yet.")
    milestones = doc.get("milestones", [])
    target = next((m for m in milestones if m.get("id") == milestone_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="Milestone not found.")

    if target.get("state") != "Completed":
        raise HTTPException(409, target.get("completionCondition", "Verified evidence required."))
    return {"milestoneId": milestone_id, "state": "Completed"}
