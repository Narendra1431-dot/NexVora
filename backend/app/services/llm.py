"""Explicit server-side provider selection; no fabricated answers or silent failover."""
import json
from fastapi import HTTPException
from ..config import settings
from . import openrouter

def provider_name():
    selected = settings.llm_provider
    if selected == 'auto':
        return 'Groq' if settings.groq_api_key else 'OpenRouter'
    if selected not in {'groq', 'openrouter'}:
        raise HTTPException(503, 'Unsupported LLM_PROVIDER. Choose groq or openrouter.')
    return 'Groq' if selected == 'groq' else 'OpenRouter'

async def resolve_model():
    return settings.groq_model if provider_name() == 'Groq' else await openrouter.resolve_model()

async def generate(prompt, *, context_blocks=None, temperature=.25, max_tokens=4096, history=None):
    if provider_name() == 'OpenRouter':
        return await openrouter.generate(prompt, context_blocks=context_blocks, temperature=temperature, max_tokens=max_tokens, history=history)
    return await openrouter.complete(prompt, provider='Groq', model=settings.groq_model,
        key=settings.groq_api_key, base_url='https://api.groq.com/openai/v1',
        context_blocks=context_blocks, temperature=temperature, max_tokens=max_tokens, history=history)

async def is_available():
    try:
        import asyncio
        return bool(await asyncio.wait_for(generate('Reply with the word ready.', max_tokens=256), timeout=5))
    except (HTTPException, asyncio.TimeoutError):
        return False

async def health():
    name = provider_name()
    configured = bool(settings.groq_api_key if name == 'Groq' else settings.openrouter_api_key)
    status = openrouter._provider_status.get(name, 'configured_unverified') if configured else 'missing_credentials'
    return {'provider':name, 'status':status, 'available':status == 'healthy', 'apiKeySet':configured,
        'configuredModel':settings.groq_model if name == 'Groq' else settings.openrouter_model}

async def extract_json(prompt, *, document, max_tokens=900):
    answer = await generate(prompt + '\nReturn a JSON object.', context_blocks=[document[:12000]], max_tokens=max_tokens)
    try:
        return json.loads(answer[answer.index('{'):answer.rindex('}')+1])
    except (ValueError, TypeError):
        raise HTTPException(502, 'AI response did not contain valid structured data.')

async def stream(prompt, context_blocks=None):
    text = await generate(prompt, context_blocks=context_blocks)
    for index in range(0, len(text), 48):
        yield text[index:index+48]
