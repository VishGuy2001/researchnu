from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Dict
from app.rag.ingestor import ingest
from app.rag.retriever import hybrid_search
from app.models.llm_client import groq_chat
import importlib

# source weights per user type
SOURCE_WEIGHTS = {
    "researcher": ["pubmed", "arxiv", "openalex", "semantic_scholar", "europe_pmc", "core", "crossref", "grants_nih", "grants_nsf", "patents_uspto", "clinical_trials"],
    "founder":    ["arxiv", "openalex", "patents_uspto", "patents_wipo", "patents_epo", "patents_lens", "market_yc", "market_ph"],
    "grant":      ["pubmed", "openalex", "grants_nih", "grants_nsf", "grants_eu", "grants_ukri", "clinical_trials", "who_ictrp"],
    "all":        ["pubmed", "arxiv", "openalex", "semantic_scholar", "europe_pmc", "core", "crossref", "grants_nih", "grants_nsf", "grants_eu", "grants_ukri", "patents_uspto", "patents_wipo", "patents_epo", "patents_lens", "clinical_trials", "who_ictrp", "fda", "market_yc", "market_ph"],
}

SOURCE_FN = {
    "pubmed":           ("app.sources.pubmed",           "search_pubmed"),
    "arxiv":            ("app.sources.arxiv",             "search_arxiv"),
    "openalex":         ("app.sources.openalex",          "search_openalex"),
    "semantic_scholar": ("app.sources.semantic_scholar",  "search_semantic_scholar"),
    "europe_pmc":       ("app.sources.europe_pmc",        "search_europe_pmc"),
    "core":             ("app.sources.core",              "search_core"),
    "crossref":         ("app.sources.crossref",          "search_crossref"),
    "grants_nih":       ("app.sources.grants_nih",        "search_nih"),
    "grants_nsf":       ("app.sources.grants_nsf",        "search_nsf"),
    "grants_eu":        ("app.sources.grants_eu",         "search_eu_horizon"),
    "grants_ukri":      ("app.sources.grants_ukri",       "search_ukri"),
    "patents_uspto":    ("app.sources.patents_uspto",     "search_uspto"),
    "patents_wipo":     ("app.sources.patents_wipo",      "search_wipo"),
    "patents_epo":      ("app.sources.patents_epo",       "search_epo"),
    "patents_lens":     ("app.sources.patents_lens",      "search_lens"),
    "clinical_trials":  ("app.sources.clinical_trials",   "search_clinical_trials"),
    "who_ictrp":        ("app.sources.who_ictrp",         "search_who"),
    "fda":              ("app.sources.fda",               "search_fda"),
    "market_yc":        ("app.sources.market_yc",         "search_yc"),
    "market_ph":        ("app.sources.market_ph",         "search_product_hunt"),
}

class State(TypedDict):
    query: str
    processed_query: str
    user_type: str
    chunks: List[Dict]
    sources_used: List[str]
    answer: str
    citations: List[Dict]
    novelty_score: float
    novelty_report: str
    summary: str

def retriever_agent(state: State) -> State:
    q = state["processed_query"]
    ut = state["user_type"]
    sources = SOURCE_WEIGHTS.get(ut, SOURCE_WEIGHTS["all"])
    papers, source_names = [], []
    for src in sources:
        try:
            mod_path, fn_name = SOURCE_FN[src]
            mod = importlib.import_module(mod_path)
            fn = getattr(mod, fn_name)
            results = fn(q)
            if results:
                papers.append(results)
                source_names.append(src)
        except Exception as e:
            print(f"source {src} failed: {e}")
    for i, p in enumerate(papers):
        try:
            ingest(p, source=source_names[i])
        except Exception as e:
            print(f"ingest {source_names[i]} failed: {e}")
    chunks = hybrid_search(q, top_k=10)
    return {**state, "chunks": chunks, "sources_used": source_names}

def reasoner_agent(state: State) -> State:
    ctx = "\n\n".join([f"[{c['source']}] {c['title']}\n{c['content']}" for c in state["chunks"]])
    prompt = f"""You are a research analyst. Based on the following sources, answer the query comprehensively.

Query: {state['query']}

Sources:
{ctx}

Provide:
1. Key findings with source references [1], [2] etc
2. Research gaps identified
3. Confidence level and why

Be specific and cite sources."""
    answer = groq_chat(prompt)
    citations = [{"title": c["title"], "url": c["url"], "source": c["source"], "year": c["year"]} for c in state["chunks"]]
    return {**state, "answer": answer, "citations": citations}

def novelty_agent(state: State) -> State:
    ctx = "\n".join([f"- {c['title']} ({c['year']}) [{c['source']}]" for c in state["chunks"]])
    prompt = f"""You are a research novelty evaluator.

Query/Idea: {state['query']}

Existing works found:
{ctx}

Rate the novelty of this query/idea on a scale of 0-100 where:
- 0-30: Well covered, many papers exist
- 31-60: Partially covered, some gaps exist
- 61-100: Highly novel, few or no papers

Respond with:
SCORE: [number 0-100]
TOP_OVERLAPS: [list 3 most overlapping works]
NOVEL_ASPECTS: [what aspects are still novel]
RECOMMENDATION: [pursue/pivot/abandon and why]"""
    report = groq_chat(prompt)
    score = 50.0
    for line in report.split("\n"):
        if line.strip().startswith("SCORE:"):
            try:
                score = float(line.replace("SCORE:", "").strip())
            except:
                pass
    return {**state, "novelty_score": score, "novelty_report": report}

def summarizer_agent(state: State) -> State:
    prompt = f"""Summarize the following research analysis in plain English under 100 words for a non-expert.

Query: {state['query']}
Analysis: {state['answer'][:1000]}

Be clear, concise, and jargon-free."""
    summary = groq_chat(prompt)
    return {**state, "summary": summary}

_pipeline = None

def get_pipeline():
    global _pipeline
    if _pipeline:
        return _pipeline
    g = StateGraph(State)
    g.add_node("retriever", retriever_agent)
    g.add_node("reasoner", reasoner_agent)
    g.add_node("novelty", novelty_agent)
    g.add_node("summarizer", summarizer_agent)
    g.set_entry_point("retriever")
    g.add_edge("retriever", "reasoner")
    g.add_edge("reasoner", "novelty")
    g.add_edge("novelty", "summarizer")
    g.add_edge("summarizer", END)
    _pipeline = g.compile()
    return _pipeline

def run_query(query: str, user_type: str = "all", privacy_mode: bool = False) -> Dict:
    # privacy mode uses local ollama for query processing
    if privacy_mode:
        try:
            from app.models.llm_client import local_chat
            processed = local_chat(f"Rephrase this search query for academic research: {query}")
        except:
            processed = query
    else:
        processed = query

    init = {
        "query": query,
        "processed_query": processed,
        "user_type": user_type,
        "chunks": [],
        "sources_used": [],
        "answer": "",
        "citations": [],
        "novelty_score": 0.0,
        "novelty_report": "",
        "summary": "",
    }
    return get_pipeline().invoke(init)