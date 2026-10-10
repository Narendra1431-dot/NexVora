"""Discover candidates on public YouTube pages; record actual metadata, no guessed stats."""
import asyncio,json,re,sys
from datetime import datetime,timezone
from pathlib import Path
import httpx
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.services.learning_catalog import TOPICS

DEST=Path(__file__).resolve().parents[1]/'app'/'assets'/'learning'/'videos.json'
CHANNELS={'freeCodeCamp.org','3Blue1Brown','StatQuest with Josh Starmer','Khan Academy','TechWorld with Nana','Corey Schafer','IBM Technology','Google Cloud Tech','Google for Developers','Microsoft Developer','Microsoft Azure','Amazon Web Services','MIT OpenCourseWare','Stanford Online','DeepLearningAI','TensorFlow','PyTorch','Databricks','Weights & Biases','Hugging Face','DataTalksClub','MLOps Community','Evidently AI','HashiCorp','Docker','Computerphile'}
def walk(v,key):
    if isinstance(v,dict):
        if key in v:yield v[key]
        for a in v.values():yield from walk(a,key)
    elif isinstance(v,list):
        for a in v:yield from walk(a,key)

async def main():
    records=json.loads(DEST.read_text(encoding='utf-8')) if DEST.exists() else {}
    async with httpx.AsyncClient(timeout=25,follow_redirects=True) as client:
        for sid,(query,aliases,_,__) in TOPICS.items():
            if records.get(sid):continue
            try:
                response=await client.get('https://www.youtube.com/results',params={'search_query':query,'hl':'en'})
                match=re.search(r'var ytInitialData = (.*?);</script>',response.text)
                if not match:raise ValueError('search metadata unavailable')
                raw=json.loads(match.group(1)); ids=[]
                for video in walk(raw,'videoRenderer'):
                    ids.append(video['videoId'])
                for lock in walk(raw,'lockupViewModel'):
                    if lock.get('contentType')=='LOCKUP_CONTENT_TYPE_VIDEO':ids.append(lock['contentId'])
                results=[]
                for vid in list(dict.fromkeys(ids))[:16]:
                    o=await client.get('https://www.youtube.com/oembed',params={'url':'https://www.youtube.com/watch?v='+vid,'format':'json'})
                    if o.status_code!=200:continue
                    info=o.json()
                    if info.get('author_name') not in CHANNELS or not any(a in info['title'].lower() for a in aliases):continue
                    page=await client.get('https://www.youtube.com/watch',params={'v':vid,'hl':'en'})
                    m=re.search(r'var ytInitialPlayerResponse\s*=\s*(\{.*?\});',page.text)
                    if not m:continue
                    player=json.loads(m.group(1));meta=player.get('videoDetails',{})
                    if meta.get('isPrivate') or player.get('playabilityStatus',{}).get('status')!='OK':continue
                    tracks=player.get('captions',{}).get('playerCaptionsTracklistRenderer',{})
                    audio=tracks.get('audioTracks',[]); default=tracks.get('defaultAudioTrackIndex',0)
                    english=bool(audio and audio[min(default,len(audio)-1)].get('audioTrackId','').startswith('en'))
                    if not english:
                        captions=tracks.get('captionTracks',[])
                        english=any(t.get('kind')=='asr' and t.get('languageCode')=='en' for t in captions)
                    if not english:continue
                    results.append({'id':vid,'title':meta['title'],'channel':meta['author'],'channelId':meta['channelId'],'url':'https://www.youtube.com/watch?v='+vid,'thumbnail':info['thumbnail_url'],
                        'views':int(meta['viewCount']) if meta.get('viewCount') else None,'durationSeconds':int(meta['lengthSeconds']) if meta.get('lengthSeconds') else None,
                        'language':'en','languageEvidence':'YouTube original/default English audio or English automatic captions','level':'Beginner' if any(w in meta['title'].lower() for w in ('beginner','fundamental','intro','basics','explained')) else 'Intermediate',
                        'lastVerifiedAt':datetime.now(timezone.utc).date().isoformat(),'source':'YouTube public watch metadata + oEmbed','relevance':sum(a in meta['title'].lower() for a in aliases)})
                    if len(results)>=4:break
                results.sort(key=lambda v:(-v['relevance'],-(v['views'] or 0)))
                records[sid]=results[:3]
                DEST.parent.mkdir(parents=True,exist_ok=True);DEST.write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
                print(sid, json.dumps([(v['id'],v['title'],v['channel'],v['views']) for v in results[:3]]),flush=True)
            except Exception as e:print(sid,type(e).__name__,str(e)[:80],flush=True)
            await asyncio.sleep(1)
if __name__=='__main__':asyncio.run(main())
