"""
app.py
Owner: Member 2 - Backend Developer

Main FastAPI application. Exposes the API that the frontend (Member 1)
talks to, and internally calls into:
  - Member 3's RAG pipeline (rag_pipeline.RAGPipeline) for scheme search
  - Member 4's LLM/NLP orchestrator (llm_integration.handle_chat_message) for chat

Run:
    uvicorn app:app --reload --port 8000

Expects the sibling packages `rag_pipeline/` and `llm_nlp/` to be present
(as they are in the assembled monorepo) so the imports below resolve.
"""

import os
import sys

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from database import (
    init_db,
    create_session,
    get_session_profile,
    update_session_profile,
    add_message,
    get_conversation_history,
)
from models import (
    ChatRequest,
    ChatResponse,
    SchemeSearchRequest,
    SchemeSearchResponse,
    SchemeSearchResult,
    EligibilityCheckRequest,
    EligibilityCheckResponse,
)

# Make sibling team packages importable
ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.append(os.path.join(ROOT, "rag_pipeline"))
sys.path.append(os.path.join(ROOT, "llm_nlp"))

app = FastAPI(
    title="AI Government Scheme Assistant API",
    description="Backend API for the LLM + RAG based government scheme discovery assistant.",
    version="1.0.0",
)

# Allow the frontend (served separately, e.g. from a different port/static host) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten to the actual frontend origin before production deployment
    allow_methods=["*"],
    allow_headers=["*"],
)

# Lazy globals populated on startup — avoids loading the ML model / vector
# index / Claude client at import time (slow, and breaks simple unit tests).
_rag_pipeline = None


@app.on_event("startup")
def startup():
    init_db()
    global _rag_pipeline
    from rag_pipeline import RAGPipeline  # Member 3's module
    _rag_pipeline = RAGPipeline()
    print("[app] RAG pipeline loaded and ready.")


@app.get("/api/health")
def health_check():
    return {"status": "ok"}


@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """
    Main conversational endpoint. Creates a session on first call, then
    reuses it for follow-up questions so profile details and history
    accumulate across the conversation.
    """
    from llm_integration import handle_chat_message  # Member 4's module

    session_id = request.session_id or create_session()
    existing_profile = get_session_profile(session_id)
    history = get_conversation_history(session_id)

    try:
        result = handle_chat_message(
            user_message=request.message,
            conversation_history=history,
            existing_profile=existing_profile,
            rag_pipeline=_rag_pipeline,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate response: {e}")

    update_session_profile(session_id, result["profile"], language=result["language"])
    add_message(session_id, "user", request.message)
    add_message(session_id, "assistant", result["reply"], matched_schemes=result["matched_schemes"])

    return ChatResponse(
        session_id=session_id,
        reply=result["reply"],
        language=result["language"],
        profile=result["profile"],
        matched_schemes=result["matched_schemes"],
    )


@app.post("/api/schemes/search", response_model=SchemeSearchResponse)
def search_schemes(request: SchemeSearchRequest):
    """Direct scheme search endpoint (used by the frontend's search bar,
    separate from the conversational chat flow)."""
    filters = {}
    if request.state:
        filters["state"] = request.state
    if request.level:
        filters["level"] = request.level

    results = _rag_pipeline.retrieve(request.query, top_k=request.top_k, filters=filters or None)
    return SchemeSearchResponse(
        results=[SchemeSearchResult(scheme=r["scheme"], relevance_score=r["relevance_score"]) for r in results]
    )


@app.post("/api/eligibility/check", response_model=EligibilityCheckResponse)
def check_eligibility(request: EligibilityCheckRequest):
    """Check a single scheme against a given profile (used when a user
    clicks 'Am I eligible?' on a specific scheme card in the UI)."""
    from eligibility_matcher import score_scheme_for_profile  # Member 4's module

    scheme_record = next(
        (r["metadata"] for r in _rag_pipeline.store.records if r["id"] == request.scheme_id), None
    )
    if scheme_record is None:
        raise HTTPException(status_code=404, detail="Scheme not found")

    result = score_scheme_for_profile(scheme_record, request.profile)
    return EligibilityCheckResponse(**result)
