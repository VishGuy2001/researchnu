"""
Tests for RAG pipeline — ingestor and retriever.
Run: pytest tests/test_rag.py -v
"""
import pytest
from dotenv import load_dotenv
load_dotenv()


SAMPLE_PAPERS = [
    {
        "title": "Deep Learning for Scoliosis Detection",
        "abstract": "We propose a CNN-based approach for automated scoliosis detection from X-rays.",
        "url": "https://example.com/paper1",
        "year": "2023",
        "source": "test",
        "content": "Deep learning methods for scoliosis detection using convolutional neural networks.",
    },
    {
        "title": "Machine Learning in Spinal Imaging",
        "abstract": "A review of ML methods applied to spinal imaging and diagnosis.",
        "url": "https://example.com/paper2",
        "year": "2022",
        "source": "test",
        "content": "Machine learning approaches for spinal imaging analysis and automated diagnosis.",
    },
]


def test_ingest():
    from app.rag.ingestor import ingest
    count = ingest(SAMPLE_PAPERS, source="test")
    assert count >= 0  # returns number of chunks ingested


def test_hybrid_search_returns_list():
    from app.rag.retriever import hybrid_search
    results = hybrid_search("scoliosis machine learning", top_k=5)
    assert isinstance(results, list)


def test_hybrid_search_structure():
    from app.rag.ingestor import ingest
    from app.rag.retriever import hybrid_search
    ingest(SAMPLE_PAPERS, source="test")
    results = hybrid_search("scoliosis deep learning", top_k=5)
    if results:
        r = results[0]
        assert "title" in r
        assert "content" in r
        assert "source" in r
        assert "url" in r
        assert "year" in r


def test_semantic_search():
    from app.rag.retriever import semantic_search
    results = semantic_search("neural network spine", top_k=5)
    assert isinstance(results, list)


def test_bm25_search():
    from app.rag.retriever import bm25_search, semantic_search
    candidates = semantic_search("machine learning", top_k=10)
    results = bm25_search("scoliosis", candidates, top_k=5)
    assert isinstance(results, list)