"""
export.py — export tabular JSON data to a CSV or PDF file.

Usage:
    python export.py --format pdf --title "Top Products" \
        --data "[{\"product\":\"A\",\"revenue\":100}, ...]"

Prints JSON: {"success":true,"file_path":"...","format":"pdf"}.
"""

import argparse
import csv
import json
import os
import sys
import uuid
from pathlib import Path

from fpdf import FPDF

# Write to OpenClaw's allowed outbound-media dir: <state>/media/outbound
_HOME = os.environ.get("OPENCLAW_HOME") or str(Path.home())
OUTPUT_DIR = Path(_HOME) / ".openclaw" / "media" / "outbound"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def _safe_name(title: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in title).strip("_").lower() or "report"


def export_csv(data, title) -> str:
    if not data:
        raise ValueError("No data provided to export.")
    output_path = OUTPUT_DIR / f"{_safe_name(title)}_{uuid.uuid4().hex[:8]}.csv"
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(data[0].keys()))
        writer.writeheader()
        writer.writerows(data)
    return str(output_path.resolve())


def export_pdf(data, title) -> str:
    if not data:
        raise ValueError("No data provided to export.")
    output_path = OUTPUT_DIR / f"{_safe_name(title)}_{uuid.uuid4().hex[:8]}.pdf"
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", "B", 16)
    pdf.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(5)

    keys = list(data[0].keys())
    col_width = pdf.epw / len(keys)
    line_height = pdf.font_size * 2

    pdf.set_font("helvetica", "B", 10)
    for key in keys:
        pdf.cell(col_width, line_height, key.replace("_", " ").title(), border=1, align="C")
    pdf.ln(line_height)

    pdf.set_font("helvetica", "", 9)
    for row in data:
        for key in keys:
            val = str(row.get(key, ""))
            if len(val) > 30:
                val = val[:27] + "..."
            pdf.cell(col_width, line_height, val, border=1, align="C")
        pdf.ln(line_height)

    pdf.output(str(output_path))
    return str(output_path.resolve())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--format", choices=["csv", "pdf"], required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--data", default=None)
    parser.add_argument("--data-file", dest="data_file", default=None,
                        help="Path to a file containing the JSON array (avoids shell quoting)")
    args = parser.parse_args()

    raw = Path(args.data_file).read_text(encoding="utf-8") if args.data_file else args.data
    if not raw:
        print(json.dumps({"error": "Provide --data or --data-file"}))
        sys.exit(1)
    try:
        data = json.loads(raw)
    except Exception as exc:
        print(json.dumps({"error": f"Invalid JSON in data: {exc}"}))
        sys.exit(1)

    try:
        file_path = export_csv(data, args.title) if args.format == "csv" else export_pdf(data, args.title)
        print(json.dumps({
            "success": True, "file_path": file_path, "format": args.format,
            "message": f"Exported to {args.format.upper()}. Send the file to the user.",
        }))
    except Exception as exc:
        print(json.dumps({"error": f"Export failed: {exc}"}))
        sys.exit(1)


if __name__ == "__main__":
    main()
