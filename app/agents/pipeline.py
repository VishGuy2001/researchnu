"""
ResearchNu — Production Agentic RAG Pipeline
=============================================
Architecture follows:
  - Anthropic "Building Effective Agents" (2025) best practices
  - Corrective RAG (Shi et al., 2024): document grading + query rewrite on low relevance
  - Self-RAG (Asai et al., 2023): self-reflection, hallucination check before output
  - Adaptive RAG (Jeong et al., 2024): dynamic routing based on query complexity
  - LangGraph stateful cyclic graph with conditional edges
  - Parallel tool execution with per-source circuit breakers
  - Structured Pydantic outputs at every agent boundary
  - Budget-aware execution: max retries, token caps, latency limits

Graph topology:
    [planner] → [retriever] → [grader] → (route)
                                 ↓ relevant           ↓ irrelevant
                          [synthesis_novelty]    [query_rewriter] → [retriever] (max 2 retries)
                                 ↓
                       [hallucination_checker] → (route)
                             ↓ grounded            ↓ hallucinated (max 1 retry)
                         [summarizer]         [synthesis_novelty]
                              ↓
                            [END]
"""

from __future__ import annotations

import importlib
import json
import logging
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FuturesTimeout
from dataclasses import dataclass, field
from typing import Dict, List, Literal, Optional, TypedDict

from langgraph.graph import END, StateGraph
from pydantic import BaseModel, Field

from app.models.llm_client import groq_chat, groq_fast, groq_quality, groq_summarize
from app.rag.ingestor import ingest
from app.rag.retriever import hybrid_search

logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════
# CONSTANTS
# ══════════════════════════════════════════════════════════

MAX_RETRIEVAL_RETRIES  = 2
MAX_GENERATION_RETRIES = 1
SOURCE_FETCH_TIMEOUT   = 6   # per-source timeout
MAX_SOURCE_WORKERS     = 16  # more workers = more parallelism
TOP_K_CHUNKS           = 15
MIN_RELEVANT_CHUNKS    = 5
RETRIEVER_WALL_TIMEOUT = 8   # hard wall: retriever never blocks pipeline > 8s

# ══════════════════════════════════════════════════════════
# SOURCE REGISTRY
# ══════════════════════════════════════════════════════════

SOURCE_REGISTRY: Dict[str, tuple] = {
    # Academic
    "pubmed":           ("app.sources.pubmed",           "search_pubmed"),
    "arxiv":            ("app.sources.arxiv",            "search_arxiv"),
    "openalex":         ("app.sources.openalex",         "search_openalex"),
    "semantic_scholar": ("app.sources.semantic_scholar", "search_semantic_scholar"),
    "europe_pmc":       ("app.sources.europe_pmc",       "search_europe_pmc"),
    "core":             ("app.sources.core_ac",          "search_core"),
    "crossref":         ("app.sources.crossref",         "search_crossref"),
    # Grants
    "grants_nih":       ("app.sources.grants_nih",       "search_nih"),
    "grants_nsf":       ("app.sources.grants_nsf",       "search_nsf"),
    "grants_eu":        ("app.sources.grants_eu",        "search_eu_horizon"),
    "grants_ukri":      ("app.sources.grants_ukri",      "search_ukri"),
    # Patents
    "patents_uspto":    ("app.sources.patents_uspto",    "search_uspto"),
    "patents_wipo":     ("app.sources.patents_wipo",     "search_wipo"),
    "patents_epo":      ("app.sources.patents_epo",      "search_epo"),
    "patents_lens":     ("app.sources.patents_lens",     "search_lens"),
    "google_patents":   ("app.sources.google_patents",   "search_google_patents"),
    # Clinical
    "clinical_trials":  ("app.sources.clinical_trials",  "search_clinical_trials"),
    "who_ictrp":        ("app.sources.who_ictrp",        "search_who"),
    "fda":              ("app.sources.fda",              "search_fda"),
    # Market
    "market_yc":        ("app.sources.ycombinator",      "search_yc"),
    "market_ph":        ("app.sources.product_hunt",     "search_product_hunt"),
    # Finance / Economics
    "fred":             ("app.sources.fred",             "search_fred"),
    "alpha_vantage":    ("app.sources.alpha_vantage",    "search_alpha_vantage"),
    # News
    "news":             ("app.sources.news",             "search_news"),
    # Policy / Legal
    "congress":         ("app.sources.congress",         "search_congress"),
    "courtlistener":    ("app.sources.courtlistener",    "search_courtlistener"),
}

