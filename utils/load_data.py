"""
Loads cleaned Olist DataFrames into a PostgreSQL database.

Tables are inserted in FK-dependency order so foreign key constraints are
satisfied. On a --reload run, all tables are truncated first (CASCADE).
"""

from __future__ import annotations

import pandas as pd
from psycopg2.extras import execute_values
from sqlalchemy import text
from sqlalchemy.engine import Engine


def _execute_values_insert(table, conn, keys, data_iter):
    """
    Fast bulk insert using psycopg2 execute_values.
    Replaces pandas' method="multi" which is broken in SQLAlchemy 2.x.
    """
    dbapi_conn = conn.connection
    with dbapi_conn.cursor() as cur:
        columns = ", ".join(f'"{k}"' for k in keys)
        values = list(data_iter)
        execute_values(
            cur,
            f'INSERT INTO "{table.name}" ({columns}) VALUES %s',
            values,
            page_size=1000,
        )


# Insertion order respects FK dependencies
LOAD_ORDER = [
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

# Map table name → DataFrame column subset to insert
# (None means "insert all columns")
COLUMN_MAP: dict[str, list[str] | None] = {
    "product_category_translation": None,
    "customers": None,
    "sellers": None,
    "geolocation": None,
    "products": [
        "product_id",
        "product_category_name",
        "product_name_length",
        "product_description_length",
        "product_photos_qty",
        "product_weight_g",
        "product_length_cm",
        "product_height_cm",
        "product_width_cm",
    ],
    "orders": None,
    "order_items": None,
    "order_payments": None,
    "order_reviews": None,
}


def truncate_all(engine: Engine) -> None:
    """Truncate all tables in reverse dependency order (CASCADE)."""
    reverse = list(reversed(LOAD_ORDER))
    with engine.begin() as conn:
        for table in reverse:
            conn.execute(text(f'TRUNCATE TABLE "{table}" CASCADE'))
    print("All tables truncated.")


def load_all(
    cleaned: dict[str, pd.DataFrame],
    engine: Engine,
    reload: bool = False,
    chunksize: int = 5_000,
) -> None:
    """
    Inserts all cleaned DataFrames into PostgreSQL.

    Args:
        cleaned:   dict of {table_name: DataFrame} from clean_data.clean_all().
        engine:    SQLAlchemy engine with admin credentials.
        reload:    If True, truncate all tables before inserting.
        chunksize: Rows per batch insert.
    """
    if reload:
        truncate_all(engine)

    print("\nLoading tables into PostgreSQL ...")
    for table in LOAD_ORDER:
        df = cleaned.get(table)
        if df is None:
            print(f"  [SKIP] {table} — not found in cleaned dict")
            continue

        cols = COLUMN_MAP.get(table)
        if cols:
            df = df[[c for c in cols if c in df.columns]]

        df.to_sql(
            name=table,
            con=engine,
            if_exists="append",
            index=False,
            method=_execute_values_insert,
            chunksize=chunksize,
        )
        print(f"  [OK]   {table:<35} {len(df):>8,} rows inserted")

    print("\nLoad complete.")


def verify_row_counts(engine: Engine) -> None:
    """Print row counts for all tables as a post-load sanity check."""
    print("\nRow count verification:")
    with engine.connect() as conn:
        for table in LOAD_ORDER:
            result = conn.execute(text(f'SELECT COUNT(*) FROM "{table}"'))
            count = result.scalar()
            print(f"  {table:<35} {count:>8,} rows")
