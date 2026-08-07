# Member 3 – RAG & Data Engineer

## responsibilities (from the project proposal)
- Collect and clean verified government scheme data
- Document processing
- Generate embeddings
- Build and maintain the vector database
- Build the RAG retrieval pipeline

## What's in this package

| File | Purpose |
|---|---|
| `data/schemes.json` | Seed knowledge base: 15 verified sample schemes (Central + Andhra Pradesh) covering farmers, students, women & children, senior citizens, persons with disabilities, housing, health, and small business categories. **You should expand this** with more schemes and keep it updated from official sources. |
| `data_loader.py` | Loads `schemes.json`, validates records, and flattens each scheme into a text "chunk" ready for embedding. |
| `embeddings.py` | Wraps `sentence-transformers` (multilingual model) to turn text into vectors. Supports English **and Telugu** queries out of the box. |
| `vector_store.py` | FAISS-based vector index: build, search, save, and load. |
| `rag_pipeline.py` | The main class (`RAGPipeline`) that Member 4 and Member 2 will import — takes a user query, returns the most relevant schemes plus a ready-to-use context string for the LLM prompt. |

## Setup

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Build the vector index

```bash
cd rag_pipeline
python vector_store.py
```

This reads `data/schemes.json`, embeds every scheme, and saves the FAISS index to `index/schemes.index` (plus metadata) so it doesn't need to be rebuilt every time the server restarts. Re-run this any time you add/edit schemes in `schemes.json`.

## Try it standalone

```bash
python rag_pipeline.py
```

## How this connects to the rest of the team

- **Member 4 (LLM & NLP)** imports `RAGPipeline` from `rag_pipeline.py`, calls `.retrieve(query, filters=...)` using the profile details their NLP layer extracts (state, occupation, etc.), and feeds `.build_context_string(results)` into the LLM prompt.
- **Member 2 (Backend)** calls the combined LLM+RAG function (exposed by Member 4) from the `/api/chat` endpoint.
- **Member 1 (Frontend)** never talks to this module directly — only through the backend API.

## Growing the knowledge base

To add a new scheme, append a new object to `data/schemes.json` following the existing structure exactly (all fields are required — see `validate_scheme()` in `data_loader.py`). Always cite the **official government source URL** — this is shown to users for verification, per the project's "Official Source Verification" feature.

## Notes for review / demo

- The dataset is a **starting sample only**. Before going further, the team should decide on an official, larger source (e.g. myscheme.gov.in, AP state department portals) and a process for periodically re-scraping/re-verifying scheme details, since eligibility criteria and benefit amounts change over time.
- `min_score` and `top_k` in `RAGPipeline.retrieve()` are tunable — raise `min_score` if you start seeing irrelevant schemes returned for narrow queries.
