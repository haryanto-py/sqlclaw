# OpenClaw Sales Analytics Agent

> An end-to-end AI agent that lets you query a real e-commerce database in plain English via Telegram — complete with charts, forecasts, customer segmentation, PDF/CSV exports, a daily automated report, a security audit layer, and a management dashboard.

Built as a portfolio project to demonstrate the full stack of a production-grade AI agent: data engineering, database design, LLM tool-use, a skill/plugin architecture, a backend API, and a React frontend — all wired together with Docker.

---

## What It Does

You send a message to a Telegram bot. The agent translates your question into SQL, runs it (read-only) against a PostgreSQL database through a validated skill, and replies — in seconds — with a formatted answer, a chart, or a downloadable report.

**Example conversations:**

> **You:** What are the top 5 product categories by revenue?
>
> **Agent:**
> 1. Health & Beauty — R$ 1,441,248.07
> 2. Watches & Gifts — R$ 1,305,541.61
> 3. Bed, Bath & Table — R$ 1,241,681.72
> ...

> **You:** Give me a bar chart of revenue for each year
>
> **Agent:** *(sends a bar chart PNG)*

> **You:** Export the top 10 categories as a PDF
>
> **Agent:** *(sends a formatted PDF document)*

> **You:** What is GMV and how is it calculated?
>
> **Agent:** *(answers from the knowledge base — GMV = SUM(price + freight_value)…)*

Every 24 hours the agent automatically sends a daily sales summary without being asked.

---

## Why This Project

Most AI agent demos use toy datasets and fake APIs. This one is different:

- **Real dataset** — 100,000 actual e-commerce orders from Olist (2016–2018), with all the quality issues real data has: missing values, encoding inconsistencies, duplicate keys, unmapped foreign keys, zip codes that lose their leading zeros.
- **Real data pipeline** — a multi-step ETL process that cleans and loads 9 related tables with proper FK constraints.
- **Real security** — two independent layers prevent the LLM from ever writing to or damaging the database.
- **Real observability** — every query the agent runs is logged, auditable, and visible in a dashboard.

---

## Architecture

```
You (Telegram)
      │
      ▼
 OpenClaw Gateway  ── systemPromptOverride: persona + schema + skill commands
      │             (editable source: openclaw/system_prompt.txt)
      │
      ▼  the model uses its exec tool to run a skill's script:
 openclaw/skills/<name>/
   ├── SKILL.md            # manifest: name, description, when-to-use, command
   └── scripts/*.py        # the executable backend

 Skills:
   • postgresql      → query.py    : validates (SELECT-only) + logs + runs read-only SQL
   • knowledge_search→ search.py   : semantic search over a ChromaDB knowledge base (RAG)
   • send_chart      → chart.py    : bar / line / pie / heatmap PNGs (matplotlib)
   • forecast        → forecast.py : linear-trend projection + chart
   • rfm_segmentation→ rfm.py      : Recency/Frequency/Monetary customer segments
   • export_report   → export.py   : PDF / CSV exports

PostgreSQL (olist_ecommerce)          Skillhub Dashboard (localhost:8000)
  └─ 9 tables, ~430K rows               ├─ Dashboard   — live stats, DB health
                                        ├─ Skills      — skill registry
                                        ├─ Query Logs  — audit trail (ALLOWED/BLOCKED)
                                        ├─ Security    — blocked-query analytics
                                        ├─ Database    — table browser + SQL runner
                                        ├─ Gateway     — agent gateway status
                                        └─ Users       — Telegram allowlist
```

Skills follow OpenClaw's **Agent Skills** model: each is a folder with a `SKILL.md` manifest plus a Python backend. The model reads the manifest, then invokes the script through its `exec` tool and sends results (text, images, files) back over Telegram.

---

## Technical Highlights

### Data Engineering
- **ETL pipeline** (`main.py`) with modular steps: download → clean → schema → load → create-user → embed.
- **9-table schema** with proper FK constraints, composite PKs, and indexes.
- Handles real data issues: deduplication (1M geolocation rows → 19K unique zip codes), type coercion, unmapped foreign keys, encoding problems.
- Idempotent loader with `--reload` flag for safe re-runs.

