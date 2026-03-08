import httpx
from typing import List, Dict

async def search(query: str, max_results: int = 20) -> List[Dict]:
    # WHO global trial registry, catches trials not in clinicaltrials.gov
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.get(
            "https://trialsearch.who.int/API/endpoint.aspx",
            params={
                "query": query,
                "count": max_results,
                "format": "json"
            }
        )
        out = []
        for t in r.json().get("trials", []):
            out.append({
                "title": t.get("public_title", ""),
                "abstract": t.get("scientific_title", ""),
                "year": t.get("date_registration", "")[:4],
                "status": t.get("recruitment_status", ""),
                "url": t.get("url", ""),
                "source": "WHO ICTRP"
            })
        return out