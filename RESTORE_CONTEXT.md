# Restore Context For Future Sessions

This repository is the persistent state for an A-share stock research conversation.

If a future assistant opens this repo with no memory of the prior chat, start here.

## User Goal

The user wants to research China A-share technology stocks, especially:

- main-fund / institutional-money-flow direction;
- whether main funds are buying or selling;
- multi-factor stock selection rather than one single factor;
- buy/sell signal logic;
- lightweight backtesting;
- reusable data and scripts so future sessions do not repeat setup or waste tokens.

The user explicitly said:

- This is A-share research.
- Do not download a large full historical dataset unless explicitly asked.
- Prefer online data lookup and small reusable snapshots.
- Save all useful files to GitHub because future chat context and local environment may be gone.

## Current Repo Contents

- `scripts/online_tech_monitor.py`
  - Online monitor for A-share tech-sector money flow.
  - Uses AKShare public interfaces.
  - Does not download a full database.

- `scripts/online_tech_backtest.py`
  - Lightweight backtest.
  - Uses current online money-flow ranking or stored snapshot to form a candidate universe.
  - Uses Baostock online daily bars for only the candidate stocks.
  - Does not download full-market history.

- `data_snapshots/tech_money_flow/`
  - Money-flow snapshot generated on 2026-06-26.
  - Includes sector, concept, STAR Market, ChiNext, and filtered tech-stock CSV files.

- `data_snapshots/baostock_csi300_sample/`
  - Small Baostock CSI300 sample, five stocks, used for schema/field checks.

- `data_snapshots/baostock_csi300_partial/`
  - Partial interrupted CSI300 online fetch, not full CSI300.
  - Keep only as a small reference sample.

- `docs/backtest_methodology.md`
  - Explains the current backtest design and limitations.

- `docs/session_notes_2026-06-26.md`
  - Summary of prior session and example backtest result.

## Environment Rebuild

Use a fresh Python environment.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Then run:

```bash
python scripts/online_tech_monitor.py --top 15
```

or:

```bash
python scripts/online_tech_backtest.py \
  --start 2025-01-01 \
  --end 2026-06-26 \
  --universe-size 10 \
  --top-k 3 \
  --rebalance-days 5
```

## Backtest Interpretation

Do not overclaim the existing lightweight backtest.

Current script behavior:

1. Uses current or snapshot money-flow data to create a tech-stock candidate universe.
2. Uses historical price/volume factors inside that candidate universe to run a causal rolling backtest.
3. Buys on the next trading day after the signal date.
4. Rebalances every N trading days.
5. Deducts turnover-based transaction costs.

This is not a strict historical replay of daily money-flow factors. A strict version requires historical money-flow time series for each stock and must build the candidate universe independently on every historical signal date.

## A-Share Notes

Any future work should respect A-share mechanics:

- T+1 trading constraint.
- Daily limit-up / limit-down effects.
- ST stocks should generally be filtered out.
- Liquidity and turnover matter.
- Public "main fund flow" fields are vendor estimates, not exchange-disclosed true account-level capital flow.

## Do Not Commit

Do not commit:

- virtual environments;
- Qlib source tree;
- AlphaGen source tree;
- huge full-market data archives;
- incomplete `qlib_bin.tar.gz` downloads;
- API keys or credentials.
