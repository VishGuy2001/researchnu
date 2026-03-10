import httpx
import os
from typing import List, Dict

BASE = "https://api.core.ac.uk/v3/search/works"


def search_core(query: str, max_results: int = 20) -> List[Dict]:
    """CORE open access research search."""
    api_key = os.getenv("CORE_API_KEY", "")

    # CORE requires a valid key — without one results are heavily rate-limited
    if not api_key or api_key in ("pending", "xxx", ""):
        return []

    headers = {"Authorization": f"Bearer {api_key}"}

    try:
        r = httpx.post(
            BASE,
            json={"q": query, "limit": max_results},
            headers=headers,
            timeout=20,
        )
        r.raise_for_status()
        results = []
        for p in r.json().get("results", []):
            urls = p.get("sourceFulltextUrls") or []
            url  = p.get("downloadUrl") or (urls[0] if urls else "")
            results.append({
                "title":    p.get("title", ""),
                "abstract": (p.get("abstract") or "")[:500],
                "url":      url,
                "year":     str(p.get("yearPublished", "")),
                "source":   "core",
            })
        return results

    except httpx.HTTPStatusError as e:
        # 401 = bad key, 429 = rate limit, 500 = server flaky — all silent
        if e.response.status_code in (401, 429, 500):
            return []
        print(f"core error: {e}")
        return []
    except Exception as e:
        print(f"core error: {e}")
        return []