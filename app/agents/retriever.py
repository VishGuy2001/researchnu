"""
ResearchNu — Retriever Agent (facade)
=======================================
Agent 2 of 7. Parallel source fetching (Anthropic 2025 best practices).

Fans out concurrently to all active sources using ThreadPoolExecutor with
per-source circuit breakers and timeouts. Ingests results into ChromaDB,
then runs hybrid BM25+semantic RRF search to return ranked chunks.
Falls back to cache on retry attempts (Corrective RAG loop).

Full implementation: app.agents.pipeline → retriever_agent()
For direct RAG search: app.rag.retriever → hybrid_search()
"""

from app.agents.pipeline import (  # noqa: F401
    retriever_agent,
    _fetch_source as fetch_source,
    SOURCE_FETCH_TIMEOUT,
    MAX_SOURCE_WORKERS,
    TOP_K_CHUNKS,
    MIN_RELEVANT_CHUNKS,
)

__all__ = [
    "retriever_agent",
    "fetch_source",
    "SOURCE_FETCH_TIMEOUT",
    "MAX_SOURCE_WORKERS",
    "TOP_K_CHUNKS",
    "MIN_RELEVANT_CHUNKS",
]