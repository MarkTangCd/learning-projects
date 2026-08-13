# backtrader Resources

高信任优先。SEO 农场文("2026 最佳回测库 Top 7")一律不收——那类文章大多没跑过代码。

## Knowledge

### 一手源(权威,优先级最高)

- [官方文档 — backtrader.com/docu](https://www.backtrader.com/docu/)
  唯一权威 API 参考。结构即本课程的骨架:Cerebro / Data Feeds / Strategy / Indicators /
  Orders / Broker / Analyzers / Observers / Sizers。**用于**:任何"这个参数到底什么意思"。
- [Quickstart — 官方](https://www.backtrader.com/docu/quickstart/quickstart/)
  从裸 Cerebro 一路加到 Sizer/Analyzer 的渐进示例。**用于**:L1 的对照。
- [源码 — github.com/mementum/backtrader](https://github.com/mementum/backtrader)
  **文档说不清的地方直接读源码**,这是本课程的核心手法。装好后本地就有:
  `practice/venv/lib/python3.14/site-packages/backtrader/`。
  **用于**:查框架替你做了什么默认决定(例:`analyzers/sharpe.py:128` 的硬编码 252)。
- [PyPI — backtrader](https://pypi.org/project/backtrader/)
  版本与发布日期的事实来源。**用于**:核实"这库还活着吗"(最后一版 1.9.78.123 / 2023-04-19)。
- [backtrader2 社区分支](https://github.com/backtrader2/backtrader)
  官方停更后的社区修 bug 分支。**用于**:撞到 bug 时先来这里看有没有人修过。

- [Indicator Development — 官方](https://www.backtrader.com/docu/inddev/)
  `lines` / `params` / `plotinfo` / `addminperiod` 的权威说明。篇幅很短。
  **用于**:写自定义 Indicator(L2 用过)。
- [Platform Concepts — 官方](https://www.backtrader.com/docu/concepts/)
  `[0]` / `(-n)` 索引语义、minperiod 传播规则。**用于**:搞不清"为什么我的 next() 没被调用"。

### 概念背景(非 backtrader 专属,但本课要用)

- [Andrew Lo, *The Statistics of Sharpe Ratios* (FAJ 2002)](https://alo.mit.edu/wp-content/uploads/2017/06/The-Statistics-of-Sharpe-Ratios.pdf)
  一手论文。夏普比率的**标准误**与自相关修正。**用于**:判断一个 Sharpe 是不是与 0 无法区分
  ——L2 附的参考卡用它算出 BTC 的 0.4559 ± 0.604(t=0.75)。

- [Backtesting.py 文档](https://kernc.github.io/backtesting.py/)
  另一个事件驱动框架,API 更小更现代。**用于**:横向对比时的参照物,不是主线。
- 隔壁课程 `learning-projects/quantitative-trading/reference/`
  你自己的成绩单/执行/词表参考卡。**用于**:对拍时的基准定义(夏普怎么算、成本怎么记)。

## Wisdom (Communities)

- [r/algotrading](https://reddit.com/r/algotrading)
  目前最活跃的通用量化社区,backtrader 相关提问仍有人答。**用于**:框架选型讨论、
  "我这个结果是不是过拟合"这类需要旁人视角的问题。注意信噪比一般,看高赞回复。
- [mementum/backtrader — GitHub Issues](https://github.com/mementum/backtrader/issues)
  官方已不维护,但 issue 区是**最好的踩坑数据库**。**用于**:报错信息直接搜这里,
  大概率有人 2019 年就踩过。
- ~~[community.backtrader.com](https://community.backtrader.com/)~~
  官方论坛。**2026-08-11 实测返回 HTTP 522(不可达)**。历史帖极有价值但目前打不开;
  若恢复可通过 Google `site:community.backtrader.com <关键词>` 搜快照。
  **这件事本身就是评估证据**:社区基础设施在退化。

## Gaps(缺口,驱动后续检索)

- **缺**:可信的 backtrader vs vectorbt vs nautilus_trader **实测**对比(带代码与数字的)。
  搜到的全是 SEO 文,无一份可复现。→ **本课程的产出之一就是自己造这把尺子**
  (`reference/framework-scorecard.html`),用同一个策略、同一份数据实测。
- **缺**:backtrader 在 Python 3.13+ / pandas 3.x 上的兼容性权威说明。
  → 已自行实测(见 [[0001-mission-and-environment]]),后续每撞一个坑就补进参考卡。
- **缺**:backtrader 横截面(多标的排序选股)的成熟范式。官方文档以单标的为主。
  → 到多标的那课时需要专门检索。

## 用户社区偏好

- 尚未询问用户是否愿意参与社区。默认先提供,不强推。
