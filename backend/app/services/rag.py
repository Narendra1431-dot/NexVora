"""Local RAG: chunking, embeddings, vector search and citation building.

Two embedding backends, chosen at runtime:

1. **Sentence-Transformers** (``all-MiniLM-L6-v2``) when the package and a local
   model copy exist. Fully local, nothing is downloaded at request time.
2. **Hashing embedder** — a deterministic bag-of-hashed-trigrams projection.
   Zero dependencies, zero network, and good enough for keyword-heavy technical
   retrieval. This is the default so RAG works on a fresh machine offline.

Embeddings are cached in-process and persisted alongside the knowledge base
collection, so restarting the API does not re-embed anything.
"""

from __future__ import annotations

import logging
import math
import os
import re
from pathlib import Path
from hashlib import blake2b
from typing import Any, Optional, Sequence

from ..config import settings
from ..db import col

logger = logging.getLogger("plcip.rag")

_STOPWORDS = {
    "the", "a", "an", "and", "or", "of", "to", "in", "is", "are", "for", "on",
    "with", "as", "by", "that", "this", "it", "be", "at", "from", "how", "what",
    "why", "when", "which", "you", "your", "my", "i", "do", "does", "can",
}


# --------------------------------------------------------------------------
# Knowledge base
# --------------------------------------------------------------------------
KNOWLEDGE_BASE: list[dict[str, Any]] = [
    {
        "id": "kb-attention",
        "title": "Scaled Dot-Product Attention and Multi-Head Projections",
        "source": "Attention Is All You Need (Vaswani et al., NeurIPS 2017)",
        "year": "2017",
        "tags": ["dl-transformers", "attention", "softmax", "scaling"],
        "content": (
            "Attention computes a weighted sum of value vectors, where weights come from a softmax over "
            "query-key dot products. Because dot products grow with the vector width d_k, the logits are "
            "divided by sqrt(d_k) to keep their variance near one; without this scaling, softmax saturates "
            "and gradients vanish. Multi-head attention runs several of these projections in parallel on "
            "smaller subspaces and concatenates the results, letting the model attend to different "
            "relationships at once. Causal masking prevents a decoder from attending to future positions."
        ),
    },
    {
        "id": "kb-kvcache",
        "title": "KV Caching in Autoregressive Decoding",
        "source": "Efficient Inference for Large Language Models (survey)",
        "year": "2023",
        "tags": ["dl-transformers", "kv cache", "inference", "latency"],
        "content": (
            "During autoregressive generation, keys and values for previous tokens do not change. Caching "
            "them avoids recomputing the projections at every step, reducing per-step attention work from "
            "quadratic in sequence length to linear. The cost moves to memory: cache size grows with "
            "batch size, sequence length, layer count and head dimension. PagedAttention manages the cache "
            "in fixed-size blocks so memory is not wasted on over-reserved contiguous buffers."
        ),
    },
    {
        "id": "kb-rope",
        "title": "Rotary Position Embeddings (RoPE)",
        "source": "RoFormer: Enhanced Transformer with Rotary Position Embedding",
        "year": "2021",
        "tags": ["dl-transformers", "rope", "positional encoding"],
        "content": (
            "RoPE rotates query and key vectors in two-dimensional subspaces by an angle proportional to "
            "the token position. The rotation is orthogonal, so vector norms are preserved, and the inner "
            "product between a query at position m and a key at position n depends only on the relative "
            "offset m minus n. This gives relative position behaviour without learned positional tables and "
            "extends more gracefully to longer contexts."
        ),
    },
    {
        "id": "kb-hybrid-rag",
        "title": "Hybrid Retrieval and Reciprocal Rank Fusion",
        "source": "LlamaIndex Advanced Retrieval Guide",
        "year": "2024",
        "tags": ["dl-rag-systems", "bm25", "hybrid search", "rrf"],
        "content": (
            "Dense retrieval generalises semantics but can blur rare exact tokens such as identifiers, "
            "error codes or function names. Lexical retrieval such as BM25 is precise for such tokens but "
            "misses paraphrases. Hybrid retrieval runs both and fuses the ranked lists; reciprocal rank "
            "fusion is a common, training-free fusion that scores each document by the sum of reciprocal "
            "ranks across lists. A cross-encoder re-ranker then jointly encodes the query and each top "
            "candidate, improving precision at the cost of additional latency."
        ),
    },
    {
        "id": "kb-rag-eval",
        "title": "Evaluating RAG: Retrieval and Groundedness Metrics",
        "source": "RAGAS: Automated Evaluation of Retrieval Augmented Generation",
        "year": "2023",
        "tags": ["ml-model-evaluation", "ragas", "faithfulness", "recall"],
        "content": (
            "RAG quality is measured in two stages. Retrieval is scored with recall at k and mean "
            "reciprocal rank against a labelled set. Generation is scored with faithfulness, meaning every "
            "claim in the answer must be supported by retrieved context, and with answer relevance. "
            "Faithfulness catches hallucination that classic classification metrics cannot express, which "
            "is why generative systems need claim-level evaluation rather than accuracy alone."
        ),
    },
    {
        "id": "kb-peft",
        "title": "Parameter-Efficient Fine-Tuning and QLoRA",
        "source": "QLoRA: Efficient Finetuning of Quantized LLMs (Dettmers et al.)",
        "year": "2023",
        "tags": ["dl-llm-finetuning", "lora", "qlora", "quantization"],
        "content": (
            "LoRA freezes the base weights and learns low-rank update matrices on selected projections, so "
            "trainable parameters fall by orders of magnitude. QLoRA adds a 4-bit NormalFloat quantisation "
            "of the frozen base model plus paged optimiser states, which makes fine-tuning a 7B model fit "
            "on a single consumer GPU. Rank and alpha control the capacity and strength of the update; "
            "adapters can be merged back into the base weights for inference."
        ),
    },
    {
        "id": "kb-serving",
        "title": "Continuous Batching and PagedAttention for Serving",
        "source": "vLLM: Easy, Fast, and Cheap LLM Serving with PagedAttention",
        "year": "2023",
        "tags": ["mlops-model-serving", "vllm", "throughput", "batching"],
        "content": (
            "Static batching wastes GPU time because requests finish at different lengths. Continuous "
            "batching schedules new requests into a running batch as soon as slots free, which raises "
            "throughput substantially at the cost of more complex scheduling. PagedAttention applies "
            "virtual-memory style paging to the KV cache, cutting fragmentation and enabling memory "
            "sharing across sequences that share a prefix."
        ),
    },
    {
        "id": "kb-vdb",
        "title": "Choosing an Approximate Nearest Neighbour Index",
        "source": "Pinecone Engineering: HNSW and Product Quantisation",
        "year": "2023",
        "tags": ["data-vector-databases", "hnsw", "ivf", "recall"],
        "content": (
            "HNSW builds a layered navigable small-world graph: search walks from coarse layers to fine "
            "ones, giving high recall and low latency at the cost of memory for graph links. IVF partitions "
            "the space into cells with a training pass and searches only nearby cells, while product "
            "quantisation compresses vectors into short codes to save memory at some recall cost. Cosine "
            "similarity and inner product rank identically when vectors are normalised to unit length."
        ),
    },
    {
        "id": "kb-eval-general",
        "title": "Validation Discipline: Leakage, Imbalance and Calibration",
        "source": "Applied Machine Learning Practice Notes",
        "year": "2024",
        "tags": ["ml-model-evaluation", "cross-validation", "leakage", "calibration"],
        "content": (
            "Any preprocessing that uses the whole dataset, such as feature scaling or target encoding, "
            "leaks validation information into training when applied before splitting. On heavily imbalanced "
            "problems, accuracy is dominated by the majority class, so precision-recall AUC is more "
            "informative. Probabilities from boosted trees are often miscalibrated; reliability curves and "
            "calibration methods should be checked before thresholds are used operationally."
        ),
    },
    {
        "id": "kb-role-ai-engineer",
        "title": "AI Engineer Role Requirements",
        "source": "Platform career requirement model",
        "year": "2025",
        "tags": ["career", "ai engineer", "requirements"],
        "content": (
            "An AI Engineer is expected to move a model from notebook to production: strong Python and "
            "testing habits, PyTorch fluency including custom training loops, working knowledge of "
            "transformer internals, retrieval system design with hybrid search and re-ranking, evaluation "
            "of non-deterministic outputs, and the ability to containerise and serve a model with measured "
            "latency and throughput. Verification evidence is weighted above self-reported familiarity."
        ),
    },
]


