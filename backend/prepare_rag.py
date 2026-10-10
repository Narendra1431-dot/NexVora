"""Explicit optional model acquisition; never called by a web request."""
from sentence_transformers import SentenceTransformer
from app.config import settings
model=SentenceTransformer(settings.embed_model, trust_remote_code=False)
print('Embedding model ready:',settings.embed_model,'dimensions:',model.get_sentence_embedding_dimension())
