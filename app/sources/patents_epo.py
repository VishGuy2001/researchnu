import httpx
from typing import List, Dict


def search_epo(query: str, max_results: int = 20) -> List[Dict]:
    """EPO Espacenet free search — no API key required."""
    try:
        r = httpx.get(
            "https://worldwide.espacenet.com/3.2/rest-services/published-data/search",
            params={
                "q": f"ctxt any \"{query}\"",
                "Range": f"1-{min(max_results, 25)}",
            },
            timeout=15,
            headers={
                "Accept": "application/json",
                "X-OPS-Accept-Datasets": "EP",
            },
        )
        # Espacenet returns 200 with empty body or non-JSON on some queries
        if not r.content or r.status_code != 200:
            return []

        try:
            data = r.json()
        except Exception:
            return []

        docs = (
            data.get("ops:world-patent-data", {})
                .get("ops:biblio-search", {})
                .get("ops:search-result", {})
                .get("ops:publication-reference", [])
        )
        if isinstance(docs, dict):
            docs = [docs]

        results = []
        for d in docs:
            doc_id = d.get("document-id", {})
            country = doc_id.get("country", {}).get("$", "")
            number  = doc_id.get("doc-number", {}).get("$", "")
            date    = doc_id.get("date", {}).get("$", "")
            results.append({
                "title":    f"Patent {country}{number}",
                "abstract": "",
                "url":      f"https://worldwide.espacenet.com/patent/search?q={country}{number}",
                "year":     str(date)[:4],
                "source":   "patents_epo",
            })
        return results

    except Exception:
        # Silently return 0 — EPO is a no-key fallback, not mission critical
        return []