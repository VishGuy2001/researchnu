import httpx
from typing import List, Dict

async def search(query: str, max_results: int = 20) -> List[Dict]:
    # YC companies, good signal for whether a startup idea already exists and got funded
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.get(
            "https://hn.algolia.com/api/v1/search",
            params={
                "query": query,
                "tags": "story",
                "hitsPerPage": max_results,
                "restrictSearchableAttributes": "title"
            }
        )
        out = []
        for h in r.json().get("hits", []):
            # filter for YC launch posts only
            if not any(kw in h.get("title", "").lower() for kw in ["launch hn", "show hn", "yc", "y combinator"]):
                continue
            out.append({
                "title": h.get("title", ""),
                "abstract": h.get("story_text", "") or h.get("comment_text", ""),
                "year": str(h.get("created_at", ""))[:4],
                "url": h.get("url", "") or f"https://news.ycombinator.com/item?id={h.get('objectID', '')}",
                "source": "Y Combinator"
            })
        return out[:max_results]