"""
Unit tests for each of the 7 pipeline agents.
Tests each agent in isolation with mock state.
Run: pytest tests/test_agents.py -v
"""
import pytest
from dotenv import load_dotenv
load_dotenv()

from app.agents.pipeline import (
    ResearchState,
    planner_agent,
    retriever_agent,
    grader_agent,
    query_rewriter_agent,
    synthesis_novelty_agent,
    hallucination_checker_agent,
    summarizer_agent,
    SOURCE_REGISTRY,
)

# ── helpers ────────────────────────────────────────────────────────────────

def base_state(**overrides) -> ResearchState:
    state: ResearchState = {
        "query":                 "scoliosis machine learning prediction",
        "user_type":             "researcher",
        "privacy_mode":          False,
        "focus_areas":           [],
        "query_plan":            None,
        "active_sources":        [],
        "current_query":         "scoliosis machine learning prediction",
        "chunks":                [],
        "sources_used":          [],
        "retrieval_attempts":    0,
        "grader_output":         None,
        "relevant_chunks":       [],
        "synthesis":             None,
        "citations":             [],
        "generation_attempts":   0,
        "novelty":               None,
        "hallucination_verdict": None,
        "summary":               "",
        "detailed_answer":       "",
        "novelty_score":         0.0,
        "novelty_report":        "",
        "pipeline_trace":        [],
    }
    state.update(overrides)
    return state


SAMPLE_CHUNKS = [
    {
        "title":            "Deep learning for scoliosis detection",
        "content":          "CNN-based approach achieves 94% accuracy on scoliosis X-ray classification.",
        "url":              "https://example.com/1",
        "source":           "pubmed",
        "year":             "2023",
        "relevance_score":  0.9,
    },
    {
        "title":            "Machine learning spinal curvature measurement",
        "content":          "Automated Cobb angle measurement using deep learning outperforms manual methods.",
        "url":              "https://example.com/2",
        "source":           "arxiv",
        "year":             "2022",
        "relevance_score":  0.85,
    },
    {
        "title":            "Random forest classification of spine pathology",
        "content":          "Ensemble methods applied to MRI features for scoliosis severity grading.",
        "url":              "https://example.com/3",
        "source":           "openalex",
        "year":             "2021",
        "relevance_score":  0.8,
    },
]

# ── Agent 1: Planner ───────────────────────────────────────────────────────

def test_planner_returns_state():
    result = planner_agent(base_state())
    assert "query_plan" in result
    assert "active_sources" in result
    assert "current_query" in result


def test_planner_sets_active_sources():
    result = planner_agent(base_state())
    assert len(result["active_sources"]) > 0
    for s in result["active_sources"]:
        assert s in SOURCE_REGISTRY


def test_planner_sets_intent():
    result = planner_agent(base_state())
    plan = result["query_plan"]
    assert "intent" in plan
    assert plan["intent"] in [
        "literature_review", "patent_search", "grant_search",
        "market_analysis", "clinical_search", "policy", "general"
    ]


def test_planner_with_focus_areas():
    result = planner_agent(base_state(focus_areas=["clinical applications", "cost"]))
    assert result["query_plan"] is not None


def test_planner_founder_profile():
    result = planner_agent(base_state(user_type="founder"))
    # founder profile should prioritize patent/market sources
    sources = result["active_sources"]
    assert any(s in sources for s in ["google_patents", "patents_lens", "market_yc"])

# ── Agent 2: Retriever ─────────────────────────────────────────────────────

def test_retriever_returns_state():
    state = base_state(active_sources=["pubmed", "arxiv"])
    result = retriever_agent(state)
    assert "chunks" in result
    assert "sources_used" in result
    assert isinstance(result["chunks"], list)


def test_retriever_increments_attempts():
    state = base_state(active_sources=["pubmed"], retrieval_attempts=0)
    result = retriever_agent(state)
    assert result["retrieval_attempts"] == 1


def test_retriever_empty_sources():
    state = base_state(active_sources=[])
    result = retriever_agent(state)
    assert isinstance(result["chunks"], list)

# ── Agent 3: Grader ────────────────────────────────────────────────────────

def test_grader_no_chunks():
    result = grader_agent(base_state(chunks=[]))
    assert result["grader_output"]["should_rewrite"] is True
    assert result["relevant_chunks"] == []


