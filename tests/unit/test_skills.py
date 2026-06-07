"""
Unit tests for the OpenClaw Agent Skills (openclaw/skills/<name>/).

Covers:
  - the postgresql skill's SQL safety validator (no DB needed)
  - that every skill folder has a SKILL.md manifest + scripts/
  - the chart and export backends actually produce files
"""

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SKILLS_DIR = PROJECT_ROOT / "openclaw" / "skills"
SKILL_NAMES = [
    "postgresql",
    "knowledge_search",
    "send_chart",
    "forecast",
    "rfm_segmentation",
    "export_report",
]


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# query.py imports psycopg2 lazily (only inside execute()), so importing the
# module to test validate() needs no database driver.
query = _load_module(SKILLS_DIR / "postgresql" / "scripts" / "query.py", "skill_query")


class TestQueryValidator:
    def test_allows_select(self):
        ok, _ = query.validate("SELECT COUNT(*) FROM orders")
        assert ok

    def test_allows_with_cte(self):
        ok, _ = query.validate("WITH x AS (SELECT 1 AS n) SELECT n FROM x")
        assert ok

    def test_allows_trailing_semicolon(self):
        ok, _ = query.validate("SELECT 1;")
        assert ok

    @pytest.mark.parametrize(
        "sql",
        [
            "INSERT INTO orders VALUES (1)",
            "UPDATE orders SET status = 'x'",
            "DELETE FROM orders",
            "DROP TABLE orders",
            "TRUNCATE orders",
            "ALTER TABLE orders ADD COLUMN x int",
            "CREATE TABLE t (id int)",
            "GRANT ALL ON orders TO public",
        ],
    )
    def test_blocks_writes_and_ddl(self, sql):
        ok, reason = query.validate(sql)
        assert not ok and reason

    def test_blocks_stacked_statements(self):
        ok, _ = query.validate("SELECT 1; DROP TABLE orders")
        assert not ok

    def test_blocks_empty(self):
        ok, _ = query.validate("   ")
        assert not ok


class TestSkillManifests:
    @pytest.mark.parametrize("name", SKILL_NAMES)
    def test_folder_has_manifest_and_scripts(self, name):
        skill_md = SKILLS_DIR / name / "SKILL.md"
        assert skill_md.exists(), f"{name} is missing SKILL.md"
        text = skill_md.read_text(encoding="utf-8")
        assert "name:" in text and "description:" in text
        assert (SKILLS_DIR / name / "scripts").is_dir()


class TestChartBackend:
    def test_generates_png(self, tmp_path):
        out = tmp_path / "chart.png"
        env = {**os.environ, "OPENCLAW_HOME": str(tmp_path)}
        result = subprocess.run(
            [
                sys.executable,
                str(SKILLS_DIR / "send_chart" / "scripts" / "chart.py"),
                "--type", "bar",
                "--title", "Test",
                "--ylabel", "Count",
                "--data", '[{"label":"a","value":1},{"label":"b","value":2}]',
                "--output", str(out),
            ],
            capture_output=True, text=True, env=env,
        )
        assert result.returncode == 0, result.stderr
        assert out.exists() and out.stat().st_size > 0


class TestExportBackend:
    def test_export_csv(self, tmp_path):
        env = {**os.environ, "OPENCLAW_HOME": str(tmp_path)}
        result = subprocess.run(
            [
                sys.executable,
                str(SKILLS_DIR / "export_report" / "scripts" / "export.py"),
                "--format", "csv",
                "--title", "Report",
                "--data", '[{"category":"a","revenue":100}]',
            ],
            capture_output=True, text=True, env=env,
        )
        assert result.returncode == 0, result.stderr
        payload = json.loads(result.stdout)
        assert payload["success"] and Path(payload["file_path"]).exists()
