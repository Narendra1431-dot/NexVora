"""Notifications and activity feed."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..db import col
from ..engine import state as state_engine
from ..security import StudentId, iso_now

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("")
async def list_notifications(student_id: str = StudentId) -> list[dict[str, Any]]:
    cursor = col("notifications").find({"studentId": student_id}).sort("createdAt", -1).limit(100)
    return [{k: v for k, v in doc.items() if k not in {"_id", "studentId"}} async for doc in cursor]


@router.post("/{notification_id}/read")
async def mark_read(notification_id: str, student_id: str = StudentId) -> dict[str, Any]:
    result = await col("notifications").update_one(
        {"studentId": student_id, "id": notification_id},
        {"$set": {"read": True, "readAt": iso_now()}},
    )
    if not result.matched_count:
        raise HTTPException(status_code=404, detail="Notification not found.")
    return {"id": notification_id, "read": True}


@router.post("/read-all")
async def mark_all_read(student_id: str = StudentId) -> dict[str, Any]:
    await col("notifications").update_many(
        {"studentId": student_id, "read": {"$ne": True}},
        {"$set": {"read": True, "readAt": iso_now()}},
    )
    return {"ok": True}


@router.get("/activity")
async def activity_feed(student_id: str = StudentId) -> list[dict[str, Any]]:
    cursor = col("events").find({"studentId": student_id}).sort("createdAt", -1).limit(100)
    return [{k: v for k, v in doc.items() if k not in {"_id", "studentId"}} async for doc in cursor]


@router.post("/test")
async def create_test_notification(student_id: str = StudentId) -> dict[str, Any]:
    """Used by the hackathon demo bar to show a live push notification."""
    notification = state_engine.build_notification(
        "Live system check",
        "The notification pipeline is working end to end.",
        notif_type="system",
        link_tab="dashboard",
    )
    await state_engine.persist_notifications(student_id, [notification])
    return {**notification, "createdAt": iso_now()}
