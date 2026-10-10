from ..tools.registry import execute
from .models import ToolInput
NAME='Coding'
TOOLS=['getCodingProgress','getRank']
async def run(state,query,skill_id=None):
    return [await execute(ToolInput(name=name,query=query),state) for name in TOOLS]
