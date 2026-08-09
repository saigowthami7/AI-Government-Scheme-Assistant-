"""
llm_integration.py
Owner: Member 4 - LLM & NLP Developer

Main orchestration module:

User message
    -> Language detection
    -> NLP profile extraction
    -> RAG retrieval
    -> Eligibility ranking
    -> Prompt construction
    -> Groq LLM
    -> Final answer
"""

import os
import sys
from typing import Dict, List

from groq import Groq

from .prompts import get_system_prompt, build_user_turn
from .nlp_extraction import extract_profile
from .eligibility_matcher import rank_schemes
from .multilingual import detect_language, language_instruction


# Make the sibling rag_pipeline package importable.
ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)

RAG_PATH = os.path.join(ROOT, "rag_pipeline")

if RAG_PATH not in sys.path:
    sys.path.append(RAG_PATH)


# Groq configuration
MODEL_NAME = os.getenv(
    "GROQ_MODEL",
    "llama-3.3-70b-versatile"
)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise RuntimeError(
        "GROQ_API_KEY environment variable is not set."
    )

client = Groq(api_key=GROQ_API_KEY)


def handle_chat_message(
    user_message: str,
    conversation_history: List[Dict] = None,
    existing_profile: Dict = None,
    rag_pipeline=None,
) -> Dict:
    """
    Main entry point called by the FastAPI backend.

    Args:
        user_message:
            Raw message from the user.

        conversation_history:
            Previous conversation messages.

        existing_profile:
            Previously extracted user profile.

        rag_pipeline:
            RAGPipeline instance supplied by the backend.

    Returns:
        Dictionary containing:
            reply
            language
            profile
            matched_schemes
    """

    conversation_history = conversation_history or []
    existing_profile = existing_profile or {}

    # ---------------------------------------------------------
    # 1. Detect language
    # ---------------------------------------------------------
    language = detect_language(user_message)

    # ---------------------------------------------------------
    # 2. Extract/update user profile using NLP
    # ---------------------------------------------------------
    profile = extract_profile(
        user_message,
        existing_profile
    )

    # ---------------------------------------------------------
    # 3. Retrieve relevant schemes using RAG
    # ---------------------------------------------------------
    if rag_pipeline is None:
        raise RuntimeError(
            "RAG pipeline was not provided to handle_chat_message()."
        )

    filters = None

    if profile.get("state"):
        filters = {
            "state": profile["state"]
        }

    retrieved = rag_pipeline.retrieve(
        user_message,
        top_k=5,
        filters=filters
    )

    retrieved_schemes = [
        item["scheme"]
        for item in retrieved
    ]

    # ---------------------------------------------------------
    # 4. Rank schemes based on eligibility
    # ---------------------------------------------------------
    ranked = rank_schemes(
        retrieved_schemes,
        profile
    )

    # ---------------------------------------------------------
    # 5. Build RAG context and prompts
    # ---------------------------------------------------------
    context_string = rag_pipeline.build_context_string(
        retrieved
    )

    system_prompt = (
        get_system_prompt(language)
        + "\n"
        + language_instruction(language)
    )

    user_turn = build_user_turn(
        user_message,
        context_string,
        profile
    )

    # ---------------------------------------------------------
    # 6. Prepare conversation messages
    # ---------------------------------------------------------
    messages = conversation_history + [
        {
            "role": "user",
            "content": user_turn
        }
    ]

    # ---------------------------------------------------------
    # 7. Call Groq LLM
    # ---------------------------------------------------------
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            *messages
        ],
        max_tokens=1024,
    )

    # ---------------------------------------------------------
    # 8. Extract final response
    # ---------------------------------------------------------
    reply_text = response.choices[0].message.content

    # ---------------------------------------------------------
    # 9. Return result to FastAPI backend
    # ---------------------------------------------------------
    return {
        "reply": reply_text,
        "language": language,
        "profile": profile,
        "matched_schemes": ranked,
    }


# -------------------------------------------------------------
# Standalone test
# -------------------------------------------------------------
if __name__ == "__main__":

    from rag_pipeline import RAGPipeline

    pipeline = RAGPipeline()

    result = handle_chat_message(
        "I am a 62 year old farmer in Andhra Pradesh. "
        "What support can I get?",
        rag_pipeline=pipeline,
    )

    print("\n==============================")
    print("LANGUAGE:")
    print(result["language"])

    print("\nPROFILE:")
    print(result["profile"])

    print("\nMATCHED SCHEMES:")
    print(result["matched_schemes"])

    print("\nREPLY:")
    print(result["reply"])

    print("==============================")