"""Public catalog data: skills, careers, assessments, resources and projects.

These are shared, immutable-from-the-client reference documents. Nothing here
needs ownership checks, but everything except health requires a valid session
so a scraping bot cannot dump the question bank (which holds answer keys).
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from ..db import col
from ..security import StudentId

router = APIRouter(tags=["catalog"])


@router.get("/catalog/skills")
async def skills(_: str = StudentId) -> list[dict[str, Any]]:
    cursor = col("skills").find({}, {"_id": 0}).sort("id", 1)
    return [doc async for doc in cursor]


@router.get("/catalog/careers")
async def careers(_: str = StudentId) -> list[dict[str, Any]]:
    cursor = col("careers").find({}, {"_id": 0}).sort("id", 1)
    return [doc async for doc in cursor]


@router.get("/catalog/resources")
async def resources(_: str = StudentId) -> list[dict[str, Any]]:
    cursor = col("resources").find({}, {"_id": 0}).sort("id", 1)
    return [doc async for doc in cursor]


@router.get("/catalog/projects")
async def projects(_: str = StudentId) -> list[dict[str, Any]]:
    cursor = col("projects").find({}, {"_id": 0}).sort("id", 1)
    return [doc async for doc in cursor]


@router.get("/catalog/assessments")
async def assessments(_: str = StudentId) -> list[dict[str, Any]]:
    """Assessment metadata + questions, with answer keys stripped.

    Correct answers are applied server-side by ``POST /assessments/{id}/attempts``
    (see ``engine.competency.score_attempt``).
    """
    cursor = col("assessments").find({}, {"_id": 0})
    result: list[dict[str, Any]] = []
    async for doc in cursor:
        cleaned = {**doc, "questions": []}
        for question in doc.get("questions", []):
            cleaned["questions"].append(
                {k: v for k, v in question.items() if k not in {"correctAnswers", "correct", "explanation"}}
            )
        result.append(cleaned)
    return result


@router.get("/catalog/assessments/{assessment_id}")
async def assessment_detail(assessment_id: str, _: str = StudentId) -> dict[str, Any]:
    doc = await col("assessments").find_one({"id": assessment_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Assessment not found.")
    questions = [
        {k: v for k, v in question.items() if k not in {"correctAnswers", "correct", "explanation"}}
        for question in doc.get("questions", [])
    ]
    return {**doc, "questions": questions}
