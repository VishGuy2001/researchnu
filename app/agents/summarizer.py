"""
ResearchNu — Summarizer Agent (facade)
========================================
Agent 7 of 7. Final output stage.

Produces a plain-English 2-3 sentence summary (max 120 words) for
non-expert readers. Weaves together the novelty score, top key findings,
and research gaps into a flowing narrative that answers: what exists,
what's missing, and whether this is worth pursuing.

Only runs after the hallucination checker confirms the answer is grounded.

Full implementation: app.agents.pipeline → summarizer_agent()
"""

from app.agents.pipeline import summarizer_agent  # noqa: F401

__all__ = ["summarizer_agent"]