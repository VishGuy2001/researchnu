import httpx
from typing import List, Dict

BASE = "https://api.reporter.nih.gov/v2/projects/search"

def search_nih(query: str, max_results: int = 20) -> List[Dict]:
    try:
        r = httpx.post(BASE, json={
            "criteria": {"advanced_text_search": {"operator": "and", "search_field": "all", "search_text": query}},
            "limit": max_results, "offset": 0
        }, timeout=15)
        results = []
        for p in r.json().get("results", []):
            results.append({
                "title": p.get("project_title", ""),
                "abstract": p.get("abstract_text", "") or "",
                "url": f"https://reporter.nih.gov/project-details/{p.get('appl_id', '')}",
                "year": str(p.get("fiscal_year", "")),
                "source": "grants_nih"
            })
        return results
    except Exception as e:
        print(f"grants_nih error: {e}")
        return []