"""Single XP ledger for learning, assessments, coding and games."""
from datetime import datetime,timezone,timedelta
from pymongo.errors import DuplicateKeyError
from ..db import col
from ..security import iso_now,new_id

async def award(sid,source_type,source_id,xp,**extra):
 doc={'transactionId':new_id('xp'),'studentId':sid,'sourceType':source_type,'sourceId':source_id,'xp':xp,'createdAt':iso_now(),**extra}
 try:await col('xp_transactions').insert_one(doc);return xp
 except DuplicateKeyError:return 0

async def sync_learning(sid):
 # No invented historical rewards: only real passed attempts and recorded completions.
 async for a in col('attempts').find({'studentId':sid,'passed':True}).sort('createdAt',1):
  await award(sid,'assessment',a['assessmentId'],50,earnedAt=a['createdAt'])
 p=await col('profiles').find_one({'studentId':sid}) or {}
 for key,value in p.get('resourceProgress',{}).items():
  if value.get('completed'):await award(sid,'learning',key,10)

async def leaderboard(sid,period='overall',kind='all'):
 query={}
 if period!='overall':
  now=datetime.now(timezone.utc);start=now-timedelta(days=now.weekday()) if period=='week' else now.replace(day=1)
  query['createdAt']={'$gte':start.replace(hour=0,minute=0,second=0,microsecond=0).isoformat().replace('+00:00','Z')}
 if kind!='all':query['sourceType']=kind
 records=[d async for d in col('xp_transactions').find(query)]
 totals={}
 for r in records:
  item=totals.setdefault(r['studentId'],dict(studentId=r['studentId'],overallXP=0,codingXP=0,problemsSolved=0,gamesCompleted=0))
  item['overallXP']+=r['xp']
  if r['sourceType'] in ['practice','game','daily']:item['codingXP']+=r['xp']
  if r['sourceType']=='practice':item['problemsSolved']+=1
  if r['sourceType']=='game':item['gamesCompleted']+=1
 totals.setdefault(sid,dict(studentId=sid,overallXP=0,codingXP=0,problemsSolved=0,gamesCompleted=0))
 ordered=sorted(totals.values(),key=lambda v:(-v['overallXP'],v['studentId']))
 rows=[];last=None;rank=0
 for i,r in enumerate(ordered):
  if r['overallXP']!=last:rank=i+1;last=r['overallXP']
  p=await col('profiles').find_one({'studentId':r['studentId']}) or {}
  rows.append({**r,'rank':rank,'name':p.get('name','Learner'),'isCurrent':r['studentId']==sid})
 return rows

async def current_streak(sid):
 dates={r['createdAt'][:10] async for r in col('xp_transactions').find({'studentId':sid,'sourceType':{'$in':['practice','game','daily']}})}
 today=datetime.now(timezone.utc).date();cursor=today if today.isoformat() in dates else today-timedelta(days=1);count=0
 while cursor.isoformat() in dates:count+=1;cursor-=timedelta(days=1)
 return count

async def stats(sid):
 await sync_learning(sid)
 rows=await leaderboard(sid);me=next(r for r in rows if r['isCurrent'])
 tx=[r async for r in col('xp_transactions').find({'studentId':sid,'sourceType':{'$in':['practice','game','daily']}}).sort('createdAt',-1)]
 dates=sorted(set(r['createdAt'][:10] for r in tx),reverse=True)
 today=datetime.now(timezone.utc).date();current=0;longest=0;run=0;previous=None
 for day in reversed(dates):
  value=datetime.fromisoformat(day).date();run=run+1 if previous and (value-previous).days==1 else 1;longest=max(longest,run);previous=value
 cursor=today if today.isoformat() in dates else today-timedelta(days=1)
 while cursor.isoformat() in dates:current+=1;cursor-=timedelta(days=1)
 attempts=await col('coding_submissions').count_documents({'studentId':sid,'mode':'submit','status':{'$ne':'Service Unavailable'}})
 accepted=await col('coding_submissions').count_documents({'studentId':sid,'mode':'submit','status':'Accepted'})
 completed_sources={r['sourceId'] for r in tx if r['sourceType']=='game'}
 full_games=0
 async for game in col('coding_games').find({}):
  if game['levels'] and all(game['gameId']+':'+str(level['level']) in completed_sources for level in game['levels']):full_games+=1
 difficulty={d.lower()+'Solved':sum(t['sourceType']=='practice' and t.get('difficulty')==d for t in tx) for d in ['Easy','Medium','Hard']}
 achievements=[{'id':key,'title':title,'earned':bool(check)} for key,title,check in [
 ('first','First Code',me['problemsSolved']>=1),('ten','10 Problems Solved',me['problemsSolved']>=10),('fifty','50 Problems Solved',me['problemsSolved']>=50),('hundred','100 Problems Solved',me['problemsSolved']>=100),('game','First Game Completed',full_games>=1),('bug','Bug Hunter',any(t.get('gameId')=='bug' for t in tx)),('race','Algorithm Master',sum(t.get('gameId')=='race' for t in tx)>=3),('streak','7 Day Coding Streak',longest>=7),('perfect','Perfect Submission',any(t.get('firstTry') for t in tx)),('hard','Hard Problem Solver',difficulty['hardSolved']>=1)]]
 data={**me,**difficulty,'fullGamesCompleted':full_games,'currentStreak':current,'longestStreak':longest,'attempts':attempts,'successRate':round(100*accepted/attempts) if attempts else 0,'recentActivity':[{k:v for k,v in t.items() if k not in ['_id','studentId']} for t in tx[:12]],'achievements':achievements,'lastActivityAt':tx[0]['createdAt'] if tx else None}
 await col('coding_stats').update_one({'studentId':sid},{'$set':data},upsert=True)
 await col('profiles').update_one({'studentId':sid},{'$set':{'overallXP':me['overallXP'],'codingXP':me['codingXP'],'overallRank':me['rank']}})
 return data