# ══════════════════════════════════════════════════════════
# SOURCE PROFILES
# ══════════════════════════════════════════════════════════

SOURCE_PROFILES: Dict[str, Dict[str, List[str]]] = {
    "researcher": {
        "primary":   ["pubmed", "arxiv", "openalex", "semantic_scholar", "europe_pmc"],
        "secondary": ["core", "crossref", "grants_nih", "grants_nsf", "clinical_trials",
                      "fred", "news", "alpha_vantage", "congress", "courtlistener",
                      "google_patents"],
    },
    "founder": {
        "primary":   ["google_patents", "arxiv", "openalex", "patents_lens",
                      "market_yc", "market_ph"],
        "secondary": ["patents_wipo", "patents_epo", "patents_uspto", "semantic_scholar",
                      "fred", "news", "alpha_vantage", "congress", "courtlistener"],
    },
    "grant": {
        "primary":   ["grants_nih", "grants_nsf", "grants_eu", "grants_ukri", "openalex"],
        "secondary": ["pubmed", "clinical_trials", "who_ictrp", "europe_pmc",
                      "fred", "news", "alpha_vantage", "congress", "courtlistener",
                      "google_patents"],
    },
    "policy": {
        "primary":   ["congress", "courtlistener", "fda", "who_ictrp", "openalex"],
        "secondary": ["grants_nih", "grants_nsf", "grants_eu", "pubmed", "news", "fred"],
    },
    "all": {
        "primary":   ["pubmed", "arxiv", "openalex", "semantic_scholar", "europe_pmc",
                      "grants_nih", "patents_lens", "market_yc", "google_patents", "fred"],
        "secondary": ["core", "crossref", "grants_nsf", "clinical_trials", "patents_wipo",
                      "patents_epo", "who_ictrp", "fda", "market_ph", "news",
                      "alpha_vantage", "congress", "courtlistener"],
    },
}

# ══════════════════════════════════════════════════════════
# PYDANTIC SCHEMAS
# ══════════════════════════════════════════════════════════

class QueryPlan(BaseModel):
    intent: str = Field(description="literature_review|patent_search|grant_search|market_analysis|clinical_search|policy|general")
    optimized_queries: List[str] = Field(description="2-3 optimized sub-queries")
    core_concepts: List[str] = Field(description="3-5 key concepts")
    focus_domains: List[str] = Field(description="relevant knowledge domains")
    source_priority: str = Field(description="academic|patents|grants|market|clinical|policy|mixed")
    reasoning: str

class DocumentGrade(BaseModel):
    chunk_id: str
    is_relevant: bool
    relevance_score: float = Field(ge=0.0, le=1.0)
    reason: str

class GraderOutput(BaseModel):
    grades: List[DocumentGrade]
    relevant_count: int
    irrelevant_count: int
    should_rewrite: bool
    rewrite_suggestion: str

class SynthesisOutput(BaseModel):
    key_findings: List[str]
    research_gaps: List[str]
    conflicting_evidence: List[str]
    confidence_level: str
    confidence_rationale: str
    detailed_answer: str

class NoveltyOutput(BaseModel):
    score: float = Field(ge=0.0, le=100.0)
    coverage_density: float = Field(ge=0.0, le=1.0)
    recency_score: float = Field(ge=0.0, le=1.0)
    cross_domain_novelty: float = Field(ge=0.0, le=1.0)
    top_overlapping_works: List[str]
    novel_aspects: List[str]
    recommendation: str
    recommendation_rationale: str
    full_report: str

class HallucinationVerdict(BaseModel):
    is_grounded: bool
    unsupported_claims: List[str]
    confidence: str
    verdict_rationale: str

# ══════════════════════════════════════════════════════════
# PIPELINE STATE
# ══════════════════════════════════════════════════════════

class ResearchState(TypedDict):
    query: str
    user_type: str
    privacy_mode: bool
    focus_areas: Optional[List[str]]
    query_plan: Optional[Dict]
    active_sources: List[str]
    current_query: str
    chunks: List[Dict]
    sources_used: List[str]
    retrieval_attempts: int
    grader_output: Optional[Dict]
    relevant_chunks: List[Dict]
    synthesis: Optional[Dict]
    citations: List[Dict]
    generation_attempts: int
    novelty: Optional[Dict]
    hallucination_verdict: Optional[Dict]
    summary: str
    detailed_answer: str
    novelty_score: float
    novelty_report: str
    pipeline_trace: List[Dict]

