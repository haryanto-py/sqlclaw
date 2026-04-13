# OpenClaw Sales Analytics Agent

> An end-to-end AI agent that lets you query a real e-commerce database in plain English via Telegram — complete with charts, daily automated reports, a security audit layer, and a management dashboard.

Built as a portfolio project to demonstrate the full stack of a production-grade AI agent: data engineering, database design, LLM integration, backend API, and a React frontend — all wired together with Docker.

---

## What It Does

You send a message to a Telegram bot. The AI agent translates your question into SQL, validates it against a security layer, runs it against a PostgreSQL database, and replies — in seconds — with a formatted answer or a chart.

**Example conversations:**

> **You:** What are the top 5 product categories by revenue?
>
> **Agent:** Here are the top 5 categories by total revenue:
> 1. Health & Beauty — R$ 1,258,032
> 2. Watches & Gifts — R$ 1,205,120
> ...
> *(sends a bar chart)*

> **You:** Show me monthly order volume for 2017 as a line chart
>
> **Agent:** *(sends a line chart with monthly trend)*

> **You:** What percentage of orders were delivered late?
>
> **Agent:** 8.1% of delivered orders (8,009 of 96,478) arrived after the estimated delivery date.

Every morning at 8:00 AM, the agent automatically sends a daily sales summary without being asked.

---

## Why This Project

Most AI agent demos use toy datasets and fake APIs. This project is different:

- **Real dataset** — 100,000 actual e-commerce orders from Olist (2016–2018), with all the quality issues real data has: missing values, encoding inconsistencies, duplicate keys, unmapped foreign keys, zip codes that lose their leading zeros
- **Real data pipeline** — a multi-step ETL process that cleans and loads 9 related tables with proper FK constraints
- **Real security** — two independent layers prevent the LLM from ever writing to or damaging the database
- **Real observability** — every query the agent runs is logged, auditable, and visible in a dashboard

---

## Architecture

```
You (Telegram)
      │
      ▼
 OpenClaw Agent  ◄──  SOUL.md  (schema + SQL rules + personality)
      │
      ├─ query_validator.js  ←  blocks any write query, logs all attempts
      │
      ├─ postgresql skill    ←  connects as read-only olist_reader user
      │
      └─ send_chart.js       ←  generates PNG charts via Python/matplotlib
             │
             ▼
      chart_generator.py  →  bar / line / pie / heatmap

PostgreSQL (olist_ecommerce)
  └─ 9 tables, ~430K rows total

Skillhub Dashboard (localhost:8000)
  ├─ Dashboard   — live stats, DB row counts, log stream
  ├─ Skills      — registered skill registry
  ├─ Query Logs  — searchable audit trail (ALLOWED / BLOCKED)
  ├─ Security    — blocked query analytics
  └─ Database    — table browser + interactive SQL runner
```

---

## Technical Highlights

### Data Engineering
- **ETL pipeline** (`main.py`) with modular steps: download → clean → schema → load → create-user
- **9-table schema** with proper FK constraints, composite PKs, and 15 indexes
- Handles real data issues: deduplication (1M geolocation rows → 19K unique zip codes), type coercion, unmapped foreign keys, encoding problems
- Idempotent loader with `--reload` flag for safe re-runs

### AI Agent
- Powered by **Claude (Anthropic)** via the OpenClaw framework
- Agent "knows" the full database schema through `SOUL.md` — a structured context file that describes every table, key JOINs, and strict SQL rules
- **ReAct reasoning loop**: the agent plans, validates, queries, and responds in a single turn

### Security (Defense-in-Depth)
Two independent layers, either of which alone would prevent writes:

1. **`query_validator.js`** — intercepts every query before execution. Blocks `INSERT`, `UPDATE`, `DELETE`, `DROP`, `TRUNCATE`, `ALTER`, and more via regex. Logs every attempt with timestamp, status, and reason.
2. **Read-only PostgreSQL user** — `olist_reader` has only `SELECT` privilege. Even if the validator were bypassed, the database rejects writes at the connection level.

### Skillhub Dashboard
- **FastAPI** backend with 5 routers: dashboard stats, query logs, security analytics, skill registry, database explorer
- **React + Tailwind CSS** frontend (Vite)
- **WebSocket** live log streaming — watch the agent's reasoning in real time
- Interactive SQL runner with SELECT-only enforcement

### DevOps & Testing
- **Multi-stage Dockerfile** — Node.js frontend build → Python base → separate `etl` and `skillhub` targets
- **Docker Compose** with profiles: `init` for one-shot ETL, `agent` for OpenClaw, always-on postgres + skillhub
- **50 automated tests** — 27 unit tests (data cleaning logic) + 23 integration tests (all API endpoints)
- **GitHub Actions CI** — lint → unit tests → integration tests → Docker build on every push

