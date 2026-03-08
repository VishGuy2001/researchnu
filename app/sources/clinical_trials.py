import httpx
from typing import List, Dict

BASE = "https://clinicaltrials.gov/api/v2/studies"

def search_clinical_trials(query: str, max_results: int = 20) -> List[Dict]:
    try:
        r = httpx.get(BASE, params={
            "query.term": query, "pageSize": max_results,
            "fields": "NCTId,BriefTitle,BriefSummary,StartDate,OverallStatus"
        }, timeout=15)
        results = []
        for s in r.json().get("studies", []):
            p = s.get("protocolSection", {})
            ident = p.get("identificationModule", {})
            desc = p.get("descriptionModule", {})
            status = p.get("statusModule", {})
            nct = ident.get("nctId", "")
            results.append({
                "title": ident.get("briefTitle", ""),
                "abstract": desc.get("briefSummary", ""),
                "url": f"https://clinicaltrials.gov/study/{nct}",
                "year": status.get("startDateStruct", {}).get("date", "")[:4],
                "source": "clinical_trials"
            })
        return results
    except Exception as e:
        print(f"clinical_trials error: {e}")
        return []