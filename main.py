"""
Olist ETL Pipeline — entry point.

Usage:
    python main.py                  # Run full pipeline (clean → schema → load)
    python main.py --step download  # Download from Kaggle (optional — or add CSVs manually)
    python main.py --step clean     # Only clean raw CSVs in ./data
    python main.py --step schema    # Only apply DB schema DDL
    python main.py --step load      # Only load cleaned data into PostgreSQL
    python main.py --step load --reload  # Truncate tables, then reload
    python main.py --step embed     # Embed KNOWLEDGE.md into pgvector (RAG)
    python main.py --step embed --reload  # Re-embed from scratch

First-time setup:
    1. Place Olist CSVs manually into ./data/   (or run --step download)
    2. Create the database:   createdb olist_ecommerce
    3. Add DATABASE_URL to .env
    4. Run: python main.py
    5. Create read-only user: python main.py --step create-user
    6. Embed knowledge base: python main.py --step embed
"""

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(override=True)

DATA_DIR = "./data"
CLEANED_DIR = "./data_cleaned"

# The 9 CSV files the Olist dataset unzips to
OLIST_CSVS = [
    "olist_orders_dataset.csv",
    "olist_order_items_dataset.csv",
    "olist_customers_dataset.csv",
    "olist_sellers_dataset.csv",
    "olist_products_dataset.csv",
    "olist_order_payments_dataset.csv",
    "olist_order_reviews_dataset.csv",
    "olist_geolocation_dataset.csv",
    "product_category_name_translation.csv",
]


def _data_ready() -> bool:
    """Return True if all expected Olist CSVs are present in DATA_DIR."""
    data_path = Path(DATA_DIR)
    return all((data_path / csv).exists() for csv in OLIST_CSVS)


def cmd_download() -> None:
    from utils.fetch_dataset import download_dataset

    download_dataset(output_path=DATA_DIR)


def cmd_clean() -> dict:
    from utils.clean_data import clean_all

    return clean_all(data_dir=DATA_DIR, output_dir=CLEANED_DIR)


def cmd_schema(engine) -> None:
    from utils.db import execute_sql_file

    execute_sql_file(engine, "sql/schema.sql")


def cmd_create_user(engine) -> None:
    import os

    import sqlalchemy

    from utils.db import execute_sql_file

    password = os.environ.get("READONLY_DB_PASSWORD")
    if not password:
        raise RuntimeError("READONLY_DB_PASSWORD is not set in .env")

    try:
        execute_sql_file(engine, "sql/create_readonly_user.sql")
    except Exception as e:
        if "already exists" in str(e):
            print("Role olist_reader already exists — skipping CREATE, re-applying grants.")
        else:
            raise

    # Always set/update the password from env
    with engine.connect() as conn:
        conn.execute(sqlalchemy.text(f"ALTER ROLE olist_reader WITH PASSWORD '{password}'"))
        conn.execute(sqlalchemy.text("GRANT CONNECT ON DATABASE olist_ecommerce TO olist_reader"))
        conn.execute(sqlalchemy.text("GRANT USAGE ON SCHEMA public TO olist_reader"))
        conn.execute(sqlalchemy.text("GRANT SELECT ON ALL TABLES IN SCHEMA public TO olist_reader"))
        conn.commit()
    print("Password set from READONLY_DB_PASSWORD.")


def cmd_load(cleaned: dict, engine, reload: bool) -> None:
    from utils.load_data import load_all, verify_row_counts

    load_all(cleaned, engine, reload=reload)
    verify_row_counts(engine)


def cmd_embed(reload: bool) -> None:
    from utils.embed_knowledge import embed_knowledge

    embed_knowledge(reload=reload)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Olist ETL Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--step",
        choices=["all", "download", "clean", "schema", "create-user", "load", "embed"],
        default="all",
        help="Which pipeline step to run (default: all)",
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Truncate all tables before loading (only applies to --step load/all)",
    )
    args = parser.parse_args()

    # Steps that need a DB engine
    needs_engine = args.step in ("all", "schema", "create-user", "load")
    engine = None
    if needs_engine:
        from utils.db import get_engine

        try:
            engine = get_engine(readonly=False)
        except RuntimeError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            sys.exit(1)

    cleaned: dict = {}

    try:
        if args.step == "download":
            print("\n[Step 1/4] Downloading dataset ...")
            cmd_download()
        elif args.step == "all":
            if _data_ready():
                print("\n[Step 1/4] Data already present in ./data — skipping download.")
            else:
                print("\n[Step 1/4] CSVs not found in ./data. Attempting Kaggle download ...")
                cmd_download()

        if args.step in ("all", "schema"):
            print("\n[Step 2/4] Applying database schema ...")
            cmd_schema(engine)

        if args.step in ("all", "clean"):
            print("\n[Step 3/4] Cleaning data ...")
            cleaned = cmd_clean()
        elif args.step == "load":
            # Load-only: read from cleaned CSVs on disk
            import pandas as pd

            cleaned_path = Path(CLEANED_DIR)
            if not cleaned_path.exists():
                print(
                    "Error: No cleaned data found. Run --step clean first.",
                    file=sys.stderr,
                )
                sys.exit(1)
            from utils.load_data import LOAD_ORDER

            cleaned = {
                name: pd.read_csv(cleaned_path / f"{name}.csv")
                for name in LOAD_ORDER
                if (cleaned_path / f"{name}.csv").exists()
            }

        if args.step in ("all", "load"):
            print("\n[Step 4/4] Loading into PostgreSQL ...")
            cmd_load(cleaned, engine, reload=args.reload)

        if args.step == "create-user":
            print("\n[Setup] Creating read-only database user ...")
            cmd_create_user(engine)

        if args.step == "embed":
            print("\n[RAG] Embedding KNOWLEDGE.md into ChromaDB ...")
            cmd_embed(reload=args.reload)

        print("\nPipeline finished successfully.")

    except Exception as exc:
        print(f"\nPipeline failed: {exc}", file=sys.stderr)
        raise


if __name__ == "__main__":
    main()