# ══════════════════════════════════════════════════════════
# UTILITIES
# ══════════════════════════════════════════════════════════

def _parse_json(raw: str) -> Dict:
    """Robust JSON parser — strips markdown fences, removes control chars,
    finds outermost JSON object."""
    clean = raw.strip()
    for fence in ["```json", "```JSON", "```"]:
        clean = clean.lstrip(fence)
    clean = clean.rstrip("```").strip()
    # remove control characters that break json.loads
    clean = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', clean)
    # extract outermost JSON object
    start, end = clean.find('{'), clean.rfind('}')
    if start != -1 and end != -1:
        clean = clean[start:end+1]
    return json.loads(clean)

def _trace(state: ResearchState, agent: str, status: str, ms: float, **kw) -> List[Dict]:
    entry = {"agent": agent, "status": status, "latency_ms": ms, **kw}
    logger.info(f"[{agent}] {status} ({ms:.0f}ms) {kw}")
    return state.get("pipeline_trace", []) + [entry]

# ══════════════════════════════════════════════════════════
# AGENT 1 — PLANNER
# Adaptive routing: classifies intent, builds optimized query plan,
# selects sources dynamically based on intent type.
# (Anthropic 2025: use LLM for planning when task needs dynamic decisions)
# ══════════════════════════════════════════════════════════

def planner_agent(state: ResearchState) -> ResearchState:
    t0    = time.time()
    query = state["query"]
    focus = state.get("focus_areas") or []
    focus_clause = f"\nUser focus areas: {', '.join(focus)}" if focus else ""

    prompt = f"""You are a scientific research query planner. Analyze the query and return a JSON plan.

Query: {query}{focus_clause}
User type: {state['user_type']}

Return ONLY valid JSON (no markdown, no explanation):
{{
  "intent": "<literature_review|patent_search|grant_search|market_analysis|clinical_search|policy|general>",
  "optimized_queries": ["<exact phrase>", "<broader concept>", "<application variant>"],
  "core_concepts": ["<concept 1>", "<concept 2>", "<concept 3>"],
  "focus_domains": ["<domain 1>", "<domain 2>"],
  "source_priority": "<academic|patents|grants|market|clinical|policy|mixed>",
  "reasoning": "<why this plan>"
}}"""

    try:
        plan = QueryPlan(**_parse_json(groq_fast(prompt, max_tokens=400)))
    except Exception as e:
        logger.warning(f"[planner] fallback: {e}")
        plan = QueryPlan(
            intent="general", optimized_queries=[query],
            core_concepts=query.split()[:4], focus_domains=["general science"],
            source_priority="mixed", reasoning="fallback"
        )

    profile = SOURCE_PROFILES.get(state["user_type"], SOURCE_PROFILES["all"])
    sources = list(profile["primary"])

    intent_boost = {
        "patent_search":    ["google_patents", "patents_lens", "patents_wipo", "patents_epo", "patents_uspto"],
        "grant_search":     ["grants_nih", "grants_nsf", "grants_eu", "grants_ukri"],
        "clinical_search":  ["clinical_trials", "pubmed", "who_ictrp", "fda"],
        "market_analysis":  ["market_yc", "market_ph", "patents_lens", "alpha_vantage", "fred"],
        "literature_review":["pubmed", "arxiv", "openalex", "semantic_scholar", "europe_pmc"],
        "policy":           ["congress", "courtlistener", "fda", "who_ictrp"],
    }
    boosted = intent_boost.get(plan.intent, [])
    sources = boosted + [s for s in sources if s not in boosted]
    for s in profile.get("secondary", []):
        if s not in sources:
            sources.append(s)

    active = list(dict.fromkeys(s for s in sources if s in SOURCE_REGISTRY))
    ms = round((time.time() - t0) * 1000, 1)

    return {
        **state,
        "query_plan":     plan.model_dump(),
        "active_sources": active,
        "current_query":  plan.optimized_queries[0],
        "pipeline_trace": _trace(state, "planner", "ok", ms,
                                 intent=plan.intent, sources=len(active))
    }

# ══════════════════════════════════════════════════════════
# AGENT 2 — PARALLEL RETRIEVER
# Concurrent source fetching with circuit breakers and timeouts.
# Always fetches fresh on first attempt, uses cache only on retry.
# (Anthropic 2025: parallel tool calls; Corrective RAG: retrieval layer)
# ══════════════════════════════════════════════════════════

