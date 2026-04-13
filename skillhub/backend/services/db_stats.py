"""
Read-only database statistics for the skillhub dashboard.
Uses the admin DATABASE_URL (not the read-only one) so it can also
query pg_catalog for table sizes.
"""

from __future__ import annotations

from sqlalchemy import create_engine, text

from skillhub.backend.config import DATABASE_URL

_engine = None


def _get_engine():
    global _engine
    if _engine is None:
        if not DATABASE_URL:
            raise RuntimeError("DATABASE_URL is not set in .env")
        _engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    return _engine


MONITORED_TABLES = [
    "product_category_translation",
    "customers",
    "sellers",
    "geolocation",
    "products",
    "orders",
    "order_items",
    "order_payments",
    "order_reviews",
]


def get_table_stats() -> list[dict]:
    """Row counts + disk size for each Olist table."""
    engine = _get_engine()
    results = []
    with engine.connect() as conn:
        for table in MONITORED_TABLES:
            row = conn.execute(
                text("""
                SELECT
                    reltuples::BIGINT                        AS row_estimate,
                    pg_size_pretty(pg_total_relation_size(quote_ident(relname))) AS total_size
                FROM pg_class
                WHERE relname = :table
            """),
                {"table": table},
            ).fetchone()

            exact = conn.execute(text(f'SELECT COUNT(*) FROM "{table}"')).scalar()

            results.append(
                {
                    "name": table,
                    "rows": exact,
                    "size": row.total_size if row else "—",
                }
            )
    return results


def get_total_rows() -> int:
    stats = get_table_stats()
    return sum(t["rows"] for t in stats)


def get_db_health() -> dict:
    """Quick connectivity check — returns True if DB is reachable."""
    try:
        engine = _get_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"connected": True, "error": None}
    except Exception as exc:
        return {"connected": False, "error": str(exc)}
