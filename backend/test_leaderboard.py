from app.main import app
from fastapi.testclient import TestClient
import asyncio

# Create a test client
c = TestClient(app)

# First, register a user
from uuid import uuid4
email = uuid4().hex + '@example.com'
name = 'Test User'
password = 'test-password-123'

register_data = {'name': name, 'email': email, 'password': password}
response = c.post('/api/v1/auth/register', json=register_data)
print('Register response:', response.status_code)
if response.status_code == 200:
    user_data = response.json()
    print('User data:', user_data)
    sid = user_data['student']['studentId']
    token = user_data['token']
    headers = {'Authorization': 'Bearer ' + token}
    
    # Test leaderboard endpoint
    leaderboard_response = c.get('/api/v1/coding/leaderboard', headers=headers)
    print('Leaderboard response:', leaderboard_response.status_code)
    if leaderboard_response.status_code == 200:
        leaderboard_data = leaderboard_response.json()
        print('Number of entries:', len(leaderboard_data))
        if leaderboard_data:
            print('First entry keys:', list(leaderboard_data[0].keys()))
        
        # Check for isCurrent flag
        for i, entry in enumerate(leaderboard_data[:5]):
            has_student_id = 'studentId' in entry
            is_current = entry.get('isCurrent', False)
            coding_xp = entry.get('codingXP', 0)
            print(f'Entry {i}: studentId={'present' if has_student_id else 'missing'}, isCurrent={is_current}, codingXP={coding_xp}')