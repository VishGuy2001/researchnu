import httpx
from typing import List, Dict

async def search(query: str, max_results: int = 20) -> List[Dict]:
    # european patents via EPO open patent services, covers EP + worldwide
    async with httpx.AsyncClient(timeout=30) as c:
        # OPS API — register free at ops.epo.org for higher rate limits
        r = await c.get(
            "https://ops.epo.org/3.2/rest-services/published-data/search",
            params={
                "q": f"txt={query}",
                "Range": f"1-{max_results}"
            },
            headers={"Accept": "application/json"}
        )
        out = []
        for p in r.json().get("ops:world-patent-data", {}).get("ops:biblio-search", {}).get("ops:search-result", {}).get("ops:publication-reference", []):
            doc = p.get("document-id", {})
            doc_num = doc.get("doc-number", {}).get("$", "")
            country = doc.get("country", {}).get("$", "EP")
            out.append({
                "title": "",  # EPO requires second call for title, added in Week 2
                "abstract": "",
                "year": doc.get("date", {}).get("$", "")[:4],
                "url": f"https://worldwide.espacenet.com/patent/search?q=pn%3D{country}{doc_num}",
                "source": "EPO"
            })
        return out