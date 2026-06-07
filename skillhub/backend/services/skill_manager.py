"""
Builds the unified skill list for the dashboard.

Skills are folder-based OpenClaw Agent Skills: each lives in
openclaw/skills/<name>/SKILL.md (+ scripts/). openclaw.json's
skills.entries records which are registered/enabled.
"""

from __future__ import annotations

import json
from pathlib import Path

from skillhub.backend.config import PROJECT_ROOT, SKILLS_DIR

OPENCLAW_JSON = PROJECT_ROOT / "openclaw" / "openclaw.json"

# Descriptions for the project's local skills.
LOCAL_DESCRIPTIONS = {
    "postgresql": "Runs read-only SQL (SELECT/WITH only) against PostgreSQL. Validates and blocks write/DDL statements, logs every attempt to queries.log, and returns results as JSON.",
    "knowledge_search": "Semantic search (RAG) over a curated ChromaDB knowledge base for business-metric definitions and dataset context.",
    "send_chart": "Renders bar/line/pie/heatmap charts from query results (matplotlib) and delivers them as PNG images via Telegram.",
    "forecast": "Projects a time series into the future (linear-trend regression) and returns a combined historical + forecast chart.",
    "rfm_segmentation": "Segments customers by Recency, Frequency, and Monetary value, returning segment counts, average spend, and a chart.",
    "export_report": "Exports query results to a downloadable PDF or CSV and sends the file via Telegram.",
}


def _skill_dir_exists(name: str) -> bool:
    """A folder-based skill is present when skills/<name>/SKILL.md exists."""
    return (SKILLS_DIR / name / "SKILL.md").exists()


def get_skills() -> list[dict]:
    skills: list[dict] = []

    # Skills registered in openclaw.json
    configured: dict = {}
    if OPENCLAW_JSON.exists():
        try:
            cfg = json.loads(OPENCLAW_JSON.read_text(encoding="utf-8"))
            configured = cfg.get("skills", {}).get("entries", {})
        except (json.JSONDecodeError, KeyError):
            pass

    seen = set()
    for name, skill in configured.items():
        seen.add(name)
        present = _skill_dir_exists(name)
        skills.append(
            {
                "name": name,
                "type": "local",
                "source": f"./skills/{name}",
                "status": "active" if present else "missing",
                "description": LOCAL_DESCRIPTIONS.get(name, f"Skill '{name}'."),
                "config": skill.get("config", {}),
            }
        )

    # Surface any skill folders on disk that aren't registered in openclaw.json
    if SKILLS_DIR.exists():
        for skill_md in sorted(SKILLS_DIR.glob("*/SKILL.md")):
            name = skill_md.parent.name
            if name not in seen:
                skills.append(
                    {
                        "name": name,
                        "type": "local",
                        "source": f"./skills/{name}",
                        "status": "unregistered",
                        "description": LOCAL_DESCRIPTIONS.get(
                            name, "Local skill folder not yet registered in openclaw.json."
                        ),
                        "config": {},
                    }
                )

    return skills
