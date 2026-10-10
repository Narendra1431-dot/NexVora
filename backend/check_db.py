from pymongo import MongoClient
from app.config import settings

db = MongoClient(settings.mongodb_uri)[settings.mongodb_db]
print('Database:', settings.mongodb_db)
print('Student IDs:', list(db.profiles.find({}, {'studentId': 1, 'name': 1})))
print('Coding XP transactions:', list(db.xp_transactions.find({'sourceType': {'$in': ['practice', 'game', 'daily']}}, {'studentId': 1, 'xp': 1, 'sourceType': 1})))
print('Coding XP totals:', list(db.xp_transactions.find({'sourceType': {'$in': ['practice', 'game', 'daily']}})))