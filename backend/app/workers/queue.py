"""Mongo outbox + Redis/ARQ transport. No HTTP request runs a long job."""
import os
import json
from datetime import datetime,timezone,timedelta
from arq import create_pool
from arq.connections import RedisSettings
from pymongo.errors import DuplicateKeyError
from fastapi import HTTPException
from ..db import col
from ..security import new_id,iso_now

QUEUE='nexvora:intelligence'

def redis_settings():
    config=RedisSettings.from_dsn(os.getenv('REDIS_URL','redis://127.0.0.1:6379/0'))
    config.conn_timeout=1;config.conn_retries=0
    if config.ssl:config.ssl_check_hostname=True
    return config

def serialize(value):return json.dumps(value).encode('utf-8')
def deserialize(value):return json.loads(value)

async def connection():return await create_pool(redis_settings(),job_serializer=serialize,job_deserializer=deserialize)

def public(job):
    return {k:v for k,v in job.items() if k not in ('_id','studentId','lease','dispatchToken','rawInput')}

async def enqueue(student_id,type,input_refs,request_id,*,state_version=None):
    prior=await col('intelligence_jobs').find_one({'studentId':student_id,'requestId':request_id})
    if prior:
        if prior['type']!=type or prior['inputRefs']!=input_refs:raise HTTPException(409,'Request ID was already used for different input.')
        return public(prior)
    job={'jobId':new_id('job'),'studentId':student_id,'type':type,'status':'Queued','progress':0,
        'inputRefs':input_refs,'outputRefs':[],'model':None,'provider':None,'createdAt':iso_now(),
        'startedAt':None,'completedAt':None,'error':None,'retryCount':0,'requestId':request_id,
        'stateVersion':state_version,'stage':'Waiting for background worker'}
    try:await col('intelligence_jobs').insert_one(job)
    except DuplicateKeyError:
        return public(await col('intelligence_jobs').find_one({'studentId':student_id,'requestId':request_id}))
    await dispatch(job)
    return public(await col('intelligence_jobs').find_one({'jobId':job['jobId']}))

async def dispatch(job,pool=None):
    owned=pool is None
    try:
        pool=pool or await connection()
        await pool.enqueue_job('process_job',job['jobId'],_job_id=job['jobId'],_queue_name=QUEUE)
        await col('intelligence_jobs').update_one({'jobId':job['jobId'],'status':'Queued'},
            {'$set':{'queueStatus':'dispatched','stage':'Waiting for background worker'}})
    except Exception:
        await col('intelligence_jobs').update_one({'jobId':job['jobId'],'status':'Queued'},
            {'$set':{'queueStatus':'unavailable','stage':'Waiting for queue service. Your request is saved.'}})
    finally:
        if owned and pool:await pool.aclose()

async def recover(ctx):
    """Durable outbox reconciliation handles enqueue crashes and worker restarts."""
    now=iso_now()
    await col('intelligence_jobs').update_many({'status':'Processing','leaseUntil':{'$lt':now},'retryCount':{'$gte':3}},
        {'$set':{'status':'Failed','stage':'Recovery limit reached','error':'worker_interrupted','completedAt':now},'$unset':{'lease':''}})
    await col('intelligence_jobs').update_many({'status':'Processing','leaseUntil':{'$lt':now},'retryCount':{'$lt':3}},
        {'$set':{'status':'Queued','stage':'Recovering interrupted work'},'$inc':{'retryCount':1},'$unset':{'lease':''}})
    async for job in col('intelligence_jobs').find({'status':'Queued'}).limit(100):
        await dispatch(job,ctx['redis'])

async def health():
    pool=None
    try:
        pool=await connection();await pool.ping()
        heartbeat=await pool.get(QUEUE+':health-check')
        return {'jobQueue':'healthy','workers':'healthy' if heartbeat else 'unavailable'}
    except Exception:return {'jobQueue':'unavailable','workers':'unavailable'}
    finally:
        if pool:await pool.aclose()
