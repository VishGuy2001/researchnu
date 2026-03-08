import httpx
from typing import List, Dict

def search_nsf(query: str, max_results: int = 20) -> List[Dict]:
    try:
        r = httpx.get("https://api.nsf.gov/services/v1/awards.json", params={
            "keyword": query, "rpp": max_results,
            "fields": "id,title,abstractText,date,pdPIName"
        }, timeout=15)
        results = []
        for p in r.json().get("response", {}).get("award", []):
            results.append({
                "title": p.get("title", ""),
                "abstract": p.get("abstractText", ""),
                "url": f"https://www.nsf.gov/awardsearch/showAward?AWD_ID={p.get('id','')}",
                "year": p.get("date", "")[-4:] if p.get("date") else "",
                "source": "grants_nsf"
            })
        return results
    except Exception as e:
        print(f"grants_nsf error: {e}")
        return []