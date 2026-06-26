from __future__ import annotations

import argparse
import datetime as dt
import math
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import akshare as ak
import baostock as bs
import numpy as np
import pandas as pd


TECH_KEYWORDS = (
    "半导体",
    "芯片",
    "电子",
    "光学",
    "光电",
    "通信",
    "软件",
    "IT",
    "计算机",
    "互联网",
    "人工智能",
    "数据",
    "云计算",
    "算力",
    "光刻",
    "封装",
    "存储",
    "OLED",
    "LED",
    "PCB",
)


MONEY_COLS = [
    "今日排行榜-主力净占比",
    "今日排行榜-今日涨跌",
    "5日排行榜-主力净占比",
    "5日排行榜-5日涨跌",
    "10日排行榜-主力净占比",
    "10日排行榜-10日涨跌",
]


@dataclass
class BacktestResult:
    total_return: float
    annual_return: float
    max_drawdown: float
    sharpe: float
    win_rate: float
    periods: int
    avg_turnover: float


def retry(name: str, fn: Callable[[], pd.DataFrame], retries: int = 3, sleep_seconds: float = 3) -> pd.DataFrame:
    last_error: Exception | None = None
    for i in range(retries + 1):
        try:
            return fn()
        except Exception as exc:
            last_error = exc
            if i < retries:
                print(f"{name} 查询失败，重试中: {exc}", flush=True)
                time.sleep(sleep_seconds)
    assert last_error is not None
    raise last_error


