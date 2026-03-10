import httpx
import os
from typing import List, Dict


def search_news(query: str, max_results: int = 20) -> List[Dict]:
    api_key = os.getenv("NEWS_API_KEY", "")
    if not api_key:
        return []
    try:
        r = httpx.get(
            "https://newsapi.org/v2/everything",
            params={
                "q": query,
                "apiKey": api_key,
                "pageSize": min(max_results, 100),
                "page": 1,
                "sortBy": "relevancy",
                "language": "en",
            },
            timeout=15,
        )
        r.raise_for_status()
        results = []
        for a in r.json().get("articles", []):
            # skip removed articles
            if a.get("title") == "[Removed]":
                continue
            abstract = a.get("description") or a.get("content", "")
            if abstract and len(abstract) > 300:
                abstract = abstract[:300]
            results.append({
                "title":    a.get("title", ""),
                "abstract": abstract,
                "url":      a.get("url", ""),
                "year":     str(a.get("publishedAt", "2024"))[:4],
                "source":   "news",
            })
        return results
    except Exception as e:
        print(f"news error: {e}")
        return []