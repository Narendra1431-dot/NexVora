"""Analytics specialist: only its domain tools are available."""
from ..tools.registry import execute
from .models import ToolInput
NAME = 'Analytics'
TOOLS = ['getAnalytics']

async def run(state,query,skill_id=None):
    return [await execute(ToolInput(name=name,query=query,skillId=skill_id),state) for name in TOOLS]