# --------------------------------------------------------------------------
# Embedding backends
# --------------------------------------------------------------------------
def _tokenize(text: str) -> list[str]:
    tokens = re.findall(r"[a-z0-9_+#.]+", text.lower())
    return [token for token in tokens if token not in _STOPWORDS and len(token) > 1]


def _hashed_embedding(text: str, dim: int) -> list[float]:
    """Deterministic hashing projection over word tokens and character trigrams."""
    vector = [0.0] * dim
    tokens = _tokenize(text)

    features: list[str] = list(tokens)
    for token in tokens:
        padded = f"^{token}$"
        features.extend(padded[i : i + 3] for i in range(max(1, len(padded) - 2)))

    for feature in features:
        digest = blake2b(feature.encode("utf-8"), digest_size=8).digest()
        bucket = int.from_bytes(digest[:4], "big") % dim
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vector[bucket] += sign

    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector
    return [value / norm for value in vector]


class _Embedder:
    """Chooses a backend once and reports which one is active."""

    def __init__(self) -> None:
        self._model: Any = None
        self._backend = "hashing"

    @property
    def backend(self) -> str:
        return self._backend

    def load(self) -> None:
        if getattr(self, "_loaded", False):
            return
        self._loaded = True
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore

            self._model = SentenceTransformer(settings.embed_model, local_files_only=True)
            self._backend = f"sentence-transformers:{settings.embed_model}"
        except Exception as exc:  # noqa: BLE001 - falls back to the hashing embedder
            logger.info("Local sentence-transformers model unavailable (%s); using hashing embedder.", exc.__class__.__name__)
            self._model = None
            self._backend = "hashing-blake2b"

    def encode(self, texts: Sequence[str]) -> list[list[float]]:
        if self._model is not None:
            vectors = self._model.encode(list(texts), normalize_embeddings=True)
            return [list(map(float, vector)) for vector in vectors]
        return [_hashed_embedding(text, settings.embed_dim) for text in texts]


