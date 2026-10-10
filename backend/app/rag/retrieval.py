from fastapi.concurrency import run_in_threadpool
from ..db import col
from .embeddings import embed
from .store import store
from .reranker import terms,rerank

async def retrieve(student_id,question,document_ids=()):
    ready=[d['id'] async for d in col('intelligence_documents').find({'studentId':student_id,'status':'Ready'},{'id':1})]
    allowed=[id for id in document_ids if id in ready] if document_ids else ready
    if not allowed:return []
    vector=(await run_in_threadpool(embed,[question]))[0]
    dense=await run_in_threadpool(lambda:store().search(vector,student_id,allowed,20))
    # Lexical retrieval stays tenant-scoped and never searches arbitrary Mongo fields.
    candidates=[d async for d in col('intelligence_chunks').find({'studentId':student_id,'documentId':{'$in':allowed}},{'_id':0}).limit(10000)]
    q=terms(question)
    lexical=sorted(candidates,key=lambda c:len(q&terms(c['text'])),reverse=True)[:20]
    lexical=[c for c in lexical if q&terms(c['text'])]
    return rerank(question,dense,lexical)
