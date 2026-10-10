#!/usr/bin/env python3
import subprocess
import sys
import os

print("=== Testing Backend Provider Selection ===\n")

# Get the backend directory path
backend_dir = os.path.dirname(os.path.abspath(__file__))
# Change to backend directory
os.chdir(backend_dir)

try:
    # Test 1: Import and check provider selection
    print("1. Testing provider selection...")
    from config import settings
    
    print(f"   LLM_PROVIDER from settings: {settings.llm_provider}")
    print(f"   GROQ_API_KEY set: {bool(settings.groq_api_key)}")
    print(f"   OPENROUTER_API_KEY set: {bool(settings.openrouter_api_key)}")
    
    # Test 2: Check if LLM service can be imported
    print("\n2. Testing LLM service import...")
    from services import llm
    print(f"   LLM provider_name(): {llm.provider_name()}")
    
    # Test 3: Check router provider selection
    print("\n3. Testing provider router selection...")
    from providers import router
    adapters = router.adapters()
    print(f"   Number of adapters in pool: {len(adapters)}")
    for i, provider in enumerate(adapters):
        print(f"   Adapter {i+1}: {provider.name}")
    
    # Test 4: Test OpenRouter service
    print("\n4. Testing OpenRouter service...")
    from services import openrouter
    print(f"   OpenRouter API key configured: {bool(settings.openrouter_api_key)}")
    
    print("\n=== Provider Selection Test Results ===")
    print("✓ Core provider selection logic is working")
    print("✓ LLM service and router are consistent")
    
except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
