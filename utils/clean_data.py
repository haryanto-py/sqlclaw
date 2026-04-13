"""
Olist Brazilian E-Commerce — multi-table data cleaning pipeline.

Each public function cleans one source CSV into a ready-to-load DataFrame.
The orchestrator clean_all() runs all of them in FK-dependency order.
"""

from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _zfill_zip(series: pd.Series, width: int = 5) -> pd.Series:
    """Zero-pad a zip-code series to a fixed width string."""
    return series.astype(str).str.strip().str.zfill(width)


def _title_city(series: pd.Series) -> pd.Series:
    """Strip and title-case a city-name series."""
    return series.str.strip().str.title()


def _report(name: str, before: int, after: int, issues: dict) -> None:
    removed = before - after
    print(f"\n[{name}]")
    print(f"  Rows : {before:,} -> {after:,}  (removed {removed:,})")
    for desc, count in issues.items():
        print(f"  {desc}: {count:,}")


# ---------------------------------------------------------------------------
# Per-table cleaning functions
# ---------------------------------------------------------------------------


def clean_category_translation(df: pd.DataFrame) -> pd.DataFrame:
    """
    olist_product_category_name_translation.csv
    Issues: a few English names have typos / duplicate semantics.
    """
    before = len(df)
    df = df.copy()

    df.columns = ["product_category_name", "product_category_name_english"]
    df = df.map(lambda v: v.strip() if isinstance(v, str) else v)

    # Normalize known typos in English names
    fixes = {
        "home_appliances_2": "home_appliances",
        "home_confort": "home_comfort",
        "home_comfort_2": "home_comfort",
        "pc_gamer": "pc_gamer",  # keep as-is
        "fashion_childrens_clothes": "fashion_childrens_clothes",
    }
    df["product_category_name_english"] = (
        df["product_category_name_english"].str.strip().replace(fixes)
    )

    # Drop true duplicates on the PK column
    dupes = df.duplicated(subset="product_category_name", keep="first").sum()
    df = df.drop_duplicates(subset="product_category_name", keep="first")

    _report(
        "category_translation",
        before,
        len(df),
        {"Typos fixed": len(fixes), "Duplicate PK rows dropped": dupes},
    )
    return df.reset_index(drop=True)


def clean_products(df_products: pd.DataFrame, df_translation: pd.DataFrame) -> pd.DataFrame:
    """
    olist_products_dataset.csv
    Issues:
      - Column name typos: 'lenght' → 'length'
      - ~610 rows have NULL product_category_name
      - NULL dimension/weight values
    """
    before = len(df_products)
    df = df_products.copy()

    # Fix column name typos that exist in the raw Olist CSV
    df = df.rename(
        columns={
            "product_name_lenght": "product_name_length",
            "product_description_lenght": "product_description_length",
        }
    )

    # Merge English translation (left join keeps all products)
    df = df.merge(
        df_translation[["product_category_name", "product_category_name_english"]],
        on="product_category_name",
        how="left",
    )

    # Null out any category that has no entry in the translation table —
    # these violate the FK constraint (e.g. 'pc_gamer' is absent from the CSV).
    no_translation = (
        df["product_category_name_english"].isna() & df["product_category_name"].notna()
    )
    unmapped_categories = df.loc[no_translation, "product_category_name"].unique().tolist()
    if unmapped_categories:
        print(f"  Unmapped categories set to NULL: {unmapped_categories}")
    df.loc[no_translation, "product_category_name"] = None

    null_category = df["product_category_name"].isna().sum()

    # Fill null numeric dimensions/weight with per-category median, then global median
    dim_cols = [
        "product_name_length",
        "product_description_length",
        "product_photos_qty",
        "product_weight_g",
        "product_length_cm",
        "product_height_cm",
        "product_width_cm",
    ]
    for col in dim_cols:
        if col in df.columns:
            cat_median = df.groupby("product_category_name")[col].transform("median")
            global_median = df[col].median()
            df[col] = df[col].fillna(cat_median).fillna(global_median)
            df[col] = df[col].round().astype("Int64")  # nullable integer

    _report(
        "products",
        before,
        len(df),
        {
            "NULL category_name (kept, FK nullable)": null_category,
        },
    )
    return df.reset_index(drop=True)


