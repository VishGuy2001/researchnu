"""
ResearchNu — Reasoner / Synthesis Agent (facade)
==================================================
Agent 5 of 7 (runs in parallel with novelty).

Synthesizes multi-source evidence into structured output:
  - key_findings: cited findings with [N] inline references
  - research_gaps: specific non-obvious gaps in the literature
  - conflicting_evidence: contradictions across sources
  - confidence_level: high / medium / low with rationale
  - detailed_answer: 300+ word substantive analysis with citations

Also houses the hallucination checker (Agent 6, Self-RAG):
  - Verifies the generated answer is grounded in retrieved evidence
  - Hallucinated answers trigger regeneration (max 1 retry)

Full implementation: app.agents.pipeline → _run_synthesis(), hallucination_checker_agent()
"""

from app.agents.pipeline import (  # noqa: F401
    SynthesisOutput,
    HallucinationVerdict,
    _run_synthesis as run_synthesis,
    hallucination_checker_agent as reasoner_agent,
    synthesis_novelty_agent,
)

__all__ = [
    "SynthesisOutput",
    "HallucinationVerdict",
    "run_synthesis",
    "reasoner_agent",
    "synthesis_novelty_agent",
]