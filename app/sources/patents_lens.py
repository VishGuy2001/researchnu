import httpx
import os
from typing import List, Dict

def search_lens(query: str, max_results: int = 20) -> List[Dict]:
    api_key = os.getenv("LENS_API_KEY", "")
    if not api_key or api_key == "pending":
        return []
    try:
        r = httpx.post("https://api.lens.org/patent/search", json={"query": {"match": {"title": query}}, "size": max_results, "include": ["title", "abstract", "lens_id", "date_published"]}, headers={"Authorization": f"Bearer {api_key}"}, timeout=15)
        results = []
        for p in r.json().get("data", []):
            results.append({"title": p.get("title", ""), "abstract": p.get("abstract", "") or "", "url": f"https://lens.org/lens/patent/{p.get('lens_id','')}", "year": str(p.get("date_published", ""))[:4], "source": "patents_lens"})
        return results
    except Exception as e:
        print(f"patents_lens error: {e}")
        return []
