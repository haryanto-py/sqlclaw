from fastapi import APIRouter

from skillhub.backend.config import QUERY_LOG
from skillhub.backend.services.log_parser import get_stats, parse_log

router = APIRouter(prefix="/api/security", tags=["security"])


@router.get("/stats")
def security_stats():
    entries = parse_log(QUERY_LOG)
    stats = get_stats(entries)

    blocked_entries = [e.as_dict() for e in entries if e.status == "BLOCKED"]

    return {
        **stats,
        "recent_blocked": blocked_entries[:20],
    }
