import httpx
from typing import List, Dict

def search_ukri(query: str, max_results: int = 20) -> List[Dict]:
    try:
        r = httpx.get("https://gtr.ukri.org/gtr/api/projects", params={"q": query, "p": 1, "n": max_results}, timeout=15, headers={"Accept": "application/json"})
        results = []
        for p in r.json().get("project", []):
            results.append({"title": p.get("title", ""), "abstract": p.get("abstractText", "") or "", "url": f"https://gtr.ukri.org/projects?ref={p.get('grantReference','')}", "year": str(p.get("fund", {}).get("start", ""))[:4], "source": "grants_ukri"})
        return results
    except Exception as e:
        print(f"grants_ukri error: {e}")
        return []
