import httpx
from typing import List, Dict

BASE = "https://api.openalex.org/works"

def _reconstruct_abstract(inverted: dict) -> str:
    if not inverted:
        return ""
    words = {}
    for word, positions in inverted.items():
        for pos in positions:
            words[pos] = word
    return " ".join(words[i] for i in sorted(words))

def search_openalex(query: str, max_results: int = 20) -> List[Dict]:
    try:
        r = httpx.get(BASE, params={
            "search": query,
            "per-page": max_results,
            "select": "title,abstract_inverted_index,doi,publication_year,primary_location"
        }, timeout=15, headers={"User-Agent": "ResearchNu/1.0 (research tool)"})
        results = []
        for w in r.json().get("results", []):
            abstract = _reconstruct_abstract(w.get("abstract_inverted_index", {}))
            doi = w.get("doi", "")
            results.append({
                "title": w.get("title", ""),
                "abstract": abstract,
                "url": doi if doi else "",
                "year": str(w.get("publication_year", "")),
                "source": "openalex"
            })
        return results
    except Exception as e:
        print(f"openalex error: {e}")
        return []