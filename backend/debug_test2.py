import asyncio
import sys
import importlib
import os
import traceback
from uuid import uuid4
from fastapi.testclient import TestClient
from pymongo import MongoClient
from concurrent.futures import ThreadPoolExecutor

os.environ['MONGODB_DB'] = 'career_intelligence_qa'
os.environ['RATE_LIMIT_PER_MINUTE'] = '2000'
os.environ['REVIEWER_EMAILS'] = 'reviewer-qa@example.com'

for mod_name in list(sys.modules.keys()):
    if mod_name.startswith('app.'):
        try:
            importlib.reload(sys.modules[mod_name])
        except Exception:
            pass

from app.main import app
from app.config import settings
from app.services import llm, openrouter
from app.coding import missions, catalog, runner
from app.db import col, connect, ensure_indexes, database
from app.routers import coding as coding_router

async def available():
    return True

llm.is_available = available
openrouter.is_available = available

received = []
async def fake_runner(code, language, tests):
    received.append(tests)
    return [dict(status='Accepted' if code == 'correct' else 'Wrong Answer', input=t['input'], output=t.get('output', '') if code == 'correct' else 'bad', expected=t.get('output'), executionTime=1, memory=100, error='') for t in tests]

runner.execute = fake_runner
runner.configured = lambda: True

assert settings.mongodb_db.endswith('_qa')
db = MongoClient(settings.mongodb_uri)[settings.mongodb_db]

# Patch reserve to trace what happens after it returns
original_reserve = coding_router.reserve

async def debug_reserve(sid, id, kind, request_id, code, language):
    print(f'DEBUG reserve: sid={sid}, id={id}, request_id={request_id}')
    try:
        result = await original_reserve(sid, id, kind, request_id, code, language)
        print(f'DEBUG reserve: returning entry={result[0]["submissionId"]}, replay={result[1]}')
        return result
    except Exception as e:
        print(f'DEBUG reserve ERROR: {e}')
        traceback.print_exc()
        raise

coding_router.reserve = debug_reserve

# Also patch the problem function
original_problem = coding_router.problem

async def debug_problem(id):
    print(f'DEBUG problem: id={id}')
    result = await original_problem(id)
    print(f'DEBUG problem: result={result["problemId"]}')
    return result

coding_router.problem = debug_problem

# Patch the coding_progress find_one_and_update
original_col = coding_router.col

async def debug_col(key):
    print(f'DEBUG col called with key={key}')
    return original_col(key)

coding_router.col = debug_col

with TestClient(app, backend_options={'loop_factory': asyncio.SelectorEventLoop}) as c:
    def register():
        return c.post('/api/v1/auth/register', json={'name': 'Coding QA', 'email': uuid4().hex + '@example.com', 'password': 'qa-secure-pass'}).json()
    u = register()
    sid = u['student']['studentId']
    h = {'Authorization': 'Bearer ' + u['token']}
    base = '/api/v1/coding'
    
    code = {'problemId': 'array-sum', 'language': 'python', 'code': 'correct'}
    
    # Run through test steps quickly
    r = c.post(base + '/run', headers=h, json=code)
    fail = c.post(base + '/submit', headers=h, json={**code, 'code': 'wrong'})
    good = c.post(base + '/submit', headers=h, json={**code, 'requestId': 'one'})
    accepted = good.json()
    
    # Duplicate
    dup = c.post(base + '/submit', headers=h, json={**code, 'requestId': 'one'})
    
    # Concurrent
    with ThreadPoolExecutor(max_workers=3) as pool:
        rs = list(pool.map(lambda _: c.post(base + '/submit', headers=h, json=code).json(), range(3)))
    
    # Game submissions
    mission = {'level': 1, 'code': 'for i in range(3):\n    moveRight()\nfor i in range(3):\n    moveDown()', 'mode': 'run'}
    r = c.post(base + '/games/robot/submit', headers=h, json=mission)
    completed = c.post(base + '/games/robot/submit', headers=h, json={**mission, 'mode': 'submit'})
    c.post(base + '/games/robot/submit', headers=h, json={**mission, 'mode': 'submit'})
    c.post(base + '/games/robot/submit', headers=h, json={**mission, 'level': 2})
    
    # Insert other student's xp
    other = register()
    db['xpTransactions'].insert_one({'studentId': other['student']['studentId'], 'sourceType': 'assessment', 'sourceId': 'qa-rank-fixture', 'xp': 150, 'createdAt': __import__('app.security', fromlist=['iso_now']).iso_now(), 'transactionId': 'qa-' + uuid4().hex})
    
    before = c.get(base + '/stats', headers=h).json()
    print('Before stats rank:', before['rank'])
    
    hard = c.post(base + '/submit', headers=h, json={**code, 'problemId': 'max-subarray'})
    print('Hard submit status:', hard.status_code)
    print('Hard submit response:', hard.json())