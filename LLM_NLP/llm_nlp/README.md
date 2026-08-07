# Member 4 – LLM & NLP Developer

## Your responsibilities (from the project proposal)
- LLM integration
- Prompt engineering
- Natural-language understanding (entity extraction)
- Eligibility matching
- Multilingual (Telugu/English) responses

## What's in this package

| File | Purpose |
|---|---|
| `nlp_extraction.py` | Extracts age, state, occupation, education, and income from a user's free-text message (English or Telugu), and accumulates them into a profile across the conversation. |
| `multilingual.py` | Detects whether the user wrote in Telugu or English (Unicode-range based, fast and reliable) and builds the language instruction for the LLM. |
| `eligibility_matcher.py` | Transparent, rule-based pre-check that flags each candidate scheme as `likely_match` / `possible_match` / `unclear` / `likely_mismatch` for the user's profile, with human-readable reasons. This is a *signal*, not a legal determination — final eligibility always depends on the official source. |
| `prompts.py` | System prompts (English + Telugu) that constrain the LLM to only answer from retrieved scheme data, and the template that assembles the final user turn. |
| `llm_integration.py` | **Main orchestrator** — `handle_chat_message()` ties together language detection → NLP extraction → RAG retrieval (Member 3's module) → eligibility ranking → Claude API call. This is the single function Member 2 (Backend) calls. |

## Setup

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
export ANTHROPIC_API_KEY="your-key-here"
```

## Try it standalone

This module depends on Member 3's `rag_pipeline` package for retrieval. For local testing, place this folder and the `rag_pipeline` folder as siblings (as they are in the full monorepo — see the top-level integration notes), then:

```bash
cd llm_nlp
python llm_integration.py
```

## Integration contract (what the Backend developer needs to know)

```python
from llm_integration import handle_chat_message
from rag_pipeline import RAGPipeline

pipeline = RAGPipeline()  # load once at server startup, reuse across requests

result = handle_chat_message(
    user_message="I am a 62 year old farmer in Andhra Pradesh",
    conversation_history=[],   # list of {"role": "user"/"assistant", "content": str}
    existing_profile={},       # carry this forward per chat session
    rag_pipeline=pipeline,
)
# result = {"reply": str, "language": "en"|"te", "profile": dict, "matched_schemes": list}
```

## Notes for review / demo

- The NLP extraction is regex/keyword-based for speed and zero extra API cost. If time allows, this could be upgraded to a small classification model or a dedicated LLM extraction call for messier phrasing — flagged as a possible v2 improvement.
- `eligibility_matcher.py` deliberately only checks a few fields (age, state, target group) — it's meant to catch obvious mismatches and give the LLM/UI a confidence signal, not to be a complete legal eligibility engine.
- Romanized Telugu (Telugu typed in English letters) is not yet detected by `multilingual.py` — currently only native Telugu script is detected. This is a good stretch goal.
- The system prompt explicitly forbids the LLM from inventing scheme details or asking for sensitive IDs (Aadhaar/PAN/bank number) in chat — keep this in place for user trust and privacy.
