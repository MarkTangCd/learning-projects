# L2 完成:第一条数据管道跑通

用户于 2026-08-01 独立跑通 L2:用 CCXT 从 binance 拉取真实 BTC/USDT 小时 K 线,装入带 UTC 时间索引的 pandas DataFrame,并通过清洗检查(无重复、时间递增)。完成 [[MISSION.md]] 里"搭建 Crypto 数据管道"这一里程碑的第一步。

## Evidence
- 脚本 `practice/fetch_ohlcv.py` 成功输出 `(500, 5)`、`duplicates: 0`、`monotonic: True`。
- 排障过程中理解了:代理需在 ccxt 显式配置(见 [[NOTES.md]] 网络/代理条目);binance API 直连超时的根因。
- 主动提问 `set_index("ts")` 的作用 → 已讲解"把普通表变成时间序列",用户对索引概念有了主动求知。

## Implications
- pandas 基础(DataFrame / 列 / 时间索引)已首次接触且用于真实数据 → L3 可在此之上直接算移动均线等列运算,无需重教建表。
- 用户会主动追问"这行代码在干嘛" → 教学中应对关键代码行给出"它做什么 + 为什么这么做",而非只给可运行代码。
- 下一课 L3:在这批已跑通的数据上算第一个信号(如 SMA 交叉),并首次引入"信号 = 一列决策"的概念,为 L4 回测铺垫。
