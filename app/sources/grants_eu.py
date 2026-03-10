import httpx
from typing import List, Dict

def search_eu_horizon(query: str, max_results: int = 20) -> List[Dict]:
    try:
        r = httpx.get("https://cordis.europa.eu/search/en", params={
            "q": query, "p": 1, "num": max_results, "srt": "/project/contentUpdateDate:decreasing", "format": "json"
        }, timeout=15)
        results = []
        for p in r.json().get("results", {}).get("result", []):
            proj = p.get("project", {})
            results.append({
                "title": proj.get("title", ""),
                "abstract": proj.get("objective", "") or proj.get("teaser", "") or "",
                "url": f"https://cordis.europa.eu/project/id/{proj.get('id','')}",
                "year": str(proj.get("startDate", ""))[:4],
                "source": "grants_eu"
            })
        return results
    except Exception as e:
        print(f"grants_eu error: {e}")
        return []