def clean_customers(df: pd.DataFrame) -> pd.DataFrame:
    """
    olist_customers_dataset.csv
    Issues:
      - zip_code_prefix stored as int (loses leading zero)
      - Inconsistent city casing
    """
    before = len(df)
    df = df.copy()

    df["customer_zip_code_prefix"] = _zfill_zip(df["customer_zip_code_prefix"])
    df["customer_city"] = _title_city(df["customer_city"])
    df["customer_state"] = df["customer_state"].str.strip().str.upper()

    dupes = df.duplicated(subset="customer_id", keep="first").sum()
    df = df.drop_duplicates(subset="customer_id", keep="first")

    _report("customers", before, len(df), {"Duplicate customer_id rows dropped": dupes})
    return df.reset_index(drop=True)


def clean_sellers(df: pd.DataFrame) -> pd.DataFrame:
    """
    olist_sellers_dataset.csv
    Issues: same zip/city problems as customers.
    """
    before = len(df)
    df = df.copy()

    df["seller_zip_code_prefix"] = _zfill_zip(df["seller_zip_code_prefix"])
    df["seller_city"] = _title_city(df["seller_city"])
    df["seller_state"] = df["seller_state"].str.strip().str.upper()

    dupes = df.duplicated(subset="seller_id", keep="first").sum()
    df = df.drop_duplicates(subset="seller_id", keep="first")

    _report("sellers", before, len(df), {"Duplicate seller_id rows dropped": dupes})
    return df.reset_index(drop=True)


def clean_orders(df: pd.DataFrame) -> pd.DataFrame:
    """
    olist_orders_dataset.csv
    Issues:
      - All timestamp columns are strings
      - Legitimate NULLs in delivery date columns (undelivered orders)
    """
    before = len(df)
    df = df.copy()

    ts_cols = [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ]
    for col in ts_cols:
        df[col] = pd.to_datetime(df[col], errors="coerce")

    valid_statuses = {
        "delivered",
        "shipped",
        "canceled",
        "unavailable",
        "invoiced",
        "processing",
        "created",
        "approved",
    }
    unknown_status = (~df["order_status"].isin(valid_statuses)).sum()

    # Drop rows missing the non-nullable columns
    required = [
        "order_id",
        "customer_id",
        "order_purchase_timestamp",
        "order_estimated_delivery_date",
    ]
    missing_required = df[required].isna().any(axis=1).sum()
    df = df.dropna(subset=required)

    dupes = df.duplicated(subset="order_id", keep="first").sum()
    df = df.drop_duplicates(subset="order_id", keep="first")

    _report(
        "orders",
        before,
        len(df),
        {
            "Unknown order_status values": unknown_status,
            "Rows dropped (missing required cols)": missing_required,
            "Duplicate order_id rows dropped": dupes,
        },
    )
    return df.reset_index(drop=True)


def clean_order_items(
    df: pd.DataFrame, valid_order_ids: set, valid_product_ids: set, valid_seller_ids: set
) -> pd.DataFrame:
    """
    olist_order_items_dataset.csv
    Issues:
      - shipping_limit_date is a string
      - price/freight_value float precision
      - Orphaned FKs (order/product/seller not in parent tables)
    """
    before = len(df)
    df = df.copy()

    df["shipping_limit_date"] = pd.to_datetime(df["shipping_limit_date"], errors="coerce")
    df["price"] = df["price"].round(2)
    df["freight_value"] = df["freight_value"].round(2)
    df["order_item_id"] = df["order_item_id"].astype(int)

    orphan_orders = (~df["order_id"].isin(valid_order_ids)).sum()
    orphan_products = (~df["product_id"].isin(valid_product_ids)).sum()
    orphan_sellers = (~df["seller_id"].isin(valid_seller_ids)).sum()

    df = df[
        df["order_id"].isin(valid_order_ids)
        & df["product_id"].isin(valid_product_ids)
        & df["seller_id"].isin(valid_seller_ids)
    ]

    dupes = df.duplicated(subset=["order_id", "order_item_id"], keep="first").sum()
    df = df.drop_duplicates(subset=["order_id", "order_item_id"], keep="first")

    _report(
        "order_items",
        before,
        len(df),
        {
            "Orphan order_id rows dropped": orphan_orders,
            "Orphan product_id rows dropped": orphan_products,
            "Orphan seller_id rows dropped": orphan_sellers,
            "Duplicate (order_id, order_item_id) dropped": dupes,
        },
    )
    return df.reset_index(drop=True)


