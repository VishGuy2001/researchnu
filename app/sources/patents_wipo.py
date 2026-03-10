import httpx
from typing import List, Dict

def search_wipo(query: str, max_results: int = 20) -> List[Dict]:
    # WIPO patentscope free search via scrape-friendly endpoint
    try:
        r = httpx.get("https://patentscope.wipo.int/search/en/results.jsf", params={
            "query": query, "office": "all", "rss": "true"
        }, timeout=15, headers={"Accept": "application/rss+xml,application/xml"})
        import re
        results = []
        items = re.findall(r"<item>(.*?)</item>", r.text, re.DOTALL)
        for item in items[:max_results]:
            title = re.search(r"<title>(.*?)</title>", item)
            link = re.search(r"<link>(.*?)</link>", item)
            desc = re.search(r"<description>(.*?)</description>", item)
            date = re.search(r"<pubDate>(.*?)</pubDate>", item)
            year = ""
            if date:
                import re as re2
                y = re2.search(r"\d{4}", date.group(1))
                year = y.group(0) if y else ""
            results.append({
                "title": title.group(1) if title else "",
                "abstract": desc.group(1) if desc else "",
                "url": link.group(1) if link else "",
                "year": year,
                "source": "patents_wipo"
            })
        return results
    except Exception as e:
        print(f"patents_wipo error: {e}")
        return []
