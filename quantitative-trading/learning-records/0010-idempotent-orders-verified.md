# L10 完成:幂等下单在测试网验证通过(dup 挑战)

用户于 2026-08-07 跑通 `practice/execution.py dup`:用同一个 `clientOrderId` 连发两次限价单,交易所拒绝/去重了第二张——超时重试不会造成双倍下单。

## 核心内化
- **幂等钥匙 = 交易意图的纯函数**(side + 价格桶,或 tick 循环里的 `(symbol, side, bar_ts)`),绝不能掺时钟。L9 初版用毫秒时间戳当 cid 是"假幂等"真 bug,已在 L10 修为 `intent_cid()`。
- **超时恢复模式**:SEND 超时后不盲目重发;先 `fetch_order(cid)` 问交易所"这单到底进去没",没进去才用**同一个 cid** 兜底重发。
- 去重是**交易所侧**保障(server-side),比客户端记账可靠:断网/进程重启后依然成立。

## 现状
执行层三大纪律已齐:SEND→READ BACK→RECONCILE([[0009-execution-lifecycle-on-testnet]])、风控闸门+急停、幂等下单。尚缺:**部分成交处理**(partial fill:剩余量是等、撤、还是追)——路线 C 的最后一块,即 L11。
