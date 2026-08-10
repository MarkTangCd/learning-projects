# L18:仓位管理 —— 波动率目标定量,风险旋钮独立于 edge

用户选路线 = 仓位管理。承接 [[0019-l17-loop-closed-signal-drives-execution]]:系统闭环但下单量硬编码 $20(风险瞎子),上真钱前必修。

## 教学要点
- **"下多大"是独立于"赌哪边"的一层**。风险瞎子(满仓 ±1 / 固定名义)在崩盘里过度暴露。
- **波动率目标定量(vol targeting)**:`weight = target_vol / realized_vol` 截断到杠杆上限。危险时缩、平静时放,治好 L16"永远满仓被崩盘重创"。realized_vol 用决策时点(shift(1))防前视。
- **核心洞察:vol 目标是风险旋钮,不改 edge**。Sharpe ≈信号属性(拧目标几乎不动),你能改的只是"为收获这个 edge 承担多大风险"。按**能扛的最大回撤**反推目标,不按最大 CAGR(=风控偷换成过拟合)。
- **诚实:edge 薄且噪声 → 保守下注**。全 Kelly 假设确知 edge,噪声下过度下注一把归零 → 分数 Kelly / vol 定量。仓位管理首先是风控(决定错信号最多亏多少)。

## 代码(全部离线跑通)
- `sizing.py`:`realized_vol` + `vol_target_position`(纯叠加在 position 列,不碰信号,L1 接口第 7 次)。
- `sizing_compare.py`:BTC 双边组合 满仓 vs vol 定量,三列 + 实际波动 + 换手。

## 真实结果(BTC 双边组合,全样本口径仅演示 sizing;edge 仍以 L16 OOS +0.12 为准)
| vol 目标 | Sharpe | CAGR | MaxDD | 实际波动 |
|---|---|---|---|---|
| 满仓原始 | +0.32 | +1.5% | **−59.1%** | 59% |
| 10% | +0.35 | +3.2% | −13.1% | 11% |
| 20% | +0.35 | +5.4% | −25.2% | 21% |
| 40% | +0.36 | +6.4% | −46.0% | 42% |

- vol 定量把实际波动拉到目标;**回撤砍一半以上**(−59%→−25%@20%);Sharpe 不降反微升;CAGR 反升(躲开深回撤 → 少被波动率拖累吃复利)。
- **拧目标 Sharpe 几乎不动(0.35上下),回撤/收益同步缩放** = 风险旋钮实锤。
- 换手意外**降**(266→116@20%):连续调仓+换手,但仓位常<1 −换手,净降。已修脚本错误注解(原写"必升")。词表 +4(仓位管理/波动率定量/Kelly)。首选源 López de Prado AFML Bet Sizing + QuantStart Kelly。

## 待办 / 岔路
- 用户跑 `sizing_compare.py` + `--target 0.10/0.40` 贴输出,并回答"按自己风险承受力把目标定几"。
- 下一步:①把 vol 定量接进 L17 runner(下单量=weight×equity);②perp 测试网真跑双边+实测 funding;③循环攒 track record;④股票赛道。见 [[0019-l17-loop-closed-signal-drives-execution]]。
