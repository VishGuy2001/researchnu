import httpx
import os
from typing import List, Dict


def search_product_hunt(query: str, max_results: int = 20) -> List[Dict]:
    token = os.getenv("PRODUCT_HUNT_DEVTOK", "")
    if not token:
        return []

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    try:
        # Step 1: find topics matching the query
        topic_gql = """query($q: String!) {
          topics(query: $q, first: 3, order: FOLLOWERS_COUNT) {
            edges { node { slug } }
          }
        }"""
        tr = httpx.post(
            "https://api.producthunt.com/v2/api/graphql",
            json={"query": topic_gql, "variables": {"q": query}},
            headers=headers,
            timeout=15,
        )
        topic_data = tr.json()
        slugs = [
            e["node"]["slug"]
            for e in (topic_data.get("data") or {})
                .get("topics", {}).get("edges", [])
        ]

        # Step 2: fetch posts for each topic slug, or fall back to trending
        results = []
        seen = set()

        if slugs:
            for slug in slugs:
                if len(results) >= max_results:
                    break
                posts_gql = """query($slug: String!, $first: Int!) {
                  posts(topic: $slug, first: $first, order: VOTES) {
                    edges {
                      node {
                        name tagline description url createdAt votesCount
                      }
                    }
                  }
                }"""
                pr = httpx.post(
                    "https://api.producthunt.com/v2/api/graphql",
                    json={"query": posts_gql, "variables": {"slug": slug, "first": max_results}},
                    headers=headers,
                    timeout=15,
                )
                for edge in (pr.json().get("data") or {}).get("posts", {}).get("edges", []):
                    n = edge.get("node", {})
                    key = n.get("url") or n.get("name")
                    if key in seen:
                        continue
                    seen.add(key)
                    results.append({
                        "title":    n.get("name", ""),
                        "abstract": (
                            f"{n.get('tagline', '')} {n.get('description', '')}".strip()
                            + f" | Topic: {slug} | Votes: {n.get('votesCount', 0)}"
                        ),
                        "url":    n.get("url", ""),
                        "year":   str(n.get("createdAt", ""))[:4],
                        "source": "market_ph",
                    })
        else:
            # No topic match — return top trending posts as fallback
            posts_gql = """query($first: Int!) {
              posts(first: $first, order: VOTES) {
                edges {
                  node { name tagline url createdAt votesCount }
                }
              }
            }"""
            pr = httpx.post(
                "https://api.producthunt.com/v2/api/graphql",
                json={"query": posts_gql, "variables": {"first": max_results}},
                headers=headers,
                timeout=15,
            )
            for edge in (pr.json().get("data") or {}).get("posts", {}).get("edges", []):
                n = edge.get("node", {})
                results.append({
                    "title":    n.get("name", ""),
                    "abstract": f"{n.get('tagline', '')} | Votes: {n.get('votesCount', 0)}",
                    "url":    n.get("url", ""),
                    "year":   str(n.get("createdAt", ""))[:4],
                    "source": "market_ph",
                })

        return results[:max_results]

    except Exception as e:
        print(f"market_ph error: {e}")
        return []