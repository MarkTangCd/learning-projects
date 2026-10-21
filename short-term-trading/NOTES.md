# NOTES — 教学工作笔记（短线交易）

## 用户画像（2026-10-09 建立）
- 目标：**走向全职交易**；现状：在 Crypto 做交易但**没有固定方法、盈亏随机**
- 执行方式：手动交易 + Python 做工具（统计 / 回放 / 复盘）
- 时间：每天 **2–4 小时**（盯盘 + 复盘）
- 背景：Python 熟练；量化工作区已学完 L1–L27（回测 / 样本外 / walk-forward / ccxt 执行 / 永续合约杠杆强平 / 预注册 / 尸检）；pandas 已会；数学一般
- 环境：Cursor、zsh、本地代理 `http://127.0.0.1:1087`（ccxt 需 `exchange.httpsProxy`）；**data.binance.vision 直连可达，不需代理**（2026-10-12 实测）
- 时区：本机 **UTC+8**（表里 local 列按此）

## 用户规则（用户自己写下的）
- **盯盘窗口（2026-10-12）：工作日 **UTC 12–15（本地 20–23）开仓**（2026-10-20 扩），之外贴 `outside-session`；在场到本地 00:00 = UTC 16:00，时间止损亲手执行。**
- **止损 v1.1（2026-10-20，用户决定）：k ∈ [1, 2]，下限 40 bp，< 60 bp 必须 maker。** 老师的 L5 数据反对意见已陈述并记录，30 笔后对照。 **本地 22:00 是生活硬约束（2026-10-12 确认），暂不可调；用户表示交易有成效后再尝试挑战窗口。** 窗口不含全日最活跃的 UTC 14–15，时间止损 UTC 16 要替它多做事；夏令时结束（2026-11-01）后开盘移到 14:30 UTC，届时窗口将不含开盘，需重新评估（可选项：改做开盘前的 12:30–14:30，或接受 13–14 单小时）。见 [[0003-window-chosen-quiet-hour-entries-abandoned-after-2h]]。

- **账户 400 USDT，1R = $2（0.5%）**，2026-10-13 定。止损距离上限 4%（最小名义 $50）。
- **合规率预测（用户，2026-10-13）：接下来 10 笔 ≥ 90%**；起点 20%。10 笔后对照并记录校准偏差。
- R1 实测（真实账户）：止损单随平仓自动撤销。
- **趋势窗口预测（用户，2026-10-14）：接下来 20 个工作日 UTC 12–16 里 4 个判为趋势**（基准 5/31）。约 2026-11-11 后用 `structure.py` 扫描对照。注意 11-01 后开盘后移，窗口性质会变，对照时要说明。

## 教学偏好（本工作区特有）
- **实战优先（2026-10-18 明确）**：用户跳过 L6 的自加分组检验，认为对实战无指导意义。此后每课的交付物必须是盯盘时能直接用的（剧本 / 练习 / 复盘模板）；检验工具作为可选保留，不做作业主线。见 [[0008-user-declines-research-drills-wants-practical]]。

## 教学偏好（继承自量化工作区）
- 中文讲解，代码 / 注释英文；解释简洁直接
- 每节课：短、单一目标、可快速完成、一个"看得见的胜利"
- 要用户预测 / 盲预测时，题面必须直接列出已知数字
- 术语首次出现给大白话定义；压缩表达要节制
- 让用户**贴工具原始输出**而不是转述数字（L5 ③ 出现过口径混用；L6 起已照做）
- 要用户预测时给模板：「我预计 A 组毛期望 高于/低于 B 组，因为……」（L6 ② 的预期写成了关于 n 的）
- 让用户改代码的作业要附骨架（函数签名 + 两行逻辑），L6 ② 未做
- 测验选项等长，不给格式暗示
- 图用真实数据生成（`structure.py --svg`），内联进课文；`qlmanage -t` 可把 svg 转 png 供老师自检

