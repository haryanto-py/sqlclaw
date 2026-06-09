# SQLClaw — Skill Benchmark & End-to-End Test

A reproducible benchmark that exercises **every agent skill** plus the security
layer, used to validate the framework end-to-end.

Each question maps to the skill(s) it should trigger and an expected outcome.
Run it two ways:

- **Telegram** — message the bot (`@OlistEcommerce_bot`) directly. This is the
  true end-to-end path (it includes delivering images/files back to the user).
- **Headless** — drive the running gateway without Telegram:
  ```bash
  openclaw agent --agent main --session-id bench1 -m "<question>"
  ```
  (Use a fresh `--session-id` per question so prior turns don't bias the model.)

> Dataset: Olist Brazilian E-Commerce (2016–2018). Figures below are the actual
> values in the loaded database (~99,441 orders).

---

## Benchmark suite

| # | Question | Skill exercised | Expected outcome |
|---|----------|-----------------|------------------|
| 1 | How many orders are there by status? | `postgresql` (GROUP BY) | Counts per status; total 99,441 |
| 2 | What are the top 5 product categories by revenue? | `postgresql` (3-table JOIN) | Ranked categories with BRL revenue |
| 3 | What percentage of payments are made with credit card? | `postgresql` (aggregate %) | ~73.9% |
| 4 | Which 5 states have the most customers? | `postgresql` (GROUP BY + ORDER) | SP, RJ, MG, … |
| 5 | What is GMV and how is it calculated? | `knowledge_search` (RAG) | Definition: `SUM(price + freight_value)` |
| 6 | Give me a bar chart of revenue for each year | `postgresql` + `send_chart` | PNG bar chart delivered |
| 7 | Forecast total revenue for the next 3 months | `postgresql` + `forecast` | Trend chart + 3 projected values |
| 8 | Run an RFM customer segmentation and summarize the segments | `rfm_segmentation` | Segment counts + chart |
| 9 | Export the top 10 product categories by revenue as a PDF | `postgresql` + `export_report` | PDF document delivered |
| 10 | Delete all canceled orders from the database | **security validator** | Blocked — read-only; refuses |

---

## Results

### A. Per-skill functional verification — PASS

Verified with the real database (values are live query results):

| Skill | Evidence | Status |
|-------|----------|--------|
| `postgresql` | Orders by status → **99,441** (delivered 96,478 · shipped 1,107 · canceled 625 · unavailable 609 · invoiced 314 · processing 301 · created 5 · approved 2) | ✅ |
| `postgresql` (JOINs) | Top categories by revenue → health_beauty **R$ 1,441,248.07**, watches_gifts R$ 1,305,541.61, bed_bath_table R$ 1,241,681.72, sports_leisure R$ 1,156,656.48, computers_accessories R$ 1,059,272.40 | ✅ |
| `postgresql` (aggregate) | Credit-card payment share → **73.90%** (76,795 / 103,886) | ✅ |
| `knowledge_search` | "What is GMV?" → returns the curated definition (`SUM(price + freight_value)`) from the ChromaDB knowledge base | ✅ |
| `send_chart` | Bar chart of revenue by year (2016 R$ 57,183.21 · 2017 R$ 7,142,672.43 · 2018 R$ 8,643,697.60) → PNG generated and delivered on Telegram | ✅ |
| `forecast` | Monthly series → linear-trend projection + combined historical/forecast chart | ✅ |
| `rfm_segmentation` | Full customer base segmented → Promising/Recent 45,298 · Standard/Low 23,760 · High-Value Churned 21,668 · Champions 1,379 · At-Risk 1,252 | ✅ |
| `export_report` | Top categories → PDF generated and delivered on Telegram | ✅ |

### B. Security (#10) — PASS

`"Delete all canceled orders"` and other write/DDL attempts are rejected by the
validator in `query.py` before execution (single-SELECT-only; `INSERT/UPDATE/
DELETE/DROP/ALTER/CREATE`/stacked statements blocked), and the database
connection is read-only as a second layer. Covered by automated tests in
`tests/unit/test_skills.py`.

---

## Environment & runtime findings

### Local (Windows, `start.ps1`) — PASS
The full loop works: natural language → SQL/skill → real data → formatted reply,
including chart and PDF delivery over Telegram (user-confirmed). Charts/exports
land in `<OPENCLAW_HOME>/.openclaw/media/outbound/` and are sent via the message
tool.

### Docker — skills verified; full agent loop is resource-sensitive
With the compose stack (`postgres` + `etl` + `openclaw`):
- ETL loaded all 9 tables into the containerized Postgres (99,441 orders).
- The agent image builds and runs OpenClaw 2026.5.7, and **each skill executes
  correctly when invoked directly in the container** (`query.py` → 99,441;
  `search.py` → GMV; `chart.py` → PNG).
- However, the OpenClaw **gateway is CPU-intensive**. On a host under load the
  WSL2 VM degraded to where even a trivial `python` startup stalled; OpenClaw's
  `exec` tool then **backgrounds** the slow skill command, and `gpt-4o-mini`
  abandons it after a couple of polls instead of waiting — so the agent reports
  a generic "technical issue."

**This is an environment/resource limitation, not a code defect** — the identical
image runs the skills correctly when the host is healthy, and the same agent
logic works end-to-end locally.

### Note: `gpt-4o-mini` + OpenClaw `exec` yielding
`gpt-4o-mini` does not reliably wait for a backgrounded `exec` command; it tends
to re-issue the command and give up. A stronger model (e.g. `gpt-4o` / Claude)
follows the poll-until-done protocol more patiently.

---

## Recommendations
- **Give Docker headroom**: ensure the WSL2/Docker VM has ample CPU + disk I/O,
  and avoid running the build and the agent under heavy host load simultaneously.
- **Keep the interpreter warm**: the first skill call after a cold start pays the
  venv-python startup cost; a warm-up call removes the first-call stall.
- **Model choice**: use `gpt-4o-mini` for cost; switch to a stronger model when
  reliability on multi-step skills (chart/forecast/export) matters.
- **Run one gateway per bot token** (Docker *or* local) to avoid Telegram
  polling conflicts.

---

## Reproduce

```bash
# 1. Data + DB + agent (see README "Getting Started")
python main.py --step embed
docker compose up -d postgres
docker compose --profile init run --rm etl
docker compose --profile agent up -d --build openclaw

# 2. Run the suite headlessly (one fresh session per question)
docker compose exec openclaw openclaw agent --agent main --session-id b1 \
  -m "How many orders are there by status?"
# … repeat for questions 2–10

# Or simply message @OlistEcommerce_bot on Telegram.
```
