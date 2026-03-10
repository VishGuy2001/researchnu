import httpx
import os
from typing import List, Dict

def search_google_patents(query: str, max_results: int = 10) -> List[Dict]:
    api_key = os.getenv("SERPAPI_KEY", "")
    if not api_key:
        return []
    try:
        r = httpx.get("https://serpapi.com/search", params={
            "engine": "google_patents",
            "q": query,
            "api_key": api_key,
            "num": max_results
        }, timeout=15)
        results = []
        for p in r.json().get("organic_results", []):
            results.append({
                "title": p.get("title", ""),
                "abstract": p.get("snippet", ""),
                "url": p.get("patent_link", "") or p.get("link", ""),
                "year": str(p.get("filing_date", p.get("publication_date", "")))[:4],
                "source": "google_patents"
            })
        return results
    except Exception as e:
        print(f"google_patents error: {e}")
        return []