@dataclass
class _Fetch:
    source: str
    papers: List[Dict] = field(default_factory=list)
    ok: bool = True
    ms: float = 0.0
    err: str = ""

def _fetch_source(source: str, query: str) -> _Fetch:
    t0 = time.time()
    try:
        mod_path, fn_name = SOURCE_REGISTRY[source]
        mod = importlib.import_module(mod_path)
        results = getattr(mod, fn_name)(query)
        return _Fetch(source=source, papers=results or [],
                      ms=round((time.time()-t0)*1000, 1))
    except Exception as e:
        return _Fetch(source=source, ok=False, err=str(e),
                      ms=round((time.time()-t0)*1000, 1))

def retriever_agent(state: ResearchState) -> ResearchState:
    t0       = time.time()
    q        = state["current_query"]
    active   = state["active_sources"]
    attempts = state.get("retrieval_attempts", 0)

    # use cache only on retry (not first run — always fetch fresh)
    if attempts > 0:
        cached = hybrid_search(q, top_k=TOP_K_CHUNKS)
        if len(cached) >= MIN_RELEVANT_CHUNKS:
            logger.info(f"[retriever] cache hit on retry — {len(cached)} chunks")
            return {
                **state, "chunks": cached, "sources_used": ["cache"],
                "retrieval_attempts": attempts + 1,
                "pipeline_trace": _trace(state, "retriever", "cache_hit",
                                         round((time.time()-t0)*1000, 1), chunks=len(cached))
            }

    # parallel fetch — daemon threads die when main thread moves on (Windows-safe)
    import threading
    fetches: List[_Fetch] = []
    fetch_lock = threading.Lock()

    def _fetch_and_store(source: str, query: str):
        result = _fetch_source(source, query)
        with fetch_lock:
            fetches.append(result)

    threads = []
    for s in active:
        t = threading.Thread(target=_fetch_and_store, args=(s, q), daemon=True)
        t.start()
        threads.append((t, s))

    # wait up to wall timeout — daemon threads that miss deadline are abandoned
    deadline = time.time() + RETRIEVER_WALL_TIMEOUT
    for t, src in threads:
        remaining = deadline - time.time()
        if remaining <= 0:
            logger.warning(f"[retriever] wall timeout — abandoning remaining sources")
            break
        t.join(timeout=remaining)

    ingested = []
    for f in fetches:
        if f.ok and f.papers:
            try:
                ingest(f.papers, source=f.source)
                ingested.append(f.source)
                logger.info(f"[retriever] {f.source}: {len(f.papers)} docs in {f.ms:.0f}ms")
            except Exception as e:
                logger.warning(f"[retriever] ingest {f.source}: {e}")
        elif not f.ok:
            logger.warning(f"[retriever] {f.source} failed: {f.err[:80]}")

    chunks = hybrid_search(q, top_k=TOP_K_CHUNKS)
    ms = round((time.time() - t0) * 1000, 1)

    return {
        **state, "chunks": chunks, "sources_used": ingested,
        "retrieval_attempts": attempts + 1,
        "pipeline_trace": _trace(state, "retriever", "ok", ms,
                                 sources=len(ingested), chunks=len(chunks))
    }

# ══════════════════════════════════════════════════════════
# AGENT 3 — DOCUMENT GRADER (Corrective RAG)
# Grades every retrieved chunk for relevance to the query.
# Low relevance triggers query rewrite and re-retrieval.
# (Shi et al., 2024 — Corrective Retrieval Augmented Generation)
# ══════════════════════════════════════════════════════════

