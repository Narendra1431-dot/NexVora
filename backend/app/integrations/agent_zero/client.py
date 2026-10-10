"""Official external API; no invented task/status endpoints or raw-log proxy."""
import httpx
from fastapi import HTTPException
from .security import configuration
from .schemas import MessageResult

class AgentZeroClient:
    def __init__(self,transport=None):
        self.base,self.key=configuration();self.transport=transport

    async def request(self,path,body,timeout=90):
        try:
            async with httpx.AsyncClient(timeout=timeout,follow_redirects=False,transport=self.transport,trust_env=False) as client:
                response=await client.post(self.base+path,json=body,headers={'X-API-KEY':self.key})
            if response.status_code>=300:raise HTTPException(503,'AGENT_ZERO_UNAVAILABLE: service rejected the request.')
            if len(response.content)>200000:raise HTTPException(502,'Agent Zero result exceeds the allowed size.')
            return response.json()
        except httpx.TimeoutException:raise HTTPException(504,'Agent Zero task timed out; remote completion is uncertain. Do not retry automatically.')
        except (httpx.HTTPError,ValueError):raise HTTPException(503,'AGENT_ZERO_UNAVAILABLE: transport failed.')

    async def submit(self,message):
        # Official api_message blocks until result. Run only in a background job.
        result=await self.request('/api_message',{'message':message,'lifetime_hours':.1})
        return MessageResult.model_validate(result)

    async def status(self,owned_context_id):
        value=await self.request('/api_log_get',{'context_id':owned_context_id,'length':0},timeout=5)
        log=value.get('log',{})
        # Deliberately omit raw items/progress text, which may contain reasoning.
        return {'running':bool(log.get('progress_active'))}

    async def cancel(self,owned_context_id):
        return await self.request('/api_terminate_chat',{'context_id':owned_context_id},timeout=10)
