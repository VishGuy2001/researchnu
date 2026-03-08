import httpx
from typing import List, Dict

async def search(query: str, max_results: int = 20) -> List[Dict]:
    # NSF awards across all science and engineering fields
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.get(
            "https://api.nsf.gov/services/v1/awards.json",
            params={
                "keyword": query,
                "rpp": max_results,
                "fields": "id,title,abstractText,fundsObligatedAmt,date,piFirstName,piLastName"
            }
        )
        out = []
        for a in r.json().get("response", {}).get("award", []):
            out.append({
                "title": a.get("title", ""),
                "abstract": a.get("abstractText", ""),
                "year": a.get("date", "")[-4:] if a.get("date") else "",
                "amount": a.get("fundsObligatedAmt", 0),
                "pi": f"{a.get('piFirstName', '')} {a.get('piLastName', '')}".strip(),
                "url": f"https://www.nsf.gov/awardsearch/showAward?AWD_ID={a.get('id', '')}",
                "source": "NSF"
            })
        return out