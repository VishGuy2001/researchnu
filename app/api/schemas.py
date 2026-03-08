from pydantic import BaseModel, Field
from typing import List

class QueryRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=500)
    user_type: str = Field(default="researcher")
    privacy_mode: bool = Field(default=False)

class Citation(BaseModel):
    title: str
    url: str
    source: str
    year: str

class QueryResponse(BaseModel):
    query: str
    summary: str
    detailed_answer: str
    novelty_score: float = Field(..., ge=0, le=100)
    novelty_report: str
    citations: List[Citation]
    sources_used: List[str]