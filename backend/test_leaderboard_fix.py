from app.coding import xp
from app.main import app
from fastapi.testclient import TestClient
from uuid import uuid4
import asyncio

async def test_leaderboard_fix():
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
        print(f'Got student ID: {sid}')
        
        # First, earn some XP to get to 100 codingXP
        # We need to submit a coding problem
        code_data = {'problemId': 'array-sum', 'language': 'python', 'code': 'correct'}
        submit_response = c.post('/api/v1/coding/submit', headers=headers, json=code_data)
        print(f'Submit response: {submit_response.status_code}')
        
        if submit_response.status_code == 200:
            submit_data = submit_response.json()
            print(f'Submit data: {submit_data}')
            print(f'XP awarded: {submit_data.get("xpAwarded")}')
            print(f'Coding XP in stats: {submit_data.get("stats", {}).get("codingXP")}')
            
            # Now check the leaderboard
            leaderboard_response = c.get('/api/v1/coding/leaderboard', headers=headers)
            print(f'Leaderboard response: {leaderboard_response.status_code}')
            
            if leaderboard_response.status_code == 200:
                leaderboard_data = leaderboard_response.json()
                print(f'Number of leaderboard entries: {len(leaderboard_data)}')
                
                # Check for the expected entry
                found_current = False
                for i, entry in enumerate(leaderboard_data):
                    is_current = entry.get('isCurrent', False)
                    coding_xp = entry.get('codingXP', 0)
                    print(f'Entry {i}: isCurrent={is_current}, codingXP={coding_xp}')
                    
                    if is_current and coding_xp == 100:
                        found_current = True
                        print('FOUND: Current student with codingXP=100')
                        break
                
                if not found_current:
                    print('ERROR: Could not find current student with codingXP=100')
                else:
                    print('SUCCESS: Test should pass now')

if __name__ == '__main__':
    asyncio.run(test_leaderboard_fix())