# L19:把 vol 定量焊进 runner —— 下单量由风险目标 + 当下波动算出

用户选路线 = vol 定量接进 runner。承接 [[0020-l18-position-sizing-vol-targeting]](用户 vol 目标 30% 意图,修正后建议 20–22% 留缓冲)+ [[0019-l17-loop-closed-signal-drives-execution]](闭环但单量硬编码 $20)。

## 教学要点(集成课,新决定有三)
- **单量公式**:`目标敞口 = signal × weight × 配给资本`,`weight = vol目标 / 当前realized_vol`,截断到 MAX_LEVERAGE。硬编码 $20 消失。
- **① 向目标再平衡(非翻转 0/1)**:每 bar 算目标敞口→比当前持仓→只交易差额。**vol 定量削回撤的发动机 = 持仓中波动一涨就减仓**,只在入场定大小会漏掉;必须每 bar 对齐。
- **② 不动区间(no-trade band)**:差额 < 最小下单额就不动,防手续费 churn(呼应 L11 换手有成本)。
- **③ 对配给资本下注(demo $40)不对全部身家**:符合真实(钱分多策略);且单量落 L9 $50 闸门内,闸门作独立硬后备永不撤。
- **现货天花板**:平静市(波动 25%)想要 vol 目标 30% → weight=1.2 被**截到 1.0**(现货不能 >100% 仓)→ 够不到高目标要上 **perp 杠杆**(连 L16 funding)。截断也挡了悄悄加杠杆。

## 代码(离线自检 sizing 数学 OK)
- `sizing.py` +`vol_target_weight(returns, target_vol, window, max_leverage=1.0)`(取最后收盘 bar 的标量权重,无前视)。
- `strategy_runner.py` 重写:signal→weight→目标敞口→差额→不动区间→guarded_create(L9)→回读对账(L11)→账本记实成。`--vol` 设风险目标,`--target` 覆盖信号,`--reset`。
- 自检:当前信号 flat;当前波动 25% → vol 目标 20%→权重 0.80、22%→0.88、30%→1.0(1.2 被截)。
- **简化(诚实标注)**:sizing 对固定配给资本(非 mark-to-market equity)。

## 待办 / 岔路
- 用户跑 ① `--reset --target 1 --vol 0.22`(看算出的单量)③ `--vol 0.10 vs 0.30`(敞口随目标缩放 + 0.30 权重截断)贴输出 → 确认风险决定驱动了单量。
- 下一步:①**perp 测试网**(双边+杠杆+实测 funding,补现货落不了地的部分)= 收敛 L16/L18/L19 遗留;②循环攒按真实风险下注的 track record;③多资产 vol 标准化合仓;④股票赛道。见 [[0020-l18-position-sizing-vol-targeting]]。
