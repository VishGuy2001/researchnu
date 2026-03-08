import httpx
from typing import List, Dict

def search_fda(query: str, max_results: int = 20) -> List[Dict]:
    try:
        r = httpx.get("https://api.fda.gov/drug/label.json", params={
            "search": query, "limit": max_results
        }, timeout=15)
        results = []
        for item in r.json().get("results", []):
            openfda = item.get("openfda", {})
            title = (openfda.get("brand_name") or openfda.get("generic_name") or [""])[0]
            abstract = " ".join((item.get("indications_and_usage") or [""]))[:500]
            results.append({"title": title, "abstract": abstract, "url": "https://www.fda.gov/drugs", "year": "", "source": "fda"})
        return results
    except Exception as e:
        print(f"fda error: {e}")
        return []
