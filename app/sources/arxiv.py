import httpx
import re
from typing import List, Dict

BASE = "https://export.arxiv.org/api/query"

def search_arxiv(query: str, max_results: int = 20) -> List[Dict]:
    try:
        r = httpx.get(BASE, params={
            "search_query": f"all:{query}",
            "start": 0,
            "max_results": max_results
        }, timeout=15)
        entries = re.findall(r'<entry>(.*?)</entry>', r.text, re.DOTALL)
        results = []
        for e in entries:
            title = re.search(r'<title>(.*?)</title>', e, re.DOTALL)
            summary = re.search(r'<summary>(.*?)</summary>', e, re.DOTALL)
            link = re.search(r'<id>(.*?)</id>', e)
            year = re.search(r'<published>(\d{4})', e)
            results.append({
                "title": title.group(1).strip().replace("\n", " ") if title else "",
                "abstract": summary.group(1).strip().replace("\n", " ") if summary else "",
                "url": link.group(1).strip() if link else "",
                "year": year.group(1) if year else "",
                "source": "arxiv"
            })
        return results
    except Exception as e:
        print(f"arxiv error: {e}")
        return []