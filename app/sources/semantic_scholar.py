import httpx
from typing import List, Dict

async def search(query: str, max_results: int = 20) -> List[Dict]:
    # good for citation counts and influence scores
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.get(
            "https://api.semanticscholar.org/graph/v1/paper/search",
            params={
                "query": query,
                "limit": max_results,
                "fields": "title,abstract,year,externalIds,citationCount,influentialCitationCount"
            }
        )
        out = []
        for p in r.json().get("data", []):
            doi = p.get("externalIds", {}).get("DOI", "")
            arxiv_id = p.get("externalIds", {}).get("ArXiv", "")
            url = f"https://doi.org/{doi}" if doi else f"https://arxiv.org/abs/{arxiv_id}" if arxiv_id else ""
            out.append({
                "title": p.get("title", ""),
                "abstract": p.get("abstract", ""),
                "year": str(p.get("year", "")),
                "url": url,
                "citations": p.get("citationCount", 0),
                "influential_citations": p.get("influentialCitationCount", 0),
                "source": "Semantic Scholar"
            })
        return out