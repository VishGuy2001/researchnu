import httpx
from typing import List, Dict

def search_yc(query: str, max_results: int = 20) -> List[Dict]:
    try:
        r = httpx.get("https://hn.algolia.com/api/v1/search", params={"query": query, "tags": "story", "hitsPerPage": max_results}, timeout=15)
        results = []
        for h in r.json().get("hits", []):
            results.append({"title": h.get("title", ""), "abstract": h.get("story_text", "") or "", "url": h.get("url", "") or f"https://news.ycombinator.com/item?id={h.get('objectID','')}", "year": str(h.get("created_at", ""))[:4], "source": "market_yc"})
        return results
    except Exception as e:
        print(f"market_yc error: {e}")
        return []