embedder = _Embedder()


def load_embedder() -> None:
    embedder.load()


def cosine(a: Sequence[float], b: Sequence[float]) -> float:
    dot = 0.0
    norm_a = 0.0
    norm_b = 0.0
    for left, right in zip(a, b):
        dot += left * right
        norm_a += left * left
        norm_b += right * right
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (math.sqrt(norm_a) * math.sqrt(norm_b))


# --------------------------------------------------------------------------
# Index
# --------------------------------------------------------------------------
def chunk_document(document_id: str, title: str, content: str, max_chars: int = 700) -> list[dict[str, Any]]:
    sentences = re.split(r"(?<=[.!?])\s+", content.strip())
    chunks: list[dict[str, Any]] = []
    buffer = ""
    for sentence in sentences:
        if len(buffer) + len(sentence) + 1 > max_chars and buffer:
            chunks.append({"documentId": document_id, "title": title, "text": buffer.strip()})
            buffer = sentence
        else:
            buffer = f"{buffer} {sentence}".strip()
    if buffer:
        chunks.append({"documentId": document_id, "title": title, "text": buffer.strip()})
    return chunks


async def catalog_documents() -> list[dict[str, Any]]:
    """Index public catalog knowledge, excluding learner data and answer keys."""
    documents=list(KNOWLEDGE_BASE)
    fields={
        'skills':['name','domain','description','prerequisites','concepts'],
        'careers':['title','description','requirements'],
        'resources':['title','skillName','description','provider','difficulty','duration','url'],
        'projects':['title','description','skillsValidated','prerequisites','deliverables','rubric'],
        'assessments':['title','skillName','description','difficulty','estimatedTime'],
    }
    import json
    for collection, public_fields in fields.items():
        async for item in col(collection).find({}, {'_id':0}):
            content=json.dumps({k:item[k] for k in public_fields if k in item},ensure_ascii=False)
            documents.append({'id':f"kb-catalog-{collection}-{item['id']}",'title':item.get('title',item.get('name',item['id'])),'source':'Platform '+collection+' catalog (curated demo)','year':'','tags':[collection,item.get('skillId',item['id'])],'category':collection,'content':content})
    from .learning_catalog import TOPICS
    from ..seed.external_certifications import CATALOG
    for item in CATALOG:
        documents.append({'id':'kb-certification-'+item['id'],'title':item['name'],'source':item['officialUrl'],
            'year':'','tags':['certifications']+item['categories'],'category':'certifications','content':json.dumps(item,ensure_ascii=False)})
    directory=Path(__file__).resolve().parents[1]/'assets'/'learning'
    for skill_id,topic in TOPICS.items():
        path=directory/(skill_id+'.json')
        if not path.exists():continue
        note=json.loads(path.read_text(encoding='utf-8'))
        content=note['introduction']+'\n'+note['summary']+'\n'+'\n'.join(c['title']+': '+c['explanation'] for c in note['concepts'])
        documents.append({'id':'kb-study-'+skill_id,'title':note['title'],'source':'NexVora AI-assisted study notes; primary reference: '+topic[3],
            'year':'','tags':[skill_id,'learning'],'category':'learning-notes','content':content})
    return documents

