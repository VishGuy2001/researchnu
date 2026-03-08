from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.api.schemas import QueryRequest, QueryResponse, Citation
from app.agents.pipeline import run_query
from app.db.database import init_db, log_query, upsert_session
from dotenv import load_dotenv
import time, uuid

load_dotenv()

# init db on startup
init_db()

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
    allow_headers=["*"]
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
    session_id = str(uuid.uuid4())
    ip = request.client.host
    start = time.time()
    try:
        r = run_query(
            query=req.query,
            user_type=req.user_type,
            privacy_mode=req.privacy_mode
        )
        latency_ms = int((time.time() - start) * 1000)

        # log every query to sqlite/postgres
        log_query(
            query_text=req.query,
            user_type=req.user_type,
            novelty_score=r["novelty_score"],
            sources_used=r.get("sources_used", []),
            latency_ms=latency_ms,
            session_id=session_id
        )
        upsert_session(session_id, ip)

        return QueryResponse(
            query=r["query"],
            summary=r["summary"],
            detailed_answer=r["answer"],
            novelty_score=r["novelty_score"],
            novelty_report=r["novelty_report"],
            citations=[Citation(**c) for c in r.get("citations", [])],
            sources_used=r.get("sources_used", [])
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))