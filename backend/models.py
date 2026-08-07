"""
models.py
Owner: Member 2 - Backend Developer

Pydantic request/response schemas for the FastAPI endpoints. Keeping these
in one place makes the API contract with Member 1 (Frontend) explicit and
easy to document.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: Optional[str] = Field(
        None, description="Existing session id. Omit on the first message to start a new session."
    )
    message: str = Field(..., description="The user's chat message, in English or Telugu.")


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    language: str
    profile: Dict[str, Any]
    matched_schemes: List[Dict[str, Any]]


class SchemeSearchRequest(BaseModel):
    query: str
    state: Optional[str] = None
    level: Optional[str] = None  # "Central" | "State"
    top_k: int = 5


class SchemeSearchResult(BaseModel):
    scheme: Dict[str, Any]
    relevance_score: float


class SchemeSearchResponse(BaseModel):
    results: List[SchemeSearchResult]


class EligibilityCheckRequest(BaseModel):
    scheme_id: str
    profile: Dict[str, Any]


class EligibilityCheckResponse(BaseModel):
    scheme_id: str
    scheme_name: str
    match_signal: str
    reasons: List[str]
