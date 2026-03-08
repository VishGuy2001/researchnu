# crossref.py
import httpx
from typing import List, Dict

def search_crossref(query: str, max_results: int = 20) -> List[Dict]:
    try:
        r = httpx.get("https://api.crossref.org/works", params={
            "query": query, "rows": max_results,
            "select": "title,abstract,DOI,published,URL"
        }, timeout=15, headers={"User-Agent": "ResearchNu/1.0 (mailto:research@researchnu.com)"})
        results = []
        for item in r.json().get("message", {}).get("items", []):
            title = item.get("title", [""])[0]
            year = ""
            pub = item.get("published", {}).get("date-parts", [[""]])
            if pub and pub[0]:
                year = str(pub[0][0])
            results.append({
                "title": title,
                "abstract": item.get("abstract", ""),
                "url": f"https://doi.org/{item.get('DOI', '')}",
                "year": year,
                "source": "crossref"
            })
        return results
    except Exception as e:
        print(f"crossref error: {e}")
        return []