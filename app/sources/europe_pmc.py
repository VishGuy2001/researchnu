import httpx
from typing import List, Dict

BASE = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"

def search_europe_pmc(query: str, max_results: int = 20) -> List[Dict]:
    try:
        r = httpx.get(BASE, params={
            "query": query, "resultType": "core",
            "pageSize": max_results, "format": "json"
        }, timeout=15)
        results = []
        for p in r.json().get("resultList", {}).get("result", []):
            results.append({
                "title": p.get("title", ""),
                "abstract": p.get("abstractText", ""),
                "url": f"https://europepmc.org/article/{p.get('source','')}/{p.get('id','')}",
                "year": str(p.get("pubYear", "")),
                "source": "europe_pmc"
            })
        return results
    except Exception as e:
        print(f"europe_pmc error: {e}")
        return []