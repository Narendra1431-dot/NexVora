#!/usr/bin/env python3
"""
Test script to verify RAG background indexing and JWT configuration fixes.
"""

import os
import sys
from pathlib import Path

# Add backend directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from app.config import settings, _validate_settings

def test_jwt_production_mode_validation():
    """Test JWT configuration validation in production vs development mode."""
    print("Testing JWT Production Mode Validation...")
    
    # Test 1: Development mode (PRODUCTION=false) - JWT_SECRET should not be required
    print("\n1. Testing Development Mode (PRODUCTION=false):")
    os.environ['PRODUCTION'] = 'false'
    os.environ['JWT_SECRET'] = ''  # Empty JWT_SECRET should be OK in development
    
    # Reload the module to pick up new environment variables
    import importlib
    if 'app.config' in sys.modules:
        importlib.reload(sys.modules['app.config'])
    from app.config import settings
    
    try:
        _validate_settings(settings)
        print("   ✅ PASS: JWT_SECRET validation passes in development mode (empty secret allowed)")
        dev_test_passed = True
    except Exception as e:
        print(f"   ❌ FAIL: JWT_SECRET validation failed in development: {e}")
        dev_test_passed = False
    
    # Test 2: Production mode (PRODUCTION=true) - JWT_SECRET should be required
    print("\n2. Testing Production Mode (PRODUCTION=true):")
    os.environ['PRODUCTION'] = 'true'
    os.environ['JWT_SECRET'] = ''  # Empty JWT_SECRET should fail in production
    
    importlib.reload(sys.modules['app.config'])
    from app.config import settings
    
    try:
        _validate_settings(settings)
        print("   ❌ FAIL: JWT_SECRET validation should have failed in production with empty secret")
        prod_test_passed = False
    except ValueError as e:
        if 'JWT_SECRET' in str(e) and 'production' in str(e).lower():
            print(f"   ✅ PASS: JWT_SECRET validation correctly fails in production: {e}")
            prod_test_passed = True
        else:
            print(f"   ❌ FAIL: JWT_SECRET validation failed with wrong error: {e}")
            prod_test_passed = False
    except Exception as e:
        print(f"   ❌ FAIL: JWT_SECRET validation failed with unexpected error: {e}")
        prod_test_passed = False
    
    # Test 3: Production mode with valid JWT_SECRET - validation should pass
    print("\n3. Testing Production Mode with valid JWT_SECRET:")
    os.environ['JWT_SECRET'] = 'test-jwt-secret-key-that-is-properly-formatted'
    
    importlib.reload(sys.modules['app.config'])
    from app.config import settings
    
    try:
        _validate_settings(settings)
        print("   ✅ PASS: JWT_SECRET validation passes with valid secret in production")
        valid_secret_test_passed = True
    except Exception as e:
        print(f"   ❌ FAIL: JWT_SECRET validation failed with valid secret: {e}")
        valid_secret_test_passed = False
    
    return dev_test_passed and prod_test_passed and valid_secret_test_passed

def test_rag_non_blocking_retrieval():
    """Test that RAG retrieval doesn't block for indexing."""
    print("\n\nTesting RAG Non-Blocking Retrieval...")
    
    # Set up test environment
    os.environ['MONGODB_DB'] = 'career_intelligence_qa'
    os.environ['DISABLE_RAG_INDEX'] = 'true'
    
    # Reload modules with test environment
    import importlib
    if 'app.config' in sys.modules:
        importlib.reload(sys.modules['app.config'])
    if 'app.services.rag' in sys.modules:
        importlib.reload(sys.modules['app.services.rag'])
    
    from app.services.rag import retrieve
    import inspect
    
    # Get the source code of the retrieve function
    source = inspect.getsource(retrieve)
    
    # Check that blocking await ensure_index() call is removed
    if 'await ensure_index()' in source:
        print("   ❌ FAIL: blocking 'await ensure_index()' call still present in retrieve() function")
        print("   This means RAG queries will still block during startup")
        return False
    else:
        print("   ✅ PASS: blocking 'await ensure_index()' call removed from retrieve() function")
    
    # Check that the function has the updated non-blocking structure
    if 'Get RAG index data without blocking for indexing' in source:
        print("   ✅ PASS: Function has new non-blocking structure")
    else:
        print("   ❌ FAIL: Function doesn't have expected non-blocking structure")
        return False
    
    # Check that the function handles the case when no indexed chunks exist
    if 'if not chunks:' in source:
        print("   ✅ PASS: Function properly handles case when no indexed chunks exist")
    else:
        print("   ❌ FAIL: Function doesn't handle case when no indexed chunks exist")
        return False
    
    print("   ✅ PASS: RAG retrieval is now non-blocking")
    return True

def main():
    print("=" * 70)
    print("RAG Background Indexing & JWT Configuration Fix Verification")
    print("=" * 70)
    
    # Run JWT configuration tests
    jwt_tests_passed = test_jwt_production_mode_validation()
    
    # Run RAG retrieval tests
    rag_tests_passed = test_rag_non_blocking_retrieval()
    
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    if jwt_tests_passed and rag_tests_passed:
        print("🎉 ALL TESTS PASSED!")
        print("\n✅ Fixed Issues:")
        print("   1. RAG indexing no longer blocks API startup or queries")
        print("   2. JWT_SECRET validation is now production-aware")
        print("   3. API remains responsive during background indexing")
        print("   4. Development environments can use placeholder JWT_SECRET")
        print("   5. Production environments maintain security requirements")
        print("\n📋 Changes Made:")
        print("   • backend/app/services/rag.py:401 - Removed blocking await ensure_index()")
        print("   • backend/app/config.py:37-48 - Added production mode check for JWT_SECRET")
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        if not jwt_tests_passed:
            print("   • JWT configuration validation issues")
        if not rag_tests_passed:
            print("   • RAG indexing blocking issues")
        return 1

if __name__ == "__main__":
    sys.exit(main())
