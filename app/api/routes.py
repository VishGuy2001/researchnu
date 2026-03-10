"""
ResearchNu — API Router
Modular routes mounted at /api prefix in main.py.
"""
from fastapi import APIRouter, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.api.schemas import QueryRequest, QueryResponse, Citation
from app.agents.pipeline import run_query, SOURCE_REGISTRY, SOURCE_PROFILES

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.post("/query", response_model=QueryResponse)
@limiter.limit("10/minute")
def query_endpoint(request: Request, req: QueryRequest):
    """Main research query endpoint."""
    try:
        r = run_query(
            query=req.query,
            user_type=req.user_type,
            privacy_mode=req.privacy_mode,
            focus_areas=req.focus_areas,
        )
        return QueryResponse(
            query=r["query"],
            summary=r.get("summary", ""),
            detailed_answer=r.get("detailed_answer", ""),
            novelty_score=r.get("novelty_score", 0.0),
            novelty_report=r.get("novelty_report", ""),
            novelty=r.get("novelty", {}),
            synthesis=r.get("synthesis", {}),
            citations=[Citation(**c) for c in r.get("citations", [])],
            sources_used=r.get("sources_used", []),
            pipeline_trace=r.get("pipeline_trace", []),
            total_time_s=r.get("total_time_s", 0.0),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sources")
def list_sources():
    """List all registered sources and their status."""
    return {
        "total": len(SOURCE_REGISTRY),
        "sources": list(SOURCE_REGISTRY.keys()),
        "profiles": {k: list(v["primary"]) for k, v in SOURCE_PROFILES.items()},
    }


@router.get("/health")
def health():
    return {"status": "healthy", "version": "1.0.0"}