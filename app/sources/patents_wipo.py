import httpx
from typing import List, Dict

def search_wipo(query: str, max_results: int = 20) -> List[Dict]:
    try:
        r = httpx.get("https://patentscope.wipo.int/search/en/rest/api/v1/results", params={"query": query, "maxResults": max_results, "fields": "PN,TI,AB,PD"}, timeout=15)
        results = []
        for p in r.json().get("results", []):
            results.append({"title": p.get("TI", ""), "abstract": p.get("AB", ""), "url": f"https://patentscope.wipo.int/search/en/detail.jsf?docId={p.get('PN','')}", "year": str(p.get("PD", ""))[:4], "source": "patents_wipo"})
        return results
    except Exception as e:
        print(f"patents_wipo error: {e}")
        return []