def clean_order_payments(df: pd.DataFrame, valid_order_ids: set) -> pd.DataFrame:
    """
    olist_order_payments_dataset.csv
    Issues:
      - Unexpected payment_type values
      - Zero-value payments (valid — voucher adjustments)
      - Orphaned order_ids
    """
    before = len(df)
    df = df.copy()

    valid_payment_types = {"credit_card", "boleto", "voucher", "debit_card", "not_defined"}
    unknown_types = (~df["payment_type"].isin(valid_payment_types)).sum()

    df["payment_value"] = df["payment_value"].round(2)
    df["payment_installments"] = df["payment_installments"].astype(int)
    df["payment_sequential"] = df["payment_sequential"].astype(int)

    orphans = (~df["order_id"].isin(valid_order_ids)).sum()
    df = df[df["order_id"].isin(valid_order_ids)]

    dupes = df.duplicated(subset=["order_id", "payment_sequential"], keep="first").sum()
    df = df.drop_duplicates(subset=["order_id", "payment_sequential"], keep="first")

    _report(
        "order_payments",
        before,
        len(df),
        {
            "Unknown payment_type values": unknown_types,
            "Orphan order_id rows dropped": orphans,
            "Duplicate (order_id, payment_sequential) dropped": dupes,
        },
    )
    return df.reset_index(drop=True)


def clean_order_reviews(df: pd.DataFrame, valid_order_ids: set) -> pd.DataFrame:
    """
    olist_order_reviews_dataset.csv
    Issues:
      - Timestamps are strings
      - Many NULL comment titles/messages (normal — star-only reviews)
      - Duplicate review_id values (composite PK is review_id + order_id)
      - Orphaned order_ids
    """
    before = len(df)
    df = df.copy()

    df["review_creation_date"] = pd.to_datetime(df["review_creation_date"], errors="coerce")
    df["review_answer_timestamp"] = pd.to_datetime(df["review_answer_timestamp"], errors="coerce")

    # Clamp scores to valid range
    invalid_scores = (~df["review_score"].between(1, 5)).sum()
    df = df[df["review_score"].between(1, 5)]

    orphans = (~df["order_id"].isin(valid_order_ids)).sum()
    df = df[df["order_id"].isin(valid_order_ids)]

    # Keep NULLs in comment columns — they represent star-only reviews
    null_titles = df["review_comment_title"].isna().sum()
    null_messages = df["review_comment_message"].isna().sum()

    # Drop true duplicates on composite PK
    dupes = df.duplicated(subset=["review_id", "order_id"], keep="first").sum()
    df = df.drop_duplicates(subset=["review_id", "order_id"], keep="first")

    _report(
        "order_reviews",
        before,
        len(df),
        {
            "Invalid score rows dropped": invalid_scores,
            "Orphan order_id rows dropped": orphans,
            "NULL comment titles (kept)": null_titles,
            "NULL comment messages (kept)": null_messages,
            "Duplicate (review_id, order_id) dropped": dupes,
        },
    )
    return df.reset_index(drop=True)