async def ensure_index() -> dict[str, Any]:
    """Embed the knowledge base once and persist the vectors in MongoDB."""
    # Skip RAG index building during tests
    if os.getenv("DISABLE_RAG_INDEX") == "true":
        return {"chunks": 0, "backend": embedder.backend, "cached": True, "skipped": True}
    
    load_embedder()
    documents = await catalog_documents()
    version = _kb_version(documents)
    existing = await col("concepts").find_one({"kind": "rag_index"})
    backend = embedder.backend
    if existing and existing.get("backend") == backend and existing.get("version") == version:
        return {"chunks": len(existing.get("chunks", [])), "backend": backend, "cached": True}

    chunks: list[dict[str, Any]] = []
    for document in documents:
        for index, chunk in enumerate(chunk_document(document["id"], document["title"], document["content"])):
            chunks.append(
                {
                    **chunk,
                    "id": f"{document['id']}#{index}",
                    "source": document["source"],
                    "year": document["year"],
                    "tags": document["tags"],
                    "category": document.get("category","curated-guidance"),
                }
            )

    for document in documents:
        await col('rag_documents').update_one({'documentId':document['id']}, {'$set':{**document,'documentId':document['id'],'category':document.get('category','curated-guidance'),'version':version,'metadata':{'tags':document['tags']}}}, upsert=True)
    vectors = embedder.encode([chunk["text"] for chunk in chunks])
    for chunk, vector in zip(chunks, vectors):
        chunk["embedding"] = vector
        chunk['chunkId'] = chunk['id']
        chunk['version'] = version
        chunk.setdefault('category', 'curated-guidance')
        chunk['metadata'] = {'tags':chunk['tags']}
        await col('rag_chunks').update_one({'chunkId':chunk['id']}, {'$set':chunk}, upsert=True)

    await col("concepts").update_one(
        {"kind": "rag_index"},
        {
            "$set": {
                "kind": "rag_index",
                "version": version,
                "backend": backend,
                "chunks": chunks,
                "documents": len(documents),
                "updatedAt": _now(),
            }
        },
        upsert=True,
    )
    try:
        import faiss
        import numpy as np
        index = faiss.IndexFlatIP(len(vectors[0]))
        index.add(np.asarray(vectors,dtype='float32'))
        destination = Path(__file__).resolve().parents[1] / 'rag'
        destination.mkdir(exist_ok=True)
        faiss.write_index(index, str(destination / 'knowledge.faiss'))
    except ImportError:
        pass
    logger.info("RAG index built: %s chunks using %s", len(chunks), backend)
    return {"chunks": len(chunks), "backend": backend, "cached": False}


