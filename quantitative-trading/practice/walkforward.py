"""L7 practice: rolling walk-forward validation.

One train/test split (L6) is a single draw of regime luck. Walk-forward slides
the window forward many times -- re-optimize params on each train window, apply
the winner to the very next (unseen) test window, then STITCH all the test
segments into one continuous out-of-sample equity curve spanning many regimes.
That stitched curve averages the luck out -> a far more honest verdict.

Reuses L4 backtest + L5 metrics + L6 score/sharpe_key. One signal, reused.
"""

import pandas as pd

from backtest import backtest
from metrics import sharpe
from oos import GRID, score, sharpe_key
from strategy import fetch_ohlcv, sma_crossover_signal

TRAIN_BARS = 365  # rolling 1-year optimization window
TEST_BARS = 90    # apply the winner to the next quarter, then roll forward


def build_folds(n):
    """Yield (train_lo, train_hi, test_lo, test_hi) for a rolling walk-forward."""
    start = 0
    while start + TRAIN_BARS + TEST_BARS <= n:
        tr_hi = start + TRAIN_BARS
        yield start, tr_hi, tr_hi, tr_hi + TEST_BARS
        start += TEST_BARS  # non-overlapping test segments


if __name__ == "__main__":
    price = fetch_ohlcv(since="2021-01-01", limit=1000)  # bull + bear + recovery
    n = len(price)

    # Backtest each param on the full series ONCE (SMA looks only backward -> no leak).
    nets = {p: backtest(sma_crossover_signal(price, p[0], p[1]))["strat_ret_net"]
            for p in GRID}
    bh_ret = price["close"].pct_change()

    folds = list(build_folds(n))
    print(f"数据 {price.index[0].date()} -> {price.index[-1].date()}  | rolling "
          f"walk-forward: train {TRAIN_BARS} / test {TEST_BARS}, {len(folds)} folds")
    print(f"\n{'fold':>4}{'test 区间':>26}{'选中参数':>12}"
          f"{'test_Shrp':>11}{'bh_Shrp':>9}")

    oos_segments, picks = [], []
    for k, (tr_lo, tr_hi, te_lo, te_hi) in enumerate(folds, 1):
        # Optimize on THIS train window only, by in-sample Sharpe.
        best = max(GRID, key=lambda p: sharpe_key(score(nets[p].iloc[tr_lo:tr_hi])))
        seg = nets[best].iloc[te_lo:te_hi]        # winner's UNSEEN test returns
        oos_segments.append(seg)
        picks.append(best)
        te_shr = sharpe(seg)
        bh_shr = sharpe(bh_ret.iloc[te_lo:te_hi])
        span = f"{price.index[te_lo].date()}->{price.index[te_hi - 1].date()}"
        print(f"{k:>4}{span:>26}{f'({best[0]},{best[1]})':>12}"
              f"{te_shr:>11.2f}{bh_shr:>9.2f}")

    # Stitch every test segment into one continuous out-of-sample curve.
    oos = pd.concat(oos_segments)
    span_lo, span_hi = folds[0][2], folds[-1][3]
    bh_span = bh_ret.iloc[span_lo:span_hi]

    wf, bh = score(oos), score(bh_span)
    print(f"\n=== 拼接样本外曲线 {price.index[span_lo].date()} -> "
          f"{price.index[span_hi - 1].date()} ===")
    print(f"walk-forward OOS: Sharpe {wf['sharpe']:+.2f}  "
          f"CAGR {wf['cagr']:+.1%}  MaxDD {wf['mdd']:.1%}")
    print(f"买入持有 同区间 : Sharpe {bh['sharpe']:+.2f}  "
          f"CAGR {bh['cagr']:+.1%}  MaxDD {bh['mdd']:.1%}   <-- 及格线")
    verdict = "跑赢" if wf["sharpe"] > bh["sharpe"] else "跑输"
    print(f"结论:滚动样本外 {verdict} 躺平。")
    print(f"参数漂移:{len(folds)} 个 fold 选了 {len(set(picks))} 种不同参数 "
          f"—— 越少越稳,越乱说明没有稳定最优(危险信号)。")