def to_num(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    df = df.copy()
    for col in cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def match_tech(s: pd.Series) -> pd.Series:
    return s.astype(str).str.contains("|".join(TECH_KEYWORDS), case=False, regex=True, na=False)


def calc_money_score(df: pd.DataFrame) -> pd.DataFrame:
    df = to_num(df, MONEY_COLS)
    today = df["今日排行榜-主力净占比"].fillna(0)
    five = df["5日排行榜-主力净占比"].fillna(0)
    ten = df["10日排行榜-主力净占比"].fillna(0)
    change = df["今日排行榜-今日涨跌"].fillna(0)
    overheat_penalty = (change - 10).clip(lower=0) * 0.6
    weak_trend_penalty = (five < 0).astype(float) * 3 + (ten < 0).astype(float) * 2
    df["资金观察分"] = (today * 0.45 + five * 0.30 + ten * 0.15 - overheat_penalty - weak_trend_penalty).round(2)
    return df.sort_values("资金观察分", ascending=False)


def online_tech_universe(limit: int) -> pd.DataFrame:
    frames = []
    errors = []
    for board_name, symbol in [("科创板", "科创板"), ("创业板", "创业板")]:
        try:
            board = retry(f"{board_name}主力资金", lambda s=symbol: ak.stock_main_fund_flow(symbol=s))
            board = to_num(board, MONEY_COLS)
            frames.append(board[match_tech(board["所属板块"])])
        except Exception as exc:
            errors.append(f"{board_name}: {exc}")

    if not frames:
        repo_root = Path(__file__).resolve().parents[1]
        fallback_files = [
            repo_root / "data_snapshots/tech_money_flow/tech_star_board.csv",
            repo_root / "data_snapshots/tech_money_flow/tech_chinext.csv",
            Path("data_snapshots/tech_money_flow/tech_star_board.csv"),
            Path("data_snapshots/tech_money_flow/tech_chinext.csv"),
            Path("outputs/tech_money_flow/tech_star_board.csv"),
            Path("outputs/tech_money_flow/tech_chinext.csv"),
        ]
        for path in fallback_files:
            if path.exists():
                frames.append(pd.read_csv(path))
        if frames:
            print("在线资金流接口暂时不可用，使用最近一次轻量资金流快照作为候选池。")
        else:
            raise RuntimeError("在线资金流接口不可用，且没有可用候选快照；" + " | ".join(errors))

    if errors:
        print("部分在线资金流接口失败，已使用可用板块继续回测：")
        for err in errors:
            print(f"- {err}")

    stocks = pd.concat(frames, ignore_index=True)
    stocks["代码"] = stocks["代码"].astype(str).str.zfill(6)
    stocks = stocks[~stocks["名称"].astype(str).str.contains("ST", case=False, na=False)]
    stocks = calc_money_score(stocks)
    if limit > 0:
        stocks = stocks.head(limit)
    return stocks.reset_index(drop=True)


def bs_code(code: str) -> str:
    code = str(code).zfill(6)
    if code.startswith(("6", "9")):
        return f"sh.{code}"
    return f"sz.{code}"


def fetch_baostock_daily(code: str, start: str, end: str, retries: int = 3) -> pd.DataFrame:
    fields = "date,code,open,high,low,close,preclose,volume,amount,turn,tradestatus,pctChg,isST"
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            rs = bs.query_history_k_data_plus(
                bs_code(code),
                fields,
                start_date=start,
                end_date=end,
                frequency="d",
                adjustflag="2",
            )
            rows: list[list[str]] = []
            while rs.error_code == "0" and rs.next():
                rows.append(rs.get_row_data())
            if rs.error_code != "0":
                raise RuntimeError(f"{rs.error_code}: {rs.error_msg}")
            df = pd.DataFrame(rows, columns=rs.fields)
            if df.empty:
                return df
            df["date"] = pd.to_datetime(df["date"])
            for col in ["open", "high", "low", "close", "preclose", "volume", "amount", "turn", "tradestatus", "pctChg", "isST"]:
                df[col] = pd.to_numeric(df[col], errors="coerce")
            df = df[(df["tradestatus"] == 1) & (df["isST"] == 0)]
            return df.sort_values("date").reset_index(drop=True)
        except Exception as exc:
            last_error = exc
            if attempt < retries:
                time.sleep(2)
    assert last_error is not None
    raise last_error


def make_panel(price_map: dict[str, pd.DataFrame]) -> pd.DataFrame:
    frames = []
    for code, df in price_map.items():
        if df.empty:
            continue
        part = df[["date", "open", "close", "volume", "turn"]].copy()
        part["code"] = code
        frames.append(part)
    if not frames:
        raise RuntimeError("没有成功取得任何候选股历史行情")
    panel = pd.concat(frames, ignore_index=True)
    return panel.set_index(["date", "code"]).sort_index()


def calc_price_score(panel: pd.DataFrame) -> pd.DataFrame:
    g = panel.groupby(level="code", group_keys=False)
    feat = panel.copy()
    feat["ret20"] = g["close"].pct_change(20)
    feat["ret60"] = g["close"].pct_change(60)
    feat["ma20_gap"] = feat["close"] / g["close"].transform(lambda s: s.rolling(20).mean()) - 1
    feat["ma60_gap"] = feat["close"] / g["close"].transform(lambda s: s.rolling(60).mean()) - 1
    feat["vol20"] = g["close"].pct_change().groupby(level="code", group_keys=False).rolling(20).std().droplevel(0)
    feat["volume_ratio"] = feat["volume"] / g["volume"].transform(lambda s: s.rolling(20).mean()) - 1

    def rank_on_date(s: pd.Series, ascending: bool = True) -> pd.Series:
        return s.groupby(level="date").rank(pct=True, ascending=ascending)

    feat["score"] = (
        rank_on_date(feat["ret20"]) * 0.35
        + rank_on_date(feat["ret60"]) * 0.20
        + rank_on_date(feat["ma20_gap"]) * 0.15
        + rank_on_date(feat["volume_ratio"]) * 0.10
        + rank_on_date(feat["vol20"], ascending=False) * 0.20
    )
    return feat


def position_weights(holdings: list[str]) -> dict[str, float]:
    if not holdings:
        return {}
    w = 1.0 / len(holdings)
    return {code: w for code in holdings}


def turnover(prev: dict[str, float], new: dict[str, float]) -> float:
    keys = set(prev) | set(new)
    return sum(abs(new.get(k, 0.0) - prev.get(k, 0.0)) for k in keys)


def run_backtest(
    feat: pd.DataFrame,
    top_k: int,
    rebalance_days: int,
    cost_rate: float,
) -> tuple[pd.DataFrame, BacktestResult]:
    dates = sorted(feat.index.get_level_values("date").unique())
    if len(dates) < 90:
        raise RuntimeError("历史行情太短，无法计算 60 日因子并回测")

    open_px = feat["open"].unstack("code")
    score = feat["score"].unstack("code")
    start_idx = 65
    signal_indices = list(range(start_idx, len(dates) - rebalance_days - 1, rebalance_days))
    equity = 1.0
    prev_w: dict[str, float] = {}
    rows = []
    period_returns = []
    turnovers = []

    for idx in signal_indices:
        signal_date = dates[idx]
        buy_date = dates[idx + 1]
        sell_date = dates[min(idx + 1 + rebalance_days, len(dates) - 1)]
        daily_scores = score.loc[signal_date].dropna().sort_values(ascending=False)
        holdings = daily_scores.head(top_k).index.tolist()
        if len(holdings) == 0:
            continue
        new_w = position_weights(holdings)
        gross_returns = []
        for code in holdings:
            buy = open_px.at[buy_date, code] if code in open_px.columns else np.nan
            sell = open_px.at[sell_date, code] if code in open_px.columns else np.nan
            if pd.notna(buy) and pd.notna(sell) and buy > 0:
                gross_returns.append(sell / buy - 1)
        if not gross_returns:
            continue
        gross = float(np.mean(gross_returns))
        to = turnover(prev_w, new_w)
        net = gross - to * cost_rate
        equity *= 1 + net
        prev_w = new_w
        period_returns.append(net)
        turnovers.append(to)
        rows.append(
            {
                "signal_date": signal_date.date(),
                "buy_date": buy_date.date(),
                "sell_date": sell_date.date(),
                "holdings": ",".join(holdings),
                "gross_return": gross,
                "turnover": to,
                "net_return": net,
                "equity": equity,
            }
        )

    trades = pd.DataFrame(rows)
    if trades.empty:
        raise RuntimeError("没有形成有效调仓记录")
    eq = trades["equity"]
    dd = eq / eq.cummax() - 1
    n_days = max((pd.Timestamp(trades["sell_date"].iloc[-1]) - pd.Timestamp(trades["buy_date"].iloc[0])).days, 1)
    ann = equity ** (365 / n_days) - 1
    rets = pd.Series(period_returns)
    scaler = math.sqrt(252 / rebalance_days)
    sharpe = 0.0 if rets.std(ddof=0) == 0 else float(rets.mean() / rets.std(ddof=0) * scaler)
    result = BacktestResult(
        total_return=equity - 1,
        annual_return=ann,
        max_drawdown=float(dd.min()),
        sharpe=sharpe,
        win_rate=float((rets > 0).mean()),
        periods=len(trades),
        avg_turnover=float(np.mean(turnovers)),
    )
    return trades, result


def print_result(result: BacktestResult) -> None:
    print("\n## 回测结果")
    print(f"累计收益: {result.total_return:.2%}")
    print(f"年化收益: {result.annual_return:.2%}")
    print(f"最大回撤: {result.max_drawdown:.2%}")
    print(f"夏普(按调仓周期估算): {result.sharpe:.2f}")
    print(f"胜率: {result.win_rate:.2%}")
    print(f"调仓次数: {result.periods}")
    print(f"平均换手: {result.avg_turnover:.2f}")


def main() -> None:
    parser = argparse.ArgumentParser(description="在线科技股轻量回测：只在线查询候选和必要日线，不下载全市场数据。")
    parser.add_argument("--start", default="2024-01-01")
    parser.add_argument("--end", default=str(dt.date.today()))
    parser.add_argument("--universe-size", type=int, default=20)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--rebalance-days", type=int, default=5)
    parser.add_argument("--cost-rate", type=float, default=0.0015)
    parser.add_argument("--show-trades", type=int, default=8)
    args = parser.parse_args()

    print("回测口径:")
    print("- 不下载全市场历史数据库；只在线查询当前科技资金流候选，以及这些候选股的必要日线。")
    print("- 当前资金流只用于生成今天的候选池；历史回测中的每日排名只使用当时已知的价格/成交量因子。")
    print("- 因此这是“当前资金流候选池 + 价格因子滚动回测”，不是完整历史资金流因子的严格回放。")
    print("- 信号日收盘后计算，下一交易日开盘买入；每 N 个交易日调仓；交易成本按换手扣除。")

    universe = online_tech_universe(args.universe_size)
    print("\n## 当前在线资金流候选池")
    print(
        universe[
            ["代码", "名称", "最新价", "所属板块", "资金观察分", "今日排行榜-主力净占比", "5日排行榜-主力净占比", "10日排行榜-主力净占比"]
        ].head(args.universe_size).to_markdown(index=False)
    )

    login = bs.login()
    if login.error_code != "0":
        raise RuntimeError(f"baostock 登录失败: {login.error_code} {login.error_msg}")
    try:
        price_map: dict[str, pd.DataFrame] = {}
        for _, row in universe.iterrows():
            code = str(row["代码"]).zfill(6)
            name = str(row["名称"])
            print(f"在线取日线: {code} {name}", flush=True)
            try:
                price_map[code] = fetch_baostock_daily(code, args.start, args.end)
            except Exception as exc:
                print(f"  跳过 {code}: {exc}", flush=True)
        panel = make_panel(price_map)
        feat = calc_price_score(panel)
        trades, result = run_backtest(feat, args.top_k, args.rebalance_days, args.cost_rate)
    finally:
        bs.logout()

    print_result(result)
    print("\n## 最近调仓记录")
    print(trades.tail(args.show_trades).to_markdown(index=False))

    latest_signal = trades.iloc[-1]
    print("\n## 最新一期持仓信号")
    print(f"信号日: {latest_signal['signal_date']}；执行日: {latest_signal['buy_date']}")
    print(latest_signal["holdings"])


if __name__ == "__main__":
    main()
