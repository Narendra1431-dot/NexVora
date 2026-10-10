import json
import re
from typing import Literal
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from ..security import StudentId
from ..db import col
from ..observability import log
from ..services import llm, rag
from ..services.agents import supervise
from ..services.mentor_context import bounded_context, bounded_history
from ..brain.schemas import Query

router = APIRouter(tags=['ai'])
class HistoryEntry(BaseModel):
    role: Literal['user', 'assistant']
    content: str = Field(max_length=8000)
class MentorMessageIn(BaseModel):
    requestId: str | None = Field(default=None,min_length=8,max_length=100)
    message: str = Field(min_length=1, max_length=8000)
    history: list[HistoryEntry] = Field(default_factory=list, max_length=20)

@router.post('/mentor/chat')
async def mentor_chat(payload: MentorMessageIn, student_id: str = StudentId):
    from ..agents.supervisor import chat
    from ..agents.models import ChatInput
    from ..security import new_id
    return await chat(ChatInput(message=payload.message,history=[h.model_dump() for h in payload.history],requestId=payload.requestId or new_id('chat')),student_id)

@router.post('/rag/query')
async def rag_query(payload: MentorMessageIn | Query, student_id: str = StudentId):
    if isinstance(payload,Query):
        from .intelligence import rag as grounded_query
        return await grounded_query(payload,student_id)
    passages = [p for p in await rag.retrieve(payload.message) if p['score'] >= .24]
    return {'passages': passages, 'sources': rag.citations(passages), 'status': 'retrieved' if passages else 'insufficient_grounded_information'}

@router.post('/mentor/check')
async def mentor_check(_: str = StudentId):
    await llm.is_available()
    return await llm.health()

@router.get('/mentor/status')
async def mentor_status(_: str = StudentId):
    return await llm.health()
