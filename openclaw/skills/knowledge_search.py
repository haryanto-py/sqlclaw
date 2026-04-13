"""
knowledge_search.py — CLI wrapper for ChromaDB semantic search.

Called by knowledge_search.js via execFile. Embeds the query using Cohere,
queries the local ChromaDB collection, and prints JSON results to stdout.

Usage:
    python knowledge_search.py --query "What is AOV?" --top_k 3
"""

import argparse
import json
import os
from pathlib import Path

CHROMA_DIR = Path(__file__).parent.parent.parent / "chroma_db"
COLLECTION_NAME = "knowledge"
COHERE_MODEL = "embed-english-v3.0"


def embed_query(query: str, api_key: str) -> list[float]:
    import cohere

    co = cohere.Client(api_key)
    response = co.embed(
        texts=[query],
        model=COHERE_MODEL,
        input_type="search_query",
    )
    return response.embeddings[0]


def search(query: str, top_k: int) -> dict:
    import chromadb

    api_key = os.environ.get("COHERE_API_KEY")
    if not api_key:
        return {"error": "COHERE_API_KEY is not set"}

    embedding = embed_query(query, api_key)

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    try:
        collection = client.get_collection(COLLECTION_NAME)
    except Exception:
        return {
            "error": f"ChromaDB collection '{COLLECTION_NAME}' not found. Run: python main.py --step embed"
        }

    results = collection.query(
        query_embeddings=[embedding],
        n_results=min(top_k, collection.count()),
        include=["documents", "metadatas", "distances"],
    )

    chunks = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        chunks.append(
            {
                "section": meta["section"],
                "similarity": round(1 - dist, 3),
                "content": doc,
            }
        )

    return {"found": True, "query": query, "results": chunks}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", required=True, help="Search query")
    parser.add_argument("--top_k", type=int, default=3, help="Number of results")
    args = parser.parse_args()

    result = search(args.query, args.top_k)
    print(json.dumps(result))


if __name__ == "__main__":
    main()