### AI Agent
- Built on the **OpenClaw** agent framework with a **model-agnostic** LLM layer — currently runs `openai/gpt-4o-mini`; swapping to Claude or any other provider is a one-line change in `openclaw/openclaw.json`.
- The agent's persona, the full database schema, the exact skill commands, and the response-formatting rules are supplied through a single system prompt (`openclaw/system_prompt.txt`), so even a small/fast model reliably routes work through the skills.
- **Retrieval-augmented** business context via a local ChromaDB knowledge base (`knowledge_search` skill).

### Security (Defense-in-Depth)
Two independent layers, either of which alone would prevent writes:

1. **Query validator** (in `skills/postgresql/scripts/query.py`) — every query is checked before execution: only a single `SELECT`/`WITH` statement is allowed; `INSERT/UPDATE/DELETE/DROP/ALTER/CREATE/…` and stacked statements are rejected; the connection is opened read-only. Every attempt is logged with timestamp, status, and reason.
2. **Read-only PostgreSQL user** — `olist_reader` has only `SELECT` privilege. Even if the validator were bypassed, the database rejects writes at the connection level.

### Skillhub Dashboard
- **FastAPI** backend (dashboard stats, query logs, security analytics, skill registry, database explorer, gateway status, user allowlist).
- **React + Tailwind CSS** frontend (Vite), with **WebSocket** live log streaming.
- Interactive SQL runner with SELECT-only enforcement.

### DevOps & Testing
- **Multi-stage Dockerfile** and **Docker Compose** (PostgreSQL, one-shot ETL, always-on Skillhub).
- **GitHub Actions CI** — lint (ruff) → unit tests → integration tests → Docker build.
- **pytest** suite covering the ETL cleaning logic, the dashboard API, and the skills (SQL safety validator, chart/export backends).
- **End-to-end test results** — a 39-prompt battery across all six skills plus the security layer, grouped by category, with the actual chart outputs and findings in **[TEST_RESULTS.md](TEST_RESULTS.md)**.

---

## Stack

| Layer | Technology |
|---|---|
| Dataset | Olist Brazilian E-Commerce (100K orders, Kaggle) |
| ETL | Python 3.12, pandas, SQLAlchemy, psycopg2 |
| Database | PostgreSQL |
| AI Agent | OpenClaw (model-agnostic; default `openai/gpt-4o-mini`) |
| Messaging | Telegram Bot API |
| Skills | Python (matplotlib, seaborn, scikit-learn, fpdf2), ChromaDB + sentence-transformers (RAG) |
| API | FastAPI, uvicorn, websockets |
| Frontend | React 18, Vite, Tailwind CSS, Recharts |
| Packaging | uv (Python) |
| Containers | Docker, Docker Compose |
| CI / Lint / Test | GitHub Actions, ruff, pytest |

---

## Project Structure

```
sqlclaw/
├── main.py                          # ETL pipeline entry point (argparse)
├── pyproject.toml                   # Python deps + ruff + pytest config
├── start.ps1                        # Launch the agent with project-local config (Windows)
│
├── utils/                           # ETL helpers
│   ├── clean_data.py                #   per-table cleaning functions
│   ├── db.py                        #   SQLAlchemy engine factory
│   ├── load_data.py                 #   FK-ordered PostgreSQL loader
│   ├── fetch_dataset.py             #   Kaggle download helper
│   └── embed_knowledge.py           #   KNOWLEDGE.md → ChromaDB embeddings
│
├── sql/                             # schema.sql, create_readonly_user.sql, drop_all.sql
│
├── openclaw/
│   ├── openclaw.json                # Agent config: model, Telegram, skills, heartbeat
│   ├── system_prompt.txt            # Editable source of the agent's system prompt
│   ├── SOUL.md / KNOWLEDGE.md       # Schema reference + curated knowledge base
│   └── skills/
│       ├── postgresql/              #   SKILL.md + scripts/query.py
│       ├── knowledge_search/        #   SKILL.md + scripts/search.py
│       ├── send_chart/              #   SKILL.md + scripts/chart.py
│       ├── forecast/                #   SKILL.md + scripts/forecast.py
│       ├── rfm_segmentation/        #   SKILL.md + scripts/rfm.py
│       └── export_report/           #   SKILL.md + scripts/export.py
│
├── skillhub/
│   ├── backend/                     # FastAPI app (routers + services)
│   └── frontend/                    # React + Tailwind (Vite)
│
├── tests/                           # pytest: ETL cleaning + API
├── Dockerfile                       # Multi-stage build
├── docker-compose.yml               # Stack deployment
└── .github/workflows/ci.yml         # GitHub Actions pipeline
```

