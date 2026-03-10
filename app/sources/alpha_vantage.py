import httpx
import os
from typing import List, Dict

def search_alpha_vantage(query: str, max_results: int = 10) -> List[Dict]:
    api_key = os.getenv("ALPHAVANTAGE_KEY", "")
    if not api_key:
        return []
    try:
        # news sentiment search
        r = httpx.get("https://www.alphavantage.co/query", params={
            "function": "NEWS_SENTIMENT",
            "q": query,
            "apikey": api_key,
            "limit": max_results,
            "sort": "RELEVANCE"
        }, timeout=15)
        results = []
        for a in r.json().get("feed", []):
            results.append({
                "title": a.get("title", ""),
                "abstract": a.get("summary", ""),
                "url": a.get("url", ""),
                "year": str(a.get("time_published", ""))[:4],
                "source": "alpha_vantage"
            })
        return results
    except Exception as e:
        print(f"alpha_vantage error: {e}")
        return []