# L6 完成:样本外验证,亲历"负过拟合税 = regime 运气"

用户于 2026-08-06 跑通 `practice/oos.py`:2021-01→2023-09 的 BTC 按 70/30 切分(train 700 / test 300,切点 2022-12),在 train 上网格搜 16 组 SMA、按样本内夏普挑冠军,再拿去 test 验一次。

## Evidence(用户看到的关键反直觉现象)
- **过拟合税为负(−0.72)**:train 全部 16 组 Sharpe 为负(-0.02~-0.68),test 全部转正。原因是 regime 不对称:train 含 2022 大熊,test 是 2023 复苏。→ 用户理解"负税不是没过拟合,而是 test 段恰好是更容易的市场;单次切分 = 赌一次 regime 运气"。
- **train 冠军 ≠ test 冠军**:train#1 (30,40)→test 0.70;test 真冠军 (30,60) 在 train 里排 #9;test#2 (5,60) 在 train 里倒数第 2。train 排名几乎反向指路 → 亲证"样本内调参是脆弱的近随机选择"。
- **train Sharpe 全挤在负数窄带** → 当 train 分不开参数时"冠军"≈ 抛硬币。

## 我(老师)的疏漏,已转成教学点
- `oos.py` **漏了买入持有基准**(违反 L5 铁律)。补算:test 段 BTC 17k→27k,买入持有 CAGR ≈ +70%,而 train 冠军 test CAGR 仅 +18.3% → **策略样本外被躺平吊打**。用户由此再次内化"绝对 Sharpe 为正≠有 edge,必须对基准"。→ 待办:给 oos.py 加 buy&hold 行。

## Implications
- 用户已同时掌握 L6 两面:①样本外方法论 ②"单次切分噪声太大、两个方向都不能下结论"。→ 强烈指向 **walk-forward**(滚动多次 train/test 平均掉 regime 运气)。
- 分支决策待用户选:(A) 先给 oos.py 补 buy&hold 基准(快、巩固 L5+L6);(B) 做一节 walk-forward 加课(L6.5);(C) 直接进 L7 paper trading。老师倾向 A→B 再 C:在把策略推向 paper trading 前,先让用户亲手看到单次切分不可信、walk-forward 才靠谱。
- SMA 单一族策略在这套数据上始终跑不赢买入持有 → 后续可考虑引入均值回归/波动率过滤等第二类信号,让"信号库"和评估框架都得到复用。
