from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Dict
import asyncio
from app.rag.ingestor import ingest
from app.rag.retriever import hybrid_search
from app.models.llm_client import complete

# source imports -- all 20
from app.sources.pubmed import search as pubmed
from app.sources.arxiv import search as arxiv
from app.sources.openalex import search as openalex
from app.sources.semantic_scholar import search as semantic_scholar
from app.sources.europe_pmc import search as europe_pmc
from app.sources.core_ac import search as core_ac
from app.sources.crossref import search as crossref
from app.sources.grants_nih import search as nih
from app.sources.grants_nsf import search as nsf
from app.sources.grants_eu import search as eu
from app.sources.grants_ukri import search as ukri
from app.sources.patents_uspto import search as uspto
from app.sources.patents_wipo import search as wipo
from app.sources.patents_epo import search as epo
from app.sources.patents_lens import search as lens
from app.sources.clinical_trials import search as clinical
from app.sources.who_ictrp import search as who
from app.sources.fda import search as fda
from app.sources.ycombinator import search as yc
from app.sources.product_hunt import search as producthunt

# source weights per mode -- all sources run, weights affect ranking
SOURCE_WEIGHTS = {
    "researcher": {
        "academic": [pubmed, arxiv, openalex, semantic_scholar, europe_pmc, core_ac, crossref],
        "grants": [nih, nsf],
        "patents": [uspto],
        "clinical": [clinical],
        "market": []
    },
    "founder": {
        "academic": [arxiv, openalex],
        "grants": [],
        "patents": [uspto, wipo, epo, lens],
        "clinical": [],
        "market": [yc, producthunt]
    },
    "grant": {
        "academic": [pubmed, openalex],
        "grants": [nih, nsf, eu, ukri],
        "patents": [],
        "clinical": [clinical, who],
        "market": []
    },
    "all": {
        "academic": [pubmed, arxiv, openalex, semantic_scholar, europe_pmc, core_ac, crossref],
        "grants": [nih, nsf, eu, ukri],
        "patents": [uspto, wipo, epo, lens],
        "clinical": [clinical, who],
        "market": [yc, producthunt]
    }
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

# -- AGENT 1: RETRIEVER --
def retriever_agent(state: State) -> State:
    # fires all sources for the mode simultaneously
    q = state["processed_query"] or state["query"]
    mode = state["user_type"]
    sources = SOURCE_WEIGHTS.get(mode, SOURCE_WEIGHTS["all"])

    async def fetch():
        tasks = []
        for group in sources.values():
            for src in group:
                tasks.append(src(q))
        return await asyncio.gather(*tasks, return_exceptions=True)

    results = asyncio.run(fetch())
    source_names = []
    for group in sources.values():
        for src in group:
            source_names.append(src.__module__.split(".")[-1])

    for i, papers in enumerate(results):
        if isinstance(papers, Exception) or not papers:
            continue
        ingest(papers, source=source_names[i])

    chunks = hybrid_search(q, top_k=10)
    used = list(set([c["source"] for c in chunks]))
    return {**state, "chunks": chunks, "sources_used": used}

# -- AGENT 2: REASONER --
def reasoner_agent(state: State) -> State:
    # synthesizes answer from chunks, groq never sees raw query
    ctx = "\n\n".join([
        f"[{i+1}] {c['title']} ({c['source']}, {c['year']})\n{c['content'][:400]}"
        for i, c in enumerate(state["chunks"])
    ])
    prompt = f"""You are a research analyst. Use ONLY the sources below. No hallucination.

Query: {state["processed_query"] or state["query"]}

Sources:
{ctx}

Provide:
1) Key findings with source references [N]
2) Research gaps identified
3) Confidence level and why"""

    ans = complete(prompt)
    cites = [
        {"title": c["title"], "url": c["url"], "source": c["source"], "year": c["year"]}
        for c in state["chunks"] if c.get("url")
    ]
    return {**state, "answer": ans, "citations": cites}

# -- AGENT 3: NOVELTY --
def novelty_agent(state: State) -> State:
    # scores how novel the query idea is 0-100
    top5 = state["chunks"][:5]
    existing = "\n".join([
        f"- {c['title']} ({c['source']}): {c['content'][:200]}"
        for c in top5
    ])
    prompt = f"""Assess novelty of this idea: {state["query"]}

Existing work:
{existing}

Give:
- Novelty score 0-100 (100 = completely novel)
- Top 3 overlapping works
- What aspects are still novel
- Recommendation: proceed, pivot, or abandon"""

    report = complete(prompt)
    score = round((1 - max((c.get("score", 0) for c in top5), default=0)) * 100, 1)
    return {**state, "novelty_score": score, "novelty_report": report}

# -- AGENT 4: SUMMARIZER --
def summarizer_agent(state: State) -> State:
    # plain english summary, accessible to non-technical users
    summary = complete(
        f"Summarize in plain English under 100 words, no jargon:\n{state['answer'][:1500]}"
    )
    return {**state, "summary": summary}

# -- WIRE LANGGRAPH -- sequential to avoid concurrent state write conflicts
_pipeline = None

def get_pipeline():
    global _pipeline
    if _pipeline is None:
        g = StateGraph(State)
        g.add_node("retriever", retriever_agent)
        g.add_node("reasoner", reasoner_agent)
        g.add_node("novelty", novelty_agent)
        g.add_node("summarizer", summarizer_agent)
        g.set_entry_point("retriever")
        # sequential -- retriever -> reasoner -> novelty -> summarizer
        g.add_edge("retriever", "reasoner")
        g.add_edge("reasoner", "novelty")
        g.add_edge("novelty", "summarizer")
        g.add_edge("summarizer", END)
        _pipeline = g.compile()
    return _pipeline

def run_query(query: str, user_type: str = "researcher", privacy_mode: bool = False) -> dict:
    # privacy_mode=True -- ollama processes query locally before groq sees it
    from app.models.llm_client import process_query_locally
    processed = process_query_locally(query) if privacy_mode else query
    return get_pipeline().invoke({
        "query": query,
        "processed_query": processed,
        "user_type": user_type,
        "chunks": [],
        "sources_used": [],
        "answer": "",
        "citations": [],
        "novelty_score": 0.0,
        "novelty_report": "",
        "summary": ""
    })