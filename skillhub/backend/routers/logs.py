import asyncio

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from skillhub.backend.config import OPENCLAW_LOG, QUERY_LOG
from skillhub.backend.services.log_parser import parse_log, tail_log

router = APIRouter(prefix="/api/logs", tags=["logs"])


@router.get("/queries")
def query_logs(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    status: str = Query("all", pattern="^(all|ALLOWED|BLOCKED)$"),
    search: str = Query(""),
):
    entries = parse_log(QUERY_LOG)

    if status != "all":
        entries = [e for e in entries if e.status == status]
    if search:
        search_lower = search.lower()
        entries = [e for e in entries if search_lower in e.query.lower()]

    total = len(entries)
    start = (page - 1) * limit
    page_entries = entries[start : start + limit]

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "entries": [e.as_dict() for e in page_entries],
    }


@router.websocket("/ws/live")
async def live_logs(websocket: WebSocket):
    """
    Streams new lines from openclaw.log in real time.
    Sends existing tail on connect, then polls for new lines every second.
    """
    await websocket.accept()
    log_file = OPENCLAW_LOG

    # Send last 50 lines immediately on connect
    existing = tail_log(log_file, n=50)
    for line in existing:
        await websocket.send_text(line)

    # Track file size to detect new writes
    last_size = log_file.stat().st_size if log_file.exists() else 0

    try:
        while True:
            await asyncio.sleep(1)
            if not log_file.exists():
                continue
            current_size = log_file.stat().st_size
            if current_size > last_size:
                # Read only the new bytes
                with open(log_file, "rb") as f:
                    f.seek(last_size)
                    new_data = f.read(current_size - last_size)
                for line in new_data.decode("utf-8", errors="replace").splitlines():
                    if line.strip():
                        await websocket.send_text(line)
                last_size = current_size
    except WebSocketDisconnect:
        pass
