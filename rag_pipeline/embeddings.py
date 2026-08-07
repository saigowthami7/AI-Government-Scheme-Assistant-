from typing import List
import numpy as np

MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"

_model = None  # lazy-loaded singleton


def get_model():
    """Lazy-load the sentence-transformers model so importing this module
    doesn't require the model weights to be downloaded until actually needed."""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def embed_texts(texts: List[str]) -> np.ndarray:
    """Embed a list of text strings into a numpy array of shape (N, dim)."""
    model = get_model()
    embeddings = model.encode(
        texts,
        show_progress_bar=False,
        normalize_embeddings=True,  # cosine similarity via dot product
    )
    return np.array(embeddings, dtype="float32")


def embed_query(query: str) -> np.ndarray:
    """Embed a single user query (English or Telugu)."""
    return embed_texts([query])[0]


if __name__ == "__main__":
    # Quick smoke test
    from data_loader import load_and_prepare_schemes

    records = load_and_prepare_schemes()
    sample_texts = [r["text_chunk"] for r in records[:3]]
    vectors = embed_texts(sample_texts)
    print(f"Embedded {len(sample_texts)} chunks -> shape {vectors.shape}")

    te_query = "60 ఏళ్లు పైబడిన వారికి పింఛను పథకాలు ఏమిటి"  # "pension schemes for people above 60"
    q_vec = embed_query(te_query)
    print(f"Telugu query embedded -> shape {q_vec.shape}")
