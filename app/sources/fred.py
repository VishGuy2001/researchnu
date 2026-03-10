import httpx
import os
from typing import List, Dict


def search_fred(query: str, max_results: int = 10) -> List[Dict]:
    """FRED economic data series search."""
    api_key = os.getenv("FRED_API_KEY", "")
    if not api_key:
        return []
    try:
        # First try full_text search
        r = httpx.get(
            "https://api.stlouisfed.org/fred/series/search",
            params={
                "search_text":  query,
                "api_key":      api_key,
                "file_type":    "json",
                "limit":        max_results,
                "order_by":     "popularity",
                "sort_order":   "desc",
                "search_type":  "full_text",
            },
            timeout=15,
        )
        r.raise_for_status()
        series = r.json().get("seriess", [])

        # If full_text returns nothing, fall back to series_id keyword search
        if not series:
            r2 = httpx.get(
                "https://api.stlouisfed.org/fred/series/search",
                params={
                    "search_text": query,
                    "api_key":     api_key,
                    "file_type":   "json",
                    "limit":       max_results,
                    "order_by":    "popularity",
                    "sort_order":  "desc",
                    "search_type": "series_id",
                },
                timeout=15,
            )
            r2.raise_for_status()
            series = r2.json().get("seriess", [])

        results = []
        for s in series:
            sid = s.get("id", "")
            notes = s.get("notes", "") or ""
            results.append({
                "title":    s.get("title", ""),
                "abstract": (
                    f"{notes.strip()[:300]} | "
                    f"Units: {s.get('units', '')} | "
                    f"Frequency: {s.get('frequency', '')} | "
                    f"Last updated: {str(s.get('last_updated', ''))[:10]}"
                ),
                "url":    f"https://fred.stlouisfed.org/series/{sid}",
                "year":   str(s.get("observation_end", "2024"))[:4],
                "source": "fred",
            })
        return results

    except Exception as e:
        print(f"fred error: {e}")
        return []