---

## Getting Started

### 1. Data + database (Docker, recommended)

```bash
cp .env.example .env                       # fill in your values

# Place the 9 Olist CSVs into ./data/
#   https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce

docker compose up -d                       # PostgreSQL + Skillhub dashboard
docker compose --profile init run --rm etl # one-time ETL (~2 min)
# Dashboard → http://localhost:8000
```

Or locally:

```bash
uv sync
createdb olist_ecommerce
python main.py --step schema
python main.py                             # clean + load
python main.py --step create-user          # olist_reader role
python main.py --step embed                 # build the knowledge base
uvicorn skillhub.backend.main:app --reload  # dashboard
```

### 2. The Telegram agent

The agent's config and state stay **scoped to this project** — it never touches a
global `~/.openclaw` config or clashes with other OpenClaw projects.

**Docker (any OS):**

```bash
python main.py --step embed                       # build the RAG knowledge base (once)
docker compose --profile agent up -d --build openclaw
```

The `agent` image bundles the OpenClaw CLI, the project venv, and all the
skill dependencies; it shares the query audit log with the dashboard and
persists sessions in a volume.

**Local (Windows):**

```bash
npm install -g openclaw     # install the OpenClaw CLI (one time)
./start.ps1                  # loads .env, scopes config to this project, runs the gateway
```

`start.ps1` sets `OPENCLAW_HOME` (project root → state in `./.openclaw/`),
`OPENCLAW_CONFIG_PATH` (the repo's `openclaw/openclaw.json`), and puts the venv
on `PATH`, then runs `openclaw gateway run`. Keep the terminal open — the bot
only responds while the gateway is running.

> Run **only one** gateway at a time per bot token (Docker *or* local) — two
> pollers on the same Telegram bot will conflict. Then message your bot.

> Required env: `OPENAI_API_KEY` (or your chosen provider), `TELEGRAM_BOT_TOKEN`,
> `TELEGRAM_ALLOWED_USER_ID` (your numeric Telegram user id — DM [@userinfobot](https://t.me/userinfobot) to find it),
> `READONLY_DB_URL`, `PYTHON_PATH` (path to this project's venv Python).

---

## ETL Pipeline Reference

```bash
python main.py                        # Full pipeline
python main.py --step clean           # Clean raw CSVs only
python main.py --step schema          # Apply DDL only
python main.py --step load            # Load into PostgreSQL
python main.py --step load --reload   # Truncate and reload
python main.py --step create-user     # Create olist_reader role
python main.py --step embed           # Build the ChromaDB knowledge base
```

---

## Adding a Skill

Skills are self-contained folders — to add one:

1. Create `openclaw/skills/<name>/SKILL.md` with YAML frontmatter (`name`, `description`, `metadata.openclaw`) and a body that documents when to use it and the exact command to run.
2. Put the executable backend in `openclaw/skills/<name>/scripts/`.
3. Reference the command in `system_prompt.txt` (so a small model invokes it reliably), then restart the gateway.

Backends that produce files for Telegram write them to `<OPENCLAW_HOME>/.openclaw/media/outbound/`, which is OpenClaw's allowlisted outbound-media directory.

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
