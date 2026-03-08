import httpx
from typing import List, Dict

async def search(query: str, max_results: int = 20) -> List[Dict]:
    # FDA drug and device approvals, useful for biomedical and pharma queries
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.get(
            "https://api.fda.gov/drug/label.json",
            params={
                "search": query,
                "limit": max_results
            }
        )
        out = []
        for d in r.json().get("results", []):
            openfda = d.get("openfda", {})
            out.append({
                "title": ", ".join(openfda.get("brand_name", ["Unknown"])),
                "abstract": " ".join(d.get("indications_and_usage", ["No description"])),
                "year": d.get("effective_time", "")[:4],
                "url": f"https://labels.fda.gov",
                "source": "FDA"
            })
        return out