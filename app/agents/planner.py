"""
ResearchNu — Planner Agent (facade)
=====================================
Agent 1 of 7. Adaptive RAG routing (Jeong et al., 2024).

Classifies query intent, builds 2-3 optimized sub-queries, and dynamically
selects sources from the 26-source registry based on intent type and user
profile. Intent-based boosting ensures patent queries hit patent sources
first, clinical queries hit PubMed/ClinicalTrials first, etc.

Full implementation: app.agents.pipeline → planner_agent()
"""

from app.agents.pipeline import (  # noqa: F401
    planner_agent,
    QueryPlan,
    SOURCE_PROFILES,
    SOURCE_REGISTRY,
)

__all__ = ["planner_agent", "QueryPlan", "SOURCE_PROFILES", "SOURCE_REGISTRY"]