from sentence_transformers import SentenceTransformer
from app.settings import settings

_model: SentenceTransformer | None = None

def get_embedder() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(settings.EMBEDDINGS_MODEL)
    return _model

def embed_text(text: str) -> list[float]:
    model = get_embedder()
    vec = model.encode([text])[0]
    return vec.tolist()
