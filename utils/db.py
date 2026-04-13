import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

load_dotenv(override=True)


def get_engine(readonly: bool = False) -> Engine:
    """
    Returns a SQLAlchemy engine using DATABASE_URL (admin) or READONLY_DB_URL.

    Args:
        readonly: If True, use the read-only connection string.
    """
    env_key = "READONLY_DB_URL" if readonly else "DATABASE_URL"
    url = os.environ.get(env_key)
    if not url:
        raise RuntimeError(f"Environment variable '{env_key}' is not set. Check your .env file.")
    return create_engine(url)


def execute_sql_file(engine: Engine, sql_file: str) -> None:
    """
    Reads a .sql file and executes each statement against the given engine.

    Args:
        engine: SQLAlchemy engine (admin connection).
        sql_file: Path to the .sql file relative to the project root.
    """
    sql_path = Path(sql_file)
    if not sql_path.exists():
        raise FileNotFoundError(f"SQL file not found: {sql_path.resolve()}")

    raw_sql = sql_path.read_text(encoding="utf-8")

    # Split on semicolons, skip blank/comment-only blocks
    statements = [s.strip() for s in raw_sql.split(";") if s.strip()]

    with engine.begin() as conn:
        for stmt in statements:
            conn.execute(text(stmt))

    print(f"Executed {len(statements)} statement(s) from {sql_path.name}")
