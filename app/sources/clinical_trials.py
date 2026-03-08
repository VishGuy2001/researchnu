import httpx
from typing import List, Dict

async def search(query: str, max_results: int = 20) -> List[Dict]:
    # US and international clinical trials, critical for biomedical queries
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.get(
            "https://clinicaltrials.gov/api/v2/studies",
            params={
                "query.term": query,
                "pageSize": max_results,
                "format": "json",
                "fields": "NCTId,BriefTitle,BriefSummary,StartDate,OverallStatus,LeadSponsorName"
            }
        )
        out = []
        for s in r.json().get("studies", []):
            p = s.get("protocolSection", {})
            id_mod = p.get("identificationModule", {})
            desc_mod = p.get("descriptionModule", {})
            status_mod = p.get("statusModule", {})
            out.append({
                "title": id_mod.get("briefTitle", ""),
                "abstract": desc_mod.get("briefSummary", ""),
                "year": status_mod.get("startDateStruct", {}).get("date", "")[:4],
                "status": status_mod.get("overallStatus", ""),
                "url": f"https://clinicaltrials.gov/study/{id_mod.get('nctId', '')}",
                "source": "ClinicalTrials.gov"
            })
        return out