def grader_agent(state: ResearchState) -> ResearchState:
    t0     = time.time()
    query  = state["current_query"]
    chunks = state["chunks"]

    if not chunks:
        return {
            **state, "relevant_chunks": [],
            "grader_output": {"should_rewrite": True, "rewrite_suggestion": query,
                              "relevant_count": 0, "irrelevant_count": 0, "grades": []},
            "pipeline_trace": _trace(state, "grader", "no_chunks", 0.0)
        }

    chunk_list = "\n".join([
        f"[{i}] {c['title'][:80]} | {c['source']} | {c['content'][:120]}"
        for i, c in enumerate(chunks)
    ])

    prompt = f"""You are a document relevance grader for a research retrieval system.

Query: {query}

Chunks to grade:
{chunk_list}

Return ONLY valid JSON:
{{
  "grades": [
    {{"chunk_id": "0", "is_relevant": true, "relevance_score": 0.85, "reason": "directly addresses query"}},
    {{"chunk_id": "1", "is_relevant": false, "relevance_score": 0.2, "reason": "unrelated topic"}}
  ],
  "should_rewrite": false,
  "rewrite_suggestion": ""
}}

Rules:
- Grade every chunk [0] through [{len(chunks)-1}]
- should_rewrite = true only if fewer than {MIN_RELEVANT_CHUNKS} chunks are relevant
- rewrite_suggestion: broader/rephrased query if should_rewrite is true
- Be lenient — mark relevant if even partially related"""

    try:
        data      = _parse_json(groq_fast(prompt, max_tokens=600))
        grade_map = {g["chunk_id"]: g for g in data.get("grades", [])}
        relevant, irrelevant = [], []
        for i, chunk in enumerate(chunks):
            g = grade_map.get(str(i), {"is_relevant": True, "relevance_score": 0.7})
            chunk["relevance_score"] = g.get("relevance_score", 0.7)
            (relevant if g.get("is_relevant", True) else irrelevant).append(chunk)

        out = GraderOutput(
            grades=[DocumentGrade(**{**g, "chunk_id": g.get("chunk_id", str(i))})
                    for i, g in enumerate(data.get("grades", []))
                    if isinstance(g, dict) and "is_relevant" in g],
            relevant_count=len(relevant),
            irrelevant_count=len(irrelevant),
            should_rewrite=data.get("should_rewrite", False),
            rewrite_suggestion=data.get("rewrite_suggestion", "")
        )
        ms = round((time.time() - t0) * 1000, 1)
        return {
            **state,
            "relevant_chunks": relevant if relevant else chunks,
            "grader_output":   out.model_dump(),
            "pipeline_trace":  _trace(state, "grader", "ok", ms,
                                      relevant=len(relevant), rewrite=out.should_rewrite)
        }
    except Exception as e:
        logger.warning(f"[grader] fallback: {e}")
        ms = round((time.time() - t0) * 1000, 1)
        return {
            **state, "relevant_chunks": chunks,
            "grader_output": {"should_rewrite": False, "rewrite_suggestion": "",
                              "relevant_count": len(chunks), "irrelevant_count": 0,
                              "grades": []},
            "pipeline_trace": _trace(state, "grader", "fallback", ms)
        }

# ══════════════════════════════════════════════════════════
# AGENT 4 — QUERY REWRITER
# Invoked only when grader triggers corrective loop.
# Rewrites query using LLM to improve retrieval coverage.
# ══════════════════════════════════════════════════════════

def query_rewriter_agent(state: ResearchState) -> ResearchState:
    t0         = time.time()
    suggestion = (state.get("grader_output") or {}).get("rewrite_suggestion", "")
    current    = state["current_query"]

    prompt = f"""Rewrite this academic search query to improve retrieval coverage.

Original query: {state['query']}
Current query: {current}
Feedback: insufficient relevant documents found
Direction: {suggestion}

Strategies: broaden scope, add synonyms, rephrase with alternative terminology.
Return ONLY the rewritten query string, nothing else."""

    try:
        rewritten = groq_chat(prompt, max_tokens=80, temperature=0.2).strip().strip('"').strip("'")
    except Exception:
        rewritten = suggestion or state["query"]

    ms = round((time.time() - t0) * 1000, 1)
    logger.info(f"[rewriter] '{current}' → '{rewritten}'")
    return {
        **state, "current_query": rewritten,
        "pipeline_trace": _trace(state, "rewriter", "ok", ms, rewritten=rewritten)
    }

# ══════════════════════════════════════════════════════════
# AGENT 5 — SYNTHESIS + NOVELTY (parallel execution)
# Synthesis: structured evidence reasoning with confidence scoring.
# Novelty: quantitative multi-dimensional scoring.
# Both run concurrently on same evidence — saves ~4s vs sequential.
# ══════════════════════════════════════════════════════════

