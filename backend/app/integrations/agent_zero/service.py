from .client import AgentZeroClient
from .schemas import ResearchTask
from .security import require_isolation
from .tool_mapper import research_message
from .result_parser import parse_result

async def research(task:ResearchTask):
    require_isolation()
    # Only a fixed public URL request leaves NexVora. No canonical student state,
    # secrets, attachments or user-controlled prompts are sent to Agent Zero.
    response=await AgentZeroClient().submit(research_message(task))
    return parse_result(response.response,task.url),response.context_id
