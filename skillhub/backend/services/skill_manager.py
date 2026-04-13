"""
Reads the skills registry from openclaw/openclaw.json and the local skills
directory to produce a unified skill list for the dashboard.
"""

from __future__ import annotations

import json
from pathlib import Path

from skillhub.backend.config import PROJECT_ROOT, SKILLS_DIR

OPENCLAW_JSON = PROJECT_ROOT / "openclaw" / "openclaw.json"

# Descriptions for known local skills
LOCAL_DESCRIPTIONS = {
    "query_validator": "Validates every SQL query before execution. Blocks INSERT, UPDATE, DELETE, DROP and other write statements. Logs all attempts to queries.log.",
    "send_chart": "Generates charts (bar, line, pie, heatmap) from query results using matplotlib and delivers them as PNG images via Telegram.",
    "chart_generator": "Python script invoked by send_chart. Renders charts using matplotlib/seaborn and saves them as PNG files.",
}


def _file_exists(filename: str) -> bool:
    return (SKILLS_DIR / filename).exists()


def get_skills() -> list[dict]:
    skills: list[dict] = []

    # Parse openclaw.json for configured skills
    configured: list[dict] = []
    if OPENCLAW_JSON.exists():
        try:
            cfg = json.loads(OPENCLAW_JSON.read_text(encoding="utf-8"))
            configured = cfg.get("skills", [])
        except (json.JSONDecodeError, KeyError):
            pass

    seen = set()
    for skill in configured:
        name = skill.get("name", "unknown")
        source = skill.get("source", "")
        seen.add(name)

        is_local = source.startswith("./")
        skill_file = source.lstrip("./") if is_local else None
        file_ok = _file_exists(Path(skill_file).name) if skill_file else True

        skills.append(
            {
                "name": name,
                "type": "local" if is_local else "clawhub",
                "source": source,
                "status": "active" if file_ok else "missing",
                "description": LOCAL_DESCRIPTIONS.get(name, f"Skill loaded from {source}"),
                "config": skill.get("config", {}),
            }
        )

    # Also surface any .js files in skills/ that aren't in openclaw.json
    if SKILLS_DIR.exists():
        for f in sorted(SKILLS_DIR.glob("*.js")):
            name = f.stem
            if name not in seen:
                skills.append(
                    {
                        "name": name,
                        "type": "local",
                        "source": f"./skills/{f.name}",
                        "status": "unregistered",
                        "description": LOCAL_DESCRIPTIONS.get(
                            name, "Local skill not yet registered in openclaw.json."
                        ),
                        "config": {},
                    }
                )

    return skills
