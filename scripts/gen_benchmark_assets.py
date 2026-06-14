"""
Generate the benchmark result images for TEST_RESULTS.md by running the
project's own chart/forecast/RFM skills against the live database.

Run:  python scripts/gen_benchmark_assets.py
Outputs PNGs into assets/benchmark/.
"""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OPENCLAW = ROOT / "openclaw"
OUT = ROOT / "assets" / "benchmark"
OUT.mkdir(parents=True, exist_ok=True)
PY = sys.executable
DB = os.environ["READONLY_DB_URL"]


def q(sql):
    import psycopg2
    from psycopg2.extras import RealDictCursor
    c = psycopg2.connect(DB, connect_timeout=10)
    cur = c.cursor(cursor_factory=RealDictCursor)
    cur.execute(sql)
    rows = cur.fetchall()
    c.close()
    return rows


def chart(kind, title, xlabel, ylabel, data, out):
    f = OUT / "_data.json"
    f.write_text(json.dumps(data), encoding="utf-8")
    cmd = [PY, str(OPENCLAW / "skills/send_chart/scripts/chart.py"),
           "--type", kind, "--title", title, "--xlabel", xlabel, "--ylabel", ylabel,
           "--data-file", str(f), "--output", str(OUT / out)]
    subprocess.run(cmd, check=True, cwd=OPENCLAW)
    print("  wrote", out)


# 1. Orders by status (bar)
rows = q("SELECT order_status, COUNT(*) AS n FROM orders GROUP BY order_status ORDER BY n DESC")
chart("bar", "Orders by Status", "Status", "Orders",
      [{"label": r["order_status"], "value": int(r["n"])} for r in rows], "orders_by_status.png")

# 2. Revenue by year (bar)
rows = q("""SELECT EXTRACT(YEAR FROM o.order_purchase_timestamp)::int AS y,
                   SUM(oi.price + oi.freight_value) AS rev
            FROM orders o JOIN order_items oi USING(order_id)
            GROUP BY y ORDER BY y""")
chart("bar", "Revenue by Year (GMV)", "Year", "Revenue (BRL)",
      [{"label": str(r["y"]), "value": float(r["rev"])} for r in rows], "revenue_by_year.png")

# 3. Top 10 categories by revenue (bar)
rows = q("""SELECT pt.product_category_name_english AS cat,
                   SUM(oi.price + oi.freight_value) AS rev
            FROM orders o JOIN order_items oi USING(order_id)
            JOIN products p USING(product_id)
            JOIN product_category_translation pt USING(product_category_name)
            GROUP BY cat ORDER BY rev DESC LIMIT 10""")
chart("bar", "Top 10 Categories by Revenue", "Category", "Revenue (BRL)",
      [{"label": r["cat"], "value": float(r["rev"])} for r in rows], "top_categories.png")

# 4. Payment methods (pie)
rows = q("SELECT payment_type, COUNT(*) AS n FROM order_payments GROUP BY payment_type ORDER BY n DESC")
chart("pie", "Payment Methods", "", "",
      [{"label": r["payment_type"], "value": int(r["n"])} for r in rows if r["payment_type"] != "not_defined"],
      "payment_methods.png")

# 5. Forecast (run the real forecast skill on monthly revenue)
rows = q("""SELECT to_char(date_trunc('month', o.order_purchase_timestamp), 'YYYY-MM') AS m,
                   SUM(oi.price + oi.freight_value) AS rev
            FROM orders o JOIN order_items oi USING(order_id)
            WHERE o.order_purchase_timestamp >= '2017-01-01'
              AND o.order_purchase_timestamp < '2018-08-01'
            GROUP BY m ORDER BY m""")
monthly = [{"date": r["m"], "value": float(r["rev"])} for r in rows]
home = OUT / "_fchome"
(home / ".openclaw").mkdir(parents=True, exist_ok=True)
env = {**os.environ, "OPENCLAW_HOME": str(home)}
df = OUT / "_fc.json"
df.write_text(json.dumps(monthly), encoding="utf-8")
r = subprocess.run([PY, str(OPENCLAW / "skills/forecast/scripts/forecast.py"),
                    "--periods", "3", "--title", "Monthly Revenue Forecast (next 3 months)",
                    "--ylabel", "Revenue (BRL)", "--data-file", str(df)],
                   capture_output=True, text=True, cwd=OPENCLAW, env=env)
path = json.loads(r.stdout)["chart_path"]
shutil.copy(path, OUT / "revenue_forecast.png")
print("  wrote revenue_forecast.png")

# 6. RFM segmentation (run the real RFM skill)
r = subprocess.run([PY, str(OPENCLAW / "skills/rfm_segmentation/scripts/rfm.py")],
                   capture_output=True, text=True, cwd=OPENCLAW, env=env)
path = json.loads(r.stdout)["chart_path"]
shutil.copy(path, OUT / "rfm_segments.png")
print("  wrote rfm_segments.png")

# cleanup temp
for p in [OUT / "_data.json", OUT / "_fc.json"]:
    p.unlink(missing_ok=True)
shutil.rmtree(home, ignore_errors=True)
print("Done ->", OUT)
