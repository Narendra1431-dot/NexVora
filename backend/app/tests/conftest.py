import os
import sys
import pytest

# Set environment variables before any app imports
os.environ['MONGODB_DB'] = 'career_intelligence_qa'
os.environ['RATE_LIMIT_PER_MINUTE'] = '2000'
os.environ['REVIEWER_EMAILS'] = 'reviewer-qa@example.com'
os.environ['SEED_ON_STARTUP'] = 'false'
os.environ['DISABLE_RAG_INDEX'] = 'true'

# Force reload of settings module
if 'app.config' in sys.modules:
    import importlib
    importlib.reload(sys.modules['app.config'])

# Also reload app.main to pick up new settings
if 'app.main' in sys.modules:
    import importlib
    importlib.reload(sys.modules['app.main'])

print(f"conftest.py: MONGODB_DB={os.environ.get('MONGODB_DB')}")

# Add backend to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from app.config import settings
print(f"conftest.py: settings.mongodb_db={settings.mongodb_db}")
print(f"conftest.py: settings.seed_on_startup={settings.seed_on_startup}")
print(f"conftest.py: DISABLE_RAG_INDEX={os.environ.get('DISABLE_RAG_INDEX')}")

@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Reset rate limiter buckets before each test."""
    from app.middleware import buckets
    buckets.clear()
    yield
    buckets.clear()
