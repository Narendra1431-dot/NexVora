"""Idempotent database seeding from the versioned catalog + demo persona.

Runs on startup when ``SEED_ON_STARTUP=true``. Catalog documents (skills,
careers, assessments, resources, projects) are overwritten wholesale because
they are code-owned. The demo persona's evidence is re-seeded only when its
fingerprint changes, so a demo student's live progress survives restarts.
"""

from __future__ import annotations

import logging
from typing import Any

from ..config import settings
from ..db import col
from ..security import hash_password, iso_now, stable_hash
from . import assessments as seed_assessments
from . import catalog as seed_catalog
from . import persona as seed_persona
from . import projects as seed_projects

logger = logging.getLogger("plcip.seed")


async def seed_all() -> dict[str, Any]:
    summary: dict[str, int] = {}

    await _replace_many("skills", seed_catalog.SKILLS)
    summary["skills"] = len(seed_catalog.SKILLS)

    careers = [_career_doc(career) for career in seed_catalog.CAREERS]
    await _replace_many("careers", careers)
    summary["careers"] = len(careers)

    await _replace_many("assessments", seed_assessments.ASSESSMENTS)
    summary["assessments"] = len(seed_assessments.ASSESSMENTS)

    await _replace_many("resources", seed_projects.RESOURCES)
    summary["resources"] = len(seed_projects.RESOURCES)

    await _replace_many("projects", seed_projects.PROJECTS)
    summary["projects"] = len(seed_projects.PROJECTS)

    if settings.seed_on_startup:
        await _seed_demo_student()
        summary["demo_student"] = 1

    logger.info("Seeded: %s", summary)
    return summary


def _career_doc(career: dict[str, Any]) -> dict[str, Any]:
    """Expand the (skillId, mastery, importance, category) tuples."""
    doc = {k: v for k, v in career.items() if k != "requirements"}
    doc["requirements"] = [
        {
            "skillId": skill_id,
            "skillName": next((s["name"] for s in seed_catalog.SKILLS if s["id"] == skill_id), skill_id),
            "requiredMastery": mastery,
            "importance": importance,
            "category": category,
        }
        for skill_id, mastery, importance, category in career["requirements"]
    ]
    return doc


async def _replace_many(key: str, documents: list[dict[str, Any]]) -> None:
    """Overwrite the whole catalog collection, keyed by ``id``."""
    collection = col(key)
    for document in documents:
        await collection.update_one(
            {"id": document["id"]},
            {"$set": document, "$setOnInsert": {"createdAt": iso_now()}},
            upsert=True,
        )


