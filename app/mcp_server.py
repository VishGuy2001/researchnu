"""
ResearchNu MCP Server
=====================
Exposes all ResearchNu sources as MCP tools.
Any MCP client (Claude Desktop, Claude Code, etc.) can call these tools directly.

Usage:
  python -m app.mcp_server

Claude Desktop config (claude_desktop_config.json):
  {
    "mcpServers": {
      "researchnu": {
        "command": "python",
        "args": ["-m", "app.mcp_server"],
        "cwd": "/path/to/researchnu"
      }
    }
  }
"""

import asyncio
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# ── source imports (correct function names) ──
from app.sources.pubmed           import search_pubmed
from app.sources.arxiv            import search_arxiv
from app.sources.openalex         import search_openalex
from app.sources.semantic_scholar import search_semantic_scholar
from app.sources.europe_pmc       import search_europe_pmc
from app.sources.core_ac          import search_core
from app.sources.crossref         import search_crossref
from app.sources.grants_nih       import search_nih
from app.sources.grants_nsf       import search_nsf
from app.sources.grants_eu        import search_eu_horizon
from app.sources.grants_ukri      import search_ukri
from app.sources.patents_uspto    import search_uspto
from app.sources.patents_wipo     import search_wipo
from app.sources.patents_epo      import search_epo
from app.sources.patents_lens     import search_lens
from app.sources.google_patents   import search_google_patents
from app.sources.clinical_trials  import search_clinical_trials
from app.sources.who_ictrp        import search_who
from app.sources.fda              import search_fda
from app.sources.ycombinator      import search_yc
from app.sources.product_hunt     import search_product_hunt
from app.sources.fred             import search_fred
from app.sources.news             import search_news
from app.sources.alpha_vantage    import search_alpha_vantage
from app.sources.congress         import search_congress
from app.sources.courtlistener    import search_courtlistener

app = Server("researchnu")

# ── tool registry: name → (sync_fn, description) ──
TOOLS = {
    "search_pubmed": (
        search_pubmed,
        "Search PubMed — 36M+ biomedical papers and clinical research"
    ),
    "search_arxiv": (
        search_arxiv,
        "Search arXiv — 2M+ preprints across CS, physics, biology, math"
    ),
    "search_openalex": (
        search_openalex,
        "Search OpenAlex — 250M+ works across all academic fields"
    ),
    "search_semantic_scholar": (
        search_semantic_scholar,
        "Search Semantic Scholar — citation graph and influence scores"
    ),
    "search_europe_pmc": (
        search_europe_pmc,
        "Search Europe PMC — European biomedical literature"
    ),
    "search_core": (
        search_core,
        "Search CORE — 200M+ open access papers globally"
    ),
    "search_crossref": (
        search_crossref,
        "Search CrossRef — 150M+ works with DOI verification"
    ),
    "search_nih_grants": (
        search_nih,
        "Search NIH Reporter — all NIH grants ever awarded"
    ),
    "search_nsf_grants": (
        search_nsf,
        "Search NSF Awards — US science and engineering grants"
    ),
    "search_eu_horizon": (
        search_eu_horizon,
        "Search EU Horizon CORDIS — European research funding"
    ),
    "search_ukri": (
        search_ukri,
        "Search UKRI — UK Research and Innovation grants"
    ),
    "search_uspto_patents": (
        search_uspto,
        "Search USPTO — US patents via OpenAlex patent filter"
    ),
    "search_wipo_patents": (
        search_wipo,
        "Search WIPO PATENTSCOPE — 100+ country PCT patents"
    ),
    "search_epo_patents": (
        search_epo,
        "Search EPO Espacenet — European patent database"
    ),
    "search_lens_patents": (
        search_lens,
        "Search Lens.org — 120M+ global unified patents and literature"
    ),
    "search_google_patents": (
        search_google_patents,
        "Search Google Patents — global patent search via SerpAPI"
    ),
    "search_clinical_trials": (
        search_clinical_trials,
        "Search ClinicalTrials.gov — US and international clinical trials"
    ),
    "search_who_ictrp": (
        search_who,
        "Search WHO ICTRP — global clinical trial registry"
    ),
    "search_fda": (
        search_fda,
        "Search FDA — drug and medical device approvals and safety data"
    ),
    "search_ycombinator": (
        search_yc,
        "Search Y Combinator — funded startups via Hacker News"
    ),
    "search_product_hunt": (
        search_product_hunt,
        "Search Product Hunt — recently launched tech products"
    ),
    "search_fred": (
        search_fred,
        "Search FRED — Federal Reserve economic and financial data series"
    ),
    "search_news": (
        search_news,
        "Search NewsAPI — recent news articles across all topics"
    ),
    "search_alpha_vantage": (
        search_alpha_vantage,
        "Search Alpha Vantage — financial news sentiment and market data"
    ),
    "search_congress": (
        search_congress,
        "Search Congress.gov — US legislation and bill text"
    ),
    "search_courtlistener": (
        search_courtlistener,
        "Search CourtListener — US court opinions and legal cases"
    ),
}

@app.list_tools()
async def list_tools() -> list[Tool]:
    """Returns all registered ResearchNu source tools to MCP clients."""
    return [
        Tool(
            name=name,
            description=desc,
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query"
                    },
                    "max_results": {
                        "type": "integer",
                        "default": 10,
                        "description": "Maximum number of results to return"
                    }
                },
                "required": ["query"]
            }
        )
        for name, (_, desc) in TOOLS.items()
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Routes MCP tool call to the correct source function."""
    if name not in TOOLS:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]

    fn, _ = TOOLS[name]
    query       = arguments.get("query", "")
    max_results = arguments.get("max_results", 10)

    try:
        # source functions are sync — run in executor to avoid blocking event loop
        loop    = asyncio.get_event_loop()
        results = await loop.run_in_executor(None, lambda: fn(query, max_results))

        if not results:
            return [TextContent(type="text", text="No results found.")]

        formatted = "\n\n".join([
            f"Title: {r.get('title', 'N/A')}\n"
            f"Source: {r.get('source', 'N/A')}\n"
            f"Year: {r.get('year', 'N/A')}\n"
            f"URL: {r.get('url', 'N/A')}\n"
            f"Abstract: {r.get('abstract', '')[:400]}"
            for r in results
        ])
        return [TextContent(type="text", text=formatted)]

    except Exception as e:
        return [TextContent(type="text", text=f"Error calling {name}: {str(e)}")]

async def main():
    async with stdio_server() as (read, write):
        await app.run(read, write, app.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())