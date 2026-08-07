from typing import List, Dict, Optional

from embeddings import embed_query
from vector_store import SchemeVectorStore, build_and_save_index, INDEX_PATH, METADATA_PATH
import os


class RAGPipeline:
    def __init__(self, auto_build: bool = True):
        if os.path.exists(INDEX_PATH) and os.path.exists(METADATA_PATH):
            self.store = SchemeVectorStore.load()
        elif auto_build:
            print("[rag_pipeline] No existing index found, building a new one...")
            self.store = build_and_save_index()
        else:
            raise FileNotFoundError(
                "Vector index not found. Run vector_store.build_and_save_index() first."
            )

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        min_score: float = 0.15,
        filters: Optional[Dict] = None,
    ) -> List[Dict]:
        """
        Retrieve relevant schemes for a query.

        filters (optional): e.g. {"state": "Andhra Pradesh"} or {"level": "Central"}
        used to narrow results after semantic search (simple metadata filtering).
        """
        query_vector = embed_query(query)
        raw_results = self.store.search(query_vector, top_k=top_k * 2)  # over-fetch, then filter

        filtered = []
        for scheme, score in raw_results:
            if score < min_score:
                continue
            if filters:
                match = True
                for key, value in filters.items():
                    scheme_value = scheme["metadata"].get(key)
                    if isinstance(scheme_value, str) and scheme_value.lower() != str(value).lower():
                        if scheme_value != "All India":  # central schemes apply everywhere
                            match = False
                            break
                if not match:
                    continue
            filtered.append({
                "scheme": scheme["metadata"],
                "relevance_score": round(score, 4),
            })
            if len(filtered) >= top_k:
                break

        return filtered

    def build_context_string(self, retrieved: List[Dict]) -> str:
        """Format retrieved schemes into a context block for the LLM prompt."""
        if not retrieved:
            return "No matching schemes were found in the knowledge base for this query."

        blocks = []
        for item in retrieved:
            s = item["scheme"]
            blocks.append(
                f"### {s['name_en']} ({s['level']} scheme, {s['state']})\n"
                f"Eligibility: {'; '.join(s['eligibility'])}\n"
                f"Benefits: {s['benefits']}\n"
                f"Documents Required: {', '.join(s['documents_required'])}\n"
                f"How to Apply: {s['application_process']}\n"
                f"Official Source: {s['official_source']}\n"
                f"(Relevance score: {item['relevance_score']})"
            )
        return "\n\n".join(blocks)


if __name__ == "__main__":
    pipeline = RAGPipeline()
    test_query = "I am a 62 year old farmer in Andhra Pradesh, what pension or income support can I get?"
    results = pipeline.retrieve(test_query, top_k=3)
    print(pipeline.build_context_string(results))
