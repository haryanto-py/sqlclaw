"""
Chunk KNOWLEDGE.md into sections, embed via Cohere, and store in ChromaDB.

Each top-level section (## section: ...) becomes one or more chunks.
Long sections are split into ~400-word chunks with 50-word overlap.
ChromaDB stores the vectors in a local folder (./chroma_db/).

Usage (via main.py):
    python main.py --step embed
    python main.py --step embed --reload   # re-embed from scratch
"""

from __future__ import annotations

import os
import re
import textwrap
from pathlib import Path

import chromadb
import cohere

KNOWLEDGE_FILE = Path(__file__).parent.parent / "KNOWLEDGE.md"
CHROMA_DIR = Path(__file__).parent.parent / "chroma_db"
COLLECTION_NAME = "knowledge"
COHERE_MODEL = "embed-english-v3.0"  # 1024-dim, free tier
CHUNK_WORDS = 400
OVERLAP_WORDS = 50


# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------


def _parse_sections(md_text: str) -> list[tuple[str, str]]:
    """Split KNOWLEDGE.md into (section_name, content) pairs by ## section: headers."""
    pattern = re.compile(r"^## section:\s*(.+)$", re.MULTILINE)
    matches = list(pattern.finditer(md_text))
    sections = []
    for i, match in enumerate(matches):
        section_name = match.group(1).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(md_text)
        content = md_text[start:end].strip()
        if content:
            sections.append((section_name, content))
    return sections


def _chunk_text(text: str, chunk_words: int, overlap_words: int) -> list[str]:
    """Split text into overlapping word-count chunks."""
    words = text.split()
    if len(words) <= chunk_words:
        return [text]
    chunks = []
    step = chunk_words - overlap_words
    for i in range(0, len(words), step):
        chunk = " ".join(words[i : i + chunk_words])
        chunks.append(chunk)
        if i + chunk_words >= len(words):
            break
    return chunks


def build_chunks(knowledge_file: Path = KNOWLEDGE_FILE) -> list[dict]:
    """Parse KNOWLEDGE.md and return list of chunk dicts."""
    md_text = knowledge_file.read_text(encoding="utf-8")
    sections = _parse_sections(md_text)
    chunks = []
    for section_name, content in sections:
        for idx, chunk in enumerate(_chunk_text(content, CHUNK_WORDS, OVERLAP_WORDS)):
            chunks.append(
                {
                    "id": f"{section_name}::{idx}",
                    "section": section_name,
                    "chunk_index": idx,
                    "content": chunk,
                }
            )
    return chunks


# ---------------------------------------------------------------------------
# Embedding via Cohere
# ---------------------------------------------------------------------------


def embed_chunks(chunks: list[dict]) -> list[dict]:
    """Call Cohere embed API and attach embeddings to each chunk."""
    api_key = os.environ.get("COHERE_API_KEY")
    if not api_key:
        raise RuntimeError("COHERE_API_KEY is not set in .env")

    co = cohere.Client(api_key)
    texts = [c["content"] for c in chunks]

    print(f"  Embedding {len(texts)} chunks via Cohere ({COHERE_MODEL}) ...")
    response = co.embed(
        texts=texts,
        model=COHERE_MODEL,
        input_type="search_document",
    )

    for chunk, embedding in zip(chunks, response.embeddings):
        chunk["embedding"] = embedding

    return chunks


# ---------------------------------------------------------------------------
# Storage in ChromaDB
# ---------------------------------------------------------------------------


def store_chunks(chunks: list[dict], reload: bool = False) -> None:
    """Upsert embedded chunks into ChromaDB collection."""
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    if reload:
        print(f"  Deleting existing collection '{COLLECTION_NAME}' ...")
        try:
            client.delete_collection(COLLECTION_NAME)
        except Exception:
            pass

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    print(f"  Storing {len(chunks)} chunks in ChromaDB ...")
    collection.upsert(
        ids=[c["id"] for c in chunks],
        embeddings=[c["embedding"] for c in chunks],
        documents=[c["content"] for c in chunks],
        metadatas=[{"section": c["section"], "chunk_index": c["chunk_index"]} for c in chunks],
    )

    print(f"  Done. Collection '{COLLECTION_NAME}' now has {collection.count()} chunks.")


# ---------------------------------------------------------------------------
# Verify
# ---------------------------------------------------------------------------


def verify_embeddings() -> None:
    """Print a summary of stored embeddings."""
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    try:
        collection = client.get_collection(COLLECTION_NAME)
    except Exception:
        print("  No ChromaDB collection found.")
        return

    results = collection.get(include=["metadatas"])
    sections: dict[str, int] = {}
    for meta in results["metadatas"]:
        sections[meta["section"]] = sections.get(meta["section"], 0) + 1

    print("\n  Knowledge base summary:")
    for section, count in sorted(sections.items()):
        label = textwrap.shorten(section, width=40, placeholder="...")
        print(f"    {label:<42} {count} chunk(s)")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def embed_knowledge(reload: bool = False) -> None:
    """Full pipeline: parse → embed → store → verify."""
    print("  Parsing KNOWLEDGE.md ...")
    chunks = build_chunks()
    print(f"  Found {len(chunks)} chunks across {len({c['section'] for c in chunks})} sections.")

    chunks = embed_chunks(chunks)
    store_chunks(chunks, reload=reload)
    verify_embeddings()
