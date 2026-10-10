"""State orchestration: the one place where student state changes.

Every mutating route (assessment submit, project verify, resume upload,
resource completion, career switch, evidence edit) funnels through
``recalculate()``. That is what makes the "no disconnected pages" rule
structurally true rather than a convention: one write path, one derived state,
one set of events.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from ..db import col
from ..security import iso_now, new_id, relative_label, sanitize_text
from . import competency as engine
from . import roadmap as roadmap_engine

logger = logging.getLogger("plcip.state")


# --------------------------------------------------------------------------
# Load
# --------------------------------------------------------------------------
async def load_nodes(student_id: str) -> list[engine.CompetencyNode]:
    doc = await col("competencies").find_one({"studentId": student_id}) or {}
    return [engine.CompetencyNode.from_doc(item) for item in doc.get("nodes", [])]


async def load_evidence(student_id: str, limit: int | None = None) -> list[dict[str, Any]]:
    analysis = await col('resume_analysis').find_one({'studentId':student_id},{'documentId':1}) or {}
    query = {'studentId':student_id,'superseded':{'$ne':True}}
    if analysis.get('documentId'):
        # The latest completed resume upload is authoritative. Older documents
        # remain in the database as history, but are not independent skill proof.
        query['$or'] = [{'type':{'$ne':'Resume Claim'}},{'documentId':analysis['documentId']},{'documentId':{'$exists':False},'provenance':{'$not':{'$regex':'^Document doc-'}}}]
    cursor = col("evidence").find(query).sort("date", -1)
    if limit is not None:
        cursor = cursor.limit(limit)
    return [doc async for doc in cursor]


async def load_career(student_id: str, profile: Optional[dict[str, Any]] = None) -> Optional[dict[str, Any]]:
    profile = profile or await col("profiles").find_one({"studentId": student_id}) or {}
    career_id = profile.get("targetCareerId")
    if not career_id:
        return None
    return await col("careers").find_one({"id": career_id})


def evidence_index(records: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    index: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        skill_id = record.get("skillId")
        if not skill_id:
            continue
        index.setdefault(skill_id, []).append(record)
    return index


# --------------------------------------------------------------------------
# Event + notification helpers (every meaningful change is persisted)
# --------------------------------------------------------------------------
def build_event(
    event_type: str,
    title: str,
    description: str,
    *,
    delta: str = "",
    link_tab: str = "dashboard",
    payload: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    return {
        "id": new_id("act"),
        "type": event_type,
        "title": sanitize_text(title, max_length=160, allow_newlines=False),
        "description": sanitize_text(description, max_length=600),
        "timestamp": iso_now(),
        "delta": delta,
        "linkTab": link_tab,
        "payload": payload or {},
    }


def build_notification(
    title: str,
    message: str,
    *,
    notif_type: str = "system",
    link_tab: str = "dashboard",
) -> dict[str, Any]:
    return {
        "id": new_id("notif"),
        "title": sanitize_text(title, max_length=160, allow_newlines=False),
        "message": sanitize_text(message, max_length=500),
        "type": notif_type,
        "timestamp": iso_now(),
        "read": False,
        "linkTab": link_tab,
    }


async def persist_events(student_id: str, events: list[dict[str, Any]]) -> None:
    if not events:
        return
    docs = [{**event, "studentId": student_id, "createdAt": iso_now()} for event in events]
    await col("events").insert_many(docs)


async def persist_notifications(student_id: str, notifications: list[dict[str, Any]]) -> None:
    if not notifications:
        return
    docs = [{**item, "studentId": student_id, "createdAt": iso_now()} for item in notifications]
    await col("notifications").insert_many(docs)


# --------------------------------------------------------------------------
# The single derived-state function
# --------------------------------------------------------------------------
async def recalculate(
    student_id: str,
    *,
    profile: Optional[dict[str, Any]] = None,
    nodes: Optional[list[engine.CompetencyNode]] = None,
    career: Optional[dict[str, Any]] = None,
    events: Optional[list[dict[str, Any]]] = None,
    notifications: Optional[list[dict[str, Any]]] = None,
    mission: Optional[dict[str, Any]] = None,
    persist: bool = True,
) -> engine.EngineResult:
    """Recompute the whole student state from evidence and persist it."""
    profile = profile or await col("profiles").find_one({"studentId": student_id}) or {}
    from ..observability import annotate
    annotate(stateVersion=profile.get("stateVersion",0))
    nodes = nodes if nodes is not None else await load_nodes(student_id)
    career = career if career is not None else await load_career(student_id, profile)

    requirements = list((career or {}).get("requirements", []))
    requirement_by_skill = {req["skillId"]: int(req.get("requiredMastery", 85)) for req in requirements}
    requirement_importance = {req["skillId"]: req.get("importance", "Preferred") for req in requirements}

    evidence = await load_evidence(student_id)
    by_skill = evidence_index(evidence)

    skills_docs = [doc async for doc in col("skills").find({})]
    skills_by_id = {doc["id"]: doc for doc in skills_docs}

    # Hard guard: a node may only exist if a skill of that id exists. This stops
    # arbitrary ids entering the graph through an API payload.
    nodes = [node for node in nodes if node.id in skills_by_id]
    existing_ids = {node.id for node in nodes}
    for doc in skills_docs:
        if doc['id'] not in existing_ids:
            nodes.append(engine.CompetencyNode.from_doc(doc))

    # Assessment timestamps come from owned attempts, never self-reported claims.
    latest_assessments = {}
    async for attempt in col('attempts').find({'studentId':student_id},{'skillId':1,'createdAt':1}).sort('createdAt',-1):
        if attempt.get('skillId') and attempt.get('createdAt'):
            latest_assessments.setdefault(attempt['skillId'],attempt['createdAt'])
    for node in nodes:
        node.lastAssessedAt = latest_assessments.get(node.id)
        node.lastAssessed = relative_label(node.lastAssessedAt)

    competencies = engine.compute_competencies(
        nodes,
        by_skill,
        requirement_by_skill,
        requirement_importance=requirement_importance,
    )

    gaps = engine.analyse_career(nodes, requirements, by_skill)
    previous_readiness = int(profile.get("readiness", gaps["readiness"]))

    resources = [doc async for doc in col("resources").find({})]
    projects = [doc async for doc in col("projects").find({})]
    milestones = roadmap_engine.build_roadmap(nodes, competencies, requirements, resources, projects, skills_by_id)

    resume = await recompute_resume_analysis(student_id, profile, competencies, gaps, career, evidence)

    if persist:
        await col("competencies").update_one(
            {"studentId": student_id},
            {
                "$set": {
                    "nodes": [node.to_doc() for node in nodes],
                    "baselineNodes": profile.get("baselineNodes", []),
                    "updatedAt": iso_now(),
                    "readiness": gaps["readiness"],
                },
                "$setOnInsert": {"studentId": student_id, "createdAt": iso_now()},
            },
            upsert=True,
        )
        await col("roadmaps").update_one(
            {"studentId": student_id},
            {
                "$set": {
                    "milestones": milestones,
                    "summary": roadmap_engine.summarise(milestones),
                    "careerId": (career or {}).get("id"),
                    "updatedAt": iso_now(),
                },
                "$setOnInsert": {"studentId": student_id, "createdAt": iso_now()},
            },
            upsert=True,
        )
        await col("profiles").update_one(
            {"studentId": student_id},
            {
                "$set": {
                    "readiness": gaps["readiness"],
                    "previousReadiness": gaps["readiness"],
                    "lastCompetencyUpdate": iso_now(),
                    "updatedAt": iso_now(),
                }, "$inc": {"stateVersion": 1}
            },
        )
        from ..observability import annotate, log
        updated_profile = await col('profiles').find_one({'studentId':student_id}, {'stateVersion':1}) or {}
        annotate(stateVersion=updated_profile.get('stateVersion',0))
        log('competency_recalculated',studentId=student_id)
        await persist_events(student_id, events or [build_event("State Updated", "Competency state recalculated", "Evidence, career readiness and roadmap synchronized.")])
        await persist_notifications(student_id, notifications or [])
        await col("analytics").insert_one(
            {
                "studentId": student_id,
                "readiness": gaps["readiness"],
                "verifiedSkills": sum(1 for c in competencies if c["state"] == "Verified"),
                "criticalGaps": sum(
                    1 for c in competencies if c["state"] in {"Skill Gap", "Prerequisite Gap"} and c["careerRequired"]
                ),
                "evidenceCount": len(evidence),
                "createdAt": iso_now(),
            }
        )
        if resume:
            await col("resume_analysis").update_one(
                {"studentId": student_id},
                {"$set": {**resume, "uploadedAt": resume.get("uploadedAtRaw"), "updatedAt": iso_now()}, "$setOnInsert": {"createdAt": iso_now()}},
                upsert=True,
            )

    mission_doc = mission or await build_mission(student_id, competencies, gaps, career)

    result = engine.EngineResult(
        nodes=nodes,
        competencies=competencies,
        readiness=gaps["readiness"],
        previous_readiness=previous_readiness,
        mission=mission_doc,
        events=events or [],
        notifications=notifications or [],
        evidence=evidence,
        resume=resume or {},
        projects=projects,
        milestones=milestones,
        unlock_code="ok",
        allowed=True,
    )
    if persist:
        # Additive post-commit workflow. Domain results remain authoritative.
        try:
            from ..workflows.adaptation import after_commit
            await after_commit(student_id,result,profile,career,events)
        except Exception as exc:
            logger.exception('Agent adaptation failed after committed state: %s',type(exc).__name__)
            await col('agent_runs').update_one({'studentId':student_id,'id':'workflow-'+str(updated_profile.get('stateVersion',0))},
                {'$set':{'kind':'workflow','status':'failed','intent':'Adaptation pending recovery','stateVersion':updated_profile.get('stateVersion',0),
                         'errorCode':type(exc).__name__,'createdAt':iso_now()}},upsert=True)
    return result


# --------------------------------------------------------------------------
# Resume analysis is derived too — never stored as independent numbers
# --------------------------------------------------------------------------
async def recompute_resume_analysis(
    student_id: str,
    profile: dict[str, Any],
    competencies: list[dict[str, Any]],
    gaps: dict[str, Any],
    career: Optional[dict[str, Any]],
    evidence: list[dict[str, Any]],
) -> dict[str, Any]:
    analysis = await col("resume_analysis").find_one({"studentId": student_id})
    if not analysis:
        return {}

    claims = []
    seen_skills = set()
    for record in evidence:
        if record.get("type") != "Resume Claim" or record.get("documentId") != analysis.get("documentId"):
            continue
        if record.get('skillId') in seen_skills: continue
        seen_skills.add(record.get('skillId'))
        entry = next((c for c in competencies if c["id"] == record.get("skillId")), None)
        proof = next((e for e in evidence if e.get('skillId') == record.get('skillId') and e.get('verificationState') == 'Verified' and engine.EVIDENCE_PROFILE.get(e.get('type'),{}).get('verifies')), None)
        verified = bool(proof and entry and entry['state'] == 'Verified')
        claims.append(
            {
                "id": record["id"],
                "claim": record.get("summary") or record.get("title"),
                "skillName": record.get("skillName", ""),
                "skillId": record.get("skillId", ""),
                "section": record.get("sourceSection", "unspecified"),
                "evidenceState": (
                    "Verified"
                    if verified
                    else ("In Progress" if entry and entry["state"] in {"In Progress", "Estimated"} else "Unsupported")
                ),
                "evidenceId": proof["id"] if verified else None,
                "relatedCareerRequirement": ("Required" if entry and entry.get("careerRequired") else "Not required"),
                "recommendedAction": (
                    "Verified by an audited artefact."
                    if verified
                    else "Produce an assessment score or rubric-verified project to support this claim."
                ),
            }
        )

    verified_count = sum(1 for c in claims if c["evidenceState"] == "Verified")
    unsupported = len(claims) - verified_count
    coverage = int(round((verified_count / len(claims)) * 100)) if claims else 0

    requirements = (career or {}).get('requirements', [])
    claimed_ids = {c['skillId'] for c in claims}
    names = {c['id']:c['name'] for c in competencies}
    missing = [r.get('skillName') or names.get(r['skillId'],r['skillId']) for r in requirements if r['skillId'] not in claimed_ids]
    weights = {'Critical':3,'High':2,'Medium':1,'Low':1}
    total = sum(weights.get(r.get('importance'),1) for r in requirements)
    alignment = round(100 * sum(weights.get(r.get('importance'),1) for r in requirements if r['skillId'] in claimed_ids) / total) if total else 0
    sections = analysis.get('sectionsDetected') or []
    structure = round(100 * len(set(sections) & {'summary','education','skills','experience','projects'}) / 5)
    ats = round(.4 * structure + .4 * alignment + .2 * coverage)
    suggestions = []
    if unsupported: suggestions.append(f"Support {unsupported} unverified skill claims with a scored assessment or reviewed project; do not add unsupported achievement metrics.")
    if missing: suggestions.append('Role keywords absent from this resume: '+', '.join(missing)+'. Add them only when accurate.')
    absent_sections = sorted({'education','skills'} - set(sections))
    if absent_sections: suggestions.append('Use clear headings for: '+', '.join(absent_sections)+'.')
    project_ids = (career or {}).get('recommendedProjects') or []
    project = await col('projects').find_one({'id':{'$in':project_ids}}) if project_ids and unsupported else None
    return {
        "fileName": analysis.get("fileName", "resume.pdf"),
        "documentId": analysis.get("documentId"),
        "parsedSections": analysis.get("parsedSections", []),
        "uploadedAt": relative_label(analysis.get("uploadedAtRaw") or analysis.get("uploadedAt")),
        "uploadedAtRaw": analysis.get("uploadedAtRaw") or analysis.get("uploadedAt"),
        "resumeScore": int(round(0.6 * alignment + 0.4 * coverage)),
        "atsCompatibilityScore": ats,
        "sectionsDetected": sections,
        "extractedSkillsCount": len(claims),
        "claimCount": len(claims),
        "targetCareerId": (career or {}).get("id"),
        "scoreBreakdown": {"sectionStructure":structure,"roleKeywordCoverage":alignment,"evidenceCoverage":coverage},
        "verifiedClaimsCount": verified_count,
        "unsupportedClaimsCount": unsupported,
        "careerAlignmentScore": alignment,
        "evidenceCoveragePercent": coverage,
        "claims": claims,
        "missingSkillsForTarget": missing,
        "weakClaims": [c["claim"] for c in claims if c["evidenceState"] != "Verified"][:4],
        "suggestedImprovements": suggestions,
        "recommendedProofProject": project.get("title", "") if project else "",
        "targetCareerTitle": (career or {}).get("title", ""),
    }


# --------------------------------------------------------------------------
# Next best action
# --------------------------------------------------------------------------
async def build_mission(
    student_id: str,
    competencies: list[dict[str, Any]],
    gaps: dict[str, Any],
    career: Optional[dict[str, Any]],
) -> dict[str, Any]:
    """The single highest-leverage next action, chosen deterministically."""
    blocked_ids = {
        prereq
        for entry in competencies
        for prereq in entry.get("unmetPrerequisites", [])
    }

    def rank(entry: dict[str, Any]) -> tuple[int, int, int]:
        state_rank = {
            "Prerequisite Gap": 0,
            "Unverified Claim": 1,
            "Skill Gap": 2,
            "In Progress": 3,
            "Estimated": 4,
            "Verified": 9,
        }.get(entry["state"], 5)
        # Prefer skills whose completion unblocks other skills.
        unlocks_others = -1 if entry["id"] in blocked_ids else 0
        return (state_rank + unlocks_others, int(-entry["priority"] * 100), -int(entry["mastery"]))

    candidates = [entry for entry in competencies if entry.get("careerRequired")]
    candidates = [entry for entry in candidates if entry["state"] != "Verified"]
    if not candidates:
        return {
            "kind": "maintain",
            "title": "Maintain verified competency",
            "description": "All target-role requirements are verified. Re-verify periodically to avoid knowledge decay.",
            "skillId": None,
            "tab": "dashboard",
            "estimatedEffort": "30 mins",
            "reason": "The deterministic engine found no unmet requirement for this target role.",
            "impact": 0,
        }

    index = {c['id']:c for c in competencies}
    prerequisite_ids = {pid for c in candidates for pid in c.get('prerequisiteChain', [])}
    actionable = [c for c in competencies if (c['careerRequired'] or c['id'] in prerequisite_ids) and not c.get('unmetPrerequisites') and (c['state']!='Verified' or c['mastery']<c['targetLevel'])]
    top = sorted(actionable or candidates, key=lambda c:(0 if c['id'] in prerequisite_ids else 1, rank(c)))[0]
    assessment_id = roadmap_engine.ASSESSMENTS_BY_SKILL.get(top["id"])
    reasons = {
        "Prerequisite Gap": "This skill is blocked by an unmet prerequisite, so progress here unlocks downstream milestones.",
        "Unverified Claim": "You claimed this skill but no verifier artefact exists — closing it converts a claim into proof.",
        "Skill Gap": "This is a required target-role competency below its mastery bar with no prerequisite blocker.",
        "In Progress": "You have started this skill; the fastest path forward is to convert practice into verified evidence.",
        "Estimated": "Evidence exists but no verifier artefact has scored it, leaving readiness credit capped.",
    }

    if top["state"] == "Unverified Claim" and not assessment_id:
        kind, tab = "verify_claim", "projects"
        title = f"Verify your {top['name']} claim"
    elif assessment_id:
        kind, tab = "assessment", "assessments"
        title = f"Take the {top['name']} assessment"
    elif top["state"] == "Prerequisite Gap":
        kind, tab = "unblock", "roadmap"
        title = f"Unblock {top['name']}"
    else:
        kind, tab = "practice", "resources"
        title = f"Build evidence for {top['name']}"

    gap_deficit = max(0, top["targetLevel"] - top["mastery"])
    return {
        "kind": kind,
        "title": title,
        "description": top["recommendedAction"],
        "skillId": top["id"],
        "skillName": top["name"],
        "state": top["state"],
        "currentMastery": top["mastery"],
        "targetMastery": top["targetLevel"],
        "assessmentId": assessment_id,
        "tab": tab,
        "estimatedEffort": "8 mins" if assessment_id else "45 mins",
        "reason": reasons.get(top["state"], "Selected as the highest-leverage unmet requirement."),
        "impact": None,
        "career": (career or {}).get("title", ""),
    }


# --------------------------------------------------------------------------
# Evidence writers
# --------------------------------------------------------------------------
async def add_evidence(student_id: str, record: dict[str, Any]) -> dict[str, Any]:
    record = {**record, "studentId": student_id, "createdAt": iso_now()}
    await col("evidence").insert_one(record)
    return record


async def remove_evidence(student_id: str, evidence_id: str) -> bool:
    result = await col("evidence").delete_one({"studentId": student_id, "id": evidence_id})
    return bool(result.deleted_count)


async def apply_evidence_to_nodes(
    nodes: list[engine.CompetencyNode],
    by_skill: dict[str, list[dict[str, Any]]],
    touched_skill_ids: list[str],
    label: str,
) -> None:
    """Refresh mastery/state for the touched skills and record history."""
    index = {node.id: node for node in nodes}
    for skill_id in touched_skill_ids:
        node = index.get(skill_id)
        if node is None:
            continue
        signal = engine.evidence_signal(by_skill.get(skill_id, []))
        node.mastery = signal["mastery"]
        node.confidence = signal["confidence"]
        node.evidenceCount = signal["count"]
        node.lastAssessed = "Just now"
        node.lastAssessedAt = iso_now()
        engine.apply_evidence(node, {"date": iso_now()}, event_label=label)
