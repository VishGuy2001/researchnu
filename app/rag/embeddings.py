from sentence_transformers import SentenceTransformer
from typing import List

# all-MiniLM-L6-v2 — 80MB, fast, strong semantic search
# loads once and stays in memory
_model = None

def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model

def embed(texts: List[str]) -> List[List[float]]:
    # text → 384-dim dense vector
    return get_model().encode(texts, convert_to_numpy=True).tolist()

def embed_one(text: str) -> List[float]:
    return embed([text])[0]