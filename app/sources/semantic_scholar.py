import httpx
from typing import List, Dict

BASE = "https://api.semanticscholar.org/graph/v1/paper/search"

def search_semantic_scholar(query: str, max_results: int = 20) -> List[Dict]:
    try:
        r = httpx.get(BASE, params={
            "query": query,
            "limit": max_results,
            "fields": "title,abstract,year,externalIds,url"
        }, timeout=15)
        results = []
        for p in r.json().get("data", []):
            ext = p.get("externalIds", {})
            url = p.get("url", "")
            if ext.get("DOI"):
                url = f"https://doi.org/{ext['DOI']}"
            elif ext.get("ArXiv"):
                url = f"https://arxiv.org/abs/{ext['ArXiv']}"
            results.append({
                "title": p.get("title", ""),
                "abstract": p.get("abstract", "") or "",
                "url": url,
                "year": str(p.get("year", "")),
                "source": "semantic_scholar"
            })
        return results
    except Exception as e:
        print(f"semantic_scholar error: {e}")
        return []