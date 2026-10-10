#!/usr/bin/env python3
import sys
sys.path.insert(0, 'app')
from app.config import settings
print('LLM_PROVIDER:', settings.llm_provider)
print('GROQ_API_KEY set:', bool(settings.groq_api_key))
print('OPENROUTER_API_KEY set:', bool(settings.openrouter_api_key))
print('GROQ_MODEL:', settings.groq_model)
print('OPENROUTER_MODEL:', settings.openrouter_model)