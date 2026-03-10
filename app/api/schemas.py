"""
ResearchNu — Pydantic API Schemas
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    query: str = Field(..., description="Research question or idea")
    user_type: str = Field("all", description="researcher|founder|grant|policy|all")
    privacy_mode: bool = Field(False, description="Use local Ollama, query never leaves server")
    focus_areas: Optional[List[str]] = Field(None, description="Specific aspects to focus on")


class Citation(BaseModel):
    title: str = ""
    url: str = ""
    source: str = ""
    year: str = ""


class QueryResponse(BaseModel):
    query: str
    summary: str = ""
    detailed_answer: str = ""
    novelty_score: float = 0.0
    novelty_report: str = ""
    novelty: Dict[str, Any] = {}
    synthesis: Dict[str, Any] = {}
    citations: List[Citation] = []
    sources_used: List[str] = []
    pipeline_trace: List[Dict[str, Any]] = []
    total_time_s: float = 0.0