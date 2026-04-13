from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from skillhub.backend.services.db_stats import _get_engine, get_db_health, get_table_stats

router = APIRouter(prefix="/api/database", tags=["database"])

# Canned sample queries shown in the UI for each table
SAMPLE_QUERIES = {
    "orders": "SELECT order_status, COUNT(*) AS total FROM orders GROUP BY order_status ORDER BY total DESC",
    "order_items": "SELECT p.product_category_name, ROUND(SUM(oi.price)::numeric, 2) AS revenue FROM order_items oi JOIN products p ON oi.product_id = p.product_id GROUP BY 1 ORDER BY revenue DESC LIMIT 10",
    "customers": "SELECT customer_state, COUNT(*) AS customers FROM customers GROUP BY customer_state ORDER BY customers DESC LIMIT 10",
    "sellers": "SELECT seller_state, COUNT(*) AS sellers FROM sellers GROUP BY seller_state ORDER BY sellers DESC",
    "order_reviews": "SELECT review_score, COUNT(*) AS total FROM order_reviews GROUP BY review_score ORDER BY review_score",
    "order_payments": "SELECT payment_type, COUNT(*) AS total, ROUND(SUM(payment_value)::numeric, 2) AS total_value FROM order_payments GROUP BY payment_type ORDER BY total DESC",
    "products": "SELECT product_category_name, COUNT(*) AS products FROM products GROUP BY product_category_name ORDER BY products DESC LIMIT 10",
    "geolocation": "SELECT geolocation_state, COUNT(*) AS zip_codes FROM geolocation GROUP BY geolocation_state ORDER BY zip_codes DESC",
    "product_category_translation": "SELECT * FROM product_category_translation ORDER BY product_category_name_english LIMIT 20",
}


@router.get("/tables")
def database_tables():
    health = get_db_health()
    if not health["connected"]:
        raise HTTPException(status_code=503, detail=f"Database unreachable: {health['error']}")
    tables = get_table_stats()
    for t in tables:
        t["sample_query"] = SAMPLE_QUERIES.get(t["name"], "")
    return {"connected": True, "tables": tables}


@router.post("/query")
def run_query(body: dict):
    """
    Execute a read-only SQL query and return up to 200 rows.
    Only SELECT statements are permitted here too.
    """
    sql = (body.get("sql") or "").strip()
    if not sql:
        raise HTTPException(status_code=400, detail="No SQL provided.")
    if not sql.upper().startswith("SELECT"):
        raise HTTPException(status_code=400, detail="Only SELECT statements are allowed.")

    try:
        engine = _get_engine()
        with engine.connect() as conn:
            result = conn.execute(text(sql))
            columns = list(result.keys())
            rows = [dict(zip(columns, row)) for row in result.fetchmany(200)]
        return {"columns": columns, "rows": rows, "count": len(rows)}
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
