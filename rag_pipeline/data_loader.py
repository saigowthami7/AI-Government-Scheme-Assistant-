"""
data_loader.py
Owner: Member 3 - RAG & Data Engineer

Loads and cleans the verified government scheme dataset from data/schemes.json,
and prepares text "chunks" that will be embedded and stored in the vector database.

Each scheme is flattened into a single descriptive text block so that semantic
search can match a user's natural-language query (in English or Telugu) against
the right scheme.
"""

import json
import os
from typing import List, Dict

DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "schemes.json")


def load_raw_schemes(path: str = DATA_PATH) -> List[Dict]:
    """Load the raw scheme records from the JSON knowledge base."""
    with open(path, "r", encoding="utf-8") as f:
        schemes = json.load(f)
    return schemes


def validate_scheme(scheme: Dict) -> bool:
    """Basic sanity check that a scheme record has the required fields
    before it is added to the knowledge base. Keeps bad/incomplete data
    out of the vector store."""
    required_fields = [
        "id", "name_en", "category", "level", "state",
        "eligibility", "benefits", "documents_required",
        "application_process", "official_source"
    ]
    return all(field in scheme and scheme[field] for field in required_fields)


def scheme_to_text_chunk(scheme: Dict) -> str:
    """
    Flatten a scheme record into a single text chunk optimized for embedding.
    This is the text that will actually be vectorized and searched over.
    """
    eligibility_text = "; ".join(scheme.get("eligibility", []))
    documents_text = ", ".join(scheme.get("documents_required", []))
    target_group_text = ", ".join(scheme.get("target_group", []))

    chunk = (
        f"Scheme Name: {scheme['name_en']}\n"
        f"Category: {scheme['category']}\n"
        f"Level: {scheme['level']} | State: {scheme['state']}\n"
        f"Target Group: {target_group_text}\n"
        f"Eligibility: {eligibility_text}\n"
        f"Benefits: {scheme['benefits']}\n"
        f"Documents Required: {documents_text}\n"
        f"Application Process: {scheme['application_process']}\n"
        f"Official Source: {scheme['official_source']}"
    )
    return chunk


def load_and_prepare_schemes(path: str = DATA_PATH) -> List[Dict]:
    """
    Main entry point used by embeddings.py / rag_pipeline.py.
    Returns a list of dicts: {id, metadata (full scheme record), text_chunk}
    """
    raw_schemes = load_raw_schemes(path)
    prepared = []
    skipped = 0

    for scheme in raw_schemes:
        if not validate_scheme(scheme):
            skipped += 1
            continue
        prepared.append({
            "id": scheme["id"],
            "metadata": scheme,
            "text_chunk": scheme_to_text_chunk(scheme),
        })

    if skipped:
        print(f"[data_loader] Skipped {skipped} invalid scheme record(s).")

    print(f"[data_loader] Loaded {len(prepared)} valid scheme records.")
    return prepared


if __name__ == "__main__":
    records = load_and_prepare_schemes()
    print("\nSample chunk:\n")
    print(records[0]["text_chunk"])
