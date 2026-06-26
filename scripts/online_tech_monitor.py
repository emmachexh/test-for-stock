from __future__ import annotations

import argparse
import datetime as dt
import time
from typing import Callable

import akshare as ak
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


def retry(name: str, fn: Callable[[], pd.DataFrame], retries: int = 3) -> pd.DataFrame:
    last_error: Exception | None = None
    for i in range(retries + 1):
        try:
            return fn()
        except Exception as exc:
            last_error = exc
            if i < retries:
                print(f"{name} 查询失败，重试中: {exc}", flush=True)
                time.sleep(3)
    assert last_error is not None
    raise last_error


def to_num(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    for col in cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def match_tech(s: pd.Series) -> pd.Series:
    return s.astype(str).str.contains("|".join(TECH_KEYWORDS), case=False, regex=True, na=False)


def md(df: pd.DataFrame, cols: list[str], n: int) -> str:
    if df.empty:
        return "暂无数据"
    return df.head(n)[[c for c in cols if c in df.columns]].to_markdown(index=False)


def calc_stock_score(df: pd.DataFrame) -> pd.DataFrame:
    today = "今日排行榜-主力净占比"
    five = "5日排行榜-主力净占比"
    ten = "10日排行榜-主力净占比"
    change = "今日排行榜-今日涨跌"
    df = df.copy()
    for col in [today, five, ten, change]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    overheat_penalty = (df[change] - 10).clip(lower=0) * 0.6
    weak_trend_penalty = (df[five] < 0).astype(float) * 3 + (df[ten] < 0).astype(float) * 2
    df["在线观察分"] = (
        df[today] * 0.45
        + df[five] * 0.30
        + df[ten] * 0.15
        - overheat_penalty
        - weak_trend_penalty
    ).round(2)
    return df.sort_values("在线观察分", ascending=False)


def main() -> None:
    parser = argparse.ArgumentParser(description="在线查看科技股主力资金流，不下载历史数据。")
    parser.add_argument("--top", type=int, default=15)
    args = parser.parse_args()

    industry = retry("行业资金流", lambda: ak.stock_fund_flow_industry(symbol="即时"))
    concept = retry("概念资金流", lambda: ak.stock_fund_flow_concept(symbol="即时"))
    star = retry("科创板主力", lambda: ak.stock_main_fund_flow(symbol="科创板"))
    chinext = retry("创业板主力", lambda: ak.stock_main_fund_flow(symbol="创业板"))

    industry = to_num(industry, ["行业-涨跌幅", "流入资金", "流出资金", "净额"])
    concept = to_num(concept, ["行业-涨跌幅", "流入资金", "流出资金", "净额"])
    stock_cols = [
        "今日排行榜-主力净占比",
        "今日排行榜-今日涨跌",
        "5日排行榜-主力净占比",
        "5日排行榜-5日涨跌",
        "10日排行榜-主力净占比",
        "10日排行榜-10日涨跌",
    ]
    star = to_num(star, stock_cols)
    chinext = to_num(chinext, stock_cols)

    tech_industry = industry[match_tech(industry["行业"])].sort_values("净额", ascending=False)
    tech_concept = concept[match_tech(concept["行业"])].sort_values("净额", ascending=False)
    tech_stocks = pd.concat(
        [
            star[match_tech(star["所属板块"])],
            chinext[match_tech(chinext["所属板块"])],
        ],
        ignore_index=True,
    )
    tech_stocks = calc_stock_score(tech_stocks)

    print(f"\n在线查询时间: {dt.datetime.now():%Y-%m-%d %H:%M:%S}")
    print("说明: 以下只使用在线公开接口即时查询，不下载历史数据。")

    print("\n## 科技行业资金流")
    print(md(tech_industry, ["行业", "行业-涨跌幅", "流入资金", "流出资金", "净额", "领涨股"], args.top))

    print("\n## 科技概念资金流")
    print(md(tech_concept, ["行业", "行业-涨跌幅", "流入资金", "流出资金", "净额", "领涨股"], args.top))

    print("\n## 科技股在线观察名单")
    print(
        md(
            tech_stocks,
            [
                "代码",
                "名称",
                "最新价",
                "所属板块",
                "在线观察分",
                "今日排行榜-主力净占比",
                "今日排行榜-今日涨跌",
                "5日排行榜-主力净占比",
                "10日排行榜-主力净占比",
            ],
            args.top,
        )
    )


if __name__ == "__main__":
    main()
