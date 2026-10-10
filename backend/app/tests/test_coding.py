"""Coding module: real MongoDB ledger/progress and mocked external judge contract."""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4
from fastapi.testclient import TestClient
from pymongo import MongoClient


def test_missions_are_bounded_and_correct():
    from app.coding import missions, catalog
    for g in catalog.GAMES:
        for l in g['levels']:
            n = l.get('grid', 1) - 1
            source = {
                'robot': f'def route():\n    for i in range({n}):\n        if canMove("right"):\n            moveRight()\n    for i in range({n}):\n        moveDown()\nroute()',
                'maze': f'for i in range({n}):\n    moveRight()\nfor i in range({n}):\n        moveDown()',
                'bug': '\n'.join('print(' + str(v) + ')' for v in l.get('expected', [])),
                'race': 'insertionSort()',
                'defender': {1: 'removeDivisible(2)', 2: 'removeDivisible(3)', 3: 'removeBelow(5)\nreverse()'}[min(l['level'], 3)]
            }[g['gameId']]
            r = missions.evaluate(g['gameId'], l, source)
            assert r['accepted'], (g['gameId'], l['level'], r)
    l = catalog.GAMES[0]['levels'][0]
    for code in ['import os\nos.system("whoami")', 'open("file")', 'while True:\n    pass', 'for i in range(100000):\n    moveRight()', 'def a():\n    a()\na()', '__import__("os")']:
        assert not missions.evaluate('robot', l, code)['accepted']


