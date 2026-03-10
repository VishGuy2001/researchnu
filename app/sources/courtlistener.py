import httpx
import os
from typing import List, Dict


def search_courtlistener(query: str, max_results: int = 10) -> List[Dict]:
    token = os.getenv("COURTLISTENER_TOKEN", "")
    if not token:
        return []
    try:
        # CourtListener v4 API (v3 deprecated — causes 403)
        r = httpx.get(
            "https://www.courtlistener.com/api/rest/v4/search/",
            params={
                "q":        query,
                "type":     "o",           # opinions
                "order_by": "score desc",
                "page_size": max_results,
            },
            headers={
                "Authorization": f"Token {token}",
                "Accept": "application/json",
            },
            timeout=15,
        )
        r.raise_for_status()
        results = []
        for op in r.json().get("results", []):
            results.append({
                "title":    op.get("caseName") or op.get("case_name", ""),
                "abstract": op.get("snippet") or op.get("text", "")[:400],
                "url":      f"https://www.courtlistener.com{op.get('absolute_url', '')}",
                "year":     str(op.get("dateFiled", "") or op.get("date_filed", ""))[:4],
                "source":   "courtlistener",
            })
        return results
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 403:
            # Token expired — go to courtlistener.com/sign-in to regenerate
            return []
        print(f"courtlistener error: {e}")
        return []
    except Exception as e:
        print(f"courtlistener error: {e}")
        return []