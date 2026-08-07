# L12:引入第二个信号族(均值回归)—— 路线 A 起步

用户选定路线 **A(回研究端找 edge)**。SMA 单族已判无 edge([[0007-walk-forward-verdict-sma-no-edge]]),继续调参是死路;正确动作是换**信号族**。L12 引入均值回归(mean reversion),作为 SMA 趋势信号的相反赌注。

## 教学要点
- **趋势 vs 均值回归 = 相反下注**:同一根大跌 K 线,趋势止损离场、回归逆势买入。谁对取决于 regime(承 [[0005-scorecard-and-regime-dependence]] 的核心洞察:没有永远对的信号)。
- **z-score 标准化**:`(close - rolling_mean) / rolling_std`,把"贵/便宜"变成跨价位可比的一个数。均值回归的度量。用户想补的统计肌肉,在这里自然长出来。
- **ffill 状态机**:标记进/出场点、中间留 NaN、`.ffill()` 前向填充 = 无 for 循环表达"持有到出场"。通用向量化套路。
- **gauntlet 白捡复用**:新信号 `zscore_reversion_signal` 与 `sma_crossover_signal` 同接口(吃价格表→吐 position 列),L4-L7 全部工具一行不改即可评。L1"一个信号处处复用"的红利兑现。

## 诚实框架(防止用户重蹈覆辙)
反复强调:**单窗口成绩 = 冒烟测试,非判决**。lookback/entry 是两个新旋钮 = 新过拟合面。真正判决是让均值回归过和 SMA 一模一样的 OOS + walk-forward gauntlet(L13)——同样的怀疑、同样的裁判、只换信号,不能双重标准。

## 代码
- `strategy.py` +`zscore_reversion_signal(df, lookback=20, entry=1.0)`:z≤-entry 进场、z≥0 出场、ffill 持有、shift(1) 防前视。**离线合成数据验证过状态机**(两次下探进/持/出正确,position 仅 0/1/NaN)。
- 新 `reversion.py`:同一窗口跑 均值回归 / SMA(20,60) / 买入持有 三方成绩单。
- 词表 +5(信号族/均值回归/z-score/标准化/ffill 状态机)。首选源:Chan《Algorithmic Trading》第2章 + QuantStart 均值回归统计检验。

## 待办 / 下一步
- 用户跑 `reversion.py` 贴三张成绩单 → 一起读(成交笔数/回撤/夏普)→ 定 L13 拿哪组参数进样本外。
- **L13**:均值回归过 OOS + walk-forward gauntlet,给反向赌注一个诚实判决。若同样无 edge → 候选:regime 过滤(震荡市开回归、趋势市开 SMA)或配对交易。
