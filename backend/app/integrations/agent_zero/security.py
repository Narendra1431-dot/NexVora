import os,ipaddress
from urllib.parse import urlsplit
from fastapi import HTTPException

def configuration():
    base=os.getenv('AGENT_ZERO_BASE_URL','').rstrip('/')
    key=os.getenv('AGENT_ZERO_API_KEY','')
    if not base or not key:raise HTTPException(503,'AGENT_ZERO_UNAVAILABLE: isolated service is not configured.')
    u=urlsplit(base)
    if u.username or u.password or u.query or u.fragment or u.path not in ('','/'):
        raise HTTPException(503,'AGENT_ZERO_UNAVAILABLE: invalid service configuration.')
    if u.scheme!='https' and not (u.scheme=='http' and u.hostname in ('127.0.0.1','localhost','agent-zero')):
        raise HTTPException(503,'AGENT_ZERO_UNAVAILABLE: use HTTPS or the isolated local service.')
    return base,key

def public_url(url):
    u=urlsplit(url)
    if u.scheme!='https' or not u.hostname or u.username or u.password or u.port not in (None,443):
        raise HTTPException(422,'Research requires an approved public HTTPS URL.')
    allowed={s.strip().lower() for s in os.getenv('AGENT_ZERO_RESEARCH_HOSTS','docs.python.org,aws.amazon.com,cloud.google.com,learn.microsoft.com').split(',')}
    if u.hostname.lower() not in allowed:raise HTTPException(403,'Research host is not allowlisted.')
    if u.query or u.fragment:raise HTTPException(422,'Research URLs must not contain query credentials or fragments.')
    try:ipaddress.ip_address(u.hostname)
    except ValueError:pass
    else:raise HTTPException(403,'IP address research targets are blocked.')
    return url

def require_isolation():
    # A transport credential is not proof of sandboxing. Operators must deploy
    # per-tenant isolation and enforce network restrictions outside the model.
    if os.getenv('AGENT_ZERO_EXECUTION_ENABLED','false').lower()!='true':
        raise HTTPException(503,'AGENT_ZERO_UNAVAILABLE: execution is disabled pending isolation verification.')
