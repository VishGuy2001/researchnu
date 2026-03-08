import httpx
from typing import List, Dict

BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

def _parse(xml: str) -> List[Dict]:
    # basic xml parse without lxml dependency
    import re
    results = []
    articles = re.findall(r'<PubmedArticle>(.*?)</PubmedArticle>', xml, re.DOTALL)
    for a in articles:
        title = re.search(r'<ArticleTitle>(.*?)</ArticleTitle>', a, re.DOTALL)
        abstract = re.search(r'<AbstractText.*?>(.*?)</AbstractText>', a, re.DOTALL)
        pmid = re.search(r'<PMID.*?>(.*?)</PMID>', a)
        year = re.search(r'<PubDate>.*?<Year>(.*?)</Year>', a, re.DOTALL)
        results.append({
            "title": title.group(1).strip() if title else "",
            "abstract": abstract.group(1).strip() if abstract else "",
            "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid.group(1)}/" if pmid else "",
            "year": year.group(1).strip() if year else "",
            "source": "pubmed"
        })
    return results

def search_pubmed(query: str, max_results: int = 20) -> List[Dict]:
    try:
        # search for IDs
        r = httpx.get(f"{BASE}/esearch.fcgi", params={
            "db": "pubmed", "term": query, "retmax": max_results, "retmode": "json"
        }, timeout=10)
        ids = r.json().get("esearchresult", {}).get("idlist", [])
        if not ids:
            return []
        # fetch full records
        r2 = httpx.get(f"{BASE}/efetch.fcgi", params={
            "db": "pubmed", "id": ",".join(ids), "retmode": "xml", "rettype": "abstract"
        }, timeout=15)
        return _parse(r2.text)
    except Exception as e:
        print(f"pubmed error: {e}")
        return []