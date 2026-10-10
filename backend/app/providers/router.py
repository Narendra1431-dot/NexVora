import os
from ..config import settings
from .base import Provider, ProviderError, STATUS
from .groq import GroqProvider
from .openrouter import OpenRouterProvider

def adapters(background=False):
    pool = {'openrouter':OpenRouterProvider(), 'groq':GroqProvider()}
    if os.getenv('FALLBACK_API_URL') and os.getenv('FALLBACK_MODEL'):
        pool['custom'] = Provider('custom',os.environ['FALLBACK_API_URL'],os.getenv('FALLBACK_API_KEY',''),os.environ['FALLBACK_MODEL'])
    
    # Use the same provider selection logic as the main LLM service
    # to ensure consistency across all parts of the system
    primary = None
    
    # First, determine which providers are actually available
    available_providers = []
    
    # Check groq availability (inspired by llm.py logic)
    if settings.groq_api_key:
        available_providers.append('groq')
    
    # Check openrouter availability  
    if settings.openrouter_api_key:
        available_providers.append('openrouter')
    
    # If explicit LLM_PROVIDER is set, respect that
    if settings.llm_provider not in {'auto', 'groq', 'openrouter'}:
        raise ProviderError('invalid_llm_provider', 'router')
    
    # Use LLM_PROVIDER for primary selection
    if settings.llm_provider == 'auto':
        # Deterministic auto-selection: prefer groq if available, then openrouter
        if 'groq' in available_providers:
            primary = 'groq'
        elif 'openrouter' in available_providers:
            primary = 'openrouter'
        else:
            raise ProviderError('no_providers_available', 'router')
    else:
        # Explicit selection
        primary = settings.llm_provider
    
    # Determine fallback order - respect settings and environment variables
    fallback_order = []
    
    # Get fallbacks from environment (backward compatibility)
    env_fallbacks = os.getenv('FALLBACK_LLM_PROVIDER','openrouter,groq').split(',')
    
    # Build deterministic fallback order based on available providers
    # First add the primary provider (already selected)
    fallback_order.append(primary)
    
    # Then add available providers in a deterministic order:
    # 1. If groq is available and not primary, add it
    # 2. If openrouter is available and not primary, add it
    # 3. Then any additional fallbacks from environment
    if 'groq' in available_providers and primary != 'groq':
        fallback_order.append('groq')
    if 'openrouter' in available_providers and primary != 'openrouter':
        fallback_order.append('openrouter')
    
    # Add any additional environment fallbacks (skip duplicates)
    for fb in env_fallbacks:
        fb = fb.strip()
        if fb and fb not in fallback_order and fb in pool:
            fallback_order.append(fb)
    
    # Remove ALLOW_AI_FALLBACK restriction since we have deterministic logic
    return [pool[n] for n in dict.fromkeys(fallback_order) if n in pool]

async def structured(prompt, schema, context, *, background=False):
    attempts=[]
    for provider in adapters(background):
        try:
            data, result = await provider.structured_generate(prompt,schema,context=context)
            return data,result,attempts
        except ProviderError as exc:
            attempts.append({'provider':provider.name,'errorCode':exc.code})
            try:
                from ..db import col
                from ..security import iso_now
                await col('intelligence_traces').insert_one({'kind':'provider_failure','provider':provider.name,
                    'model':provider.model,'errorCode':exc.code,'status':'Failed','createdAt':iso_now()})
            except RuntimeError:pass # Standalone provider configuration checks have no DB.
    raise ProviderError('all_configured_providers_failed', ','.join(a['provider'] for a in attempts))

def health():
    return {p.name:STATUS.get(p.name,{'status':'configured_unverified' if p.key else 'missing_credentials','model':p.model})
            for p in [OpenRouterProvider(),GroqProvider()]}
