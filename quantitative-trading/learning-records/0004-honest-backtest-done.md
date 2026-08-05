# L4 完成:诚实的向量化回测(收益 − 成本)

用户于 2026-08-05 独立跑通 L4:在 `practice/backtest.py` 里实现了向量化回测,复用 L3 的 `sma_crossover_signal`,算出 `strat_ret → cost → equity_net / equity_hold` 全链路,并**主动多做了一步**——用 matplotlib 把 `equity_net` vs `equity_hold` 画成收益曲线保存为 png(headless `savefig`)。

## Evidence
- 代码结构清晰:把回测拆成 `backtest()` / `report()` / `plot_equity()` 三个函数,`report` 里同时打印含成本、零成本、买入持有三条线 + 成交笔数,亲手兑现了 L4 的"让成本说话"。
- 保留了 `equity_gross`(零成本)一列专门做对比 → 已理解"成本拖累"这个量。
- 理解四步:`pct_change → position*ret → diff().abs()*FEE → cumprod`,全程无 for 循环。

## Implications
- 用户现在手里有一条**收益曲线**和"总收益 / 买入持有"两个数,但还只会看"赚了多少"。→ L5 正好承接:把 equity 曲线压成 **成绩单三数**(最大回撤、夏普、CAGR),教他看"值不值得拿"和"是不是过拟合"。
- 用户会主动加戏(自己上 matplotlib)→ 说明动手能力强,L5 可以直接给"往 backtest 里加 metrics()"的挑战,难度可略升。
- 教学节奏延续:可运行代码 + 关键行解释 + 一个动手挑战 + 悬念(9/6/11 → 现在用夏普/回撤重新给三组参数排名)。
