#!/usr/bin/env python
"""
query.py — read-only PostgreSQL executor for the OpenClaw `postgresql` skill.

Defense-in-depth (on top of the read-only DB user):
  1. Rejects any statement that is not a single SELECT / WITH query.
  2. Blocks mutating / DDL keywords and stacked statements.
  3. Logs every attempt (ALLOWED / BLOCKED) to the audit log the Skillhub
     dashboard reads.

Usage:
    python query.py "SELECT ... ;"

Connection string is read from the READONLY_DB_URL environment variable
(so credentials never appear in the process argument list).
Output: a single JSON object on stdout.
  success -> {"success": true, "rowcount": N, "truncated": bool, "rows": [...]}
  failure -> {"error": "..."}  and a non-zero exit code
"""
import os
import re
import sys
import json
from datetime import datetime, timezone

MAX_ROWS = 200  # cap result size so Telegram replies / model context stay sane

# Statements that must never appear in a read-only query.
BLOCKED_PATTERNS = [
    r"\bINSERT\b", r"\bUPDATE\b", r"\bDELETE\b", r"\bDROP\b",
    r"\bTRUNCATE\b", r"\bALTER\b", r"\bCREATE\b", r"\bGRANT\b",
    r"\bREVOKE\b", r"\bEXECUTE\b", r"\bCALL\b", r"\bCOPY\b",
    r"\bMERGE\b", r"\bVACUUM\b", r"\bSET\b",
]


def _log_path():
    # Default is relative to the gateway's working dir (the openclaw/ folder),
    # which resolves to openclaw/logs/queries.log — the file the dashboard reads.
    return os.environ.get("QUERY_LOG_PATH", os.path.join("logs", "queries.log"))


def audit(query, status, reason=""):
    try:
        path = _log_path()
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        ts = datetime.now(timezone.utc).isoformat()
        one_line = re.sub(r"\s+", " ", query).strip()
        parts = [f"[{ts}]", f"STATUS: {status}", f"QUERY: {one_line}"]
        if reason:
            parts.append(f"REASON: {reason}")
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(" | ".join(parts) + "\n")
    except Exception:
        pass  # never let logging crash the query


def validate(sql):
    """Return (ok, reason). Allows a single SELECT/WITH statement only."""
    stripped = sql.strip().rstrip(";").strip()
    if not stripped:
        return False, "Empty query."

    # Reject stacked statements (anything after the first ';').
    if ";" in stripped:
        return False, "Multiple statements are not allowed."

    head = re.sub(r"^\s*(--[^\n]*\n|/\*.*?\*/)\s*", "", stripped, flags=re.S).lstrip()
    if not re.match(r"(?is)^(SELECT|WITH)\b", head):
        return False, "Only SELECT / WITH queries are permitted."

    for pat in BLOCKED_PATTERNS:
        if re.search(pat, stripped, flags=re.IGNORECASE):
            return False, f"Query blocked: matched forbidden keyword /{pat}/"

    return True, ""


def execute(conn_str, query):
    import psycopg2
    from psycopg2.extras import RealDictCursor

    conn = psycopg2.connect(conn_str)
    try:
        # Read-only transaction as a third safety layer.
        conn.set_session(readonly=True, autocommit=False)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(query)
        rows = cur.fetchall() if cur.description else []
        truncated = len(rows) > MAX_ROWS
        return {
            "success": True,
            "rowcount": len(rows),
            "truncated": truncated,
            "rows": rows[:MAX_ROWS],
        }
    finally:
        conn.close()


def main():
    if len(sys.argv) < 2 or not sys.argv[1].strip():
        print(json.dumps({"error": "Usage: query.py \"SELECT ...\""}))
        sys.exit(1)

    query = sys.argv[1]
    conn_str = os.environ.get("READONLY_DB_URL")
    if not conn_str:
        print(json.dumps({"error": "READONLY_DB_URL environment variable is not set."}))
        sys.exit(1)

    ok, reason = validate(query)
    if not ok:
        audit(query, "BLOCKED", reason)
        print(json.dumps({"error": reason, "blocked": True}))
        sys.exit(1)

    audit(query, "ALLOWED")
    try:
        result = execute(conn_str, query)
    except Exception as exc:  # noqa: BLE001 - surface DB errors to the agent
        print(json.dumps({"error": f"PostgreSQL query failed: {exc}"}))
        sys.exit(1)

    print(json.dumps(result, default=str))


if __name__ == "__main__":
    main()
