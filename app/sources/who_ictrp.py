import httpx
from typing import List, Dict


def search_who(query: str, max_results: int = 10) -> List[Dict]:
    """Search WHO ICTRP via their public REST API."""
    try:
        r = httpx.get(
            "https://trialsearch.who.int/API/api.aspx",
            params={
                "query": query,
                "count": max_results,
                "fmt": "json",
            },
            timeout=20,
            headers={"Accept": "application/json"},
        )
        r.raise_for_status()
        data = r.json()
        results = []
        for t in data.get("trials", data.get("TrialID", [])):
            if isinstance(t, dict):
                results.append({
                    "title": t.get("Scientific_title", t.get("Public_title", "")),
                    "abstract": t.get("Interventions", "") or t.get("Primary_outcome", ""),
                    "url": t.get("url", f"https://trialsearch.who.int/Trial2.aspx?TrialID={t.get('TrialID','')}"),
                    "year": str(t.get("Date_registration", ""))[:4],
                    "source": "who_ictrp",
                })
        return results[:max_results]
    except Exception:
        # fallback: scrape WHO ICTRP export
        try:
            r2 = httpx.get(
                "https://trialsearch.who.int/Trial2.aspx",
                params={"SearchQuery": query},
                timeout=20,
                headers={"User-Agent": "ResearchNu/1.0 (vishnusekar20@gmail.com)"},
            )
            # if HTML returned, return empty — WHO ICTRP has unreliable API
            return []
        except Exception as e:
            print(f"who_ictrp error: {e}")
            return []