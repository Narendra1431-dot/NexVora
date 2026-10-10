import re

def terms(text):return set(re.findall(r'[a-z0-9]{3,}',text.lower()))-{'the','and','for','with','this','that','from','what','how','does','based','explain','material','course'}

def rerank(question,dense,lexical):
    # Deterministic reciprocal-rank fusion, followed by relevance thresholding.
    candidates={};scores={}
    for ranking in (dense,lexical):
        for rank,item in enumerate(ranking):
            candidates[item['id']]={**candidates.get(item['id'],{}),**item}
            scores[item['id']]=scores.get(item['id'],0)+1/(60+rank+1)
    result=[];query=terms(question)
    for id in sorted(scores,key=scores.get,reverse=True):
        item=candidates[id];overlap=len(query&terms(item['text']))/max(1,len(query))
        if item.get('similarity',0)<.32 and overlap<.25:continue
        result.append({**item,'retrievalScore':round(scores[id],6),'lexicalCoverage':round(overlap,3)})
    return result[:5]
