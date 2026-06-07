"""
forecast.py — simple linear-regression time-series forecast + chart.

Usage:
    python forecast.py --data "[{\"date\":\"2017-01\",\"value\":1000}, ...]" \
        --periods 3 --title "Revenue Forecast" --ylabel "Revenue (BRL)"

Prints JSON: {"success":true,"chart_path":"...","forecast_results":[...]}.
"""

import argparse
import json
import sys
import uuid
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
from sklearn.linear_model import LinearRegression

sns.set_theme(style="whitegrid", palette="muted")

# skills/forecast/scripts/forecast.py -> parents[3] = openclaw/
OUTPUT_DIR = Path(__file__).resolve().parents[3] / "charts"
OUTPUT_DIR.mkdir(exist_ok=True)


def forecast_and_plot(data, periods, title, ylabel):
    df = pd.DataFrame(data)
    if "date" not in df.columns or "value" not in df.columns:
        raise ValueError("Data must contain 'date' and 'value' keys.")
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)
    df["value"] = pd.to_numeric(df["value"])

    df["time_index"] = np.arange(len(df))
    model = LinearRegression()
    model.fit(df[["time_index"]], df["value"])
    df["trend"] = model.predict(df[["time_index"]])

    last_date = df["date"].iloc[-1]
    freq = pd.infer_freq(df["date"]) or "MS"
    future_dates = pd.date_range(start=last_date, periods=periods + 1, freq=freq)[1:]
    future_X = pd.DataFrame({"time_index": np.arange(len(df), len(df) + periods)})
    future_y = model.predict(future_X)
    future_df = pd.DataFrame({"date": future_dates, "trend": future_y})

    fig, ax = plt.subplots(figsize=(11, 5))
    ax.plot(df["date"], df["value"], marker="o", linewidth=2, label="Actual", color="#2196F3")
    ax.plot(df["date"], df["trend"], linestyle="--", color="#FF9800", alpha=0.7, label="Trend")
    ax.plot(future_df["date"], future_df["trend"], marker="s", linestyle="--", linewidth=2,
            color="#F44336", label="Forecast")
    ax.set_title(title, fontsize=14, fontweight="bold", pad=12)
    ax.set_xlabel("Date")
    ax.set_ylabel(ylabel)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
    ax.legend()
    fig.tight_layout()

    output_path = OUTPUT_DIR / f"forecast_{uuid.uuid4().hex[:8]}.png"
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)

    results = [
        {"date": d.strftime("%Y-%m-%d"), "forecasted_value": round(v, 2)}
        for d, v in zip(future_df["date"], future_df["trend"])
    ]
    return str(output_path.resolve()), results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default=None, help="JSON array of historical data")
    parser.add_argument("--data-file", dest="data_file", default=None,
                        help="Path to a file containing the JSON array (avoids shell quoting)")
    parser.add_argument("--periods", type=int, default=3)
    parser.add_argument("--title", default="Forecast")
    parser.add_argument("--ylabel", default="Value")
    args = parser.parse_args()

    raw = Path(args.data_file).read_text(encoding="utf-8") if args.data_file else args.data
    if not raw:
        print(json.dumps({"error": "Provide --data or --data-file"}))
        sys.exit(1)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(json.dumps({"error": f"Invalid JSON in data: {exc}"}))
        sys.exit(1)

    try:
        chart_path, results = forecast_and_plot(data, args.periods, args.title, args.ylabel)
    except Exception as exc:
        print(json.dumps({"error": f"Forecasting failed: {exc}"}))
        sys.exit(1)

    print(json.dumps({"success": True, "chart_path": chart_path, "forecast_results": results}))


if __name__ == "__main__":
    main()
