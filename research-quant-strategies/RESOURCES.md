# 量化策略研究 Resources

> 全部链接于 2026-08-11 逐一核实存活与质量。抓取限制与付费墙已标注。
> 排除项（永久）：Telegram/微信带单群、卖信号者、"X 天学会量化"卖课号。

## Knowledge

### 聚合器 / 从业者博客（每日发现层）

- [Quantocracy](https://quantocracy.com/)
  ~150+ 量化博客的每日链接聚合，纯策展无产品推销。Use for: 每日发现信息流的第一站。
- [Quantpedia 免费策略页](https://quantpedia.com/strategies/time-series-momentum-effect)（示例：TSMOM）；[筛选器](https://quantpedia.com/screener/)
  学术策略百科：每条含交易规则、回测区间、指示性绩效、源论文链接。免费页足够支撑复现。⚠ 完整数据库/图表付费。Use for: 把"想找个策略"变成"具体规则 + 源论文"。
- [Alpha Architect Blog](https://alphaarchitect.com/blog/)
  资管机构写的学术因子论文白话解读，月更多篇。⚠ 反爬 403，浏览器正常。Use for: 复现前理解一个因子**为什么**有效；找值得读的论文。
- [Robot Wealth Blog](https://robotwealth.com/blog/)
  前职业交易员写的研究方法论与统计套利，代码驱动。Use for: 研究**流程**怎么做（如何验证 edge），不是策略目录。
- [QuantStart Articles](https://www.quantstart.com/articles/)
  回测/时间序列教程库，2012–2020 为主，常青但不新鲜。Use for: 基础概念补课。
- [川流不息（石川，知乎专栏）](https://zhuanlan.zhihu.com/mitcshi) + [factorwar.com（因子动物园）](https://www.factorwar.com)
  因子投资/资产定价，每篇有论文支撑，无卖课卖信号，配套出版书《因子投资：方法与实践》。Use for: 因子方向的中文方法论必读；文献综述与选题。
- 公众号「量化投资与机器学习 QIML」
  ML 策略/论文解读，信息密度高；论文搬运需回读原文。Use for: 追踪前沿论文与开源复现动态。

### 学术一手（最高信任层）

- [SSRN](https://papers.ssrn.com/)（⚠ 反爬，浏览器正常）
  金融工作论文主库。关键可复现论文：
  - [Moskowitz, Ooi & Pedersen — Time Series Momentum](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2089463)（免费 PDF）
  - [McLean & Pontiff — Does Academic Research Destroy Stock Return Predictability?](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2156623)（97 个学术预测变量：样本外收益 −26%，发表后 −58%——**信源信任分层的实证地基**）
  - [Jegadeesh & Titman 1993（横截面动量，早于 SSRN，免费 PDF）](https://www.bauer.uh.edu/rsusmel/phd/jegadeesh-titman93.pdf)
- [arXiv q-fin.TR](https://arxiv.org/list/q-fin.TR/recent) / [arXiv q-fin.PM](https://arxiv.org/list/q-fin.PM/recent)
  预印本，每周各 ~7 篇，免费 PDF 常带代码链接，含 crypto 永续/DeFi 论文。⚠ 无同行评审——先查有无真实回测与数据描述。Use for: 前沿想法，尤其 crypto 方向。

### 开源代码库（可执行层）

- [freqtrade/freqtrade-strategies](https://github.com/freqtrade/freqtrade-strategies)（5.3k★，2026-08 活跃）
  freqtrade 官方策略示例库，开箱可回测。⚠ 明示为教学示例，盈利性自验。Use for: **第一次 crypto 复现的最低摩擦入口**。
- [freqtrade 官方文档](https://www.freqtrade.io/en/stable/) / [中文文档](https://www.freqtrade.cn)（社区翻译，可能滞后）
  开源 crypto bot 事实标准：策略开发/回测/hyperopt/dry-run 全流程。Use for: 本课 crypto 线的复现工具链。
- [microsoft/qlib](https://github.com/microsoft/qlib)（47.3k★，活跃）
  `examples/benchmarks/` 含 25+ 可复现模型（LightGBM/LSTM/TFT/HIST/TRA…）+ Alpha158/Alpha360 因子库。**中文世界唯一系统化的开源策略库**。Use for: A股/ML 阶段的策略与因子来源。
- [je-suis-tm/quant-trading](https://github.com/je-suis-tm/quant-trading)（10.5k★）
  经典具名策略的干净 Python 参考实现（配对交易/Dual Thrust/London Breakout…）。⚠ 单作者、回测简化。Use for: 读懂经典策略的结构，不直接信其绩效。
- [stefan-jansen/machine-learning-for-trading](https://github.com/stefan-jansen/machine-learning-for-trading)(20.4k★，活跃)
  《Machine Learning for Trading》第 3 版配套码库，数据→执行端到端。Use for: ML 策略阶段的结构化教材。
- [QuantConnect 策略库与论坛](https://www.quantconnect.com/learning/articles/)
  数十个学术策略的完整实现，附共享基础设施上的真实回测，免费层够用。Use for: 可直接 clone 运行的策略实现（股票为主，支持 crypto）。
- [Papers With Backtest](https://paperswithbacktest.com/)
  5000+ 论文配代码与清洗数据，deflated-Sharpe 验证方法论。⚠ freemium（$10–50/月解锁全量）。Use for: 论文→代码映射（免费层查目录）。
- [FMZ 发明者量化 策略广场](https://www.fmz.com/square)
  数百个 crypto/期货策略源码，免费部分真开源。⚠ 付费订阅策略按"卖信号"处理，一律排除；免费代码质量参差，只作思路来源。Use for: 学 crypto 策略实现范式（网格/资金费率套利等）。
- [Hummingbot Blog](https://hummingbot.org/blog/)
  开源做市 bot 的策略指南（网格/PMM），附可部署配置。Use for: crypto 做市/网格策略专题。
- [ricequant/rqalpha](https://github.com/ricequant/rqalpha)
  开源 A股 回测框架。Use for: A股 阶段的回测引擎候选（米筐社区本身已弱化，只取框架）。
- 数据接口（A股 阶段）：[akshare](https://github.com/akfamily/akshare)（免费，活跃）、[tushare.pro](https://tushare.pro)（积分制）。基础设施：[vnpy/vnpy](https://github.com/vnpy/vnpy)（44.4k★，事件驱动框架，策略需自写）。

### 教学体系（方法论层）

- [Quantopian Lecture Series（重制版）](https://community.quantopian.com/) + [论坛存档](https://quantopian-archive.netlify.app/)
  55 讲免费量化研究课（因子分析/过拟合），仍是最好的免费研究方法论课程之一。⚠ 代码面向已死平台——**移植概念，不移植代码**。
- [Barca0412/Introduction-to-Quantitative-Finance](https://github.com/Barca0412/Introduction-to-Quantitative-Finance)（1.6k★，活跃）
  中文开源多因子教程 + AI 金融论文收录。

## Wisdom (Communities)

- [r/algotrading](https://www.reddit.com/r/algotrading/)（~190 万成员）
  高流量、信号不稳；wiki 和高票帖质量好。Use for: 想法 sanity-check、工具链问题；不用于直接找策略。
- [QuantConnect 论坛](https://www.quantconnect.com/forum/discussions/1/hot)
  帖子附可 clone 的策略代码 + 真实回测。Use for: 复现问题求助、看别人怎么改策略。
- [vn.py 官方论坛](https://www.vnpy.com/forum/)（9 万用户，日活跃）
  CTA/期权/价差策略讨论与代码求助，开源社区无卖课主导。Use for: 中文 CTA 策略实现细节。
- [聚宽社区](https://www.joinquant.com/community)（⚠ 仅限大陆 IP）
  A股 策略分享区，大量帖附完整可回测源码；普遍过拟合，需自己 OOS 复验。Use for: A股 阶段策略复现素材首选。
- [雪球](https://xueqiu.com)
  泛投资社区，量化含量低。Use for: 散户情绪与市场叙事观察，不作为策略来源。
- [QuantJourney Substack](https://quantjourney.substack.com/)
  经核实的少数高信号 crypto/Python 策略 substack（单作者，freemium）。Use for: crypto 资金费率等专题的从业者视角。

## Gaps

- **高信号中文 crypto 社区几乎不存在**——中文 crypto 圈以带单/卖信号为主，已全部排除。crypto 的 wisdom 层暂时只能依赖英文社区（r/algotrading、freqtrade Discord）。
- **A股 留出集数据的免费方案**未定：akshare 免费但质量需验证，tushare.pro 高级接口要积分。A股 阶段开始前需专门一课解决。
- Hudson & Thames mlfinlab 已冻结（2023-10 停更，开发转入付费门户）——López de Prado 方法需要时读原书，不依赖该库。
- 已死/排除：Nuclear Phynance（已关站）、EliteTrader（主观交易为主）、hummingbot 中文文档仓（停更）。
