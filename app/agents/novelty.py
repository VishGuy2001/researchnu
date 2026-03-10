"""
ResearchNu — Novelty Agent (facade)
=====================================
Agent 5 of 7 (runs in parallel with synthesis).

Scores the research idea across 4 dimensions:
  - score (0-100): overall novelty
  - coverage_density (0-1): how saturated the space is
  - recency_score (0-1): computed from avg publication year of evidence
  - cross_domain_novelty (0-1): novelty across different fields

Outputs pursue / pivot / abandon recommendation with rationale.
Runs concurrently with synthesis_agent on the same chunks — saves ~4s.

Full implementation: app.agents.pipeline → _run_novelty(), synthesis_novelty_agent()
"""

from app.agents.pipeline import (  # noqa: F401
    NoveltyOutput,
    _run_novelty as run_novelty,
    synthesis_novelty_agent as novelty_agent,
)

__all__ = ["NoveltyOutput", "run_novelty", "novelty_agent"]