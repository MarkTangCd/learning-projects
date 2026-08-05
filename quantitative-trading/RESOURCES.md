# 量化交易 Resources

> 所有链接均由检索时逐一验证可访问(Reddit 因抓取策略未自动验证,但为公认活跃社区)。
> 学习路径建议:**Chan《Quantitative Trading》打概念 → CCXT + freqtrade 动手做 Crypto → NautilusTrader 升级为正式系统 → yfinance + zipline 拓展股票 → López de Prado + Stefan Jansen 上 AI/ML**。

## Knowledge

### 入门经典(先读)
- [Book: 《Quantitative Trading》(2nd ed.) — Ernest P. Chan](https://www.amazon.com/Quantitative-Trading-Build-Algorithmic-Business/dp/1119800064)
  个人量化系统的"从这里开始"之书,2 版加了 Python/R 回测。作者前摩根士丹利/瑞信 quant。**用于:** 建立研究→回测→实盘的整体流程认知。
- [Book: 《Algorithmic Trading: Winning Strategies and Their Rationale》 — Ernest P. Chan](https://www.amazon.com/Algorithmic-Trading-Winning-Strategies-Rationale/dp/1118460146)
  深入均值回归、动量、风控,并讲清每个策略背后的道理。**用于:** 挑选和理解具体策略族。
- [Book: 《Machine Trading》 — Ernest P. Chan](https://www.porchlightbooks.com/products/machine-trading-ernest-p-chan-9781119219606) · [作者官网](https://www.epchan.com/books/)
  把 ML 与现代技术用于系统化交易。**用于:** 从传统策略过渡到 AI 量化。

### AI / ML 量化(后期)
- [Book: 《Advances in Financial Machine Learning》 — Marcos López de Prado](https://www.wiley.com/en-us/Advances+in+Financial+Machine+Learning-p-9781119482086)
  ML 用于金融的权威著作(meta-labeling、purged CV、分数差分)。作者管理过数十亿美元量化基金。**用于:** 避开金融 ML 的致命陷阱(数据泄漏、错误的交叉验证)。
- [López de Prado 官方研究站](https://www.quantresearch.org/)
  作者本人的论文、讲义、数据集。**用于:** AFML 一书的免费配套 + 研究生级 ML-finance 教材。
- [Book+Code: 《Machine Learning for Algorithmic Trading》 — Stefan Jansen](https://github.com/stefan-jansen/machine-learning-for-trading)
  从取数到实盘的端到端 ML 交易流水线,200+ notebook,持续维护。**用于:** 代码优先地学 ML 量化(极契合"会编程"的你)。
- [MlFinLab / Hudson & Thames](https://hudsonthames.org/)
  把 López de Prado 的算法实现成 Python 库(部分已商业化)。**用于:** 把 AFML 理论落成代码。

## Tooling

### Crypto 接口与数据
- [CCXT — 统一交易所 API 库](https://github.com/ccxt/ccxt) · [文档](https://docs.ccxt.com/)
  一套 API 打通 100+ 中心化/去中心化交易所(Python/JS/…),REST + WebSocket。**事实标准,多交易所系统的第一依赖。** 我们下一课就用它。
- [Binance API 官方文档](https://developers.binance.com/docs) — 最大交易所的行情/交易/WebSocket 官方文档。
- [Coinbase Developer Platform](https://docs.cdp.coinbase.com/) — 美国合规上市交易所的官方 API 文档。
- [Bybit API V5 文档](https://bybit-exchange.github.io/docs/) — 现货/合约/期权一套集成。
- [CoinGecko API](https://docs.coingecko.com/reference/introduction) — 数千币种的行情/元数据,有可用免费额度。**用于:** 研究与回填历史数据。

### 回测框架(Python)
- [freqtrade](https://www.freqtrade.io/en/stable/) — 开源 Crypto 交易机器人,自带回测/调参/实盘。**社区最大,Crypto-first 首选。**
- [NautilusTrader](https://nautilustrader.io/) · [文档](https://nautilustrader.io/docs/latest/) — Rust 内核、事件驱动、生产级,回测与实盘同引擎(呼应 L1 的"一份信号两处运行")。
- [vectorbt](https://vectorbt.dev/) — 向量化回测,借 NumPy/Numba 秒扫上千组参数。**用于:** 大规模参数研究。
- [backtrader](https://www.backtrader.com/) — 老牌、对新手友好、文档丰富。
- [zipline-reloaded](https://github.com/stefan-jansen/zipline-reloaded) — Quantopian Zipline 的社区续作,股票事件驱动回测。**用于:** 股票赛道。

### 数据与基础库
- [pandas](https://pandas.pydata.org/docs/) — Python 量化的骨架。
- [NumPy](https://numpy.org/doc/stable/) — 数值计算底座。
- [yfinance](https://github.com/ranaroussi/yfinance) — 免费拉 Yahoo 股票数据(非官方封装,研究/原型够用)。**用于:** 股票赛道取数。
- [TA-Lib](https://ta-lib.org/) — 200+ 技术指标与 K 线形态,业界标准(2001 至今)。
- [pandas-ta-classic](https://github.com/xgboosted/pandas-ta-classic) — 纯 Python、200+ 指标。**注意:** 原 `pandas-ta` 2025 年转商业、原仓库已 404,这是当前推荐的开源续维护分支。

## Wisdom(Communities)
- [r/algotrading](https://www.reddit.com/r/algotrading/) — 最大的散户/独立算法交易社区(策略、基建、数据、券商)。**用于:** 策略吐槽、基建选型。
- [r/quant](https://www.reddit.com/r/quant/) — 更偏学术/职业的量化金融社区。**用于:** 方法论、职业向讨论。
- [QuantConnect 社区与论坛](https://www.quantconnect.com/) · [文档](https://www.quantconnect.com/docs/v2/) — 开源 LEAN 引擎 + 活跃论坛 + 免费数据。**用于:** 共享策略、动手平台。
- [QuantStart 文章](https://www.quantstart.com/articles/) — Michael Halls-Moore 的系统化交易/ML/Python 教程,低 SEO 噪声。

## 免费课程 / 讲义
- [QuantConnect Boot Camp / Learning Center](https://www.quantconnect.com/learning/task/122/welcome-to-quantconnect) — 免费交互式、代码优先地建策略。
- [Stefan Jansen ML-for-Trading 仓库](https://github.com/stefan-jansen/machine-learning-for-trading) — 200+ notebook,可当自学课程。
- [López de Prado 讲义与数据](https://www.quantresearch.org/) — 免费研究生级 ML-finance 教材。

## Gaps(待补)
- **数学补课资源**(统计/概率/线代,面向"数学一般"的工程师)——尚未收录专门资源,后续按需检索。
- **中文优质社区**——目前列的都是英文社区,若你偏好中文交流,下次为你找。
- **实盘券商/合规**(尤其传统股票赛道的美股券商 API,如 IBKR/Alpaca)——进入股票赛道时再补。
