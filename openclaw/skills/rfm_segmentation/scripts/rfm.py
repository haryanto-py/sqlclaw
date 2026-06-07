"""
rfm.py — RFM (Recency, Frequency, Monetary) customer segmentation.

Queries PostgreSQL (READONLY_DB_URL) directly, scores every customer, assigns
a segment, and renders a summary chart.

Usage:
    python rfm.py

Prints JSON: {"success":true,"chart_path":"...","segments_count":{...},"segments_avg_monetary":{...}}.
"""

import json
import os
import sys
import uuid
from pathlib import Path

import matplotlib
import pandas as pd
from sqlalchemy import create_engine

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_theme(style="whitegrid", palette="muted")

# Write to OpenClaw's allowed outbound-media dir: <state>/media/outbound
_HOME = os.environ.get("OPENCLAW_HOME") or str(Path.home())
OUTPUT_DIR = Path(_HOME) / ".openclaw" / "media" / "outbound"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def get_rfm_data() -> pd.DataFrame:
    db_url = os.environ.get("READONLY_DB_URL")
    if not db_url:
        raise RuntimeError("READONLY_DB_URL is not set in environment.")
    engine = create_engine(db_url)
    query = """
    SELECT
        c.customer_unique_id,
        MAX(o.order_purchase_timestamp) AS last_purchase_date,
        COUNT(DISTINCT o.order_id) AS frequency,
        SUM(op.payment_value) AS monetary
    FROM customers c
    JOIN orders o ON c.customer_id = o.customer_id
    JOIN order_payments op ON o.order_id = op.order_id
    WHERE o.order_status = 'delivered'
    GROUP BY c.customer_unique_id
    """
    return pd.read_sql(query, engine)


def calculate_rfm_segments(df: pd.DataFrame) -> pd.DataFrame:
    df["last_purchase_date"] = pd.to_datetime(df["last_purchase_date"])
    max_date = df["last_purchase_date"].max()
    df["recency"] = (max_date - df["last_purchase_date"]).dt.days
    df["R"] = pd.qcut(df["recency"], 4, labels=[4, 3, 2, 1], duplicates="drop")

    def f_score(x):
        if x >= 3:
            return 4
        if x == 2:
            return 3
        return 1

    df["F"] = df["frequency"].apply(f_score)
    df["M"] = pd.qcut(df["monetary"], 4, labels=[1, 2, 3, 4], duplicates="drop")
    df["R"] = df["R"].astype(str)
    df["F"] = df["F"].astype(str)
    df["M"] = df["M"].astype(str)
    df["RFM_Score"] = df["R"] + df["F"] + df["M"]

    def segment(row):
        r, f, m = int(row["R"]), int(row["F"]), int(row["M"])
        if r >= 3 and f >= 3 and m >= 3:
            return "Champions"
        if r >= 3 and f <= 2:
            return "Promising / Recent"
        if r <= 2 and f >= 3:
            return "At Risk (Loyal but inactive)"
        if r <= 2 and m >= 3:
            return "High Value, Churned"
        return "Standard / Low Value"

    df["Segment"] = df.apply(segment, axis=1)
    return df


def plot_segments(df: pd.DataFrame) -> str:
    counts = df["Segment"].value_counts().reset_index()
    counts.columns = ["Segment", "Count"]
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(data=counts, y="Segment", x="Count", palette="viridis", ax=ax)
    ax.set_title("Customer Segmentation (RFM Analysis)", fontsize=14, fontweight="bold", pad=12)
    ax.set_xlabel("Number of Customers")
    ax.set_ylabel("")
    for p in ax.patches:
        ax.annotate(f"{int(p.get_width()):,}",
                    (p.get_width() * 1.02, p.get_y() + p.get_height() / 2),
                    va="center", fontsize=10)
    fig.tight_layout()
    output_path = OUTPUT_DIR / f"rfm_{uuid.uuid4().hex[:8]}.png"
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return str(output_path.resolve())


def main():
    try:
        df = get_rfm_data()
        df = calculate_rfm_segments(df)
        chart_path = plot_segments(df)
        print(json.dumps({
            "success": True,
            "chart_path": chart_path,
            "segments_count": df["Segment"].value_counts().to_dict(),
            "segments_avg_monetary": df.groupby("Segment")["monetary"].mean().round(2).to_dict(),
            "message": "RFM segmentation complete. Send the chart as a photo and summarize the segments.",
        }))
    except Exception as exc:
        print(json.dumps({"error": f"RFM segmentation failed: {exc}"}))
        sys.exit(1)


if __name__ == "__main__":
    main()
