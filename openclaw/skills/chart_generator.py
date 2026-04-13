"""
chart_generator.py — called by send_chart.js as a subprocess.

Usage:
    python chart_generator.py --type bar --title "Revenue by Category" \
        --xlabel "Category" --ylabel "Revenue (BRL)" \
        --data '[{"label":"Electronics","value":120000}, ...]' \
        --output /tmp/chart_abc123.png

Supported chart types: bar | line | pie | heatmap

Prints the output file path to stdout on success.
Exits with code 1 and an error message on stderr on failure.
"""

import argparse
import json
import sys
import uuid
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # non-interactive backend — no display needed
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns

sns.set_theme(style="whitegrid", palette="muted")

OUTPUT_DIR = Path(__file__).parent.parent / "charts"
OUTPUT_DIR.mkdir(exist_ok=True)


# ---------------------------------------------------------------------------
# Chart renderers
# ---------------------------------------------------------------------------


def _bar_chart(data: list[dict], title: str, xlabel: str, ylabel: str) -> plt.Figure:
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
                f"R$ {x:,.0f}"
                if "revenue" in ylabel.lower() or "brl" in ylabel.lower()
                else f"{x:,.0f}"
            )
        )
    )

    for bar, val in zip(bars, values[::-1]):
        ax.text(
            val * 1.01, bar.get_y() + bar.get_height() / 2, f"{val:,.0f}", va="center", fontsize=8
        )

    fig.tight_layout()
    return fig


def _line_chart(data: list[dict], title: str, xlabel: str, ylabel: str) -> plt.Figure:
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


def _pie_chart(data: list[dict], title: str, **_) -> plt.Figure:
    labels = [str(d["label"]) for d in data]
    values = [float(d["value"]) for d in data]

    fig, ax = plt.subplots(figsize=(8, 7))
    wedges, texts, autotexts = ax.pie(
        values,
        labels=labels,
        autopct="%1.1f%%",
        startangle=140,
        colors=sns.color_palette("muted", len(labels)),
        pctdistance=0.82,
    )
    for at in autotexts:
        at.set_fontsize(9)

    ax.set_title(title, fontsize=14, fontweight="bold", pad=16)
    fig.tight_layout()
    return fig


def _heatmap_chart(data: list[dict], title: str, xlabel: str, ylabel: str) -> plt.Figure:
    """
    Expects data as a list of {row, col, value} dicts.
    Pivots into a 2-D matrix for the heatmap.
    """
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


RENDERERS = {
    "bar": _bar_chart,
    "line": _line_chart,
    "pie": _pie_chart,
    "heatmap": _heatmap_chart,
}


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a chart and save it as PNG.")
    parser.add_argument("--type", required=True, choices=list(RENDERERS), help="Chart type")
    parser.add_argument("--title", required=True, help="Chart title")
    parser.add_argument("--xlabel", default="", help="X-axis label")
    parser.add_argument("--ylabel", default="", help="Y-axis label")
    parser.add_argument("--data", required=True, help="JSON array of data points")
    parser.add_argument(
        "--output", default=None, help="Output PNG path (auto-generated if omitted)"
    )
    args = parser.parse_args()

    try:
        data = json.loads(args.data)
    except json.JSONDecodeError as exc:
        print(f"Invalid JSON in --data: {exc}", file=sys.stderr)
        sys.exit(1)

    renderer = RENDERERS[args.type]

    try:
        fig = renderer(data, title=args.title, xlabel=args.xlabel, ylabel=args.ylabel)
    except Exception as exc:
        print(f"Chart generation failed: {exc}", file=sys.stderr)
        sys.exit(1)

    output_path = (
        Path(args.output) if args.output else OUTPUT_DIR / f"chart_{uuid.uuid4().hex[:8]}.png"
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)

    # Print path to stdout — send_chart.js reads this
    print(str(output_path.resolve()))


if __name__ == "__main__":
    main()
