import chromadb
import hashlib
from typing import List, Dict
from app.rag.embeddings import embed_one

# persistent store — data accumulates over time, never deleted
# upsert deduplicates by content hash so no duplicates
CHROMA_PATH = "./chroma_db"
COLLECTION = "researchnu"

def get_col():
    c = chromadb.PersistentClient(path=CHROMA_PATH)
    return c.get_or_create_collection(
        COLLECTION,
        metadata={"hnsw:space": "cosine"}
    )

def chunk(text: str, size: int = 400, overlap: int = 50) -> List[str]:
    # split into overlapping passages for retrieval
    words = text.split()
    chunks = []
    for i in range(0, len(words), size - overlap):
        c = " ".join(words[i:i + size])
        if len(c.strip()) > 30:
            chunks.append(c)
    return chunks

def ingest(papers: List[Dict], source: str = "unknown"):
    col = get_col()
    docs, embs, metas, ids = [], [], [], []
    seen_ids = set()
    for p in papers:
        text = f"{p.get('title', '')} {p.get('abstract', '')}"
        for c in chunk(text):
            doc_id = hashlib.md5(c.encode()).hexdigest()
            # skip duplicates within this batch
            if doc_id in seen_ids:
                continue
            seen_ids.add(doc_id)
            docs.append(c)
            embs.append(embed_one(c))
            metas.append({
                "title": p.get("title", ""),
                "url": p.get("url", ""),
                "year": str(p.get("year", "")),
                "source": source
            })
            ids.append(doc_id)
    if docs:
        col.upsert(documents=docs, embeddings=embs, metadatas=metas, ids=ids)
        print(f"ingested {len(docs)} chunks [{source}]")