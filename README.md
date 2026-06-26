# test-for-stock

Lightweight China A-share tech-stock research workspace.

If you are opening this repo in a new chat/session with no memory of prior work, read `RESTORE_CONTEXT.md` first.

This repo is designed to preserve reusable scripts, methodology notes, and small data snapshots so future research sessions can resume without re-downloading large datasets or re-spending context on setup.

## Contents

- `scripts/online_tech_monitor.py`  
  Online tech-stock money-flow monitor. It queries public AKShare interfaces and prints sector/concept/stock rankings.

- `scripts/online_tech_backtest.py`  
  Lightweight online backtest. It avoids full-market historical downloads and only queries daily bars for the current candidate stocks.

- `data_snapshots/tech_money_flow/`  
  Lightweight money-flow CSV snapshots and report generated on 2026-06-26.

- `data_snapshots/baostock_csi300_sample/`  
  Small Baostock CSI300 sample for field/reference checks.

- `data_snapshots/baostock_csi300_partial/`  
  Partial interrupted CSI300 online fetch. This is not full CSI300 history; keep it only as a small schema/data sample.

- `docs/backtest_methodology.md`  
  Backtest assumptions, signal timing, limitations, and strict-vs-lightweight distinction.

- `docs/data_inventory.md`  
  Inventory of saved lightweight data snapshots and excluded large files.

- `docs/session_notes_2026-06-26.md`  
  Notes and example result from the 2026-06-26 research session.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Online Monitor

```bash
python scripts/online_tech_monitor.py --top 15
```

This does not download a full historical database. It queries online public interfaces at runtime.

## Lightweight Backtest

```bash
python scripts/online_tech_backtest.py \
  --start 2025-01-01 \
  --end 2026-06-26 \
  --universe-size 10 \
  --top-k 3 \
  --rebalance-days 5
```

The backtest:

- uses current online money-flow data to define the candidate universe;
- queries only necessary candidate-stock daily bars;
- ranks stocks historically with causal price/volume factors;
- buys on the next trading day after signal generation;
- deducts transaction cost by turnover.

Important: this is not a strict historical replay of money-flow signals. See `docs/backtest_methodology.md`.

## Data Policy

This repo intentionally avoids storing large full-market datasets, virtual environments, Qlib source trees, or incomplete archive downloads. Store only small snapshots and reproducible scripts here.