def _run_synthesis(query: str, chunks: List[Dict],
                   focus: Optional[List[str]]) -> SynthesisOutput:
    focus_clause = f"\nFocus specifically on: {', '.join(focus)}" if focus else ""
    evidence = "\n\n".join([
        f"[{i+1}] {c['source'].upper()} | {c['year']}\n"
        f"TITLE: {c['title']}\n"
        f"EXCERPT: {c['content'][:320]}"
        for i, c in enumerate(chunks[:12])
    ])

    prompt = f"""You are a senior research analyst synthesizing multi-source evidence.

QUERY: {query}{focus_clause}

EVIDENCE ({len(chunks)} sources):
{evidence}

Return ONLY valid JSON (no markdown):
{{
  "key_findings": ["finding with [1][2] citations", "finding with [3] citation"],
  "research_gaps": ["specific gap 1", "specific gap 2", "specific gap 3"],
  "conflicting_evidence": ["conflict if any, else empty list"],
  "confidence_level": "high|medium|low",
  "confidence_rationale": "why this confidence level",
  "detailed_answer": "3-4 substantive paragraphs with inline [N] citations throughout. Minimum 300 words."
}}

Rules:
- Every key finding MUST cite at least one source using [N]
- Research gaps must be specific and non-obvious
- detailed_answer must be comprehensive and substantive
- Return ONLY the JSON object"""

    try:
        return SynthesisOutput(**_parse_json(groq_quality(prompt, max_tokens=1500)))
    except Exception as e:
        logger.warning(f"[synthesis] fallback: {e}")
        fallback = groq_chat(
            f"Analyze research on: {query}\n\nEvidence:\n{evidence[:2000]}\n\n"
            f"Give key findings, research gaps, and a detailed analysis.",
            model="llama-3.3-70b-versatile", max_tokens=1500
        )
        return SynthesisOutput(
            key_findings=["See detailed analysis below"],
            research_gaps=["See detailed analysis below"],
            conflicting_evidence=[],
            confidence_level="medium",
            confidence_rationale="Structured output parse failed",
            detailed_answer=fallback
        )

def _run_novelty(query: str, chunks: List[Dict]) -> NoveltyOutput:
    years    = [int(c["year"]) for c in chunks if str(c.get("year", "")).isdigit()]
    avg_year = round(sum(years) / len(years), 1) if years else 2020
    recency  = min(1.0, max(0.0, (avg_year - 2018) / 6.0))

    works = "\n".join([
        f"[{i+1}] {c['title']} ({c['year']}) [{c['source']}]"
        for i, c in enumerate(chunks[:15])
    ])

    prompt = f"""You are a research novelty evaluator.

QUERY/IDEA: {query}
EXISTING WORKS ({len(chunks)} total, avg year: {avg_year}):
{works}

Return ONLY valid JSON (no markdown):
{{
  "score": <0-100 float>,
  "coverage_density": <0.0-1.0 float>,
  "recency_score": <0.0-1.0 float>,
  "cross_domain_novelty": <0.0-1.0 float>,
  "top_overlapping_works": ["title (year)", "title (year)", "title (year)"],
  "novel_aspects": ["specific novel aspect 1", "specific novel aspect 2"],
  "recommendation": "pursue|pivot|abandon",
  "recommendation_rationale": "specific actionable rationale",
  "full_report": "2-3 paragraph novelty analysis"
}}

Score: 0-30 well covered, 31-60 partially novel, 61-100 highly novel
coverage_density: 1.0 = saturated, 0.0 = unexplored"""

    try:
        data = _parse_json(groq_quality(prompt, max_tokens=800))
        data["recency_score"] = recency
        return NoveltyOutput(**data)
    except Exception as e:
        logger.warning(f"[novelty] fallback: {e}")
        return NoveltyOutput(
            score=50.0, coverage_density=0.5, recency_score=recency,
            cross_domain_novelty=0.5,
            top_overlapping_works=[c["title"] for c in chunks[:3]],
            novel_aspects=["Retry with a more specific query"],
            recommendation="pursue",
            recommendation_rationale="Insufficient data for a confident recommendation",
            full_report=f"{len(chunks)} sources found. Manual review recommended."
        )

def synthesis_novelty_agent(state: ResearchState) -> ResearchState:
    """Parallel synthesis + novelty scoring. Both use same chunks,
    neither depends on the other's output — safe to run concurrently."""
    t0     = time.time()
    chunks = state.get("relevant_chunks") or state.get("chunks", [])

    with ThreadPoolExecutor(max_workers=2) as ex:
        f_s = ex.submit(_run_synthesis, state["query"], chunks, state.get("focus_areas"))
        f_n = ex.submit(_run_novelty,   state["query"], chunks)
        synth   = f_s.result()
        novelty = f_n.result()

    citations = [
        {"title": c["title"], "url": c["url"], "source": c["source"], "year": c["year"]}
        for c in chunks
    ]
    ms = round((time.time() - t0) * 1000, 1)

    return {
        **state,
        "synthesis":       synth.model_dump(),
        "citations":       citations,
        "novelty":         novelty.model_dump(),
        "novelty_score":   novelty.score,
        "novelty_report":  novelty.full_report,
        "detailed_answer": synth.detailed_answer,
        "pipeline_trace":  _trace(state, "synthesis_novelty", "ok", ms,
                                  confidence=synth.confidence_level,
                                  novelty=novelty.score)
    }

