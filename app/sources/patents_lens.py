import httpx
from typing import List, Dict

async def search(query: str, max_results: int = 20) -> List[Dict]:
    # lens.org unifies patents + literature, best global patent coverage
    # free api key at lens.org/lens/user/subscriptions
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.post(
            "https://api.lens.org/patent/search",
            json={
                "query": {
                    "match_phrase": {
                        "abstract.text": query
                    }
                },
                "size": max_results,
                "sort": [{"relevance_score": "desc"}],
                "include": ["title", "abstract", "date_published", "jurisdiction", "lens_id"]
            },
            headers={
                "Authorization": f"Bearer {__import__('os').getenv('LENS_API_KEY', '')}",
                "Content-Type": "application/json"
            }
        )
        out = []
        for p in r.json().get("data", []):
            out.append({
                "title": p.get("title", [{}])[0].get("text", "") if p.get("title") else "",
                "abstract": p.get("abstract", [{}])[0].get("text", "") if p.get("abstract") else "",
                "year": p.get("date_published", "")[:4],
                "url": f"https://lens.org/lens/patent/{p.get('lens_id', '')}",
                "source": "Lens.org"
            })
        return out