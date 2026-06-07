---
name: send_chart
description: "Render a chart (bar, line, pie, heatmap) as a PNG image from data you already queried, then send it to the user on Telegram. Use when the user asks for a chart, graph, plot, or visualization."
metadata:
  {
    "openclaw": { "emoji": "📈", "requires": { "bins": ["python"] } }
  }
---

# Send Chart

Turn query results into a chart image and deliver it to the user.

## Workflow

1. First get the data with the **postgresql** skill.
2. Render the chart — call `exec` with (change only the values):

```bash
..\.venv\Scripts\python.exe "skills/send_chart/scripts/chart.py" --type bar --title "Revenue by Category (2017)" --xlabel "Category" --ylabel "Revenue (BRL)" --data "[{\"label\":\"health_beauty\",\"value\":1441248.07},{\"label\":\"watches_gifts\",\"value\":1305541.61}]"
```

The script prints the absolute PNG path on stdout.

3. **Send the image to the user**: use the `message` tool to send that PNG file path as a photo to the current Telegram chat. Then add a one-line caption summarizing the chart.

## Chart types & data shape

- `bar` / `line` / `pie`: `--data` is a JSON array of `{"label": ..., "value": number}`.
- `heatmap`: each item is `{"row": ..., "col": ..., "value": number}`.

Always set a clear `--title` (include the time period) and, for bar/line, `--xlabel` / `--ylabel`. If `--ylabel` mentions "revenue" or "BRL", bars are auto-formatted as R$.
