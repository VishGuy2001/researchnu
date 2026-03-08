import httpx
from typing import List, Dict

async def search(query: str, max_results: int = 20) -> List[Dict]:
    # 200M+ open access papers, good for non-US research coverage
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.get(
            "https://api.core.ac.uk/v3/search/works",
            params={
                "q": query,
                "limit": max_results,
                "sort": "relevance"
            },
            headers={"Authorization": "Bearer core_api_key_here"}  # free at core.ac.uk/services/api
        )
        out = []
        for p in r.json().get("results", []):
            out.append({
                "title": p.get("title", ""),
                "abstract": p.get("abstract", ""),
                "year": str(p.get("yearPublished", "")),
                "url": p.get("sourceFulltextUrls", [""])[0] or p.get("downloadUrl", ""),
                "source": "CORE"
            })
        return out