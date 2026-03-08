from rank_bm25 import BM25Okapi
from typing import List, Dict
from app.rag.embeddings import embed_one
from app.rag.ingestor import get_col

CONFIDENCE_THRESHOLD = 0.15

def semantic_search(query: str, top_k: int = 10) -> List[Dict]:
    # dense retrieval -- cosine similarity in embedding space
    col = get_col()
    res = col.query(
        query_embeddings=[embed_one(query)],
        n_results=top_k,
        include=["documents", "metadatas", "distances"]
    )
    out = []
    for doc, meta, dist in zip(res["documents"][0], res["metadatas"][0], res["distances"][0]):
        score = round(1 - dist, 4)
        if score < CONFIDENCE_THRESHOLD:
            continue
        out.append({
            "content": doc,
            "title": meta.get("title", ""),
            "url": meta.get("url", ""),
            "source": meta.get("source", ""),
            "year": meta.get("year", ""),
            "score": score
        })
    return out

def hybrid_search(query: str, top_k: int = 8) -> List[Dict]:
    # hybrid retrieval -- dense + sparse fused with reciprocal rank fusion
    sem = semantic_search(query, top_k * 2)
    if not sem:
        return []

    # sparse retrieval -- BM25 keyword matching
    bm25 = BM25Okapi([r["content"].lower().split() for r in sem])
    bm25_scores = bm25.get_scores(query.lower().split()).tolist()

    # reciprocal rank fusion -- K=60 is standard
    K = 60
    fused = {}
    for rank, r in enumerate(sem):
        key = r["url"] + r["content"][:40]
        fused[key] = {"r": r, "score": 1 / (K + rank + 1)}

    # sort by float score only, not dict
    scored_pairs = sorted(zip(bm25_scores, sem), key=lambda x: x[0], reverse=True)
    for rank, (score, r) in enumerate(scored_pairs):
        key = r["url"] + r["content"][:40]
        if key in fused:
            fused[key]["score"] += 1 / (K + rank + 1)

    ranked = sorted(fused.values(), key=lambda x: x["score"], reverse=True)
    return [v["r"] for v in ranked][:top_k]