"""
ResearchNu — FastAPI Application Entry Point
"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.api.schemas import QueryRequest, QueryResponse, Citation
from app.agents.pipeline import run_query
from dotenv import load_dotenv

load_dotenv()

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="ResearchNu",
    description="Free agentic AI for researchers, founders and R&D teams.",
    version="1.0.0"
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"app": "ResearchNu", "version": "1.0.0", "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "healthy", "version": "1.0.0"}


@app.post("/query", response_model=QueryResponse)
@limiter.limit("10/minute")
def query_endpoint(request: Request, req: QueryRequest):
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
            detailed_answer=r.get("detailed_answer", ""),  # fixed: was r["answer"]
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


# include router for modular routes
from app.api.routes import router
app.include_router(router, prefix="/api")