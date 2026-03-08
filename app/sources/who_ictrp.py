import httpx
import re
from typing import List, Dict

def search_who(query: str, max_results: int = 20) -> List[Dict]:
    try:
        r = httpx.get("https://trialsearch.who.int/API/Clinical_Trials_REST.asmx/GetTrials", params={"query": query, "count": max_results}, timeout=15)
        results = []
        trials = re.findall(r"<Trial>(.*?)</Trial>", r.text, re.DOTALL)
        for t in trials[:max_results]:
            title = re.search(r"<Title>(.*?)</Title>", t)
            desc = re.search(r"<Intervention>(.*?)</Intervention>", t)
            url = re.search(r"<url>(.*?)</url>", t)
            year = re.search(r"<Date_registration>(\d{4})", t)
            results.append({"title": title.group(1) if title else "", "abstract": desc.group(1) if desc else "", "url": url.group(1) if url else "", "year": year.group(1) if year else "", "source": "who_ictrp"})
        return results
    except Exception as e:
        print(f"who_ictrp error: {e}")
        return []
