# Changelog

All notable changes to ResearchNu are documented here.

## [1.0.0] - 2026-03-10

### Added
- 7-agent LangGraph pipeline (planner, retriever, grader, rewriter, synthesis+novelty, hallucination checker, summarizer)
- 20 working data sources across academic, grants, patents, clinical, market, finance, news, policy/legal
- Corrective RAG: document grading + query rewrite on low relevance (Shi et al., 2024)
- Self-RAG: hallucination check before output (Asai et al., 2023)
- Adaptive RAG: dynamic routing based on query intent (Jeong et al., 2024)
- Parallel source fetching with per-source circuit breakers
- Multi-dimensional novelty scoring (0-100) with pursue/pivot/abandon recommendation
- Hybrid BM25 + semantic search with RRF fusion
- FastAPI backend with rate limiting
- Streamlit frontend with 6 tabs
- Python SDK (sdk/client.py)
- MCP server exposing all sources as tools
- Docker + Kubernetes deployment configs
- Multi-model LLM routing: llama-3.1-8b-instant (fast) + llama-3.3-70b-versatile (quality)

### Sources (20 working)
Academic: PubMed, arXiv, OpenAlex, Europe PMC, CORE, Crossref
Grants: NIH, NSF, UKRI
Patents: Lens.org, Google Patents
Clinical: ClinicalTrials.gov, FDA
Market: Y Combinator, Product Hunt
Finance: FRED, Alpha Vantage
News: NewsAPI
Policy/Legal: Congress.gov, CourtListener

### Pending
- Semantic Scholar (key approval pending)
- EU Horizon grants (timeout issues)
- EPO patents (OAuth registration)