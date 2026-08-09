# L14:regime 过滤(趋势+回归按 regime 路由)—— 组合信号,同一台裁判第三次

用户选路线 A 内的 **regime 过滤**。承接 L13 判决([[0014-mean-reversion-verdict-downside-protection-not-edge]]):均值回归 = 下跌保护、软肋在单边上涨(fold 5),趋势反之——两者软肋错开,motivate 组合。

## 教学要点
- **regime = 市场性格**(趋势市 vs 震荡市);同一信号不同 regime 天差地别(承 [[0005-scorecard-and-regime-dependence]])。
- **Efficiency Ratio 检测器**:`|净位移|/总路程`,ER→1 趋势、ER→0 震荡。纯 pandas。走路比喻(直线 vs 原地踱步)。
- **组合=路由器不发明新逻辑**:ER>thresh 用 SMA signal,否则用 reversion signal,一次干净 shift。照样吐 position → gauntlet 第四次复用(L1 红利)。
- **核心纪律(本课灵魂)**:组合有 6 旋钮 = 大过拟合面。钉死子信号默认值、只调 regime 1-2 旋钮。**奥卡姆剃刀:复杂度必须样本外自证其值;组合打不过零件单飞就砍掉。**

## 代码(全部离线验证)
- `strategy.py` +`efficiency_ratio(close, window)` +`regime_switch_signal(...)`。离线验路由:上涨段 ER≈1.0→trend、震荡段 ER≈0.06→range,position 仅 0/1/NaN。✅
- `walkforward_regime.py`:regime 组合过同一 walk-forward,只调 (er_window, er_thresh) 9 组网格;三行并排打印 组合/买入持有/回归单飞(-0.18)。端到端离线跑通。✅
- 词表 +5(市场状态/regime 过滤/Efficiency Ratio/奥卡姆剃刀量化版)。首选源 QuantStart HMM regime detection + Chan regime switching 章。

## 判据(讲给用户的诚实标准)
组合样本外 Sharpe **必须 > 回归单飞 −0.18 且 > 躺平**才算成立。特别看 **fold 5(2022-12→2023-03 反弹)**:组合有没有切到趋势把这一 fold 扳回来 = regime 过滤成立命门。打平/更差 → 砍掉,选更简单的。

## 待办 / 岔路
- 用户跑 `walkforward_regime.py` 贴输出 → 判组合是真互补还是过拟合花衣裳。
- 若成立 → 样本外再切/换资产/上小资金(路线 B);若也躺平 → **认真考虑掉头股票赛道**(均值回归股票史更扎实)或引入更强特征/ML。