def _kb_version(documents=None) -> str:
    digest = blake2b(digest_size=8)
    for document in (documents or KNOWLEDGE_BASE):
        digest.update(document["id"].encode())
        digest.update(document["content"].encode())
    return "v3-" + digest.hexdigest()


def _now() -> str:
    from ..security import iso_now

    return iso_now()


async def retrieve(query: str, *, top_k: Optional[int] = None, tags: Optional[list[str]] = None) -> list[dict[str, Any]]:
    """Hybrid lexical + vector retrieval over the local knowledge base."""
    load_embedder()
    top_k = top_k or settings.rag_top_k
    
    # Get RAG index data without blocking for indexing
    record = await col("concepts").find_one({"kind": "rag_index"})
    chunks = (record or {}).get("chunks", [])
    
    # If no indexed chunks, return empty list
    if not chunks:
        return []

    query_vector = embedder.encode([query])[0]
    vector_scores = None
    try:
        import faiss
        import numpy as np
        matrix = np.asarray([c['embedding'] for c in chunks], dtype='float32')
        index = faiss.IndexFlatIP(matrix.shape[1])
        index.add(matrix)
        scores, positions = index.search(np.asarray([query_vector],dtype='float32'),len(chunks))
        vector_scores = {int(pos):float(score) for pos,score in zip(positions[0],scores[0])}
    except ImportError:
        pass  # Honest CPU cosine implementation remains available offline.

    query_tokens = set(_tokenize(query))

    scored: list[tuple[float, dict[str, Any]]] = []
    for chunk_position, chunk in enumerate(chunks):
        if tags and not (set(chunk.get("tags", [])) & set(tags)):
            # Explicit metadata constraints must exclude unrelated documents.
            continue
        else:
            tag_bonus = 0.12 if tags else 0.0

        vector_score = vector_scores[chunk_position] if vector_scores is not None else cosine(query_vector, chunk.get("embedding", []))
        chunk_tokens = set(_tokenize(chunk.get("text", "")))
        overlap = len(query_tokens & chunk_tokens) / max(1, len(query_tokens))
        score = 0.65 * vector_score + 0.35 * overlap + tag_bonus
        scored.append((score, chunk))

    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [
        {
            "id": chunk["id"],
            "documentId": chunk["documentId"],
            "title": chunk["title"],
            "source": chunk.get("source", ""),
            "year": chunk.get("year", ""),
            "text": chunk["text"],
            "score": round(score, 4),
        }
        for score, chunk in scored[:top_k] if score >= .24
    ]


def citations(passages: list[dict[str, Any]]) -> list[dict[str, str]]:
    seen: set[str] = set()
    output: list[dict[str, str]] = []
    for passage in passages:
        key = passage["title"]
        if key in seen:
            continue
        seen.add(key)
        output.append({"documentId": passage["documentId"], "chunkId": passage["id"], "title": passage["title"], "source": passage.get("source", ""), "year": passage.get("year", "")})
    return output


async def health() -> dict[str, Any]:
    record = await col("concepts").find_one({"kind": "rag_index"})
    return {
        "backend": embedder.backend,
        "dimensions": settings.embed_dim,
        "vectorIndex": "faiss" if __import__("importlib.util",fromlist=["find_spec"]).find_spec("faiss") else "exact-cosine",
        "documents": (record or {}).get("documents", len(KNOWLEDGE_BASE)),
        "chunks": len((record or {}).get("chunks", [])),
        "indexed": bool(record),
    }
