from fastapi import APIRouter, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.api.schemas import QueryRequest, QueryResponse, Citation
from app.agents.pipeline import run_query

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

@router.post("/query", response_model=QueryResponse)
def query_endpoint(request: Request, req: QueryRequest):
    try:
        r = run_query(
            query=req.query,
            user_type=req.user_type,
            privacy_mode=req.privacy_mode
        )
        return QueryResponse(
            query=r["query"],
            summary=r.get("summary", ""),
            detailed_answer=r.get("answer", ""),
            novelty_score=r.get("novelty_score", 0.0),
            novelty_report=r.get("novelty_report", ""),
            citations=[Citation(**c) for c in r.get("citations", [])],
            sources_used=r.get("sources_used", [])
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))