---

## Stack

| Layer | Technology |
|---|---|
| Dataset | Olist Brazilian E-Commerce (100K orders, Kaggle) |
| ETL | Python 3.12, pandas, SQLAlchemy, psycopg2 |
| Database | PostgreSQL 17 |
| AI Agent | OpenClaw + Claude (claude-opus-4-6) |
| Messaging | Telegram Bot API |
| Charts | matplotlib, seaborn |
| API | FastAPI, uvicorn |
| Frontend | React 18, Vite, Tailwind CSS, Recharts |
| Packaging | UV (Python), npm |
| Containers | Docker, Docker Compose |
| CI | GitHub Actions |
| Testing | pytest, httpx |
| Linting | ruff |

---

## Project Structure

```
sales-rag/
├── main.py                        # ETL pipeline entry point (argparse)
├── pyproject.toml                 # Python deps + ruff + pytest config
│
├── utils/
│   ├── clean_data.py              # 9 per-table cleaning functions
│   ├── db.py                      # SQLAlchemy engine factory
│   ├── load_data.py               # FK-ordered PostgreSQL loader
│   └── fetch_dataset.py           # Kaggle download helper
│
├── sql/
│   ├── schema.sql                 # DDL: 9 tables, FKs, 15 indexes
│   ├── create_readonly_user.sql   # olist_reader role setup
│   └── drop_all.sql               # Clean-slate tear-down
│
├── openclaw/
│   ├── SOUL.md                    # Agent context: schema + rules + personality
│   ├── openclaw.json              # Config: LLM, Telegram, skills, heartbeat
│   └── skills/
│       ├── query_validator.js     # SQL safety layer + audit logger
│       ├── chart_generator.py     # matplotlib chart renderer
│       └── send_chart.js          # JS wrapper → Python chart generator
│
├── skillhub/
│   ├── backend/                   # FastAPI app (routers + services)
│   └── frontend/                  # React + Tailwind (Vite)
│
├── tests/
│   ├── unit/test_clean_data.py    # 27 tests for ETL cleaning logic
│   └── integration/test_api.py   # 23 tests for all API endpoints
│
├── Dockerfile                     # Multi-stage build
├── docker-compose.yml             # Full stack deployment
└── .github/workflows/ci.yml       # GitHub Actions pipeline
```

---

## Getting Started

### Option A — Docker (recommended)

```bash
# 1. Copy and fill in environment variables
cp .env.example .env

# 2. Place the 9 Olist CSVs into ./data/
#    Download from: https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce

# 3. Start PostgreSQL + Skillhub dashboard
docker compose up -d

# 4. Run ETL (first time only, ~2 minutes)
docker compose --profile init run --rm etl

# 5. Open the dashboard
# http://localhost:8000

# 6. Start the agent (requires Telegram + Anthropic keys in .env)
docker compose --profile agent up -d openclaw
```

### Option B — Local

```bash
git clone <your-repo-url>
cd sales-rag

# Install Python deps
uv sync

# Configure .env (see .env.example)
cp .env.example .env

# Create the database and run ETL
createdb olist_ecommerce
python main.py --step schema
# Place CSVs in ./data/, then:
python main.py
python main.py --step create-user

# Start the dashboard
uvicorn skillhub.backend.main:app --reload

# Install and start the agent
npm install -g openclaw
cd openclaw && npx clawhub@latest install postgresql
openclaw start openclaw.json
```

---

## ETL Pipeline Reference

```bash
python main.py                        # Full pipeline
python main.py --step clean           # Clean raw CSVs only
python main.py --step schema          # Apply DDL only
python main.py --step load            # Load into PostgreSQL
python main.py --step load --reload   # Truncate and reload
python main.py --step create-user     # Create olist_reader role
```

---

## Data Cleaning Notes

The Olist dataset ships with several real-world quality issues:

| Table | Issue | Fix |
|---|---|---|
| `products` | Column name typo (`lenght`) | Renamed at load |
| `products` | `pc_gamer` category not in translation table | Nulled out (unmapped FK) |
| `customers` / `sellers` | Zip codes stored as integers, losing leading zeros | Zero-padded to 5 chars |
| `geolocation` | 1,000,163 rows for 19,010 unique zip codes | Deduplicated (mean lat/lng, mode city/state) |
| `order_reviews` | Duplicate `review_id` across different orders | Composite PK `(review_id, order_id)` |
| All timestamps | Stored as strings | Parsed with `pd.to_datetime(errors='coerce')` |

---

## Dataset

**[Olist Brazilian E-Commerce Public Dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)**
100,000 orders placed on the Olist marketplace between 2016 and 2018. Released under CC BY-NC-SA 4.0.
