# L9 完成:测试网上跑通完整订单生命周期 —— 并抓到"测试网撒谎"的两处

用户于 2026-08-07 在 Binance 现货测试网跑通 `practice/execution.py` 的挑战 ③④⑤,SEND→READ BACK→RECONCILE 纪律走完整圈。

## Evidence(用户亲眼看到)
- **③ rest**:限价买单 @ $51,448.41(市价 80%)→ `open` filled=0 remaining=0.00048 average=None cost=0 → 回读仍 `open` → `canceled`。回测里不存在的"挂着不成交"状态,亲眼看到。
- **④ fill**:市价买 0.00031 BTC → `closed` filled=0.00031 average=64318.0 cost=19.93858。风控通过(名义 $19.94 ≤ $50)。
- **⑤ kill/unkill**:kill 后 fill 被风控闸门**秒拒**("急停已激活")→ unkill 解除。急停最先、最便宜地拦截,验证成立。

## 高光:RECONCILE 行的两个反常 = 本课最贵的知识(测试网在撒谎)
1. **滑点 +0.0 bps —— 假的**。`average` 与 `assumed` 一分不差,因为测试网撮合是合成的、盘口极薄,常直接用 last 价成交。结论:**测试网能验证代码路径,不能估算真实成本/滑点**。L4 回测的滑点假设无法在此步被校准,只能等小资金实盘。
2. **手续费 None None —— 费在别处**。Binance `fetch_order` 的订单头**不返回 commission**;手续费住在成交明细(fills/trades)里。ccxt 单数 `fee` 字段对 Binance 常为 None。对账 = **两个 API 返回的拼接**(`average` 在订单头,`fee` 在 fills),少读一个就对不平。

## 补丁(2026-08-07)
`cmd_fill` 原来只读订单头 → 手续费漏计,对账不完整。新增 `fee_from_trades()`:`fetch_order_trades(id)` 聚合每条 fill 的 `fee.cost`,并算出 fee_bps;滑点为 0 时打印"测试网假象"提示。让"真实手续费"看得见。

## 与 L4 的对账结论
L4 成本是**固定假设**(`FEE=0.1%` + 常数滑点)。真实执行揭示:①滑点测试网测不到;②真实费率受 maker/taker、BNB 抵扣、VIP 等级影响,非单一常数;③对账要跨两个返回拼。核心内化:**测试网验证代码正确性,不验证成本假设准确性**——这正是"testnet 稳→小资金实盘"不能跳的理由。见 [[0008-paper-trading-loop-working]]。

## 分支决策(承接 0007 / 0008,待用户选)
- (A) **回找真 edge**:SMA 单族无 edge([[0007-walk-forward-verdict-sma-no-edge]]),给信号加 regime 过滤 / 换均值回归,复用整套 gauntlet —— 最贴使命。
- (B) **小资金实盘**:把执行层接回 L8 的 tick 循环,替换那行"即时成交";真实盘口才能校准 L4 的成本假设。
- 老师倾向:先做少量 A(有值得下的单)再上 B(能安全下真单),否则实盘只是把一个无 edge 策略搬到真钱上。
