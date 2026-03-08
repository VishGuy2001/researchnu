import httpx
from typing import List, Dict

async def search(query: str, max_results: int = 20) -> List[Dict]:
    # every NIH grant ever awarded, huge signal for what's being funded
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.post(
            "https://api.reporter.nih.gov/v2/projects/search",
            json={
                "criteria": {
                    "advanced_text_search": {
                        "operator": "and",
                        "search_field": "all",
                        "search_text": query
                    }
                },
                "limit": max_results,
                "offset": 0,
                "fields": [
                    "ProjectTitle", "AbstractText", "ContactPiName",
                    "AwardAmount", "FiscalYear", "ProjectNum"
                ]
            }
        )
        out = []
        for g in r.json().get("results", []):
            out.append({
                "title": g.get("project_title", ""),
                "abstract": g.get("abstract_text", ""),
                "year": str(g.get("fiscal_year", "")),
                "amount": g.get("award_amount", 0),
                "pi": g.get("contact_pi_name", ""),
                "url": f"https://reporter.nih.gov/project-details/{g.get('project_num', '')}",
                "source": "NIH"
            })
        return out