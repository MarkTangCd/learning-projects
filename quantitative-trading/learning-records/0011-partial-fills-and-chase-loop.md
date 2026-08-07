# L11 完成:部分成交与有界追单跑通 —— 执行层四件套集齐,路线 C 收官

用户于 2026-08-07 在 Binance 现货测试网跑通 `practice/execution.py chase`(有界 IOC 阶梯追单),并完成 ③ 急停验证。同时抓到并修掉一个真 bug。

## Evidence(用户亲眼看到)
- **IOC 三终局都见到**:Leg 1 `status=expired, filled=0`(挂不上当场作废,IOC 不休息在盘口)、Leg 2 `status=closed, filled=0.0003`(一口吃满,remaining=0 循环干净退出)。
- **汇总行**:意图 0.0003 = 实成 0.0003,VWAP $64,964.03,急迫成本 **+0.0 bps**。
- **③ 急停**:kill 后 chase 的 Leg 1 被风控闸门**秒拒**(一张单未发),unkill 解除。追单不豁免前置检查,验证成立。

## 抓到的真 bug(边界住在成功路径的终点)
`cmd_chase` 首版在"算还剩多少"用 `float(ex.amount_to_precision(SYMBOL, intended - total_filled))`。当阶梯把意图**成满**(残量=0)时,ccxt 的 `amount_to_precision` 对低于最小精度(0.00001)的量抛 `InvalidOrder` → 崩在**意图 100% 完成之后**。
- 教训:边界 bug 不只住失败路径,也住**成功路径的终点**。我只防了"残量太小不值得追",没防"残量正好为零"。
- 修法:先用**裸数字** `intended - total_filled` 与交易所 `limits.amount.min` 比,判定"还剩没剩",够格才送进 `amount_to_precision`。循环内 + 市价兜底两处都改。

## 与既有课的对账
- **急迫成本 +0.0 bps = 测试网撒谎**(承 [[0009-execution-lifecycle-on-testnet]]):合成盘口按 last 撮合,±0bps 腿正好成交,真实急迫税在此测不出——同 L4 成本假设只能等小资金实盘校准。
- **账本记 filled 不记 intended**:本课核心纪律,汇总行显式打印二者。
- 幂等每腿独立 cid(承 [[0010-idempotent-orders-verified]]);每腿过闸门(承 L9 风控)。

## 现状与分支决策(待用户选)
执行层四件套(生命周期 / 风控闸门+急停 / 幂等 / 部分成交)全部在测试网亲手跑通,**路线 C 完成**。下一步二选一:
- (A) **回研究端找真 edge**:SMA 单族无 edge([[0007-walk-forward-verdict-sma-no-edge]]),上均值回归 / regime 过滤,复用整套 gauntlet —— 最贴使命。
- (B) **小资金实盘**:把执行层接回 L8 tick 循环,替换"即时成交"那行,用真实盘口校准 L4 成本假设。
- 老师倾向:先 A(有值得下的单)再 B(能安全下真单),否则实盘只是把无 edge 策略搬到真钱上。
