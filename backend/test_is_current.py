from app.coding import xp
from app.main import app
from fastapi.testclient import TestClient
from uuid import uuid4
import asyncio

# Register a user
from app.routers.auth import register
import sys

async def test_leaderboard_is_current():
    # Create a test client
    c = TestClient(app)
    
    # Register a user
    email = uuid4().hex + '@example.com'
    name = 'Test User'
    password = 'test-password-123'
    
    register_data = {'name': name, 'email': email, 'password': password}
    response = c.post('/api/v1/auth/register', json=register_data)
    print('Register response:', response.status_code)
    
    if response.status_code == 200:
        user_data = response.json()
        sid = user_data['student']['studentId']
        token = user_data['token']
        headers = {'Authorization': 'Bearer ' + token}
        
        # Test the xp.leaderboard function directly
        rows = await xp.leaderboard(sid)
        print(f'xp.leaderboard() returned {len(rows)} rows')
        
        # Check if isCurrent is set correctly
        for i, row in enumerate(rows[:5]):
            print(f'Row {i}: studentId={row.get("studentId")}, isCurrent={row.get("isCurrent")}, codingXP={row.get("codingXP")}')
        
        # Now test the router endpoint
        leaderboard_response = c.get('/api/v1/coding/leaderboard', headers=headers)
        print(f'Router response status: {leaderboard_response.status_code}')
        
        if leaderboard_response.status_code == 200:
            leaderboard_data = leaderboard_response.json()
            print(f'Router returned {len(leaderboard_data)} entries')
            
            # Check for isCurrent flag
            for i, entry in enumerate(leaderboard_data[:5]):
                has_student_id = 'studentId' in entry
                is_current = entry.get('isCurrent', False)
                coding_xp = entry.get('codingXP', 0)
                print(f'Entry {i}: studentId={"present" if has_student_id else "missing"}, isCurrent={is_current}, codingXP={coding_xp}')

if __name__ == '__main__':
    asyncio.run(test_leaderboard_is_current())