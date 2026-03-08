import httpx
from typing import List, Dict

async def search(query: str, max_results: int = 20) -> List[Dict]:
    # international patents via WIPO, covers 100+ countries PCT filings
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.get(
            "https://patentscope.wipo.int/search/en/rest/api/query",
            params={
                "q": query,
                "fl": "pctnumber,en_title,en_abs,filing_date,applicant_names",
                "rows": max_results,
                "start": 0,
                "so": "score desc"
            },
            headers={"Accept": "application/json"}
        )
        out = []
        for p in r.json().get("results", {}).get("patents", []):
            out.append({
                "title": p.get("en_title", ""),
                "abstract": p.get("en_abs", ""),
                "year": p.get("filing_date", "")[:4] if p.get("filing_date") else "",
                "url": f"https://patentscope.wipo.int/search/en/detail.jsf?docId={p.get('pctnumber', '')}",
                "source": "WIPO"
            })
        return out