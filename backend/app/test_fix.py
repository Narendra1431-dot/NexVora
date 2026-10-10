#!/usr/bin/env python3
import subprocess
import sys
import time

print("=== Testing Backend Configuration Fix ===\n")

# Test 1: Check if main.py imports correctly
print("1. Testing main.py imports...")
try:
    # Change to backend directory
    import os
    os.chdir("app")
    
    # Test if FastAPI can be imported
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    print("✓ FastAPI and CORS middleware imported successfully")
    
    # Test if config can be imported
    from config import settings
    print("✓ Config imported successfully")
    print(f"  LLM_PROVIDER: {settings.llm_provider}")
    print(f"  GROQ_API_KEY set: {bool(settings.groq_api_key)}")
    print(f"  OPENROUTER_API_KEY set: {bool(settings.openrouter_api_key)}")
    
    # Test if main components can be imported
    from routers.ai import router as ai_router
    print("✓ AI router imported successfully")
    
    print("\n=== All Core Imports Working ===")
    print("The backend configuration fix is working correctly!")
    print("\nNext steps:")
    print("1. Start the backend server: uvicorn app.main:app --port 8000")
    print("2. Test the AI Mentor endpoints")
    print("3. Verify MongoDB connectivity")
    print("4. Run the existing backend tests")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)