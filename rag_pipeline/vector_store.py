"""
vector_store.py
Owner: Member 3 - RAG & Data Engineer

Builds and queries a FAISS vector index over the embedded scheme chunks.
Also persists the index + metadata to disk so the backend doesn't have to
re-embed the whole knowledge base on every server restart.

Install:
    pip install faiss-cpu
"""

import json
import os
import pickle
from typing import List, Dict, Tuple

import numpy as np

INDEX_DIR = os.path.join(os.path.dirname(__file__), "index")
INDEX_PATH = os.path.join(INDEX_DIR, "schemes.index")
METADATA_PATH = os.path.join(INDEX_DIR, "schemes_metadata.pkl")


class SchemeVectorStore:
    def __init__(self, dim: int = 384):
        """dim=384 matches paraphrase-multilingual-MiniLM-L12-v2 output size."""
        import faiss
        self.dim = dim
        self.index = faiss.IndexFlatIP(dim)  # inner product == cosine (normalized vectors)
        self.records: List[Dict] = []  # parallel list: records[i] <-> vector i

    def build(self, records: List[Dict], vectors: np.ndarray):
        """
        records: list of {id, metadata, text_chunk}
        vectors: np.ndarray shape (N, dim), same order as records
        """
        assert len(records) == vectors.shape[0], "records/vectors length mismatch"
        self.index.add(vectors)
        self.records = records

    def search(self, query_vector: np.ndarray, top_k: int = 5) -> List[Tuple[Dict, float]]:
        """Return top_k (scheme_record, similarity_score) tuples for a query vector."""
        query_vector = np.expand_dims(query_vector, axis=0)
        scores, indices = self.index.search(query_vector, top_k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue
            results.append((self.records[idx], float(score)))
        return results

    def save(self, index_path: str = INDEX_PATH, metadata_path: str = METADATA_PATH):
        import faiss
        os.makedirs(INDEX_DIR, exist_ok=True)
        faiss.write_index(self.index, index_path)
        with open(metadata_path, "wb") as f:
            pickle.dump(self.records, f)
        print(f"[vector_store] Saved index ({self.index.ntotal} vectors) to {index_path}")

    @classmethod
    def load(cls, index_path: str = INDEX_PATH, metadata_path: str = METADATA_PATH, dim: int = 384):
        import faiss
        store = cls(dim=dim)
        store.index = faiss.read_index(index_path)
        with open(metadata_path, "rb") as f:
            store.records = pickle.load(f)
        print(f"[vector_store] Loaded index ({store.index.ntotal} vectors) from {index_path}")
        return store


def build_and_save_index():
    """One-off / periodic job: rebuild the vector index from data/schemes.json."""
    from data_loader import load_and_prepare_schemes
    from embeddings import embed_texts

    records = load_and_prepare_schemes()
    texts = [r["text_chunk"] for r in records]
    vectors = embed_texts(texts)

    store = SchemeVectorStore(dim=vectors.shape[1])
    store.build(records, vectors)
    store.save()
    return store


if __name__ == "__main__":
    build_and_save_index()
