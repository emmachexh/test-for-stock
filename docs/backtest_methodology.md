# Backtest Methodology

This repository stores a lightweight, reusable stock research state for online A-share tech-stock monitoring.

## Current Design

The current workflow avoids downloading a full historical market database.

1. Query current tech-stock money-flow rankings online.
2. Build a candidate universe from STAR Market and ChiNext stocks whose sector labels match technology keywords.
3. Score candidates with current money-flow fields:
   - today's main-fund net inflow ratio
   - 5-day main-fund net inflow ratio
   - 10-day main-fund net inflow ratio
   - overheating penalty for very large same-day gains
4. For lightweight backtesting, query only the candidate stocks' necessary historical daily bars online.
5. During the historical backtest, rank stocks using only price/volume features available at each signal date.
6. Execute at the next trading day's open and rebalance every N trading days.
7. Deduct transaction cost based on turnover.

## Important Limitation

The current backtest is not a full historical replay of the money-flow strategy.

The current money-flow snapshot is used to define today's candidate universe. Historical rebalancing uses causal price/volume factors within that candidate universe. This is useful for checking whether the current candidate pool has had tradable historical behavior, but it is not equivalent to replaying historical money-flow signals day by day.

A strict version requires reliable historical money-flow time series for each stock and should generate the universe and scores independently on each historical signal date.

## Default Backtest Rules

- Signal date: after close
- Execution: next trading day's open
- Rebalance frequency: every 5 trading days
- Position count: configurable Top K
- Weighting: equal weight
- Transaction cost: `cost_rate * turnover`
- Risk metrics:
  - total return
  - annualized return
  - max drawdown
  - Sharpe ratio approximation
  - win rate
  - average turnover

## Why This Is Stored

The goal is to avoid repeating setup and exploratory work in future sessions. The stored files include scripts and lightweight snapshots, not large historical databases.
