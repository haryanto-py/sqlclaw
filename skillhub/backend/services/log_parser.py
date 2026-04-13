"""
Parses the queries.log file written by openclaw/skills/query_validator.js.

Log line format:
  [2026-04-12T08:23:14Z] STATUS: ALLOWED | QUERY: SELECT ... | REASON: ...
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

LINE_RE = re.compile(
    r"\[(?P<ts>[^\]]+)\]"
    r"\s*STATUS:\s*(?P<status>ALLOWED|BLOCKED)"
    r"\s*\|\s*QUERY:\s*(?P<query>.+?)"
    r"(?:\s*\|\s*REASON:\s*(?P<reason>.+))?$"
)


@dataclass
class QueryEntry:
    timestamp: str
    status: str
    query: str
    reason: str = ""

    def as_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "status": self.status,
            "query": self.query,
            "reason": self.reason,
        }


def parse_log(log_file: Path) -> list[QueryEntry]:
    """Read and parse the entire query log. Returns newest-first."""
    if not log_file.exists():
        return []

    entries: list[QueryEntry] = []
    for line in log_file.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        m = LINE_RE.match(line)
        if m:
            entries.append(
                QueryEntry(
                    timestamp=m.group("ts"),
                    status=m.group("status"),
                    query=m.group("query").strip(),
                    reason=(m.group("reason") or "").strip(),
                )
            )

    entries.reverse()  # newest first
    return entries


def get_stats(entries: list[QueryEntry]) -> dict:
    total = len(entries)
    blocked = sum(1 for e in entries if e.status == "BLOCKED")
    allowed = total - blocked

    # Count which blocked patterns triggered most
    pattern_counts: dict[str, int] = {}
    for e in entries:
        if e.status == "BLOCKED" and e.reason:
            # Extract the keyword from "Query blocked: matched forbidden pattern /\bDELETE\b/"
            kw_match = re.search(r"\\b(\w+)\\b", e.reason)
            if kw_match:
                kw = kw_match.group(1).upper()
                pattern_counts[kw] = pattern_counts.get(kw, 0) + 1

    top_patterns = sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True)[:5]

    # Queries per hour for the last 24 hours (UTC)
    now = datetime.now(timezone.utc)
    hourly: dict[str, int] = {}
    for e in entries:
        try:
            ts = datetime.fromisoformat(e.timestamp.replace("Z", "+00:00"))
            delta_hours = (now - ts).total_seconds() / 3600
            if delta_hours <= 24:
                hour_label = ts.strftime("%H:00")
                hourly[hour_label] = hourly.get(hour_label, 0) + 1
        except ValueError:
            pass

    return {
        "total": total,
        "allowed": allowed,
        "blocked": blocked,
        "block_rate": round(blocked / total, 4) if total else 0,
        "top_blocked_patterns": [{"pattern": k, "count": v} for k, v in top_patterns],
        "queries_per_hour": [{"hour": k, "count": v} for k, v in sorted(hourly.items())],
    }


def tail_log(log_file: Path, n: int = 100) -> list[str]:
    """Return the last n lines of any log file as raw strings."""
    if not log_file.exists():
        return []
    lines = log_file.read_text(encoding="utf-8", errors="replace").splitlines()
    return lines[-n:]
