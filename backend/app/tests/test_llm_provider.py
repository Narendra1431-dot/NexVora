import asyncio
import json
from dataclasses import replace
import httpx
import pytest
from fastapi import HTTPException
from app.services import llm, openrouter


def test_groq_uses_own_key_and_preserves_question(monkeypatch):
    monkeypatch.setattr(llm,'settings',replace(llm.settings,llm_provider='groq',groq_api_key='groq-fixture',groq_model='fixture-model'))
    seen=[]
    def handler(request):
        seen.append(request)
        return httpx.Response(200,json={'choices':[{'message':{'content':'fixture answer'}}]})
    factory=httpx.AsyncClient
    monkeypatch.setattr(openrouter.httpx,'AsyncClient',lambda **kw:factory(transport=httpx.MockTransport(handler),**kw))
    assert asyncio.run(llm.generate('Explain recursion',history=[{'role':'user','content':'I know Python'}])) == 'fixture answer'
    assert str(seen[0].url)=='https://api.groq.com/openai/v1/chat/completions'
    assert seen[0].headers['Authorization']=='Bearer groq-fixture'
    assert json.loads(seen[0].content)['messages'][-1]['content']=='Explain recursion'
    assert asyncio.run(llm.health())['provider']=='Groq'


def test_missing_groq_key_does_not_silently_use_openrouter(monkeypatch):
    monkeypatch.setattr(llm,'settings',replace(llm.settings,llm_provider='groq',groq_api_key=''))
    with pytest.raises(HTTPException) as exc:
        asyncio.run(llm.generate('Hello'))
    assert exc.value.status_code==503
    assert 'Groq' in exc.value.detail
    assert asyncio.run(llm.health())['available'] is False


def test_invalid_provider_fails_closed(monkeypatch):
    monkeypatch.setattr(llm,'settings',replace(llm.settings,llm_provider='unknown'))
    with pytest.raises(HTTPException):
        asyncio.run(llm.generate('Hello'))
