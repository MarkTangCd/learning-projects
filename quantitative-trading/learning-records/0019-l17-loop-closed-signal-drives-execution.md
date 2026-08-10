# L17:闭环 —— 已验证信号第一次驱动真实执行管路(capstone / 使命里程碑)

用户选路线 = 接执行层跑纸上交易。承接 [[0018-l16-shorting-breaks-ceiling-on-btc-but-not-free]]:六课研究讁出"下跌保护 + 薄做空 edge",信号研究边际递减 → 转而闭合系统。

## 这一课的性质:capstone,不教新概念,把旧零件焊成一台机器
`strategy_runner.py` 一次 tick 串起到目前为止造的每个零件:
1. **BRAIN(L12–L16)**:收盘K线 → `regime_switch_signal` → 目标仓位。live 用**固定一组参**(walk-forward 是验方法非实盘再优化)。
2. **L8 三纪律**:只用收盘 bar / 只在严格更新 bar 上动作 / 目标==当前不下单。
3. **L9 风控闸门**:`guarded_create`(名义上限/最小额/急停)。
4. **L10 幂等**:`cid = run-{side}-{bar}`,钥匙绑 bar 不绑时钟 → 崩溃重启重跑同一 bar 不下重单。
5. **L11 回读对账**:不信 create 回执,`fetch_order` 读真相。
6. **账本铁律**:记**实成 filled**,非意图 intended。

## 诚实边界(讲清楚了)
- **现货测试网不能做空** → 桥先跑 long/flat `{0,+1}`;真执行双边(做空)需 **perp 测试网**(接 L16 funding),留后面一课。
- **纸上交易验的是管路,不是 edge**:小样本 + long/flat 版,证明不了 BTC +0.12 会赚钱。系统可靠性 与 策略盈利 **分开验,别混**。

## 代码
- `strategy_runner.py`:复用 `execution.py`(connect/guarded_create/show_order)+ `strategy.py`(regime_switch_signal)。`--target {0,1}` 覆盖信号逼管路点火(plumbing test),`--reset` 清账本。本地账本 `runner_ledger.json`。
- 离线自检:brain 路径 OK(当前信号 target=0),cid 16 字符(< Binance 36 上限)。执行半边需用户 testnet 密钥实跑(L9-11 已跑通,密钥在)。
- 词表 +3(信号→执行闭环/纸上交易/dry-run)。首选源 freqtrade dry-run + ccxt orders。

## 动手结果(2026-08-10):第一枪打中 + 纸上交易抓到真 bug
- **步骤① `--reset --target 1` 成功点火全程**:buy intended 0.0003 → filled 0.0003(全成)@ $65,253.56,cid run-buy-20260809,账本 position=1/coin=0.0003 记的是实成。六零件一次串通 = capstone 成立。
- **抓到真 live bug**:第二次跑(同一根 bar 幂等路径)崩 —— `bar_obj`(tz-aware UTC)vs 存的 `last_bar`(naive 日期串)比较抛 TypeError;且 `and` 从左到右求值,`--target` 覆盖没能短路先撞比较。**回测撞不到(没有"重启重跑同一 bar"),只有活循环暴露** = 纸上交易存在的意义现场兑现。已修:改 ISO 日期字符串比较 + `forced_target is None` 提到条件最前短路。
- **①③⑤ 全绿(2026-08-10)**:①开仓 buy filled 0.0003 @ $65,253.56→position=1;③平仓 sell filled 0.0003 @ $65,224.79→position=0/coin=0;⑤kill→--target 1 被风控拒单、账本不变。**六零件焊成能开/关/叫停的机器,真实撮合上跑通** = 使命"回测→纸上交易"打勾。
- 白捡体感:一个空转来回亏 ~4.4bps(费+点差),回测 `FEE=0.1%` 的实体第一次被摸到 —— 薄 edge 难赚的根因现场。
- **对不上的地方(下一步动因)**:系统跑 long/flat,但 L16 验证出正夏普的是**双边(做空)版**;且下单量是硬编码 $20 名义(拍脑袋),无仓位管理。

## 岔路
- 下一步:①循环跑几天攒 track record;②**perp 测试网**真执行做空 + 实测 funding;③仓位管理(波动率目标/固定风险),下单量不再拍脑袋固定名义;④掉头股票赛道。见 [[0018-l16-shorting-breaks-ceiling-on-btc-but-not-free]]。
