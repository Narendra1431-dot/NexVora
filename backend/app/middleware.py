import time
import secrets
from collections import defaultdict, deque
from fastapi import Request
from starlette.responses import JSONResponse
from .config import settings
from .observability import request_context, log

buckets = defaultdict(deque)
async def rate_limit(request: Request, call_next):
    started=time.monotonic()
    request_id=secrets.token_hex(12)
    context_token=request_context.set({'requestId':request_id})
    status=500
    error=None
    try:
        key = (request.client.host if request.client else 'unknown', 'auth' if '/auth/' in request.url.path else 'api')
        now = time.monotonic()
        if len(buckets) > 10000:
            for old in list(buckets):
                if not buckets[old] or now-buckets[old][-1]>60: buckets.pop(old,None)
        queue = buckets[key]
        while queue and now-queue[0]>60: queue.popleft()
        limit = settings.sensitive_rate_limit_per_minute if key[1]=='auth' else settings.rate_limit_per_minute
        if len(queue)>=limit:
            response=JSONResponse({'detail':'Rate limit exceeded. Retry in a minute.'},429,headers={'Retry-After':'60'})
        else:
            queue.append(now)
            response=await call_next(request)
        status=response.status_code
    except Exception as exc:
        error=type(exc).__name__
        response=JSONResponse({'detail':'Internal service error. Retry or provide the request ID for diagnosis.','requestId':request_id},500)
    finally:
        route=getattr(request.scope.get('route'),'path','unmatched')
        log('request_completed',status=status,method=request.method,route=route,latency=round((time.monotonic()-started)*1000,2),error=error)
        request_context.reset(context_token)
    response.headers['X-Request-ID']=request_id
    response.headers['X-Content-Type-Options']='nosniff'
    response.headers['Cache-Control']='no-store'
    return response
