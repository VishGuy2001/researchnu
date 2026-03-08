import httpx
from typing import List, Dict

def search_eu_horizon(query: str, max_results: int = 20) -> List[Dict]:
    try:
        r = httpx.get("https://cordis.europa.eu/api/projects", params={"q": query, "p": 1, "n": max_results, "format": "json"}, timeout=15)
        results = []
        for p in r.json().get("results", []):
            results.append({"title": p.get("title", ""), "abstract": p.get("objective", "") or "", "url": f"https://cordis.europa.eu/project/id/{p.get('id','')}", "year": str(p.get("startDate", ""))[:4], "source": "grants_eu"})
        return results
    except Exception as e:
        print(f"grants_eu error: {e}")
        return []
