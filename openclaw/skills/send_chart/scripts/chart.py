"""
chart.py — render a chart as a PNG. Prints the saved file path to stdout.

Usage:
    python chart.py --type bar --title "Revenue by Category" \
        --xlabel "Category" --ylabel "Revenue (BRL)" \
        --data "[{\"label\":\"Electronics\",\"value\":120000}, ...]"

Types: bar | line | pie | heatmap (heatmap data needs row/col/value keys).
"""

import argparse
import json
import os
import sys
import uuid
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns

sns.set_theme(style="whitegrid", palette="muted")

# Write where OpenClaw's message tool is allowed to read outbound media:
# <state>/media/outbound, where state = <OPENCLAW_HOME or ~>/.openclaw
_HOME = os.environ.get("OPENCLAW_HOME") or str(Path.home())
OUTPUT_DIR = Path(_HOME) / ".openclaw" / "media" / "outbound"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def _bar_chart(data, title, xlabel, ylabel):
    labels = [str(d["label"]) for d in data]
    values = [float(d["value"]) for d in data]
    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.barh(labels[::-1], values[::-1], color=sns.color_palette("muted", len(labels)))
    ax.set_title(title, fontsize=14, fontweight="bold", pad=12)
    ax.set_xlabel(ylabel)
    ax.set_ylabel(xlabel)
    ax.xaxis.set_major_formatter(
        mticker.FuncFormatter(
            lambda x, _: (
                f"R$ {x:,.0f}" if "revenue" in ylabel.lower() or "brl" in ylabel.lower() else f"{x:,.0f}"
            )
        )
    )
    for bar, val in zip(bars, values[::-1]):
        ax.text(val * 1.01, bar.get_y() + bar.get_height() / 2, f"{val:,.0f}", va="center", fontsize=8)
    fig.tight_layout()
    return fig


def _line_chart(data, title, xlabel, ylabel):
    labels = [str(d["label"]) for d in data]
    values = [float(d["value"]) for d in data]
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.plot(labels, values, marker="o", linewidth=2, markersize=5, color="#2196F3")
    ax.fill_between(range(len(labels)), values, alpha=0.08, color="#2196F3")
    ax.set_title(title, fontsize=14, fontweight="bold", pad=12)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=8)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
    fig.tight_layout()
    return fig


def _pie_chart(data, title, **_):
    labels = [str(d["label"]) for d in data]
    values = [float(d["value"]) for d in data]
    fig, ax = plt.subplots(figsize=(8, 7))
    _, _, autotexts = ax.pie(
        values, labels=labels, autopct="%1.1f%%", startangle=140,
        colors=sns.color_palette("muted", len(labels)), pctdistance=0.82,
    )
    for at in autotexts:
        at.set_fontsize(9)
    ax.set_title(title, fontsize=14, fontweight="bold", pad=16)
    fig.tight_layout()
    return fig


def _heatmap_chart(data, title, xlabel, ylabel):
    import pandas as pd

    df = pd.DataFrame(data)
    if not {"row", "col", "value"}.issubset(df.columns):
        raise ValueError("Heatmap data must have 'row', 'col', 'value' keys.")
    matrix = df.pivot(index="row", columns="col", values="value").fillna(0)
    fig, ax = plt.subplots(figsize=(12, 6))
    sns.heatmap(matrix, ax=ax, cmap="YlOrRd", linewidths=0.3, annot=True, fmt=".0f")
    ax.set_title(title, fontsize=14, fontweight="bold", pad=12)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    fig.tight_layout()
    return fig


RENDERERS = {"bar": _bar_chart, "line": _line_chart, "pie": _pie_chart, "heatmap": _heatmap_chart}


def main():
    parser = argparse.ArgumentParser(description="Generate a chart PNG.")
    parser.add_argument("--type", required=True, choices=list(RENDERERS))
    parser.add_argument("--title", required=True)
    parser.add_argument("--xlabel", default="")
    parser.add_argument("--ylabel", default="")
    parser.add_argument("--data", default=None, help="JSON array of data points")
    parser.add_argument("--data-file", dest="data_file", default=None,
                        help="Path to a file containing the JSON array (avoids shell quoting)")
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    raw = args.data
    if args.data_file:
        raw = Path(args.data_file).read_text(encoding="utf-8")
    if not raw:
        print("Provide --data or --data-file", file=sys.stderr)
        sys.exit(1)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"Invalid JSON in data: {exc}", file=sys.stderr)
        sys.exit(1)

    try:
        fig = RENDERERS[args.type](data, title=args.title, xlabel=args.xlabel, ylabel=args.ylabel)
    except Exception as exc:
        print(f"Chart generation failed: {exc}", file=sys.stderr)
        sys.exit(1)

    output_path = Path(args.output) if args.output else OUTPUT_DIR / f"chart_{uuid.uuid4().hex[:8]}.png"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(str(output_path.resolve()))


if __name__ == "__main__":
    main()
