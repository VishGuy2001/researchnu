import httpx
from typing import List, Dict

def search_epo(query: str, max_results: int = 20) -> List[Dict]:
    try:
        r = httpx.get("https://ops.epo.org/3.2/rest-services/published-data/search", params={"q": f'ctxt any "{query}"', "Range": f"1-{min(max_results,25)}"}, timeout=15, headers={"Accept": "application/json"})
        results = []
        docs = r.json().get("ops:world-patent-data", {}).get("ops:biblio-search", {}).get("ops:search-result", {}).get("ops:publication-reference", [])
        if isinstance(docs, dict):
            docs = [docs]
        for d in docs:
            doc_id = d.get("document-id", {})
            country = doc_id.get("country", {}).get("$", "")
            number = doc_id.get("doc-number", {}).get("$", "")
            results.append({"title": f"Patent {country}{number}", "abstract": "", "url": f"https://worldwide.espacenet.com/patent/search?q={country}{number}", "year": doc_id.get("date", {}).get("$", "")[:4], "source": "patents_epo"})
        return results
    except Exception as e:
        print(f"patents_epo error: {e}")
        return []
