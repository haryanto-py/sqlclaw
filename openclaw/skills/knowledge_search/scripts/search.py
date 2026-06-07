"""
search.py — semantic search over the curated knowledge base (ChromaDB).

Embeds the query locally (sentence-transformers) and queries the persistent
ChromaDB collection built by `python main.py --step embed`.

Usage:
    python search.py --query "What is AOV?" --top_k 3

Prints JSON to stdout.
"""

import argparse
import json
from pathlib import Path

# skills/knowledge_search/scripts/search.py -> parents[4] = project root
CHROMA_DIR = Path(__file__).resolve().parents[4] / "chroma_db"
COLLECTION_NAME = "knowledge"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"


def embed_query(query: str) -> list:
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(EMBEDDING_MODEL)
    return model.encode([query], convert_to_numpy=True).tolist()[0]


def search(query: str, top_k: int) -> dict:
    import chromadb

    if not CHROMA_DIR.exists():
        return {"error": f"ChromaDB not found at {CHROMA_DIR}. Run: python main.py --step embed"}

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    try:
        collection = client.get_collection(COLLECTION_NAME)
    except Exception:
        return {"error": f"ChromaDB collection '{COLLECTION_NAME}' not found. Run: python main.py --step embed"}

    embedding = embed_query(query)
    results = collection.query(
        query_embeddings=[embedding],
        n_results=min(top_k, collection.count()),
        include=["documents", "metadatas", "distances"],
    )

    chunks = []
    for doc, meta, dist in zip(
        results["documents"][0], results["metadatas"][0], results["distances"][0]
    ):
        chunks.append(
            {"section": meta.get("section"), "similarity": round(1 - dist, 3), "content": doc}
        )

    return {"found": True, "query": query, "results": chunks}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", required=True, help="Search query")
    parser.add_argument("--top_k", type=int, default=3, help="Number of results")
    args = parser.parse_args()
    print(json.dumps(search(args.query, args.top_k)))


if __name__ == "__main__":
    main()
