import chromadb
from rank_bm25 import BM25Okapi
from typing import List, Dict
from app.rag.embeddings import embed_one

CHROMA_PATH = "./chroma_db"
COLLECTION = "researchnu"
CONFIDENCE_THRESHOLD = 0.15  # lowered -- was filtering too aggressively

def get_col():
    c = chromadb.PersistentClient(path=CHROMA_PATH)
    return c.get_or_create_collection(COLLECTION, metadata={"hnsw:space": "cosine"})

def semantic_search(query: str, top_k: int = 20) -> List[Dict]:
    col = get_col()
    if col.count() == 0:
        return []
    q_emb = embed_one(query)
    r = col.query(query_embeddings=[q_emb], n_results=min(top_k, col.count()))
    results = []
    for i, doc in enumerate(r["documents"][0]):
        dist = r["distances"][0][i]
        score = 1 - dist  # cosine distance to similarity
        if score >= CONFIDENCE_THRESHOLD:
            meta = r["metadatas"][0][i]
            results.append({
                "content": doc,
                "title": meta.get("title", ""),
                "url": meta.get("url", ""),
                "source": meta.get("source", ""),
                "year": meta.get("year", ""),
                "score": round(score, 4),
            })
    return results

def bm25_search(query: str, candidates: List[Dict], top_k: int = 20) -> List[Dict]:
    if not candidates:
        return []
    corpus = [c["content"].split() for c in candidates]
    bm25 = BM25Okapi(corpus)
    scores = bm25.get_scores(query.split())
    ranked = sorted(zip(scores, candidates), key=lambda x: x[0], reverse=True)
    return [c for _, c in ranked[:top_k]]

def hybrid_search(query: str, top_k: int = 10) -> List[Dict]:
    # semantic first, then bm25 rerank, then RRF fusion
    sem = semantic_search(query, top_k=top_k * 2)
    if not sem:
        return []
    bm = bm25_search(query, sem, top_k=top_k * 2)

    # RRF fusion
    scores: Dict[str, float] = {}
    urls: Dict[str, Dict] = {}
    k = 60  # RRF constant
    for rank, item in enumerate(sem):
        key = item["url"] or item["title"]
        scores[key] = scores.get(key, 0) + 1 / (k + rank + 1)
        urls[key] = item
    for rank, item in enumerate(bm):
        key = item["url"] or item["title"]
        scores[key] = scores.get(key, 0) + 1 / (k + rank + 1)
        urls[key] = item

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [urls[key] for key, _ in ranked[:top_k]]