def clean_geolocation(df: pd.DataFrame) -> pd.DataFrame:
    """
    olist_geolocation_dataset.csv
    Issues:
      - ~1 million rows for ~19K unique zip codes (massive duplication)
      - Inconsistent city/state across duplicate rows for same zip
      - Zip codes stored as int (lose leading zero)
      - Some lat/lng outside Brazil bounds
    """
    before = len(df)
    df = df.copy()

    df["geolocation_zip_code_prefix"] = _zfill_zip(df["geolocation_zip_code_prefix"])
    df["geolocation_city"] = _title_city(df["geolocation_city"])
    df["geolocation_state"] = df["geolocation_state"].str.strip().str.upper()

    # Filter points outside Brazil bounding box
    lat_bounds = (-34.0, 5.5)
    lng_bounds = (-74.0, -34.0)
    out_of_bounds = (
        ~df["geolocation_lat"].between(*lat_bounds) | ~df["geolocation_lng"].between(*lng_bounds)
    ).sum()
    df = df[df["geolocation_lat"].between(*lat_bounds) & df["geolocation_lng"].between(*lng_bounds)]

    # Deduplicate: one row per zip code
    # Mean of lat/lng, mode of city and state
    def _agg(group: pd.DataFrame) -> pd.Series:
        return pd.Series(
            {
                "geolocation_lat": group["geolocation_lat"].mean(),
                "geolocation_lng": group["geolocation_lng"].mean(),
                "geolocation_city": group["geolocation_city"].mode().iloc[0],
                "geolocation_state": group["geolocation_state"].mode().iloc[0],
            }
        )

    df = (
        df.groupby("geolocation_zip_code_prefix", as_index=False).apply(_agg).reset_index(drop=True)
    )

    _report(
        "geolocation",
        before,
        len(df),
        {
            "Out-of-bounds coordinates removed": out_of_bounds,
            "Unique zip codes after deduplication": len(df),
        },
    )
    return df


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


def clean_all(
    data_dir: str = "./data", output_dir: str = "./data_cleaned"
) -> dict[str, pd.DataFrame]:
    """
    Reads all 9 Olist CSVs from data_dir, cleans them in FK-dependency order,
    optionally saves cleaned CSVs to output_dir, and returns a dict of DataFrames.

    Returns:
        dict mapping table name → cleaned DataFrame, ready for load_data.py.
    """
    src = Path(data_dir)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("Olist Data Cleaning Pipeline")
    print("=" * 60)

    # --- Load raw CSVs ---
    raw = {
        "category_translation": pd.read_csv(src / "product_category_name_translation.csv"),
        "products": pd.read_csv(src / "olist_products_dataset.csv"),
        "customers": pd.read_csv(src / "olist_customers_dataset.csv"),
        "sellers": pd.read_csv(src / "olist_sellers_dataset.csv"),
        "orders": pd.read_csv(src / "olist_orders_dataset.csv"),
        "order_items": pd.read_csv(src / "olist_order_items_dataset.csv"),
        "order_payments": pd.read_csv(src / "olist_order_payments_dataset.csv"),
        "order_reviews": pd.read_csv(src / "olist_order_reviews_dataset.csv"),
        "geolocation": pd.read_csv(src / "olist_geolocation_dataset.csv"),
    }

    # --- Clean in FK-dependency order ---
    cleaned: dict[str, pd.DataFrame] = {}

    cleaned["product_category_translation"] = clean_category_translation(
        raw["category_translation"]
    )
    cleaned["products"] = clean_products(raw["products"], cleaned["product_category_translation"])
    cleaned["customers"] = clean_customers(raw["customers"])
    cleaned["sellers"] = clean_sellers(raw["sellers"])
    cleaned["orders"] = clean_orders(raw["orders"])

    # Build valid-ID sets for referential integrity checks
    valid_order_ids = set(cleaned["orders"]["order_id"])
    valid_product_ids = set(cleaned["products"]["product_id"])
    valid_seller_ids = set(cleaned["sellers"]["seller_id"])

    cleaned["order_items"] = clean_order_items(
        raw["order_items"], valid_order_ids, valid_product_ids, valid_seller_ids
    )
    cleaned["order_payments"] = clean_order_payments(raw["order_payments"], valid_order_ids)
    cleaned["order_reviews"] = clean_order_reviews(raw["order_reviews"], valid_order_ids)
    cleaned["geolocation"] = clean_geolocation(raw["geolocation"])

    # --- Save cleaned CSVs ---
    for name, df in cleaned.items():
        path = out / f"{name}.csv"
        df.to_csv(path, index=False)

    print("\n" + "=" * 60)
    print("Cleaning complete. Summary:")
    for name, df in cleaned.items():
        print(f"  {name:<35} {len(df):>8,} rows")
    print(f"\nCleaned files saved to: {out.resolve()}")
    print("=" * 60)

    return cleaned


if __name__ == "__main__":
    clean_all()
