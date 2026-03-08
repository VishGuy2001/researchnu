import httpx
import os
from typing import List, Dict

BASE = "https://api.core.ac.uk/v3/search/works"

def search_core(query: str, max_results: int = 20) -> List[Dict]:
    api_key = os.getenv("CORE_API_KEY", "")
    headers = {"Authorization": f"Bearer {api_key}"} if api_key and api_key != "pending" else {}
    try:
        r = httpx.post(BASE, json={
            "q": query, "limit": max_results
        }, headers=headers, timeout=15)
        results = []
        for p in r.json().get("results", []):
            results.append({
                "title": p.get("title", ""),
                "abstract": p.get("abstract", "") or "",
                "url": p.get("downloadUrl", "") or p.get("sourceFulltextUrls", [""])[0],
                "year": str(p.get("yearPublished", "")),
                "source": "core"
            })
        return results
    except Exception as e:
        print(f"core error: {e}")
        return []