def test_coding_journey(monkeypatch):
    from app.main import app
    from app.config import settings
    from app.services import llm, openrouter
    from app.coding import missions, catalog, runner
    
    async def available():
        return True
    monkeypatch.setattr(llm, 'is_available', available)
    monkeypatch.setattr(openrouter, 'is_available', available)
    received = []
    async def fake_runner(code, language, tests):
        received.append(tests)
        return [dict(status='Accepted' if code == 'correct' else 'Wrong Answer', input=t['input'], output=t.get('output', '') if code == 'correct' else 'bad', expected=t.get('output'), executionTime=1, memory=100, error='') for t in tests]
    monkeypatch.setattr(runner, 'execute', fake_runner)
    monkeypatch.setattr(runner, 'configured', lambda: True)
    assert settings.mongodb_db.endswith('_qa')
    db = MongoClient(settings.mongodb_uri)[settings.mongodb_db]
    with TestClient(app, backend_options={'loop_factory': asyncio.SelectorEventLoop}) as c:
        def register():
            return c.post('/api/v1/auth/register', json={'name': 'Coding QA', 'email': uuid4().hex + '@example.com', 'password': 'qa-secure-pass'}).json()
        u = register()
        sid = u['student']['studentId']
        h = {'Authorization': 'Bearer ' + u['token']}
        base = '/api/v1/coding'
        assert c.get(base + '/stats').status_code == 401
        problems = c.get(base + '/problems', headers=h).json()
        assert len(problems) >= 13 and all('hiddenTests' not in p for p in problems)
        assert 'hiddenTests' not in c.get(base + '/problems/array-sum', headers=h).json()
        code = {'problemId': 'array-sum', 'language': 'python', 'code': 'correct'}
        r = c.post(base + '/run', headers=h, json=code)
        assert r.status_code == 200, r.text
        assert c.get(base + '/stats', headers=h).json()['codingXP'] == 0
        fail = c.post(base + '/submit', headers=h, json={**code, 'code': 'wrong'}).json()
        assert fail['xpAwarded'] == 0 and not fail['completed']
        good = c.post(base + '/submit', headers=h, json={**code, 'requestId': 'one'})
        assert good.status_code == 200, good.text
        accepted = good.json()
        assert accepted['xpAwarded'] == 50 and accepted['stats']['codingXP'] == 50
        assert len(received[-1]) > len(problems[0]['publicTests'])
        assert len(accepted['results']) == 1
        assert c.post(base + '/submit', headers=h, json={**code, 'requestId': 'one'}).json() == accepted
        assert c.post(base + '/submit', headers=h, json={**code, 'code': 'changed', 'requestId': 'one'}).status_code == 409
        with ThreadPoolExecutor(max_workers=3) as pool:
            rs = list(pool.map(lambda _: c.post(base + '/submit', headers=h, json=code).json(), range(3)))
        assert all(r['xpAwarded'] == 0 for r in rs)
        assert db['xpTransactions'].count_documents({'studentId': sid, 'sourceId': 'array-sum', 'sourceType': 'practice'}) == 1
        assert c.get(base + '/stats', headers=h).json()['codingXP'] == 50
        draft = {'problemId': 'array-sum', 'language': 'python', 'code': 'print(42)', 'fontSize': 18, 'clientUpdatedAt': 100}
        assert c.put(base + '/draft', headers=h, json=draft).status_code == 200
        assert c.put(base + '/draft', headers=h, json={**draft, 'code': 'old', 'clientUpdatedAt': 99}).status_code == 200
        assert c.get(base + '/draft?problemId=array-sum&language=python', headers=h).json()['code'] == 'print(42)'
        other = register()
        oh = {'Authorization': 'Bearer ' + other['token']}
        assert c.get(base + '/draft?problemId=array-sum&language=python', headers=oh).json() == {}
        assert c.post(base + '/problems/array-sum/bookmark', headers=h, json={'bookmarked': True}).status_code == 200
        mission = {'level': 1, 'code': 'for i in range(3):\n    moveRight()\nfor i in range(3):\n    moveDown()', 'mode': 'run'}
        r = c.post(base + '/games/robot/submit', headers=h, json=mission).json()
        assert r['accepted'] and r['xpAwarded'] == 0
        assert c.post(base + '/games/robot/submit', headers=h, json={**mission, 'level': 2}).status_code == 403
        completed = c.post(base + '/games/robot/submit', headers=h, json={**mission, 'mode': 'submit'})
        assert completed.status_code == 200, completed.text
        assert completed.json()['xpAwarded'] == 50
        assert c.post(base + '/games/robot/submit', headers=h, json={**mission, 'mode': 'submit'}).json()['xpAwarded'] == 0
        assert c.post(base + '/games/robot/submit', headers=h, json={**mission, 'level': 2}).status_code == 200
        s = c.get(base + '/stats', headers=h).json()
        assert s['currentStreak'] == 1 and s['codingXP'] == 100
        leader = c.get(base + '/leaderboard', headers=h).json()
        assert any(r['isCurrent'] and r['codingXP'] == 100 for r in leader)
        assert not any('studentId' in r for r in leader)
        assert db.profiles.find_one({'studentId': sid})['codingXP'] == 100
        assert c.post(base + '/ai/review', headers=h, json={'problemId': 'array-sum', 'code': 'not accepted'}).status_code == 409
        # A real ledger balance supplies the rank comparison; client XP is never accepted.
        db['xpTransactions'].insert_one({'studentId': other['student']['studentId'], 'sourceType': 'assessment', 'sourceId': 'qa-rank-fixture', 'xp': 150, 'createdAt': __import__('app.security', fromlist=['iso_now']).iso_now(), 'transactionId': 'qa-' + uuid4().hex})
        before = c.get(base + '/stats', headers=h).json()
        hard = c.post(base + '/submit', headers=h, json={**code, 'problemId': 'max-subarray'}).json()
        assert hard['xpAwarded'] == 220 and hard['rankAfter'] < before['rank']
        day = c.get(base + '/stats', headers=h).json()['dailyProblemId']
        daily = c.post(base + '/submit', headers=h, json={**code, 'problemId': day}).json()
        assert daily['dailyBonus'] == 20
        assert c.post(base + '/submit', headers=h, json={**code, 'problemId': day}).json()['xpAwarded'] == 0
        monkeypatch.setattr(runner, 'configured', lambda: False)
        assert c.post(base + '/submit', headers=h, json=code).status_code == 503
    db.client.close()