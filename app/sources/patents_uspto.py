import httpx
from typing import List, Dict

async def search(query: str, max_results: int = 20) -> List[Dict]:
    # US patents, most detailed patent data available
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.post(
            "https://search.patentsview.org/api/v1/patent/",
            json={
                "q": {"_text_any": {"patent_abstract": query}},
                "f": ["patent_id", "patent_title", "patent_abstract", "patent_date", "inventor_first_name", "inventor_last_name"],
                "o": {"per_page": max_results}
            }
        )
        out = []
        for p in r.json().get("patents", []):
            out.append({
                "title": p.get("patent_title", ""),
                "abstract": p.get("patent_abstract", ""),
                "year": p.get("patent_date", "")[:4] if p.get("patent_date") else "",
                "url": f"https://patents.google.com/patent/US{p.get('patent_id', '')}",
                "source": "USPTO"
            })
        return out