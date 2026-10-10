"""Request correlation without logging credentials, prompt text, or documents."""
import json
import logging
from contextvars import ContextVar
request_context = ContextVar('request_context', default=None)
logger = logging.getLogger('plcip.audit')

def annotate(**fields):
    context=request_context.get()
    if context is not None: context.update(fields)

def log(event, **fields):
    allowed={'requestId','studentId','stateVersion','agent','event','latency','error','status','method','route','agentRunId'}
    record={**(request_context.get() or {}),'event':event,**fields}
    logger.info(json.dumps({k:v for k,v in record.items() if k in allowed},ensure_ascii=True))