## 待确认
- 11 月后窗口怎么办（22:00 约束 + 开盘后移到 14:30 UTC）
- 挑战③的 10 个止损价是当时写下的还是现在重建的？
- 是否已用 TradingView（回放练习工具选型）
- 是否愿意加入英文社区（r/Daytrading、futures.io、Elite Trader）

## 课程路线（草案，随进展修订）
**阶段 0 · 量尺**（先能测量，再谈方法）
1. ✅ L1 先量尺后方法：R、期望值、手续费拖累、交易日志 `practice/journal.py`
2. ✅ L2 把 2–4 小时放在哪：`practice/hour_profile.py`（1m klines → 每 UTC 小时行程 / 区间 / 成交量中位数）。老师已跑 27 天（至 2026-10-10）：峰 UTC 13–16（本地 21–24）行程 991 bp vs 平均 571；最静 UTC 21 仅 35%；周末全日行程 2239 vs 工作日 5358 bp。公共数据里 **无 liquidationSnapshot**（um/daily 只有 aggTrades/bookDepth/bookTicker/klines/metrics/trades 等），清算走 Coinglass。待用户跑并选窗口。
   - **挑战③判决（2026-10-12）**：见 [[0002-challenge3-plans-exist-execution-fails]]——10/10 有止损，E −0.38R，0 笔到目标，2 笔超出止损，计划 R 仅 1.25。L3 据此改为针对执行。
3. ✅ L3 规则 v1（2026-10-12 发布）：R1 交易所止损单（STOP_MARKET/closePosition/MARK_PRICE，API 下的不随平仓自动撤）、R2 窗口、R3 三种合法出场（止损 / 目标 / **时间止损 UTC 16**）、R4 日亏 −3R、R5 连亏 3 停。`practice/rules.py` 在用户 10 笔上合规率 **20%**（2 笔 R1、6 笔 R3；R2/R4/R5 因无时间无法检查）。日志新增 `closedAt`。参考卡 `rules-v1.html`。挑战全部答复（见 [[0004-rules-v1-finalized-1r-2usd-compliance-prediction-90]]）。**下一步：用户按规则记 10 笔，然后进 L4 市场结构**（L4 可在此期间发布，不必等 10 笔）。

