import os,httpx
from fastapi import HTTPException
from .security import configuration

async def health():
    try:base,key=configuration()
    except HTTPException:return {'status':'not_configured','execution':'disabled'}
    try:
        async with httpx.AsyncClient(timeout=3,follow_redirects=False,trust_env=False) as c:
            r=await c.post(base+'/api_log_get',headers={'X-API-KEY':key},json={'context_id':'nexvora-health-probe-nonexistent','length':0})
        # Authenticated invalid context is a read-only connectivity probe, not a
        # claim that browser execution or isolation has been verified.
        status='reachable' if r.status_code==404 else 'unauthorized' if r.status_code in (401,403) else 'unverified'
    except httpx.HTTPError:status='unavailable'
    return {'status':status,'execution':'configured_unverified' if os.getenv('AGENT_ZERO_EXECUTION_ENABLED')=='true' else 'disabled'}
