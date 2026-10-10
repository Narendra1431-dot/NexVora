#!/usr/bin/env python3
import sys
import os

# Change to the backend/app directory
os.chdir('backend/app')

# Now test the imports
try:
    # Import config first
    from config import settings
    print("Configuration loaded successfully")
    print(f"LLM_PROVIDER: {settings.llm_provider}")
    print(f"GROQ_API_KEY: {bool(settings.groq_api_key)}")
    print(f"OPENROUTER_API_KEY: {bool(settings.openrouter_api_key)}")
    
    # Test the LLM provider selection logic
    selected = settings.llm_provider
    print(f"\nSelected provider logic:")
    print(f"  LLM_PROVIDER value: '{selected}'")
    
    if selected == 'auto':
        print(f"  Auto-selection logic:")
        print(f"    - GROQ_API_KEY available: {bool(settings.groq_api_key)}")
        print(f"    - OPENROUTER_API_KEY available: {bool(settings.openrouter_api_key)}")
        print(f"    - Should select: {'Groq' if settings.groq_api_key else 'OpenRouter'}")
    elif selected not in {'groq', 'openrouter'}:
        print(f"  ERROR: Unsupported LLM_PROVIDER. Choose groq or openrouter.")
    else:
        print(f"  Explicit selection: {selected}")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()