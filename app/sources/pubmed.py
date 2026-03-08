import httpx
import xml.etree.ElementTree as ET
from typing import List, Dict

async def search(query: str, max_results: int = 20) -> List[Dict]:
    # fetch pmids first, then abstracts
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.get(
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
            params={"db": "pubmed", "term": query, "retmax": max_results, "retmode": "json", "sort": "relevance"}
        )
        pmids = r.json()["esearchresult"]["idlist"]
        if not pmids:
            return []
        r2 = await c.get(
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi",
            params={"db": "pubmed", "id": ",".join(pmids), "rettype": "abstract", "retmode": "xml"}
        )
        return _parse(r2.text)

def _parse(xml: str) -> List[Dict]:
    out = []
    try:
        root = ET.fromstring(xml)
        for a in root.findall(".//PubmedArticle"):
            pmid = a.findtext(".//PMID", "")
            out.append({
                "title": a.findtext(".//ArticleTitle", "No title"),
                "abstract": a.findtext(".//AbstractText", "No abstract"),
                "year": a.findtext(".//PubDate/Year", "Unknown"),
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}",
                "source": "PubMed"
            })
    except ET.ParseError:
        pass
    return out