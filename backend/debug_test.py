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

# Patch submit to add detailed debug output
original_submit = coding_router.submit

async def debug_submit(payload, student_id):
    print(f'DEBUG submit START: problemId={payload.problemId}, requestId={payload.requestId}')
    try:
        p = await coding_router.problem(payload.problemId)
        print(f'DEBUG submit: problem found: {p["problemId"]}')
        
        if not runner.configured():
            raise Exception('Runner not configured')
        print(f'DEBUG submit: runner configured')
        
        entry, replay = await coding_router.reserve(student_id, payload.problemId, 'practice', payload.requestId, payload.code, payload.language)
        print(f'DEBUG submit: reserve done, replay={replay}')
        if replay:
            print(f'DEBUG submit: returning replay')
            return entry['response']
        
        key = {'studentId': student_id, 'problemId': payload.problemId}
        print(f'DEBUG submit: key={key}')
        
        progress = await col('coding_progress').find_one_and_update(key, {'$inc': {'attempts': 1}, '$setOnInsert': {'status': 'In Progress', 'taskType': 'practice', 'difficulty': p['difficulty']}}, upsert=True, return_document=ReturnDocument.AFTER)
        print(f'DEBUG submit: progress updated, attempts={progress["attempts"]}')
        
        try:
            async with coding_router.slots:
                results = await runner.execute(payload.code, payload.language, p['publicTests'] + p['hiddenTests'])
            print(f'DEBUG submit: runner execute done, results={len(results)}')
        except Exception as e:
            print(f'DEBUG submit: runner execute ERROR: {e}')
            await col('coding_submissions').update_one({'submissionId': entry['submissionId']}, {'$set': {'status': 'Service Unavailable'}})
            raise
        
        accepted = all(r['status'] == 'Accepted' for r in results)
        status = 'Accepted' if accepted else next(r['status'] for r in results if r['status'] != 'Accepted')
        detail = {'status': status, 'testsPassed': sum(r['status'] == 'Accepted' for r in results), 'totalTests': len(results), 'results': results[:len(p['publicTests'])], 'executionTime': sum(r['executionTime'] for r in results), 'memory': max((r['memory'] or 0 for r in results), default=0)}
        first = progress['attempts'] == 1
        print(f'DEBUG submit: calling finish, accepted={accepted}, first={first}')
        result = await coding_router.finish(student_id, entry, key, 'coding_progress', accepted, detail, p['xpReward'] + (20 if first else 0), {'difficulty': p['difficulty'], 'title': p['title'], 'firstTry': first})
        print(f'DEBUG submit: finish done')
        return result
    except Exception as e:
        print(f'DEBUG submit ERROR: {e}')
        traceback.print_exc()
        raise

coding_router.submit = debug_submit

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