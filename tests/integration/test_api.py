"""
Integration tests for the Skillhub FastAPI backend.

Services (log_parser, db_stats, skill_manager) are patched so tests
run without a live database or log files on disk.
"""

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from skillhub.backend.main import app

client = TestClient(app)

# ── Shared mock data ──────────────────────────────────────────────────────────

MOCK_ENTRIES = [
    MagicMock(
        timestamp="2026-04-12T08:00:00Z",
        status="ALLOWED",
        query="SELECT * FROM orders LIMIT 10",
        reason="",
        as_dict=lambda: {
            "timestamp": "2026-04-12T08:00:00Z",
            "status": "ALLOWED",
            "query": "SELECT * FROM orders LIMIT 10",
            "reason": "",
        },
    ),
    MagicMock(
        timestamp="2026-04-12T09:00:00Z",
        status="BLOCKED",
        query="DELETE FROM orders",
        reason="Query blocked: matched forbidden pattern /\\bDELETE\\b/",
        as_dict=lambda: {
            "timestamp": "2026-04-12T09:00:00Z",
            "status": "BLOCKED",
            "query": "DELETE FROM orders",
            "reason": "Query blocked: matched forbidden pattern /\\bDELETE\\b/",
        },
    ),
]

MOCK_STATS = {
    "total": 2,
    "allowed": 1,
    "blocked": 1,
    "block_rate": 0.5,
    "top_blocked_patterns": [{"pattern": "DELETE", "count": 1}],
    "queries_per_hour": [{"hour": "09:00", "count": 1}],
}

MOCK_TABLES = [
    {
        "name": "orders",
        "rows": 99441,
        "size": "12 MB",
        "sample_query": "SELECT order_status, COUNT(*) FROM orders GROUP BY order_status",
    },
    {"name": "customers", "rows": 99441, "size": "8 MB", "sample_query": ""},
    {"name": "order_items", "rows": 112650, "size": "15 MB", "sample_query": ""},
]

MOCK_SKILLS = [
    {
        "name": "query_validator",
        "type": "local",
        "source": "./skills/query_validator.js",
        "status": "active",
        "description": "Validates SQL queries.",
        "config": {},
    },
    {
        "name": "postgresql",
        "type": "clawhub",
        "source": "clawhub:postgresql",
        "status": "active",
        "description": "PostgreSQL skill.",
        "config": {"connectionString": "${READONLY_DB_URL}"},
    },
]


# ── /api/dashboard/stats ──────────────────────────────────────────────────────


class TestDashboardStats:
    def _patch(self):
        return [
            patch("skillhub.backend.routers.dashboard.parse_log", return_value=MOCK_ENTRIES),
            patch("skillhub.backend.routers.dashboard.get_stats", return_value=MOCK_STATS),
            patch(
                "skillhub.backend.routers.dashboard.get_db_health",
                return_value={"connected": True, "error": None},
            ),
            patch("skillhub.backend.routers.dashboard.get_table_stats", return_value=MOCK_TABLES),
        ]

    def test_returns_200(self):
        with (
            patch("skillhub.backend.routers.dashboard.parse_log", return_value=MOCK_ENTRIES),
            patch("skillhub.backend.routers.dashboard.get_stats", return_value=MOCK_STATS),
            patch(
                "skillhub.backend.routers.dashboard.get_db_health",
                return_value={"connected": True, "error": None},
            ),
            patch("skillhub.backend.routers.dashboard.get_table_stats", return_value=MOCK_TABLES),
        ):
            res = client.get("/api/dashboard/stats")
        assert res.status_code == 200

    def test_response_shape(self):
        with (
            patch("skillhub.backend.routers.dashboard.parse_log", return_value=MOCK_ENTRIES),
            patch("skillhub.backend.routers.dashboard.get_stats", return_value=MOCK_STATS),
            patch(
                "skillhub.backend.routers.dashboard.get_db_health",
                return_value={"connected": True, "error": None},
            ),
            patch("skillhub.backend.routers.dashboard.get_table_stats", return_value=MOCK_TABLES),
        ):
            data = client.get("/api/dashboard/stats").json()
        assert "db_connected" in data
        assert "total_rows" in data
        assert "total_queries" in data
        assert "tables" in data
        assert "recent_queries" in data

    def test_db_offline_still_returns_200(self):
        with (
            patch("skillhub.backend.routers.dashboard.parse_log", return_value=[]),
            patch(
                "skillhub.backend.routers.dashboard.get_stats",
                return_value={**MOCK_STATS, "total": 0},
            ),
            patch(
                "skillhub.backend.routers.dashboard.get_db_health",
                return_value={"connected": False, "error": "connection refused"},
            ),
        ):
            res = client.get("/api/dashboard/stats")
        assert res.status_code == 200
        assert res.json()["db_connected"] is False


# ── /api/skills ───────────────────────────────────────────────────────────────


class TestSkills:
    def test_returns_200(self):
        with patch("skillhub.backend.routers.skills.get_skills", return_value=MOCK_SKILLS):
            res = client.get("/api/skills")
        assert res.status_code == 200

    def test_returns_skills_list(self):
        with patch("skillhub.backend.routers.skills.get_skills", return_value=MOCK_SKILLS):
            data = client.get("/api/skills").json()
        assert "skills" in data
        assert len(data["skills"]) == 2

    def test_skill_has_required_fields(self):
        with patch("skillhub.backend.routers.skills.get_skills", return_value=MOCK_SKILLS):
            skill = client.get("/api/skills").json()["skills"][0]
        for field in ("name", "type", "source", "status", "description"):
            assert field in skill


