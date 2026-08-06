# L7 完成:walk-forward 定案 —— SMA 交叉在 BTC 日线上无 edge

用户于 2026-08-06 跑通 `practice/walkforward.py`:2021-01→2023-09,train=365/test=90 滚动 7 fold,每 fold 重选参数,拼接样本外曲线覆盖 2022 全熊 + 2023 复苏。

## Evidence(用户亲眼看到)
- **运气翻转**:L6 单刀样本外 Sharpe +0.70(test 恰为 2023 复苏,好运)→ walk-forward 拼接 Sharpe **−0.86**,跑输买入持有(−0.28)。用户亲手量出"单次回测不可信"。
- **逐 fold**:7 fold 只 1 个(2022-Q2 崩盘季)跑赢躺平,靠空仓少亏;fold 3/4 横盘季被均线假突破反复收割、亏得最惨。→ 内化"趋势策略只在持续单边暴跌有用,震荡/横盘被收割"。
- **参数漂移 5/7**:每换市场换"最优" → 无跨市场稳定赢家,最优=噪声。
- **公平一面**:walk-forward MaxDD −50.2% vs 买入持有 −66.9%,少痛 ~17 点 → 趋势跟踪唯一兑现的价值是"牺牲收益换更浅回撤",但无收益 edge。

## 最终判决
BTC 日线 2021–2023,SMA 交叉族对买入持有无 edge,不作为赚钱策略推进实盘。用户由此理解:诚实流水线的最大价值 = 在赔钱前给出可信的"别做";多数策略会死在这关,是流水线在工作。

## 里程碑与工具资产
- 完整诚实回测流水线已成型且全部函数化可复用:`strategy.fetch_ohlcv(since=)` / `sma_crossover_signal` → `backtest.backtest` → `metrics`(mdd/sharpe/cagr) → `oos`(train/test + score/sharpe_key + buy&hold) → `walkforward`。
- 评估"关卡"(gauntlet)已就绪:任何新信号只需产出 position 列,即可直接过 backtest→metrics→oos→walkforward 全套。

## 分支决策(待用户选)
- (A) 找真 edge:给 SMA 加 regime 过滤(如 200 日均线之上才做多)或换均值回归/波动率信号,复用整套 gauntlet —— 遵守"没 edge 不上实盘"的纪律。
- (B) L8 纸上交易:把简单策略当载体,学执行/接实时行情的工程管道(工位 4),明确与"策略赚钱"解耦。
- (C) 知识向:为何单资产趋势跟踪易失效、edge 从哪来(多资产/regime 过滤/不同周期)。
- 老师倾向 A(最贴使命的工程下一步、且兑现刚学的纪律),但用户明确想学 paper trading 机制则 B 也正当。
