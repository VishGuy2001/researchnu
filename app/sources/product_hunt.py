import httpx
import os
from typing import List, Dict

def search_product_hunt(query: str, max_results: int = 20) -> List[Dict]:
    token = os.getenv("PRODUCT_HUNT_DEVTOK", "")
    if not token:
        return []
    try:
        gql = """query($q: String!) {
          posts(first: 20, order: VOTES, search: {query: $q}) {
            edges { node { name tagline description url createdAt } }
          }
        }"""
        r = httpx.post("https://api.producthunt.com/v2/api/graphql",
            json={"query": gql, "variables": {"q": query}},
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            timeout=15)
        data = r.json()
        posts = data.get("data") or {}
        results = []
        for edge in (posts.get("posts") or {}).get("edges", []):
            n = edge.get("node", {})
            results.append({
                "title": n.get("name", ""),
                "abstract": f"{n.get('tagline','')} {n.get('description','')}".strip(),
                "url": n.get("url", ""),
                "year": str(n.get("createdAt", ""))[:4],
                "source": "market_ph"
            })
        return results
    except Exception as e:
        print(f"market_ph error: {e}")
        return []
