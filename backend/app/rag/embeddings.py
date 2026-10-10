from functools import lru_cache

@lru_cache(maxsize=1)
def model():
    from chromadb.utils.embedding_functions import ONNXMiniLM_L6_V2
    return ONNXMiniLM_L6_V2()

def embed(texts):
    # Real local semantic embeddings. No hash/keyword fallback labelled semantic.
    return [v.tolist() for v in model()(texts)]