**阶段 1 · 结构**（看图的语言）
4. ✅ L4 市场结构（2026-10-13 发布）：摆动点（strength 3）→ HH/HL/LH/LL → 判决规则（两 HH + 两 HL 才算趋势，否则区间）；推动 vs 回调（Brooks：不过起点；Grimes：顺势腿更长 always in price）；Grimes 四格 ↔ 用户五个 setup 名；Brooks 80% 规则；Kitron&Wengrowicz 15 分钟反转。`practice/structure.py`（+`binance_data.py` 共享加载器；`--svg` 出图）。三张真实数据图：09-29 下降、09-24 上升、10-10 区间→突破→首次回调（最重要的一题）。扫描：过去 31 个工作日 UTC 12–16 只有 5 个判为趋势。**阶段 1 只练趋势延续（pullback）一格。** 挑战全部答复，见 [[0005-l4-answers-structure-vocab-and-higher-timeframe]]；note 三段式词汇表已加进结构卡 + `rules.py` 软检查。
5. ✅ L5 止损距离（2026-10-14 发布）：`practice/stop_distance.py`（机械顺势回调，确认后收盘进场，k×ATR14(5m) 止损，2R 目标，收盘时间止损；`--k/--fee/--session/--target`）。60 天 207 笔：**毛期望每个 k 都 ≈ 0（结构机械执行无 edge）**；净期望全负，主因手续费（k=1 占 0.60R，k=4 占 0.22R）；被扫率 54%→21% 但时间止损 18%→69%。挂单 2bp 把 k=4 净期望 −0.16→−0.03。窗口内 40 笔毛期望略负。**规则：止损 = 回调极值 − 4×ATR14(5m)，≥60 bp；进场优先限价；note 第四段 maker/taker/missed。** 参考卡 `stop-distance-card.html`；词表 +5（摆动点、判决、推动/回调、四格、ATR）。挑战已答，见 [[0006-l5-predictions-correct-eth-atr-misread]]：②六个方向全对；③ETH ATR 误报 6 倍（实为 1.3 倍）待澄清；⑤两个杠杆答对。
6. ✅ L6 挑选的第一层（2026-10-16 发布）：`practice/location.py --by location|depth|speed`（复用 L5 测试台，加分组 + 标准误）。BTC 120 天 444 笔：**位置 / 深度 / 速度三个假设全部不成立**——VWAP 附近被扫率 56% vs 35%（磁铁非垫子）、PDH/PDL 与前推动起点样本仅 8/6；深度差 0.11 < 2 se；速度 BTC fast −0.20 看似成立但 **ETH 反向 +0.15** → 噪声。新参考 `selection-ledger.html`（负结果账本，3 假设 9 分组）。结论：K 线几何机械检验无 edge → L7 剧本不用它们当触发器；剩余候选 = K 线之外的信息（阶段 2）与用户判断（日志 30 笔）。答复见 [[0007-l6-answers-raw-output-habit-near-misapplied]]：①✓ ③✓ ④参数用错 ②用户选择跳过（代码已加 `--by session/htf`，未跑），见 [[0008]]。
7. ✅ L7 剧本与回放（2026-10-18 发布）：`reference/playbook-trend-continuation.html`（一页剧本 v1，挑选栏留空，描述字段进 note）+ `practice/replay.py`（随机工作日 + 窗口内随机切点 → replay.svg → 判决 / 动作两问 → 按剧本定止损目标放行情 → replay_log.csv；`--stats` 判决准确率 / 一致率 / 练习 E）。日程：窗口前 8 次回放、窗口内只找一个剧本、次日 10 分钟复盘。答复见 [[0009-l7-first-drills-k-override-session-extended]]：①8 次回放 38%/50%（工具已修 not-enough→RANGE）、②在场延至 00:00 本地、③**用户改 k=4→1–2（v1.1）**、④五天后再贴。30 笔闸门 → v2。

**阶段 2 · 流**（盘口与成交）
8. ✅ L8 盘口与成交流（2026-10-20 发布）：`practice/flow.py`（离线：K 线 taker_buy 列 → 5m delta / CVD 表 + 双面板 SVG，自动标摆动点处的 CVD 背离；实时：轮询 aggTrades + depth，每 N 秒一行，tape_log.csv；直连可用）。Binance `m` = "Was the buyer the maker?" 已核对。两张图：10-10（13:25 HH 背离→失败→14:00 LL→突破 CVD −11k→+22k→HL 回调守住）、09-29（无背离，尾段吸收候选）。note 新增 `cvd=confirm|diverge|flat`（描述字段）。参考卡 `flow-card.html`。待用户答：①实时 tape 5 行、②昨天的背离、④回调里 CVD 降但 HL 守住。
9. L9 足迹与吸收：把 delta 拆到每个价位（足迹），看回调极值处的吸收；数据源需 aggTrades（每日文件大，先用 live 轮询录一个窗口）
10. L10 Crypto 特有数据：资金费率、OI、清算热图、基差——各回答什么问题
11. L11 剥头皮的经济学：手续费、滑点、挂单成交率；什么时候剥头皮根本不可能赚

**阶段 3 · 过程**（让它可持续）
12. L12 复盘系统：每日 / 每周复盘、错误标签、playbook 迭代（Steenbarger 自我教练法）
13. L13 心理与 tilt：损失追逐的信号与熔断（Douglas / Steenbarger / 赌博行为研究）
14. L14 闸门：从回放到小资金到加仓的统计判据（预注册思路移植）

**阶段 4 · 扩展**
15. L15+ 外汇：会话、点差 / ECN、prop firm 规则；把 playbook 迁移到 FX
