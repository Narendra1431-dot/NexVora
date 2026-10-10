from fastapi import APIRouter
from ..security import StudentId
from ..assistant.schemas import AssistantInput
from ..assistant.service import respond, history
from ..assistant.research import configured

router = APIRouter(prefix='/assistant', tags=['conversational-assistant'])

@router.post('/chat')
async def chat(payload: AssistantInput, student_id: str = StudentId):
    return await respond(payload, student_id)

@router.get('/history')
async def messages(student_id: str = StudentId):
    return await history(student_id)

@router.get('/capabilities')
async def capabilities(student_id: str = StudentId):
    return {'conversation': 'existing_governed_runtime', 'search': 'configured_unverified' if configured() else 'not_configured',
            'voice': 'browser_dependent', 'rasa': 'not_selected_python_dependency_conflict'}
