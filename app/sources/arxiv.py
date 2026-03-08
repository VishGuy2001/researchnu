import httpx
import xml.etree.ElementTree as ET
from typing import List, Dict

NS = {"atom": "http://www.w3.org/2005/Atom"}

async def search(query: str, max_results: int = 20) -> List[Dict]:
    # preprint server for CS, physics, math, biology, economics
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.get(
            "http://export.arxiv.org/api/query",
            params={
                "search_query": f"all:{query}",
                "start": 0,
                "max_results": max_results,
                "sortBy": "relevance",
                "sortOrder": "descending"
            }
        )
        root = ET.fromstring(r.text)
        out = []
        for e in root.findall("atom:entry", NS):
            aid = e.find("atom:id", NS).text.split("/abs/")[-1]
            out.append({
                "title": e.find("atom:title", NS).text.strip().replace("\n", " "),
                "abstract": e.find("atom:summary", NS).text.strip().replace("\n", " "),
                "year": e.find("atom:published", NS).text[:4],
                "url": f"https://arxiv.org/abs/{aid}",
                "source": "arXiv"
            })
        return out