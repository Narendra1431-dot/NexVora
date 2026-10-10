"""Persist public actions/results, never model reasoning or prompts."""
import time
from contextvars import ContextVar
from datetime import datetime,timezone
from ..db import col
from ..security import new_id
from ..runtime.redaction import redact
from .models import safe

execution_context=ContextVar('agent_execution_context',default=None)

def now():return datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00','Z')

def summary(value):
    """Bound structured output without storing hidden/private transport fields."""
    if isinstance(value,dict):
        cleaned=safe(value);result={}
        for k,v in cleaned.items():
            if k in {'systemPrompt','reasoning','chainOfThought','rawInput','email','phone','address'}:continue
            if k in ('totalTokens','inputTokens','outputTokens') and isinstance(v,int):result[k]=v
            elif redact({k:'value'}).get(k)!='value':result[k]='[REDACTED]'
            else:result[k]=summary(v)
        return result
    if isinstance(value,list):return [summary(v) for v in value[:20]]
    if isinstance(value,str):return redact(value)[:1800]
    return value

async def event(run,kind,message,step_id=None):
    await col('agent_events').insert_one({'eventId':new_id('evt'),'runId':run['id'],'studentId':run['studentId'],
        'stepId':step_id,'eventType':kind,'safeMessage':message[:300],'timestamp':now()})

async def traced_tool(call,state,executor):
    ctx=execution_context.get()
    if not ctx:return await executor(call,state)
    started=time.monotonic();tool_id=new_id('tool')
    row={'toolCallId':tool_id,'runId':ctx['id'],'studentId':state.studentId,'stepId':ctx['stepId'],
        'agentName':ctx['agentName'],'toolName':call.name,'riskLevel':'READ_ONLY','status':'RUNNING',
        'startedAt':now(),'inputSummary':{'skillId':call.skillId},'sourceRefs':[],'approvalId':None}
    await col('agent_tool_calls').insert_one(row)
    await event(ctx,'tool.started',call.name,ctx['stepId'])
    try:
        result=await executor(call,state)
        sources=[p.get('id') or p.get('documentId') for p in result.data] if call.name=='retrieveRAG' and isinstance(result.data,list) else []
        await col('agent_tool_calls').update_one({'toolCallId':tool_id},{'$set':{'status':'COMPLETED','completedAt':now(),
            'durationMs':round((time.monotonic()-started)*1000),'resultSummary':summary(result.data),'sourceRefs':sources}})
        await event(ctx,'tool.completed',call.name,ctx['stepId'])
        return result
    except BaseException as exc:
        await col('agent_tool_calls').update_one({'toolCallId':tool_id},{'$set':{'status':'FAILED','completedAt':now(),
            'durationMs':round((time.monotonic()-started)*1000),'error':type(exc).__name__}})
        await event(ctx,'tool.failed',call.name+' could not complete',ctx['stepId'])
        raise
