"""Seven-day cache for approved videos; no search or invented metadata at request time."""
import asyncio,json,re
from datetime import datetime,timezone,timedelta
import httpx
from ..db import col
from ..security import iso_now

_refresh_lock=asyncio.Lock()
def expired(doc):
    try:return datetime.fromisoformat(doc['lastCheckedAt'].replace('Z','+00:00'))<datetime.now(timezone.utc)-timedelta(days=7)
    except (KeyError,ValueError):return True

async def cached(seed):
    if not seed:return [],[]
    ids=list({v['id'] for v in seed})
    existing={v['id']:v async for v in col('learning_videos').find({'id':{'$in':ids}},{'_id':0})}
    stale=[];result=[]
    for video in seed:
        doc=existing.get(video['id'])
        if doc is None:
            doc={**video,'available':True,'lastCheckedAt':video['lastVerifiedAt']+'T00:00:00+00:00'}
            await col('learning_videos').update_one({'id':doc['id']},{'$setOnInsert':doc},upsert=True)
        if expired(doc):stale.append(doc['id'])
        if doc.get('available',True):
            result.append({**video,**{k:doc.get(k) for k in ('title','channel','thumbnail','views','durationSeconds','lastVerifiedAt','source')},'stale':expired(doc)})
    return result,list(dict.fromkeys(stale))

async def refresh(ids):
    if _refresh_lock.locked():return
    async with _refresh_lock:
        async with httpx.AsyncClient(timeout=12,follow_redirects=True) as client:
            for id in ids:
                if not re.fullmatch(r'[A-Za-z0-9_-]{11}',id):continue
                doc=await col('learning_videos').find_one({'id':id})
                if not doc or not expired(doc):continue
                try:
                    page=await client.get('https://www.youtube.com/watch',params={'v':id,'hl':'en'})
                    match=re.search(r'var ytInitialPlayerResponse\s*=\s*(\{.*?\});',page.text)
                    if page.status_code!=200 or not match:continue
                    player=json.loads(match.group(1));meta=player.get('videoDetails',{})
                    if player.get('playabilityStatus',{}).get('status') in {'ERROR','UNPLAYABLE'}:
                        await col('learning_videos').update_one({'id':id},{'$set':{'available':False,'lastCheckedAt':iso_now()}});continue
                    if not meta.get('title') or meta.get('channelId')!=doc.get('channelId'):continue
                    tracks=player.get('captions',{}).get('playerCaptionsTracklistRenderer',{})
                    audio=tracks.get('audioTracks',[]);index=tracks.get('defaultAudioTrackIndex',0)
                    english=bool(audio and audio[min(index,len(audio)-1)].get('audioTrackId','').startswith('en')) or any(t.get('languageCode')=='en' and t.get('kind')=='asr' for t in tracks.get('captionTracks',[]))
                    if not english:continue
                    await col('learning_videos').update_one({'id':id},{'$set':{'title':meta['title'],'channel':meta['author'],'views':int(meta['viewCount']) if meta.get('viewCount') else None,
                        'durationSeconds':int(meta['lengthSeconds']) if meta.get('lengthSeconds') else None,'available':True,'lastCheckedAt':iso_now(),'lastVerifiedAt':iso_now()[:10],'source':'YouTube public watch metadata'}})
                except (httpx.HTTPError,ValueError,KeyError):continue
