import os
from pathlib import Path
from functools import lru_cache
from typing import Protocol

class VectorStore(Protocol):
    def upsert(self,chunks,vectors): ...
    def search(self,vector,student_id,document_ids,limit): ...
    def health(self): ...

class ChromaStore:
    def __init__(self):
        import chromadb
        from chromadb.config import Settings
        path=os.getenv('CHROMA_PATH',str(Path(__file__).resolve().parents[2]/'data'/'chroma'))
        host=os.getenv('CHROMA_HOST')
        # API and ARQ are separate processes: share one Chroma server instead of
        # opening independently cached embedded indexes against the same files.
        if host:
            self.client=chromadb.HttpClient(host=host,port=int(os.getenv('CHROMA_PORT','8003')),
                ssl=os.getenv('CHROMA_SSL','false').lower()=='true',settings=Settings(anonymized_telemetry=False))
        else:
            self.client=chromadb.PersistentClient(path=path,settings=Settings(anonymized_telemetry=False))
        self.collection=self.client.get_or_create_collection('nexvora-documents-v1',embedding_function=None,
            metadata={'hnsw:space':'cosine'})

    def upsert(self,chunks,vectors):
        self.collection.upsert(ids=[c['id'] for c in chunks],embeddings=vectors,
            documents=[c['text'] for c in chunks],metadatas=[{k:v for k,v in c.items() if k not in ('text','id')} for c in chunks])

    def search(self,vector,student_id,document_ids,limit=20):
        where={'studentId':student_id}
        if document_ids:where={'$and':[where,{'documentId':{'$in':document_ids}}]}
        data=self.collection.query(query_embeddings=[vector],where=where,n_results=limit,
            include=['documents','metadatas','distances'])
        return [{'id':id,'text':data['documents'][0][i],**data['metadatas'][0][i],
                 'similarity':1-float(data['distances'][0][i])} for i,id in enumerate(data['ids'][0])]

    def health(self):
        self.client.heartbeat()
        return {'status':'healthy','chunks':self.collection.count()}

@lru_cache(maxsize=1)
def store()->VectorStore:
    if os.getenv('VECTOR_STORE','chroma')!='chroma':raise RuntimeError('Unsupported vector store adapter')
    return ChromaStore()
