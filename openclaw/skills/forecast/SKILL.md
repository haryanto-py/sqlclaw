---
name: forecast
description: "Project a time series into the future (linear-regression trend) and render a historical+forecast chart. Use when the user asks to forecast, predict, or project a future trend (e.g. revenue or order volume for the next N months)."
metadata:
  {
    "openclaw": { "emoji": "🔮", "requires": { "bins": ["python"] } }
  }
---

# Forecast

Forecast future periods from historical data and produce a chart.

## Workflow

1. Get the historical series with the **postgresql** skill (one row per period, e.g. monthly revenue). Each point needs a `date` and a `value`.
2. Run the forecast — call `exec`:

```bash
..\.venv\Scripts\python.exe "skills/forecast/scripts/forecast.py" --periods 3 --title "Revenue Forecast" --ylabel "Revenue (BRL)" --data "[{\"date\":\"2017-01\",\"value\":120000},{\"date\":\"2017-02\",\"value\":135000}]"
```

Output JSON: `{"success":true,"chart_path":"...","forecast_results":[{"date","forecasted_value"}, ...]}`.

3. **Send the chart**: use the `message` tool to send the PNG at `chart_path` to the user, and summarize the `forecast_results` in text.

Note: this is a simple linear-trend forecast — state that it's an estimate, not a seasonal model.
