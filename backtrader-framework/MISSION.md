# Mission: backtrader 框架评估与掌握

## Why

用户**已经手搓了一整套量化系统**(见隔壁 `learning-projects/quantitative-trading`,已完成 L1–L23):
自建向量化回测、walk-forward、留出集判决、执行层(幂等/部分成交/追单)、perp 杠杆、
波动率目标仓位管理。手搓栈已经跑出过真实结论——包括一个"不上钱"的诚实否定判决。

所以本使命**不是**"学会回测"。是:

> **摸清 backtrader 的完整能力面,判断它值不值得进我的工具箱;
> 并在这个过程中造出一把能横向对比其他框架(vectorbt / backtesting.py /
> zipline-reloaded / nautilus_trader)的尺子。**

核心动机是**提速研究、少造轮子**——不想再自己写指标、Analyzer、参数优化器。
但用户的判断标准很硬:框架省下的时间,不能用"看不见的假设"来换。

## Success looks like

- 能不查文档写出一个完整的 backtrader 回测:Cerebro / Data Feed / Strategy /
  Indicator / Order / Sizer / Broker / Analyzer 八件套各就各位
- 能说清 backtrader 的**执行模型**与手搓向量化栈的差异(成交时点、成交价、
  资金与保证金核算),并知道差异会往哪个方向改变结论
- 能把手搓栈已验证过的结果在 backtrader 上**对拍**,数字对不上时能定位是哪一方错
- 能用 backtrader 做到手搓栈做不到的事:限价/止损/bracket 单、多数据源、
  重采样、横截面多标的
- **产出一份评估结论**:backtrader 在哪些场景该用、哪些场景该躲,写成可复用的
  框架对比尺子(`reference/framework-scorecard.html`)
- 能识别框架的**静默失败**——凡是框架替你做的决定,都要能翻出来看一眼

## Constraints

- **backtrader 官方已停更**:PyPI 最后一版 `1.9.78.123` 发布于 2023-04-19;
  原作者仓库基本不动,社区靠 [backtrader2](https://github.com/backtrader2/backtrader) 修 bug。
  → 学它是为了**评估与读懂生态**,不是把它当十年基础设施。遇 bug 需自行打补丁。
- 技术背景:Python 熟练;pandas 已在隔壁课程中边用边学;数学一般
- 学习方式:中文讲解;代码与注释用英文;每课短小、单一目标、有一个看得见的胜利
- **教学切入姿态(用户选定)**:系统扫一遍 API,按框架组件面排课——
  但每课必须落到可运行代码 + 一栏评估结论,不做纯 API 罗列
- 数据:crypto 与股票**两边都用**。crypto 用于对拍(用户对那些数字烂熟于心),
  股票用于新场景(接隔壁 L23 的 yfinance 赛道)
- 编辑器 Cursor;终端 zsh

## Out of scope(暂不涉及)

- backtrader 的实盘经纪商接入(IB / Oanda / VisualChart)——已停更的库接实盘钱包
  风险不对等;执行层用户已有自己的 ccxt 实现
- 深挖 backtrader 的元类(metaclass)内部实现——除非它开始咬人
- 把手搓栈**替换**掉——本使命是评估与增补,不是迁移。是否迁移由评估结论决定

## Open question(评估结束时必须回答)

> 对我"研究阶段快速试策略"这个具体需求,backtrader 是净省时间,还是净加负担?
> 如果是负担,哪个框架更该学?
