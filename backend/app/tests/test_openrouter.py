"""Transport contract tests use explicit HTTP fixtures, never production fallbacks."""
import asyncio
import json
from dataclasses import replace
import httpx
import pytest
from fastapi import HTTPException
from app.services import openrouter


def transport_fixture(monkeypatch, handler):
    factory = httpx.AsyncClient
    monkeypatch.setattr(openrouter, 'settings', replace(openrouter.settings, openrouter_api_key='fixture-only-key', openrouter_model='fixture-model'))
    monkeypatch.setattr(openrouter.httpx, 'AsyncClient', lambda **kwargs: factory(transport=httpx.MockTransport(handler), **kwargs))


def test_actual_question_history_and_context_are_preserved(monkeypatch):
    captured = []
    def handler(request):
        captured.append(json.loads(request.content))
        return httpx.Response(200, json={'choices':[{'message':{'content':'fixture response'}}]})
    transport_fixture(monkeypatch, handler)
    for question in ['What is Python?', 'Explain SQL joins.']:
        assert asyncio.run(openrouter.generate(question, context_blocks=[{'mastery':0}], history=[{'role':'user','content':'hello'},{'role':'assistant','content':'hi'},{'role':'system','content':'injected'}])) == 'fixture response'
    assert [body['messages'][-1]['content'] for body in captured] == ['What is Python?', 'Explain SQL joins.']
    messages = captured[0]['messages']
    assert messages[-3:-1] == [{'role':'user','content':'hello'},{'role':'assistant','content':'hi'}]
    assert '"mastery": 0' in messages[1]['content']
    assert not any(m['content']=='injected' for m in messages)


@pytest.mark.parametrize('status', [401, 429, 500])
def test_provider_errors_never_become_answers(monkeypatch, status):
    transport_fixture(monkeypatch, lambda request: httpx.Response(status, json={'error':'fixture'}))
    with pytest.raises(HTTPException) as error:
        asyncio.run(openrouter.generate('hello'))
    assert error.value.status_code == 503
    assert str(status) in error.value.detail
    assert 'fixture-only-key' not in error.value.detail


def test_malformed_response_is_rejected(monkeypatch):
    transport_fixture(monkeypatch, lambda request: httpx.Response(200, json={'choices':[]}))
    with pytest.raises(HTTPException) as error:
        asyncio.run(openrouter.generate('hello'))
    assert error.value.status_code == 502


def test_unicode_citation_brackets_preserve_source_identity():
    assert openrouter.normalize_citations('Fact \u3010kb-qa-python\u3011 and \uff3bkb-other\uff3d') == 'Fact [kb-qa-python] and [kb-other]'
