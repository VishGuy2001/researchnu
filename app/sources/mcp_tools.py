import asyncio
from typing import Any
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
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

# MCP server -- each source registered as a callable tool
# agents call sources through MCP protocol instead of direct imports
app = Server("researchnu")

# all 20 sources registered as MCP tools
TOOLS = {
    "search_pubmed": (pubmed, "Search PubMed -- 36M biomedical papers"),
    "search_arxiv": (arxiv, "Search arXiv -- 2M preprints across CS, physics, biology"),
    "search_openalex": (openalex, "Search OpenAlex -- 250M works across all fields"),
    "search_semantic_scholar": (semantic_scholar, "Search Semantic Scholar -- citation graph + influence scores"),
    "search_europe_pmc": (europe_pmc, "Search Europe PMC -- EU biomedical literature"),
    "search_core": (core_ac, "Search CORE -- 200M open access papers globally"),
    "search_crossref": (crossref, "Search CrossRef -- 150M works, DOI verification"),
    "search_nih": (nih, "Search NIH Reporter -- all NIH grants ever awarded"),
    "search_nsf": (nsf, "Search NSF Awards -- US science and engineering grants"),
    "search_eu_horizon": (eu, "Search EU Horizon Cordis -- European research funding"),
    "search_ukri": (ukri, "Search UKRI -- UK research council grants"),
    "search_uspto": (uspto, "Search USPTO -- US patents"),
    "search_wipo": (wipo, "Search WIPO PATENTSCOPE -- 100+ country PCT patents"),
    "search_epo": (epo, "Search EPO -- European patents"),
    "search_lens": (lens, "Search Lens.org -- global unified patents + literature"),
    "search_clinical_trials": (clinical, "Search ClinicalTrials.gov -- US and international trials"),
    "search_who_ictrp": (who, "Search WHO ICTRP -- global trial registry"),
    "search_fda": (fda, "Search FDA -- drug and device approvals"),
    "search_ycombinator": (yc, "Search Y Combinator -- funded startups via HN"),
    "search_product_hunt": (producthunt, "Search Product Hunt -- launched products"),
}

@app.list_tools()
async def list_tools() -> list[Tool]:
    # returns all 20 registered tools to any MCP client
    return [
        Tool(
            name=name,
            description=desc,
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "max_results": {"type": "integer", "default": 20}
                },
                "required": ["query"]
            }
        )
        for name, (_, desc) in TOOLS.items()
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    # routes tool call to the correct source client
    if name not in TOOLS:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]
    fn, _ = TOOLS[name]
    query = arguments.get("query", "")
    max_results = arguments.get("max_results", 20)
    try:
        results = await fn(query, max_results)
        # format results as text for MCP response
        out = "\n\n".join([
            f"Title: {r.get('title', '')}\nSource: {r.get('source', '')}\nYear: {r.get('year', '')}\nURL: {r.get('url', '')}\nAbstract: {r.get('abstract', '')[:300]}"
            for r in results
        ])
        return [TextContent(type="text", text=out or "No results found")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]

async def main():
    async with stdio_server() as (read, write):
        await app.run(read, write, app.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())