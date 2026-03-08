import httpx
from typing import List, Dict

async def search(query: str, max_results: int = 20) -> List[Dict]:
    # product hunt for market signal — if it launched here it exists
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.get(
            "https://api.producthunt.com/v2/api/graphql",
            json={
                "query": """
                query {
                    posts(first: %d, order: RELEVANCE, search: { query: "%s" }) {
                        edges {
                            node {
                                name
                                tagline
                                description
                                votesCount
                                website
                                createdAt
                            }
                        }
                    }
                }
                """ % (max_results, query.replace('"', ''))
            },
            headers={
                "Authorization": f"Bearer {__import__('os').getenv('PRODUCT_HUNT_API_KEY', '')}",
                "Content-Type": "application/json"
            }
        )
        out = []
        for edge in r.json().get("data", {}).get("posts", {}).get("edges", []):
            p = edge.get("node", {})
            out.append({
                "title": p.get("name", ""),
                "abstract": p.get("description", "") or p.get("tagline", ""),
                "year": p.get("createdAt", "")[:4],
                "url": p.get("website", ""),
                "votes": p.get("votesCount", 0),
                "source": "Product Hunt"
            })
        return out


