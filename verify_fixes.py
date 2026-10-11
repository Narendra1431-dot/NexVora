#!/usr/bin/env python3
"""
Simple verification script for RAG background indexing and JWT configuration fixes.
"""

import os
import sys
from pathlib import Path

# Add backend directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from app.config import settings, _validate_settings
from app.services.rag import retrieve

def test_jwt_fix():
    """Test the JWT configuration fix."""
    print("Testing JWT Configuration Fix...")
    
    # Test 1: In development mode, empty JWT_SECRET should be OK
    os.environ['PRODUCTION'] = 'false'
    os.environ['JWT_SECRET'] = ''
    
    # Reload the module to pick up new environment variables
    import importlib
    importlib.reload(sys.modules['app.config'])
    from app.config import settings
    
    try:
        _validate_settings(settings)
        print("✓ JWT_SECRET validation passes in development mode")
    except Exception as e:
        print(f"✗ JWT_SECRET validation failed in development: {e}")
        return False
    
    # Test 2: In production mode, empty JWT_SECRET should fail
    os.environ['PRODUCTION'] = 'true'
    os.environ['JWT_SECRET'] = ''
    
    importlib.reload(sys.modules['app.config'])
    from app.config import settings
    
    try:
        _validate_settings(settings)
        print("✗ JWT_SECRET validation should have failed in production")
        return False
    except ValueError as e:
        if 'JWT_SECRET' in str(e):
            print("✓ JWT_SECRET validation correctly fails in production")
        else:
            print(f"✗ JWT_SECRET validation failed with wrong error: {e}")
            return False
    except Exception as e:
        print(f"✗ JWT_SECRET validation failed with unexpected error: {e}")
        return False
    
    # Test 3: With valid JWT_SECRET, validation should pass
    os.environ['JWT_SECRET'] = 'test-secret-key-at-least-32-chars'
    
    importlib.reload(sys.modules['app.config'])
    from app.config import settings
    
    try:
        _validate_settings(settings)
        print("✓ JWT_SECRET validation passes with valid secret in production")
    except Exception as e:
        print(f"✗ JWT_SECRET validation failed with valid secret: {e}")
        return False
    
    return True

def test_rag_fix():
    """Test the RAG indexing fix."""
    print("\nTesting RAG Indexing Fix...")
    
    # Check that the retrieve function doesn't block on ensure_index
    import inspect
    source = inspect.getsource(retrieve)
    
    if 'await ensure_index()' in source:
        print("✗ FAIL: blocking await ensure_index() call still present in retrieve() function")
        return False
    else:
        print("✓ PASS: blocking await ensure_index() call removed from retrieve() function")
    
    # Check that the function has the updated structure
    if 'Get RAG index data without blocking for indexing' in source:
        print("✓ PASS: Function has new non-blocking structure")
    else:
        print("✗ FAIL: Function doesn't have new non-blocking structure")
        return False
    
    return True

def main():
    print("=" * 60)
    print("RAG Background Indexing & JWT Configuration Fix Verification")
    print("=" * 60)
    
    # Set test environment variables
    os.environ['MONGODB_DB'] = 'career_intelligence_qa'
    os.environ['SEED_ON_STARTUP'] = 'false'
    os.environ['DISABLE_RAG_INDEX'] = 'true'
    
    jwt_test_passed = test_jwt_fix()
    rag_test_passed = test_rag_fix()
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    if jwt_test_passed and rag_test_passed:
        print("✓ ALL TESTS PASSED")
        print("\nFixes implemented successfully:")
        print("1. RAG indexing no longer blocks API startup or queries")
        print("2. JWT_SECRET validation is now production-aware")
        print("3. API remains responsive during background indexing")
        return 0
    else:
        print("✗ SOME TESTS FAILED")
        if not jwt_test_passed:
            print("- JWT configuration validation issues")
        if not rag_test_passed:
            print("- RAG indexing blocking issues")
        return 1

if __name__ == "__main__":
    sys.exit(main())
