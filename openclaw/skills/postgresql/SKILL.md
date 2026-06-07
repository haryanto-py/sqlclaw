---
name: postgresql
description: "Query the Olist Brazilian e-commerce PostgreSQL database (read-only) to answer questions about orders, products, customers, sellers, payments, reviews, and revenue. Use whenever the user asks for any data, metric, count, ranking, or trend."
metadata:
  {
    "openclaw":
      {
        "emoji": "🐘",
        "requires": { "bins": ["python"] }
      }
  }
---

# PostgreSQL Sales Data

Run read-only SQL against the `olist_ecommerce` database to answer data questions.

## When to Use

✅ Any question that needs real numbers: counts, sums, averages, rankings, trends, "how many / which / top / by state / by category / over time", revenue, review scores, delivery performance, etc.

❌ Pure definitions or business context with no data needed (e.g. "what does GMV mean?") — answer directly or use the `knowledge_search` skill.

## How to Run a Query

Execute exactly one SELECT (or WITH) statement at a time:

```bash
"$PYTHON_PATH" {baseDir}/scripts/query.py "SELECT order_status, COUNT(*) AS n FROM orders GROUP BY order_status ORDER BY n DESC;"
```

- The connection is read-only and read from the environment — do **not** put credentials in the SQL.
- Output is JSON: `{"success": true, "rowcount": N, "truncated": bool, "rows": [...]}`.
- On a blocked or failed query it prints `{"error": "..."}`. If `blocked` is true, the SQL was rejected by the safety validator — tell the user only read-only SELECT queries are allowed; do not retry the same statement.
- Results are capped at 200 rows (`truncated: true` means there were more — add `LIMIT`/aggregation).

## Safety (already enforced — do not bypass)

The script rejects anything that is not a single SELECT/WITH statement and blocks INSERT/UPDATE/DELETE/DROP/ALTER/CREATE/etc. and stacked statements. Never attempt to mutate data.

## Schema (`olist_ecommerce`, 9 tables)

- **orders** — one row per order. `order_id` (PK), `customer_id` (FK→customers), `order_status` (delivered|shipped|canceled|unavailable|invoiced|processing|created|approved), `order_purchase_timestamp`, `order_approved_at`, `order_delivered_carrier_date`, `order_delivered_customer_date`, `order_estimated_delivery_date`.
- **order_items** — `order_id`+`order_item_id` (PK), `product_id` (FK→products), `seller_id` (FK→sellers), `price`, `freight_value` (BRL), `shipping_limit_date`.
- **order_payments** — `order_id`+`payment_sequential` (PK), `payment_type` (credit_card|boleto|voucher|debit_card|not_defined), `payment_installments`, `payment_value` (BRL).
- **order_reviews** — `review_id`+`order_id` (PK), `review_score` (1–5), `review_comment_title`, `review_comment_message`, `review_creation_date`, `review_answer_timestamp`.
- **products** — `product_id` (PK), `product_category_name` (FK→product_category_translation), `product_weight_g`, `product_length_cm`, `product_height_cm`, `product_width_cm`, `product_photos_qty`.
- **product_category_translation** — `product_category_name` (PK, Portuguese), `product_category_name_english`.
- **customers** — `customer_id` (PK, ties to orders), `customer_unique_id` (the real person — use for repeat-customer analysis), `customer_zip_code_prefix`, `customer_city`, `customer_state`.
- **sellers** — `seller_id` (PK), `seller_zip_code_prefix`, `seller_city`, `seller_state`.
- **geolocation** — `geolocation_zip_code_prefix`, `geolocation_lat`, `geolocation_lng`, `geolocation_city`, `geolocation_state`.

### Key Joins

```sql
-- Revenue by category
FROM orders o
  JOIN order_items oi ON o.order_id = oi.order_id
  JOIN products p     ON oi.product_id = p.product_id
  JOIN product_category_translation t ON p.product_category_name = t.product_category_name
-- Revenue = SUM(oi.price); GMV = SUM(oi.price + oi.freight_value)

-- Customer geography:  orders o JOIN customers c ON o.customer_id = c.customer_id
-- Seller performance:  order_items oi JOIN sellers s ON oi.seller_id = s.seller_id
-- Payments:            orders o JOIN order_payments op ON o.order_id = op.order_id
-- Reviews:             orders o JOIN order_reviews r ON o.order_id = r.order_id
```

## Answering

- Format BRL as `R$ 1,234.56`; large counts with comma separators (`99,441`); dates as `YYYY-MM-DD`.
- If many rows, summarize (top 10 + total) rather than dumping everything.
- Be concise and professional (Telegram). Bold key figures with `*...*`.