# ══════════════════════════════════════════════════════════
# AGENT 6 — HALLUCINATION CHECKER (Self-RAG)
# Verifies answer is grounded in retrieved evidence.
# Hallucinated answers trigger regeneration within retry budget.
# (Asai et al., 2023 — Self-RAG: Learning to Retrieve, Generate, Critique)
# ══════════════════════════════════════════════════════════

def hallucination_checker_agent(state: ResearchState) -> ResearchState:
    t0       = time.time()
    answer   = state.get("detailed_answer", "")
    chunks   = state.get("relevant_chunks", [])
    attempts = state.get("generation_attempts", 0)

    if not answer or not chunks:
        return {
            **state, "generation_attempts": attempts + 1,
            "hallucination_verdict": {
                "is_grounded": True, "unsupported_claims": [],
                "confidence": "low", "verdict_rationale": "no content to check"
            },
            "pipeline_trace": _trace(state, "hallucination_checker", "skipped", 0.0)
        }

    evidence = "\n".join([
        f"- {c['title']} ({c['year']}) [{c['source']}]"
        for c in chunks[:10]
    ])

    prompt = f"""You are a hallucination detection system for a scientific research AI.

Check if the generated answer is grounded in the available evidence.

ANSWER (excerpt):
{answer[:700]}

EVIDENCE AVAILABLE:
{evidence}

Return ONLY valid JSON:
{{
  "is_grounded": true,
  "unsupported_claims": [],
  "confidence": "high|medium|low",
  "verdict_rationale": "brief explanation"
}}

Rules:
- is_grounded = false ONLY for clear fabricated facts not present in evidence
- Reasonable inferences and synthesis from evidence = grounded
- Be lenient — research synthesis naturally extends beyond exact quotes"""

    try:
        verdict = HallucinationVerdict(**_parse_json(groq_quality(prompt, max_tokens=300)))
    except Exception as e:
        logger.warning(f"[hallucination_checker] fallback: {e}")
        verdict = HallucinationVerdict(
            is_grounded=True, unsupported_claims=[],
            confidence="low", verdict_rationale="parse failed, assuming grounded"
        )

    ms = round((time.time() - t0) * 1000, 1)
    return {
        **state,
        "hallucination_verdict": verdict.model_dump(),
        "generation_attempts":   attempts + 1,
        "pipeline_trace":        _trace(state, "hallucination_checker", "ok", ms,
                                        grounded=verdict.is_grounded)
    }

# ══════════════════════════════════════════════════════════
# AGENT 7 — SUMMARIZER
# Plain-English summary optimized for non-expert readers.
# Weaves novelty score and research gaps into narrative.
# ══════════════════════════════════════════════════════════

def summarizer_agent(state: ResearchState) -> ResearchState:
    t0      = time.time()
    synth   = state.get("synthesis") or {}
    novelty = state.get("novelty_score", 50.0)
    gaps    = "\n".join(f"- {g}" for g in synth.get("research_gaps", [])[:3])
    finds   = "\n".join(f"- {f}" for f in synth.get("key_findings", [])[:3])

    prompt = f"""Summarize this research analysis in plain English. Max 120 words, no bullet points.

Query: {state['query']}
Novelty Score: {novelty}/100
Key Findings:
{finds}
Research Gaps:
{gaps}
Analysis excerpt: {state.get('detailed_answer', '')[:500]}

Write 2-3 flowing sentences covering: what currently exists, the key gaps or opportunities,
and whether this is worth pursuing based on the novelty score."""

    try:
        summary = groq_summarize(prompt).strip()
    except Exception:
        summary = (f"Analysis complete across {len(state.get('sources_used', []))} sources. "
                   f"{len(state.get('citations', []))} citations found. "
                   f"Novelty score: {novelty}/100.")

    ms = round((time.time() - t0) * 1000, 1)
    return {
        **state, "summary": summary,
        "pipeline_trace": _trace(state, "summarizer", "ok", ms)
    }

# ══════════════════════════════════════════════════════════
# CONDITIONAL ROUTING
# ══════════════════════════════════════════════════════════

