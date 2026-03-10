import httpx
import os
from typing import List, Dict

def search_lens(query: str, max_results: int = 20) -> List[Dict]:
    api_key = os.getenv("LENS_API_KEY", "")
    if not api_key or api_key == "pending":
        return []
    try:
        r = httpx.post("https://api.lens.org/patent/search", json={
            "query": {"query_string": {"query": query}},
            "size": max_results
        }, headers={"Authorization": f"Bearer {api_key}"}, timeout=15)
        results = []
        for p in r.json().get("data", []):
            biblio = p.get("biblio", {})
            titles = biblio.get("invention_title", [])
            title = ""
            for t in titles:
                if t.get("lang") == "en":
                    title = t.get("text", "")
                    break
            if not title and titles:
                title = titles[0].get("text", "")
            abstract_list = biblio.get("abstract", [])
            abstract = ""
            for a in abstract_list:
                if a.get("lang") == "en":
                    abstract = a.get("text", "")
                    break
            results.append({
                "title": title,
                "abstract": abstract,
                "url": f"https://lens.org/lens/patent/{p.get('lens_id','')}",
                "year": str(p.get("date_published", ""))[:4],
                "source": "patents_lens"
            })
        return results
    except Exception as e:
        print(f"patents_lens error: {e}")
        return []
