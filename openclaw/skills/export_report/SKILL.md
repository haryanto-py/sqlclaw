---
name: export_report
description: "Export tabular data the user asked for to a downloadable PDF or CSV file and send it on Telegram. Use when the user asks to export, download, or get a report/file/PDF/CSV of results."
metadata:
  {
    "openclaw": { "emoji": "📄", "requires": { "bins": ["python"] } }
  }
---

# Export Report

Turn query results into a PDF or CSV file and deliver it to the user.

## Workflow

1. Get the data with the **postgresql** skill.
2. Export it — call `exec` (`--format pdf` or `--format csv`):

```bash
..\.venv\Scripts\python.exe "skills/export_report/scripts/export.py" --format pdf --title "Top 10 Categories by Revenue" --data "[{\"category\":\"health_beauty\",\"revenue\":1441248.07},{\"category\":\"watches_gifts\",\"revenue\":1305541.61}]"
```

Output JSON: `{"success":true,"file_path":"...","format":"pdf"}`.

3. **Send the file**: use the `message` tool to send the document at `file_path` to the user as an attachment, with a short caption.

`--data` is a JSON array of flat objects (all rows should share the same keys); keys become column headers.
