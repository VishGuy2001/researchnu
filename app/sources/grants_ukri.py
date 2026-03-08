import httpx
from typing import List, Dict

async def search(query: str, max_results: int = 20) -> List[Dict]:
    # UK research funding, covers all major UK research councils
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.get(
            "https://gtr.ukri.org/resources/search.json",
            params={
                "q": query,
                "p": 1,
                "s": max_results,
                "sf": "score",
                "so": "desc",
                "f": "pro.gr"  # projects with grants only
            }
        )
        out = []
        for p in r.json().get("projectOverview", {}).get("projectComposition", []):
            proj = p.get("project", {})
            out.append({
                "title": proj.get("title", ""),
                "abstract": proj.get("abstractText", ""),
                "year": proj.get("startDate", "")[:4],
                "amount": proj.get("fund", {}).get("valuePounds", 0),
                "url": f"https://gtr.ukri.org/projects?ref={proj.get('grantReference', '')}",
                "source": "UKRI"
            })
        return out