def test_grader_with_chunks():
    result = grader_agent(base_state(chunks=SAMPLE_CHUNKS))
    assert "grader_output" in result
    assert "relevant_chunks" in result
    assert isinstance(result["relevant_chunks"], list)


def test_grader_output_structure():
    result = grader_agent(base_state(chunks=SAMPLE_CHUNKS))
    out = result["grader_output"]
    assert "should_rewrite" in out
    assert "relevant_count" in out
    assert "irrelevant_count" in out


def test_grader_fallback_passes_chunks():
    # even if LLM fails, chunks should pass through
    result = grader_agent(base_state(chunks=SAMPLE_CHUNKS))
    assert len(result["relevant_chunks"]) > 0

# ── Agent 4: Query Rewriter ────────────────────────────────────────────────

def test_rewriter_changes_query():
    state = base_state(
        current_query="scoliosis ML",
        grader_output={"should_rewrite": True, "rewrite_suggestion": "spinal curvature deep learning prediction"},
    )
    result = query_rewriter_agent(state)
    assert "current_query" in result
    assert isinstance(result["current_query"], str)
    assert len(result["current_query"]) > 0


def test_rewriter_fallback_on_empty_suggestion():
    state = base_state(
        grader_output={"should_rewrite": True, "rewrite_suggestion": ""},
    )
    result = query_rewriter_agent(state)
    assert len(result["current_query"]) > 0

# ── Agent 5: Synthesis + Novelty ───────────────────────────────────────────

def test_synthesis_novelty_with_chunks():
    result = synthesis_novelty_agent(base_state(
        relevant_chunks=SAMPLE_CHUNKS,
        chunks=SAMPLE_CHUNKS,
    ))
    assert "synthesis" in result
    assert "novelty" in result
    assert "novelty_score" in result
    assert "detailed_answer" in result
    assert result["novelty_score"] >= 0
    assert result["novelty_score"] <= 100


def test_synthesis_has_key_findings():
    result = synthesis_novelty_agent(base_state(relevant_chunks=SAMPLE_CHUNKS))
    assert "key_findings" in result["synthesis"]
    assert isinstance(result["synthesis"]["key_findings"], list)


def test_novelty_has_recommendation():
    result = synthesis_novelty_agent(base_state(relevant_chunks=SAMPLE_CHUNKS))
    assert "recommendation" in result["novelty"]
    assert result["novelty"]["recommendation"] in ["pursue", "pivot", "abandon"]


def test_synthesis_no_chunks_fallback():
    result = synthesis_novelty_agent(base_state(relevant_chunks=[], chunks=[]))
    assert "detailed_answer" in result

# ── Agent 6: Hallucination Checker ────────────────────────────────────────

def test_hallucination_checker_no_content():
    result = hallucination_checker_agent(base_state())
    verdict = result["hallucination_verdict"]
    assert verdict["is_grounded"] is True  # skipped = assume grounded


def test_hallucination_checker_with_content():
    result = hallucination_checker_agent(base_state(
        detailed_answer="Deep learning achieves 94% accuracy for scoliosis detection [1].",
        relevant_chunks=SAMPLE_CHUNKS,
    ))
    assert "hallucination_verdict" in result
    assert "is_grounded" in result["hallucination_verdict"]
    assert isinstance(result["hallucination_verdict"]["is_grounded"], bool)


def test_hallucination_increments_attempts():
    result = hallucination_checker_agent(base_state(
        detailed_answer="Test answer.",
        relevant_chunks=SAMPLE_CHUNKS,
        generation_attempts=0,
    ))
    assert result["generation_attempts"] == 1

# ── Agent 7: Summarizer ────────────────────────────────────────────────────

def test_summarizer_returns_summary():
    result = summarizer_agent(base_state(
        synthesis={
            "key_findings": ["Deep learning achieves 94% accuracy [1]"],
            "research_gaps": ["No large-scale prospective studies"],
        },
        detailed_answer="Deep learning methods for scoliosis...",
        novelty_score=72.5,
        sources_used=["pubmed", "arxiv"],
        citations=SAMPLE_CHUNKS,
    ))
    assert "summary" in result
    assert isinstance(result["summary"], str)
    assert len(result["summary"]) > 0


def test_summarizer_fallback():
    # minimal state — should still return something
    result = summarizer_agent(base_state(novelty_score=50.0))
    assert len(result["summary"]) > 0