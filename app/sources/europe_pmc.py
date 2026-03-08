import httpx
from typing import List, Dict

async def search(query: str, max_results: int = 20) -> List[Dict]:
    # european biomedical literature, good overlap with pubmed but catches more EU research
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.get(
            "https://www.ebi.ac.uk/europepmc/webservices/rest/search",
            params={
                "query": query,
                "resultType": "core",
                "pageSize": max_results,
                "format": "json",
                "sort": "RELEVANCE"
            }
        )
        out = []
        for p in r.json().get("resultList", {}).get("result", []):
            out.append({
                "title": p.get("title", ""),
                "abstract": p.get("abstractText", ""),
                "year": str(p.get("pubYear", "")),
                "url": f"https://europepmc.org/article/{p.get('source', '')}/{p.get('id', '')}",
                "source": "Europe PMC"
            })
        return out