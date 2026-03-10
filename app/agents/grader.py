"""
ResearchNu — Grader Agent (facade)
=====================================
Agent 3 of 7. Corrective RAG document grading (Shi et al., 2024).

Grades every retrieved chunk for relevance to the current query using an
LLM. If fewer than MIN_RELEVANT_CHUNKS pass, sets should_rewrite=True to
trigger the query rewriter and a second retrieval attempt (max 2 retries).

Full implementation: app.agents.pipeline → grader_agent()
"""

from app.agents.pipeline import (  # noqa: F401
    grader_agent,
    DocumentGrade,
    GraderOutput,
    MIN_RELEVANT_CHUNKS,
)

__all__ = ["grader_agent", "DocumentGrade", "GraderOutput", "MIN_RELEVANT_CHUNKS"]