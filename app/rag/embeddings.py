from sentence_transformers import SentenceTransformer
from typing import List

# all-MiniLM-L6-v2 -- fast, small, good enough for semantic search
_model = None

def get_model():
    global _model
    if not _model:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model

def embed(texts: List[str]) -> List[List[float]]:
    return get_model().encode(texts, show_progress_bar=False).tolist()

def embed_one(text: str) -> List[float]:
    return get_model().encode([text], show_progress_bar=False)[0].tolist()