# AI Government Scheme Assistant — Integration Guide

This project is split into four packages, one per team member, matching the roles in the proposal. Each has its own ZIP and README with setup steps. This document explains how the four pieces fit together into one working system, for whoever does the final integration/demo.

## Folder layout (put all four folders as siblings to run the full system)

```
project-root/
├── frontend/       Member 1 — Frontend Developer
├── backend/        Member 2 — Backend Developer
├── rag_pipeline/   Member 3 — RAG & Data Engineer
└── llm_nlp/        Member 4 — LLM & NLP Developer
```

## Data flow

```
User types a message (English or Telugu)
        │
        ▼
frontend/script.js  ──POST /api/chat──▶  backend/app.py
                                             │
                                             ▼
                          llm_nlp/llm_integration.py : handle_chat_message()
                                             │
                     ┌───────────────────────┼────────────────────────┐
                     ▼                       ▼                        ▼
        llm_nlp/multilingual.py   llm_nlp/nlp_extraction.py   rag_pipeline/rag_pipeline.py
        (detect EN/TE)            (extract age/state/etc.)   (semantic search over schemes.json
                                                                via embeddings.py + vector_store.py)
                     │                       │                        │
                     └───────────────────────┴────────────────────────┘
                                             │
                                             ▼
                          llm_nlp/eligibility_matcher.py (rank retrieved schemes)
                                             │
                                             ▼
                      llm_nlp/prompts.py builds the final prompt → Claude API call
                                             │
                                             ▼
                      backend/database.py stores the turn, returns JSON
                                             │
                                             ▼
                          frontend/script.js renders the reply + profile
```

## First-time setup (all four folders present)

```bash
python -m venv venv
source venv/bin/activate

pip install -r backend/requirements.txt
pip install -r rag_pipeline/requirements.txt
pip install -r llm_nlp/requirements.txt

export ANTHROPIC_API_KEY="your-key-here"

# Build the vector index once (Member 3's data → embeddings → FAISS)
cd rag_pipeline && python vector_store.py && cd ..

# Start the backend (loads the RAG pipeline + serves the API)
cd backend && uvicorn app:app --reload --port 8000
```

In a second terminal:

```bash
cd frontend && python -m http.server 3000
# open http://localhost:3000
```

## Suggested order of work for the team

1. **Member 3** finalizes `schemes.json` and gets `rag_pipeline.py` returning sensible results for a few test queries (works standalone, no API key needed).
2. **Member 4** wires up `llm_integration.py` against Member 3's `RAGPipeline` — this needs an `ANTHROPIC_API_KEY` to test end-to-end, but `nlp_extraction.py`, `eligibility_matcher.py`, and `multilingual.py` can all be tested independently first.
3. **Member 2** builds `app.py` against Member 4's `handle_chat_message()` function — the API contract in `backend/README.md` is stable, so this can start in parallel using a stub/mock reply.
4. **Member 1** builds the UI against the API contract in `backend/README.md` — can also start in parallel with a mocked backend response, then switch to the real server once it's up.

## What's included vs. what's next

**Included in this scaffold:** a working end-to-end slice — sample verified scheme data, semantic retrieval, multilingual detection, profile extraction, rule-based eligibility signals, LLM-generated answers grounded in retrieved context, a chat + search API, and a chat UI.

**Natural next steps for the team to divide up further:**
- Expand `schemes.json` well beyond the 15 seed entries (Member 3)
- Add automated tests for each module (all members, for their own package)
- Deploy the backend + frontend somewhere reachable (e.g. Render/Railway + Vercel/Netlify)
- Add authentication/session persistence if needed (Member 1 + Member 2)
- Add a small evaluation set of sample queries with expected schemes to track retrieval quality over time (Member 3 + Member 4)