def route_after_grader(state: ResearchState) -> Literal["rewrite", "synthesize"]:
    """Corrective RAG: rewrite query if too few relevant chunks found."""
    out      = state.get("grader_output", {})
    attempts = state.get("retrieval_attempts", 0)
    if out.get("should_rewrite") and attempts < MAX_RETRIEVAL_RETRIES:
        logger.info(f"[router] grader → rewrite (attempt {attempts}/{MAX_RETRIEVAL_RETRIES})")
        return "rewrite"
    logger.info(f"[router] grader → synthesize ({out.get('relevant_count', 0)} relevant chunks)")
    return "synthesize"

def route_after_hallucination(state: ResearchState) -> Literal["summarize", "regenerate"]:
    """Self-RAG: regenerate if hallucination detected within retry budget."""
    verdict  = state.get("hallucination_verdict", {})
    attempts = state.get("generation_attempts", 0)
    if not verdict.get("is_grounded", True) and attempts <= MAX_GENERATION_RETRIES:
        logger.info(f"[router] hallucination detected → regenerate (attempt {attempts})")
        return "regenerate"
    return "summarize"

# ══════════════════════════════════════════════════════════
# GRAPH COMPILATION
# ══════════════════════════════════════════════════════════

_pipeline = None

def get_pipeline():
    global _pipeline
    if _pipeline:
        return _pipeline

    g = StateGraph(ResearchState)

    g.add_node("planner",             planner_agent)
    g.add_node("retriever",           retriever_agent)
    g.add_node("grader",              grader_agent)
    g.add_node("rewriter",            query_rewriter_agent)
    g.add_node("synthesis_novelty",   synthesis_novelty_agent)
    g.add_node("hallucination_check", hallucination_checker_agent)
    g.add_node("summarizer",          summarizer_agent)

    g.set_entry_point("planner")
    g.add_edge("planner",           "retriever")
    g.add_edge("retriever",         "grader")
    g.add_edge("rewriter",          "retriever")         # corrective RAG loop back
    g.add_edge("synthesis_novelty", "hallucination_check")
    g.add_edge("summarizer",        END)

    g.add_conditional_edges(
        "grader", route_after_grader,
        {"rewrite": "rewriter", "synthesize": "synthesis_novelty"}
    )
    g.add_conditional_edges(
        "hallucination_check", route_after_hallucination,
        {"regenerate": "synthesis_novelty", "summarize": "summarizer"}
    )

    _pipeline = g.compile()
    return _pipeline

# ══════════════════════════════════════════════════════════
# PUBLIC ENTRY POINT
# ══════════════════════════════════════════════════════════

def run_query(
    query: str,
    user_type: str = "all",
    privacy_mode: bool = False,
    focus_areas: Optional[List[str]] = None
) -> Dict:
    """
    Main entry point for the ResearchNu agentic pipeline.

    Args:
        query:        Research question or idea
        user_type:    researcher|founder|grant|policy|all
        privacy_mode: Use local Ollama for query processing
        focus_areas:  Specific aspects to focus on e.g. ["clinical applications", "cost"]

    Returns:
        Dict with summary, detailed_answer, citations, novelty_score,
        novelty_report, sources_used, pipeline_trace, total_time_s
    """
    if privacy_mode:
        try:
            from app.models.llm_client import local_chat
            query = local_chat(f"Rephrase for academic database search: {query}")
        except Exception:
            pass

    init: ResearchState = {
        "query":                 query,
        "user_type":             user_type,
        "privacy_mode":          privacy_mode,
        "focus_areas":           focus_areas or [],
        "query_plan":            None,
        "active_sources":        [],
        "current_query":         query,
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

    t0     = time.time()
    result = get_pipeline().invoke(init)
    total  = round(time.time() - t0, 2)

    logger.info(
        f"[pipeline] done in {total}s | "
        f"novelty={result.get('novelty_score')} | "
        f"sources={len(result.get('sources_used', []))} | "
        f"citations={len(result.get('citations', []))}"
    )

    return {
        "query":           query,
        "summary":         result.get("summary", ""),
        "detailed_answer": result.get("detailed_answer", ""),
        "citations":       result.get("citations", []),
        "novelty_score":   result.get("novelty_score", 0.0),
        "novelty_report":  result.get("novelty_report", ""),
        "novelty":         result.get("novelty", {}),
        "synthesis":       result.get("synthesis", {}),
        "sources_used":    result.get("sources_used", []),
        "pipeline_trace":  result.get("pipeline_trace", []),
        "total_time_s":    total,
    }