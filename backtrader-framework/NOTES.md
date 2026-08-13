# NOTES — 教学工作笔记(backtrader)

## 用户画像(2026-08-11 建立,继承自隔壁工作区)

- **不是新手。** 隔壁 `learning-projects/quantitative-trading` 已完成 **L1–L23**:
  手搓向量化回测、walk-forward、留出集判决(结论是"不上钱")、执行层四件套
  (生命周期/风控/幂等/部分成交)、perp 杠杆与强平、波动率目标仓位管理、股票日历校准。
- **判断力已经很硬**:会自己预注册判据、会分辨样本内外、会怀疑"三资产一致"不等于独立检验、
  多次用数据反驳老师的说法(见隔壁 [[0025]] [[0027]])。
  → **不能用"这就是回测"的口吻教。要用同行评审的口吻。**
- Python 熟练;pandas 已在隔壁课程边用边学到能改能读;数学一般
- 编辑器 Cursor;终端 zsh

## 教学偏好(继承 + 本课新增)

- 中文讲解,代码/注释用英文;解释简洁直接,不铺垫
- 每课:短、单一目标、可快速完成、有一个"看得见的胜利"
- **本课特有**:每课末尾必须有一栏 **`省了 / 坑了`** 的评估结论(`.verdict` 组件)。
  用户的使命是评估,不是崇拜框架。
- **用户吃"抓 bug"这一套。** 隔壁最值钱的几课都是"在自己代码里抓到一个静默错误"。
  → 本课程的黄金素材 = **框架替你做的默认决定,而它做错了**。
- **不要空谈 API。** 用户选了"系统扫一遍 API",但仍要求每条 API 落到可运行代码。
  系统性体现在 `reference/backtrader-api-map.html` 这张图上,不体现在课堂罗列上。

## 环境实测(2026-08-11,全部亲手跑过,非推测)

- venv: `practice/venv`,**Python 3.14.2**
- `backtrader 1.9.78.123`(官方最后一版,2023-04-19)+ `pandas 3.0.5` + `numpy 2.5.2`
  + `matplotlib 3.11.1` → **端到端跑通,无需打补丁**。比预想的雷少。
- `cerebro.plot(savefig=True)` 在 matplotlib 3.11 上 **PLOT OK**(老教程常说这里会炸,实测没炸)
- 已实测确认的三条框架行为:
  1. **成交时点**:`next()` 里下单 → **下一根 bar 的 open 价成交**(默认 `cheat_on_open=False`)。
     微观实验见 scratchpad `fill.py`;bar#2 close=20.5 下单 → bar#3 open=30.0 成交。
  2. **`SharpeRatio` 默认值撒谎**(2026-08-13 修正,原写"静默返回 None",不准确):
     默认 `timeframe=Years` + `riskfreerate=0.01` + `ddof=0`,算的是
     `mean(年度收益 - 0.01)/std_总体(年度收益)`。数据够长 → 返回一个基于 **n=4**
     个年度样本(含 2 个残年)的数;数据太短 → 返回 `None`。
     **同一个 API,失败模式随数据长度改变**,两种都不报错。
     已逐位复现:手算 0.3130781175 vs 框架 0.3130781174566167。见 [[0002]]。
  3. **`annualize=True` 硬编码 252**(`analyzers/sharpe.py:128`),crypto 7×24 数据上
     系统性虚低 `sqrt(365/252)=1.2035`。实测:框架 −0.6241 vs 手算 ×√365 −0.7511,比值 1.2035。
     **这正是隔壁 [[0027]] 用户刚从自己代码里赶走的那个常数。**

## 课程路线(草案,按"系统扫 API"排,随进展修订)

1. ⏳ **L1 Cerebro 装配线**:八件套一次跑通 + 三条 backtrader 语法怪癖(`[0]`/`[-1]` 索引、
   `params`+`self.p`、指标在 `__init__` 声明)+ 成交时点实验 + Sharpe 静默 None/252 常数。
   ← **已发布,待用户跑**
2. ✅ **L2 Strategy & Indicator**(用户点名要的,与原 L3 合并):五个钩子、
   `minperiod` 传染实验(死代码把 +28.7% 翻成 −11.4%)、自定义 Indicator 两种写法 +
   与 pandas 逐位对拍、ER 闸门的诚实否定结果。← **已发布,待用户跑**
   附产:`reference/sharpe-ratio.html`(回答用户"夏普怎么算")
3. L3 Data Feeds(原 L2 下移):PandasData 列映射、`fromdate/todate`(**L2 已埋伏笔:
   固定起点是 minperiod 传染的解药**)、多数据源 `adddata`、重采样 `resampledata`、
   股票日历与 backtrader 的关系
4. L4 Orders & Broker:市价/限价/止损/StopTrail/**bracket 单**(手搓栈没有)、
   `notify_order` 生命周期 vs 隔壁 L9 的 ccxt 生命周期对照、滑点模型、成交量限制
5. L5 Sizers & 资金核算:`PercentSizer`/自定义 Sizer、把隔壁 L18 的 vol-target 搬进来、
   backtrader 的资金/保证金核算与手搓的差异
6. L6 Analyzers & 对拍:全 analyzer 清单、TimeReturn 导出到 pandas、
   **用 backtrader 复现隔壁的 SMA 结论,数字对不上时定位谁错**
7. L7 optstrategy 参数优化:网格搜索、多进程、**与隔壁 L22"选择方差"的碰撞**——
   框架让扫参数变得太容易,这是特性还是陷阱
8. L8 多标的/横截面:多 data feed、`self.datas` 遍历、排序选股范式(文档薄弱区)
9. L9 评估收官:`reference/framework-scorecard.html` 横向尺子 + 回答 MISSION 的 Open question

## 用户已确认的知识缺口(2026-08-13)

- **不会手推夏普公式**。会用、会怀疑、能读懂结果,但没拆过公式(隔壁 L1–L23 一路在用)。
  → 教学含义:**继承的先验里有空洞,不能默认"绩效指标全部掌握"**。
  下次涉及 Sortino / Calmar / t 统计量时,先问一句再决定要不要展开。
- 已交付 `reference/sharpe-ratio.html` 补上。其中"误差棒"一节(Lo 2002)可能是
  比公式本身更重要的东西——用户此前把 0.4559 当结论看。

## 待确认

- 学习节奏 / 每周可投入时间?
- 是否愿意参与社区(r/algotrading)?