async def _seed_demo_student() -> None:
    email = settings.demo_email.lower()
    fingerprint = stable_hash(
        *(f"{record['id']}:{record['type']}:{record['skillId']}:{record['confidenceScore']}" for record in seed_persona.EVIDENCE)
    )

    user = await col("users").find_one({"email": email})
    if not user:
        student_id = f"stu-demo-{stable_hash(email)[:8]}"
        user = {
            "studentId": student_id,
            "email": email,
            "name": seed_persona.PROFILE["name"],
            "passwordHash": hash_password(settings.demo_password),
            "createdAt": iso_now(),
        }
        await col("users").insert_one(user)
        logger.info("Created demo user %s", email)

    student_id = user["studentId"]

    existing_profile = await col("profiles").find_one({"studentId": student_id})
    if existing_profile:
        return  # Live demo state: never clobber a finished demo.

    profile = {
        **{k: v for k, v in seed_persona.PROFILE.items() if k != "email"},
        "studentId": student_id,
        "email": email,
        "seedFingerprint": fingerprint,
        "updatedAt": iso_now(),
    }
    await col("profiles").update_one(
        {"studentId": student_id},
        {"$set": profile, "$setOnInsert": {"createdAt": iso_now()}},
        upsert=True,
    )

    # Evidence: only reseed if the fingerprint changed (protects live additions).
    current = await col("evidence").find_one({"studentId": student_id, "id": seed_persona.EVIDENCE[0]["id"]})
    stored_fp = (await col("profiles").find_one({"studentId": student_id}) or {}).get("seedFingerprint")
    if not current or stored_fp != fingerprint:
        for record in seed_persona.EVIDENCE:
            await col("evidence").update_one(
                {"studentId": student_id, "id": record["id"]},
                {"$set": {**record, "studentId": student_id}, "$setOnInsert": {"createdAt": iso_now()}},
                upsert=True,
            )

    # Competency graph nodes for the persona's started/in-progress skills.
    from ..engine import competency as engine

    skills_docs = [doc async for doc in col("skills").find({})]
    skills_by_id = {doc["id"]: doc for doc in skills_docs}

    existing_doc = await col("competencies").find_one({"studentId": student_id})
    existing_nodes = {n["id"]: n for n in (existing_doc or {}).get("nodes", [])}

    nodes = []
    for doc in skills_docs:
        if doc["id"] in existing_nodes:
            nodes.append(engine.CompetencyNode.from_doc({**existing_nodes[doc["id"]]}))
            continue
        if doc["id"] not in seed_persona.IN_PROGRESS_SKILLS:
            continue  # only started skills get graph nodes at seed time
        node = engine.CompetencyNode(
            id=doc["id"],
            name=doc["name"],
            domain=doc["domain"],
            type=doc.get("type", "Skill"),
            prerequisites=list(doc.get("prerequisites", [])),
            relatedConcepts=list(doc.get("relatedConcepts", [])),
            targetLevel=int(doc.get("targetLevel", 85)),
            careerImportance=doc.get("careerImportance", "Medium"),
            x=int(doc.get("x", 0)),
            y=int(doc.get("y", 0)),
        )
        nodes.append(node)

    # Build any missing prerequisite chain nodes too.
    for node in list(nodes):
        for prereq_id in node.prerequisites:
            if prereq_id in skills_by_id and all(n.id != prereq_id for n in nodes):
                doc = skills_by_id[prereq_id]
                nodes.append(
                    engine.CompetencyNode(
                        id=doc["id"],
                        name=doc["name"],
                        domain=doc["domain"],
                        type=doc.get("type", "Skill"),
                        prerequisites=list(doc.get("prerequisites", [])),
                        relatedConcepts=list(doc.get("relatedConcepts", [])),
                        targetLevel=int(doc.get("targetLevel", 85)),
                        careerImportance=doc.get("careerImportance", "Medium"),
                        x=int(doc.get("x", 0)),
                        y=int(doc.get("y", 0)),
                    )
                )

    if nodes:
        await col("competencies").update_one(
            {"studentId": student_id},
            {
                "$set": {"nodes": [node.to_doc() for node in nodes], "updatedAt": iso_now()},
                "$setOnInsert": {"studentId": student_id, "createdAt": iso_now()},
            },
            upsert=True,
        )

    # Notifications + activity feed baseline.
    for notification in seed_persona.NOTIFICATIONS:
        await col("notifications").update_one(
            {"studentId": student_id, "id": notification["id"]},
            {
                "$set": {**notification, "studentId": student_id, "timestamp": iso_now()},
                "$setOnInsert": {"createdAt": iso_now()},
            },
            upsert=True,
        )
    for activity in seed_persona.ACTIVITIES:
        await col("events").update_one(
            {"studentId": student_id, "id": activity["id"]},
            {
                "$set": {**activity, "studentId": student_id, "timestamp": iso_now()},
                "$setOnInsert": {"createdAt": iso_now()},
            },
            upsert=True,
        )

    # A resume analysis doc so the resume tab shows the seeded claims story.
    await col("resume_analysis").update_one(
        {"studentId": student_id},
        {
            "$set": {
                "fileName": "Alex_Rivera_Resume_2026.pdf",
                "uploadedAt": iso_now(),
                "sectionsDetected": ["education", "experience", "projects", "skills"],
                "extractedSkillsCount": 9,
                "suggestedImprovements": [
                    "Add measurable outcomes to the RAG project bullet.",
                    "Link the GitHub repository for the PyTorch vision models.",
                ],
                "updatedAt": iso_now(),
            },
            "$setOnInsert": {"createdAt": iso_now()},
        },
        upsert=True,
    )
