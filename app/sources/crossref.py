import httpx
from typing import List, Dict

async def search(query: str, max_results: int = 20) -> List[Dict]:
    # 150M+ works, used for doi verification and citation trust
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.get(
            "https://api.crossref.org/works",
            params={
                "query": query,
                "rows": max_results,
                "sort": "relevance",
                "select": "title,abstract,published,DOI,author,type"
            },
            headers={"User-Agent": "Researchnu/1.0 (vps39@drexel.edu)"}  # polite pool
        )
        out = []
        for p in r.json().get("message", {}).get("items", []):
            year = ""
            date_parts = p.get("published", {}).get("date-parts", [[""]])
            if date_parts and date_parts[0]:
                year = str(date_parts[0][0])
            out.append({
                "title": p.get("title", [""])[0],
                "abstract": p.get("abstract", ""),
                "year": year,
                "url": f"https://doi.org/{p.get('DOI', '')}",
                "source": "CrossRef"
            })
        return out