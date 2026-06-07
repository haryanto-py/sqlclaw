---
name: rfm_segmentation
description: "Run an RFM (Recency, Frequency, Monetary) customer segmentation across the whole customer base and return segment counts, average spend per segment, and a chart. Use when the user asks about customer segments, RFM, churn risk, champions/loyal/at-risk customers."
metadata:
  {
    "openclaw": { "emoji": "🧩", "requires": { "bins": ["python"] } }
  }
---

# RFM Segmentation

Score every customer on Recency, Frequency, and Monetary value, assign a segment, and chart the distribution. Reads the database itself — no prior query needed.

## How to Run

```bash
..\.venv\Scripts\python.exe "skills/rfm_segmentation/scripts/rfm.py"
```

Output JSON:
`{"success":true,"chart_path":"...","segments_count":{...},"segments_avg_monetary":{...}}`.

Segments: Champions, Promising / Recent, At Risk (Loyal but inactive), High Value Churned, Standard / Low Value.

## After running

1. **Send the chart**: use the `message` tool to send the PNG at `chart_path` to the user.
2. Summarize `segments_count` (how many customers per segment) and `segments_avg_monetary` (average spend per segment) in a short, readable list. Note most Olist customers are one-time buyers, so "Standard / Low Value" dominates.
