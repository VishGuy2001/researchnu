import httpx
from typing import List, Dict

BASE = "https://api.patentsview.org/patents/query"

def search_uspto(query: str, max_results: int = 20) -> List[Dict]:
    try:
        r = httpx.post(BASE, json={
            "q": {"_text_any": {"patent_abstract": query}},
            "f": ["patent_id", "patent_title", "patent_abstract", "patent_date"],
            "o": {"per_page": max_results}
        }, timeout=15)
        results = []
        for p in r.json().get("patents") or []:
            results.append({
                "title": p.get("patent_title", ""),
                "abstract": p.get("patent_abstract", ""),
                "url": f"https://patents.google.com/patent/US{p.get('patent_id','')}",
                "year": p.get("patent_date", "")[:4],
                "source": "patents_uspto"
            })
        return results
    except Exception as e:
        print(f"patents_uspto error: {e}")
        return []