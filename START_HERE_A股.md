# START HERE: A股科技股研究

如果下次对话没有任何记忆，先读这个文件，再读 `RESTORE_CONTEXT.md`。

## 这是什么

这是一个面向中国 A 股科技股的轻量研究仓库，目标是把可复用的脚本、回测思路、小型数据快照和本次研究结论保存在 GitHub，避免下次重新下载大量数据或重复消耗上下文。

## 当前研究目标

- 看科技股主力资金动态：主力买入还是卖出。
- 多因子选股，而不是只依赖单一因子。
- 形成候选股票、买入卖出信号和轻量回测流程。
- 优先在线查看数据，只保存小型快照和可复现实验脚本。

## 重要边界

- 这是 A 股，不是美股。
- 不要默认下载全市场大历史数据。
- 不要把虚拟环境、Qlib/AlphaGen 源码、大型数据包、API key 或账号凭证提交到仓库。
- 当前回测是轻量版：用当前或快照资金流选候选池，再用历史价量因子做滚动回测；这不是严格逐日历史资金流回放。

## 下次恢复步骤

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/online_tech_monitor.py --top 15
```

轻量回测：

```bash
python scripts/online_tech_backtest.py \
  --start 2025-01-01 \
  --end 2026-06-26 \
  --universe-size 10 \
  --top-k 3 \
  --rebalance-days 5
```

更多细节见：

- `RESTORE_CONTEXT.md`
- `docs/backtest_methodology.md`
- `docs/data_inventory.md`
- `docs/session_notes_2026-06-26.md`
