"""
ResearchNu — Query Rewriter Agent (facade)
===========================================
Agent 4 of 7. Corrective RAG query rewriting (Shi et al., 2024).

Invoked only when the grader finds too few relevant chunks. Uses an LLM to
broaden, rephrase, or add synonyms to the current query based on the
grader's rewrite_suggestion. After rewriting, control returns to the
retriever for a second fetch attempt.

Full implementation: app.agents.pipeline → query_rewriter_agent()
"""

from app.agents.pipeline import query_rewriter_agent as rewriter_agent  # noqa: F401

__all__ = ["rewriter_agent"]