import httpx
import os
from typing import List, Dict

def search_congress(query: str, max_results: int = 10) -> List[Dict]:
    api_key = os.getenv("CONGRESS_API_KEY", "")
    if not api_key:
        return []
    try:
        r = httpx.get("https://api.congress.gov/v3/bill", params={
            "query": query,
            "api_key": api_key,
            "limit": max_results,
            "format": "json"
        }, timeout=15)
        results = []
        for b in r.json().get("bills", []):
            bill_num = f"{b.get('type','')}{b.get('number','')}"
            congress = b.get("congress", "")
            results.append({
                "title": b.get("title", ""),
                "abstract": f"Congress: {congress} | Latest action: {b.get('latestAction',{}).get('text','')}",
                "url": b.get("url", f"https://congress.gov/bill/{congress}th-congress/{b.get('type','').lower()}-bill/{b.get('number','')}"),
                "year": str(b.get("latestAction", {}).get("actionDate", ""))[:4],
                "source": "congress"
            })
        return results
    except Exception as e:
        print(f"congress error: {e}")
        return []