import httpx
from typing import List, Dict

async def search(query: str, max_results: int = 20) -> List[Dict]:
    # 250M+ works across all fields, best broad academic coverage
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.get(
            "https://api.openalex.org/works",
            params={
                "search": query,
                "per-page": max_results,
                "sort": "relevance_score:desc",
                "filter": "is_oa:true",  # open access only, always has full data
                "mailto": "vps39@drexel.edu"  # polite pool = faster responses
            }
        )
        out = []
        for w in r.json().get("results", []):
            out.append({
                "title": w.get("title", ""),
                "abstract": _reconstruct_abstract(w.get("abstract_inverted_index", {})),
                "year": str(w.get("publication_year", "")),
                "url": w.get("doi", "") or w.get("id", ""),
                "source": "OpenAlex"
            })
        return out

def _reconstruct_abstract(inverted: dict) -> str:
    # openalex stores abstracts as inverted index, need to rebuild
    if not inverted:
        return ""
    words = [""] * (max(max(v) for v in inverted.values()) + 1)
    for word, positions in inverted.items():
        for pos in positions:
            words[pos] = word
    return " ".join(words)