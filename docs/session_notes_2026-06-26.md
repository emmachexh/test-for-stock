# Session Notes - 2026-06-26

## What Was Built

- Online tech money-flow monitor.
- Lightweight online backtest script.
- Tech money-flow snapshot from public AKShare interfaces.
- Small CSI300 Baostock sample for field/reference checks.

## Key Findings From Snapshot

At the time of the scan, broad technology money flow was mixed to weak overall, with stronger pockets in optical electronics, military electronics, and electronic chemicals. Several candidate stocks had positive short-term main-fund net inflow ratios.

## Example Lightweight Backtest

Parameters:

- candidate universe: current tech money-flow candidates, top 10
- holdings: top 3
- period: 2025-01-01 to 2026-06-26
- rebalance: every 5 trading days
- transaction cost: 0.15% times turnover

Observed output in the original session:

- total return: 136.04%
- annualized return: 107.65%
- max drawdown: -21.85%
- Sharpe approximation: 1.94
- win rate: 66.67%
- rebalance periods: 57
- average turnover: 0.68

Latest simulated signal from that run:

- signal date: 2026-06-10
- execution date: 2026-06-11
- holdings: 688479, 688141, 688500

Important: this result is candidate-pool validation, not strict historical money-flow replay.
