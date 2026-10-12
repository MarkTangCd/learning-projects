# NOTES — 教学工作笔记（短线交易）

## 用户画像（2026-10-09 建立）
- 目标：**走向全职交易**；现状：在 Crypto 做交易但**没有固定方法、盈亏随机**
- 执行方式：手动交易 + Python 做工具（统计 / 回放 / 复盘）
- 时间：每天 **2–4 小时**（盯盘 + 复盘）
- 背景：Python 熟练；量化工作区已学完 L1–L27（回测 / 样本外 / walk-forward / ccxt 执行 / 永续合约杠杆强平 / 预注册 / 尸检）；pandas 已会；数学一般
- 环境：Cursor、zsh、本地代理 `http://127.0.0.1:1087`（ccxt 需 `exchange.httpsProxy`）；**data.binance.vision 直连可达，不需代理**（2026-10-12 实测）
- 时区：本机 **UTC+8**（表里 local 列按此）

## 教学偏好（继承自量化工作区）
- 中文讲解，代码 / 注释英文；解释简洁直接
- 每节课：短、单一目标、可快速完成、一个"看得见的胜利"
- 要用户预测 / 盲预测时，题面必须直接列出已知数字
- 术语首次出现给大白话定义；压缩表达要节制
- 测验选项等长，不给格式暗示

## 待确认
- 挑战③的 10 个止损价是当时写下的还是现在重建的？
- 用户选定的盯盘窗口（L2 挑战③）
- 实盘资金规模级别（决定最小名义 $50 约束下的 R 大小）
- 是否已用 TradingView（回放练习工具选型）
- 是否愿意加入英文社区（r/Daytrading、futures.io、Elite Trader）

## 课程路线（草案，随进展修订）
**阶段 0 · 量尺**（先能测量，再谈方法）
1. ✅ L1 先量尺后方法：R、期望值、手续费拖累、交易日志 `practice/journal.py`
2. ✅ L2 把 2–4 小时放在哪：`practice/hour_profile.py`（1m klines → 每 UTC 小时行程 / 区间 / 成交量中位数）。老师已跑 27 天（至 2026-10-10）：峰 UTC 13–16（本地 21–24）行程 991 bp vs 平均 571；最静 UTC 21 仅 35%；周末全日行程 2239 vs 工作日 5358 bp。公共数据里 **无 liquidationSnapshot**（um/daily 只有 aggTrades/bookDepth/bookTicker/klines/metrics/trades 等），清算走 Coinglass。待用户跑并选窗口。
   - **挑战③判决（2026-10-12）**：见 [[0002-challenge3-plans-exist-execution-fails]]——10/10 有止损，E −0.38R，0 笔到目标，2 笔超出止损，计划 R 仅 1.25。L3 据此改为针对执行。
3. L3 风险与执行规则 v1：交易所真实止损单（针对 2 笔超出止损）、出场规则（针对 0 笔到目标）、单笔 R、日亏损上限、连亏停手（借 FTMO 模板）、outside-session 标签 + 每日复盘模板

**阶段 1 · 结构**（看图的语言）
4. L4 市场结构：趋势 / 区间 / 回调（Grimes 框架），多时间框架对齐
5. L5 波动率与 ATR：止损距离该多大才不被噪声扫掉（接量化 vol 知识）
6. L6 VWAP、会话高低点、关键价位：短线最常用的三个参考系
7. L7 第一个 setup 写成剧本（Bellafiore PlayBook 模板）+ 回放练习流程（TradingView bar replay / 自建回放）

**阶段 2 · 流**（盘口与成交）
8. L8 盘口与成交流基础：maker/taker、吃单 / 挂单、盘口失衡（aggTrade / depth 流）
9. L9 CVD / delta / 足迹图：读吸收与扫单；用 Python 从 aggTrades 算 CVD
10. L10 Crypto 特有数据：资金费率、OI、清算热图、基差——各回答什么问题
11. L11 剥头皮的经济学：手续费、滑点、挂单成交率；什么时候剥头皮根本不可能赚

**阶段 3 · 过程**（让它可持续）
12. L12 复盘系统：每日 / 每周复盘、错误标签、playbook 迭代（Steenbarger 自我教练法）
13. L13 心理与 tilt：损失追逐的信号与熔断（Douglas / Steenbarger / 赌博行为研究）
14. L14 闸门：从回放到小资金到加仓的统计判据（预注册思路移植）

**阶段 4 · 扩展**
15. L15+ 外汇：会话、点差 / ECN、prop firm 规则；把 playbook 迁移到 FX
