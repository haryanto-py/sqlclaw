---
name: knowledge_search
description: "Look up business context, metric definitions (GMV, AOV, NPS, on-time delivery rate), Brazilian e-commerce facts, and data caveats from the curated Olist knowledge base. Use for 'what does X mean' / 'why' questions, NOT for fetching live numbers (use postgresql for that)."
metadata:
  {
    "openclaw": { "emoji": "📚", "requires": { "bins": ["python"] } }
  }
---

# Knowledge Search

Semantic search over a curated knowledge base about the Olist dataset (metric definitions, business context, data limitations, geographic and analytical notes).

## When to Use

✅ "What is AOV / GMV / on-time delivery rate?", "Why are deliveries slow in the North?", "What are the data limitations?", "What does review score 1 mean?"

❌ Live numbers / counts / rankings → use the **postgresql** skill instead. For questions that need both (e.g. "what is AOV and what is ours?"), search here for the definition, then query the database.

## How to Run

```bash
..\.venv\Scripts\python.exe "skills/knowledge_search/scripts/search.py" --query "average order value definition" --top_k 3
```

Output is JSON: `{"found":true,"results":[{"section","similarity","content"}, ...]}` or `{"error":"..."}`. Use the returned `content` chunks to frame your answer; cite the section if helpful.
