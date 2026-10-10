from app.coding import xp
from app.security import create_access_token
from app.config import settings
import asyncio

async def debug_leaderboard():
    # Get the student ID that the router expects (from JWT)
    student_id_from_jwt = 'stu-test123'
    
    # Test the xp.leaderboard function
    rows = await xp.leaderboard(student_id_from_jwt)
    print(f'xp.leaderboard({student_id_from_jwt}) returned {len(rows)} rows')
    
    # Check the first few rows
    for i, row in enumerate(rows[:5]):
        print(f'Row {i}:')
        print(f'  studentId: {row.get("studentId")}')
        print(f'  isCurrent: {row.get("isCurrent")}')
        print(f'  codingXP: {row.get("codingXP")}')
        print(f'  studentId == student_id_from_jwt: {row.get("studentId") == student_id_from_jwt}')
        print()

if __name__ == '__main__':
    asyncio.run(debug_leaderboard())