import httpx
from typing import List, Dict

async def search(query: str, max_results: int = 20) -> List[Dict]:
    # EU Horizon grants, biggest research funding program in the world
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.get(
            "https://cordis.europa.eu/api/rest/project",
            params={
                "q": query,
                "p": 1,
                "num": max_results,
                "format": "json"
            }
        )
        out = []
        for p in r.json().get("hits", {}).get("hit", []):
            proj = p.get("project", {})
            out.append({
                "title": proj.get("title", ""),
                "abstract": proj.get("objective", ""),
                "year": proj.get("startDate", "")[:4],
                "amount": proj.get("totalCost", 0),
                "url": f"https://cordis.europa.eu/project/id/{proj.get('id', '')}",
                "source": "EU Horizon"
            })
        return out