import httpx
from typing import List, Dict

def search_uspto(query: str, max_results: int = 20) -> List[Dict]:
    try:
        r = httpx.get("https://api.openalex.org/works", params={
            "search": query,
            "filter": "type:patent",
            "per-page": max_results,
            "select": "title,abstract_inverted_index,doi,publication_year"
        }, timeout=15, headers={"User-Agent": "ResearchNu/1.0"})
        results = []
        for w in r.json().get("results", []):
            words = {}
            for word, positions in (w.get("abstract_inverted_index") or {}).items():
                for pos in positions:
                    words[pos] = word
            abstract = " ".join(words[i] for i in sorted(words))
            results.append({
                "title": w.get("title", ""),
                "abstract": abstract,
                "url": w.get("doi", ""),
                "year": str(w.get("publication_year", "")),
                "source": "patents_uspto"
            })
        return results
    except Exception as e:
        print(f"patents_uspto error: {e}")
        return []
