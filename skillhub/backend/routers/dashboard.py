from datetime import datetime, timezone

from fastapi import APIRouter

from skillhub.backend.config import QUERY_LOG
from skillhub.backend.services.db_stats import get_db_health, get_table_stats
from skillhub.backend.services.log_parser import get_stats, parse_log

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/stats")
def dashboard_stats():
    entries = parse_log(QUERY_LOG)
    stats = get_stats(entries)
    db_health = get_db_health()

    today = datetime.now(timezone.utc).date().isoformat()
    queries_today = sum(1 for e in entries if e.timestamp.startswith(today))
    blocked_today = sum(
        1 for e in entries if e.timestamp.startswith(today) and e.status == "BLOCKED"
    )

    tables = []
    total_rows = 0
    if db_health["connected"]:
        try:
            tables = get_table_stats()
            total_rows = sum(t["rows"] for t in tables)
        except Exception:
            pass

    return {
        "db_connected": db_health["connected"],
        "db_error": db_health["error"],
        "total_rows": total_rows,
        "queries_today": queries_today,
        "blocked_today": blocked_today,
        "total_queries": stats["total"],
        "total_blocked": stats["blocked"],
        "tables": tables,
        "recent_queries": [e.as_dict() for e in entries[:10]],
    }
