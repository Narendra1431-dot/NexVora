"""Bounded search adapter. Search receives only public technical topics, never student records."""
import asyncio,os,re,time,ipaddress
from urllib.parse import urlsplit
from html import unescape
from html.parser import HTMLParser
import httpx
from ..security import iso_now

class SearchUnavailable(Exception): pass
_cache={}
OFFICIAL={'docs.python.org','react.dev','fastapi.tiangolo.com','docs.docker.com','kubernetes.io','docs.aws.amazon.com','learn.microsoft.com','cloud.google.com','pytorch.org','www.tensorflow.org','huggingface.co','rasa.com','openai.com','www.anthropic.com','ai.meta.com'}

def public_url(url):
    try:
        u=urlsplit(url)
        if u.scheme!='https' or not u.hostname or u.username or u.password or u.port not in (None,443):return False
        if u.hostname in ('localhost','localhost.localdomain') or '.' not in u.hostname:return False
        try:return ipaddress.ip_address(u.hostname).is_global
        except ValueError:return not u.hostname.endswith(('.local','.internal','.localhost'))
    except ValueError:return False

def configured():return bool(os.getenv('BRAVE_SEARCH_API_KEY') or os.getenv('SEARXNG_URL'))

def clean(text):return unescape(re.sub('<[^>]+>',' ',str(text)))[:3000]

async def search(query):
    now=time.monotonic()
    if query in _cache and now-_cache[query][0]<900:return _cache[query][1]
    key=os.getenv('BRAVE_SEARCH_API_KEY','');base=os.getenv('SEARXNG_URL','').rstrip('/')
    if not key and not base:raise SearchUnavailable('Web search is not configured. Current claims have not been researched.')
    try:
        async with httpx.AsyncClient(timeout=15,follow_redirects=False,trust_env=False) as client:
            if key:
                r=await client.get('https://api.search.brave.com/res/v1/web/search',params={'q':query,'count':6,'search_lang':'en','extra_snippets':'true'},headers={'X-Subscription-Token':key})
            else:
                u=urlsplit(base)
                if not (public_url(base) or (u.scheme=='http' and u.hostname in ('127.0.0.1','localhost') and not u.username and not u.password)) or u.query or u.fragment:raise SearchUnavailable('Search service configuration is invalid.')
                r=await client.get(base+'/search',params={'q':query,'format':'json','language':'en','safesearch':1})
            r.raise_for_status();data=r.json();raw=data.get('web',{}).get('results',[]) if key else data.get('results',[])
            results=[]
            for v in raw[:8]:
                url=v.get('url','')
                if not public_url(url):continue
                text=clean(v.get('description',v.get('content','')))+' '+clean(' '.join(v.get('extra_snippets',[])))
                results.append({'title':clean(v.get('title','Source'))[:200],'url':url,'text':text[:3000],'retrievedAt':iso_now(),'basis':'search excerpt','official':urlsplit(url).hostname in OFFICIAL})
            if len(_cache)>128:_cache.clear()
            _cache[query]=(now,results)
            return results
    except (httpx.HTTPError,ValueError,KeyError,TypeError):raise SearchUnavailable('Search service could not return valid results. No current findings were verified.')

class PageText(HTMLParser):
    def __init__(self):super().__init__();self.parts=[];self.skip=0
    def handle_starttag(self,tag,attrs):
        if tag in ('script','style','nav','footer'):self.skip+=1
    def handle_endtag(self,tag):
        if tag in ('script','style','nav','footer') and self.skip:self.skip-=1
    def handle_data(self,data):
        if not self.skip:self.parts.append(data)

async def read_official(row):
    # Exact public host allowlist; no redirects, arbitrary URL fetching or cookies.
    if urlsplit(row['url']).hostname not in OFFICIAL:return row
    try:
        async with httpx.AsyncClient(timeout=10,follow_redirects=False,trust_env=False) as client:
            async with client.stream('GET',row['url']) as r:
                if r.status_code!=200 or 'text/html' not in r.headers.get('content-type',''):return row
                data=b''
                async for chunk in r.aiter_bytes():
                    data+=chunk
                    if len(data)>400000:return row
        parser=PageText();parser.feed(data.decode('utf-8',errors='replace'))
        text=' '.join(' '.join(parser.parts).split())
        return {**row,'text':text[:9000],'basis':'official page excerpt'} if text else row
    except (httpx.HTTPError,ValueError):return row

async def research(topics,deep=False):
    queries=[topic+' current official documentation' for topic in topics[:(3 if deep else 1)]]
    if deep and topics:queries.append(topics[0]+' official limitations prerequisites comparison')
    batches=await asyncio.gather(*(search(q) for q in queries),return_exceptions=True)
    rows={};warnings=[]
    for batch in batches:
        if isinstance(batch,Exception):warnings.append(str(batch));continue
        for row in batch:rows.setdefault(row['url'],row)
    values=sorted(rows.values(),key=lambda r:not r['official'])[:(6 if deep else 4)]
    if deep:values=await asyncio.gather(*(read_official(v) for v in values))
    sources=[{**v,'id':'web-'+str(i+1)} for i,v in enumerate(values)]
    domains={urlsplit(v['url']).hostname for v in sources}
    if deep and len(domains)<2:warnings.append('Fewer than two independent source domains were retrieved; cross-source research is incomplete.')
    return sources,{'queries':queries,'sourcesRetrieved':len(sources),'domainsCompared':len(domains),'pagesRead':sum(v['basis']=='official page excerpt' for v in sources),'warnings':warnings}
