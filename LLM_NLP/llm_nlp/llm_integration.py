"""
llm_integration.py
Owner: Member 4 - LLM & NLP Developer

This is the main orchestration module that ties everything together:

  user message
      -> multilingual.detect_language()
      -> nlp_extraction.extract_profile()
      -> rag_pipeline.RAGPipeline.retrieve()   (Member 3's module)
      -> eligibility_matcher.rank_schemes()
      -> prompts.build_user_turn()
      -> Anthropic Claude API call
      -> final natural-language answer

Member 2 (Backend) imports `handle_chat_message()` from this file and calls
it from the /api/chat endpoint. That's the entire integration contract
between the LLM/NLP layer and the backend.

Install:
    pip install anthropic

Set your API key as an environment variable before running:
    export ANTHROPIC_API_KEY="your-key-here"
"""

import os
import sys
from typing import Dict, List

import anthropic

from prompts import get_system_prompt, build_user_turn
from nlp_extraction import extract_profile
from eligibility_matcher import rank_schemes
from multilingual import detect_language, language_instruction

# Make the sibling rag_pipeline package importable when this repo is
# assembled back into the full monorepo (see PROJECT_INTEGRATION notes).
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "rag_pipeline"))

MODEL_NAME = "claude-sonnet-4-6"

client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env automatically


def handle_chat_message(
    user_message: str,
    conversation_history: List[Dict] = None,
    existing_profile: Dict = None,
    rag_pipeline=None,
) -> Dict:
    """
    Main entry point called by the backend.

    Args:
        user_message: the raw text the user just typed
        conversation_history: list of {"role": "user"/"assistant", "content": str}
        existing_profile: previously extracted profile dict, to be updated
        rag_pipeline: an instance of rag_pipeline.RAGPipeline (Member 3's module),
                       injected by the backend so this module doesn't need to
                       own the vector index lifecycle.

    Returns: {
        "reply": str,
        "language": "en" | "te",
        "profile": dict,
        "matched_schemes": [ ... ]
    }
    """
    conversation_history = conversation_history or []
    existing_profile = existing_profile or {}

    # 1. Language detection
    language = detect_language(user_message)

    # 2. NLP: extract/update structured profile fields
    profile = extract_profile(user_message, existing_profile)

    # 3. RAG: retrieve relevant schemes
    filters = {"state": profile["state"]} if profile.get("state") else None
    retrieved = rag_pipeline.retrieve(user_message, top_k=5, filters=filters)
    retrieved_schemes = [item["scheme"] for item in retrieved]

    # 4. Eligibility pre-ranking (transparent, rule-based signal for the LLM & UI)
    ranked = rank_schemes(retrieved_schemes, profile)

    # 5. Build context string + prompt
    context_string = rag_pipeline.build_context_string(retrieved)
    system_prompt = get_system_prompt(language) + "\n" + language_instruction(language)
    user_turn = build_user_turn(user_message, context_string, profile)

    # 6. Call Claude
    messages = conversation_history + [{"role": "user", "content": user_turn}]
    response = client.messages.create(
        model=MODEL_NAME,
        max_tokens=1024,
        system=system_prompt,
        messages=messages,
    )
    reply_text = "".join(
        block.text for block in response.content if getattr(block, "type", None) == "text"
    )

    return {
        "reply": reply_text,
        "language": language,
        "profile": profile,
        "matched_schemes": ranked,
    }


if __name__ == "__main__":
    # Standalone smoke test (requires ANTHROPIC_API_KEY and a built vector index)
    sys.path.append(os.path.join(os.path.dirname(__file__), "..", "rag_pipeline"))
    from rag_pipeline import RAGPipeline  # noqa: E402

    pipeline = RAGPipeline()
    result = handle_chat_message(
        "I am a 62 year old farmer in Andhra Pradesh. What support can I get?",
        rag_pipeline=pipeline,
    )
    print(result["reply"])
    print(result["matched_schemes"])