# ── /api/logs/queries ─────────────────────────────────────────────────────────


class TestQueryLogs:
    def test_returns_200(self):
        with patch("skillhub.backend.routers.logs.parse_log", return_value=MOCK_ENTRIES):
            res = client.get("/api/logs/queries")
        assert res.status_code == 200

    def test_pagination_fields_present(self):
        with patch("skillhub.backend.routers.logs.parse_log", return_value=MOCK_ENTRIES):
            data = client.get("/api/logs/queries").json()
        assert "total" in data
        assert "page" in data
        assert "limit" in data
        assert "entries" in data

    def test_filter_by_blocked(self):
        with patch("skillhub.backend.routers.logs.parse_log", return_value=MOCK_ENTRIES):
            data = client.get("/api/logs/queries?status=BLOCKED").json()
        assert all(e["status"] == "BLOCKED" for e in data["entries"])

    def test_filter_by_allowed(self):
        with patch("skillhub.backend.routers.logs.parse_log", return_value=MOCK_ENTRIES):
            data = client.get("/api/logs/queries?status=ALLOWED").json()
        assert all(e["status"] == "ALLOWED" for e in data["entries"])

    def test_search_filters_by_query_text(self):
        with patch("skillhub.backend.routers.logs.parse_log", return_value=MOCK_ENTRIES):
            data = client.get("/api/logs/queries?search=DELETE").json()
        assert len(data["entries"]) == 1
        assert "DELETE" in data["entries"][0]["query"]

    def test_invalid_status_returns_422(self):
        with patch("skillhub.backend.routers.logs.parse_log", return_value=MOCK_ENTRIES):
            res = client.get("/api/logs/queries?status=INVALID")
        assert res.status_code == 422


# ── /api/security/stats ───────────────────────────────────────────────────────


class TestSecurityStats:
    def test_returns_200(self):
        with patch("skillhub.backend.routers.security.parse_log", return_value=MOCK_ENTRIES):
            res = client.get("/api/security/stats")
        assert res.status_code == 200

    def test_response_has_counts(self):
        with patch("skillhub.backend.routers.security.parse_log", return_value=MOCK_ENTRIES):
            data = client.get("/api/security/stats").json()
        assert "total" in data
        assert "allowed" in data
        assert "blocked" in data
        assert "block_rate" in data

    def test_recent_blocked_present(self):
        with patch("skillhub.backend.routers.security.parse_log", return_value=MOCK_ENTRIES):
            data = client.get("/api/security/stats").json()
        assert "recent_blocked" in data
        assert all(e["status"] == "BLOCKED" for e in data["recent_blocked"])


# ── /api/database/tables ──────────────────────────────────────────────────────


class TestDatabaseTables:
    def test_returns_200(self):
        with (
            patch(
                "skillhub.backend.routers.database.get_db_health",
                return_value={"connected": True, "error": None},
            ),
            patch("skillhub.backend.routers.database.get_table_stats", return_value=MOCK_TABLES),
        ):
            res = client.get("/api/database/tables")
        assert res.status_code == 200

    def test_returns_tables_list(self):
        with (
            patch(
                "skillhub.backend.routers.database.get_db_health",
                return_value={"connected": True, "error": None},
            ),
            patch("skillhub.backend.routers.database.get_table_stats", return_value=MOCK_TABLES),
        ):
            data = client.get("/api/database/tables").json()
        assert "tables" in data
        assert len(data["tables"]) == 3

    def test_db_offline_returns_503(self):
        with patch(
            "skillhub.backend.routers.database.get_db_health",
            return_value={"connected": False, "error": "refused"},
        ):
            res = client.get("/api/database/tables")
        assert res.status_code == 503


# ── /api/database/query ───────────────────────────────────────────────────────


class TestDatabaseQuery:
    MOCK_RESULT = MagicMock()

    def _mock_engine(self):
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_result = MagicMock()
        mock_result.keys.return_value = ["order_status", "total"]
        mock_result.fetchmany.return_value = [("delivered", 96478), ("canceled", 625)]
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.execute = MagicMock(return_value=mock_result)
        mock_engine.connect = MagicMock(return_value=mock_conn)
        return mock_engine

    def test_select_returns_200(self):
        with patch(
            "skillhub.backend.routers.database._get_engine", return_value=self._mock_engine()
        ):
            res = client.post(
                "/api/database/query",
                json={"sql": "SELECT order_status, COUNT(*) FROM orders GROUP BY 1"},
            )
        assert res.status_code == 200

    def test_select_response_has_columns_and_rows(self):
        with patch(
            "skillhub.backend.routers.database._get_engine", return_value=self._mock_engine()
        ):
            data = client.post("/api/database/query", json={"sql": "SELECT 1"}).json()
        assert "columns" in data
        assert "rows" in data
        assert "count" in data

    def test_non_select_returns_400(self):
        res = client.post("/api/database/query", json={"sql": "DELETE FROM orders"})
        assert res.status_code == 400

    def test_empty_sql_returns_400(self):
        res = client.post("/api/database/query", json={"sql": ""})
        assert res.status_code == 400

    def test_missing_sql_key_returns_400(self):
        res = client.post("/api/database/query", json={})
        assert res.status_code == 400
