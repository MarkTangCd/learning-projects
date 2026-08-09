"""L13 practice: run the mean-reversion signal through the SAME walk-forward.

The L7 gauntlet (walkforward.py) was hardcoded to SMA. But the rolling
optimize-on-train / apply-on-next-test / stitch-the-OOS-curve LOGIC is
identical for any signal — only two things change:
    1. the param GRID (mean-reversion knobs, not SMA windows)
    2. the one line that turns a param into net returns (the signal call)

So we import the fold machinery and scoring UNCHANGED from L6/L7 and swap in
the reversion signal. Same judge, new signal — the honest way to test the
second family with the exact skepticism that killed SMA.

Crucial: we do NOT hand-pick lookback/entry. Twiddling them on one window
(what L12 did) is overfitting. Walk-forward RE-OPTIMIZES on each train window
and is graded on the next unseen one. The verdict lives in the stitched OOS
curve, not in any single-window number.

Run:  python walkforward_reversion.py
"""

import pandas as pd

from backtest import backtest
from metrics import sharpe
from oos import score, sharpe_key          # reused UNCHANGED from L6
from walkforward import build_folds, TRAIN_BARS, TEST_BARS  # reused from L7
from strategy import fetch_ohlcv, zscore_reversion_signal

# The reversion param grid — the ONLY signal-specific thing here.
RGRID = [(lb, e) for lb in (10, 20, 30) for e in (1.0, 1.5, 2.0)]


def label(p):
    return f"z<{-p[1]},lb={p[0]}"


if __name__ == "__main__":
    price = fetch_ohlcv(since="2021-01-01", limit=1000)  # bull + bear + recovery
    n = len(price)

    # Backtest each param on the full series ONCE. The z-score uses only a
    # trailing rolling window -> it looks backward only -> computing across the
    # whole series leaks no future (same argument as SMA in L7).
    nets = {p: backtest(zscore_reversion_signal(price, lookback=p[0], entry=p[1]))["strat_ret_net"]
            for p in RGRID}
    bh_ret = price["close"].pct_change()

    folds = list(build_folds(n))
    print(f"数据 {price.index[0].date()} -> {price.index[-1].date()}  | rolling "
          f"walk-forward: train {TRAIN_BARS} / test {TEST_BARS}, {len(folds)} folds")
    print(f"\n{'fold':>4}{'test 区间':>26}{'选中参数':>14}"
          f"{'test_Shrp':>11}{'bh_Shrp':>9}")

    oos_segments, picks = [], []
    for k, (tr_lo, tr_hi, te_lo, te_hi) in enumerate(folds, 1):
        # Re-optimize on THIS train window only (in-sample Sharpe). No hand-picking.
        best = max(RGRID, key=lambda p: sharpe_key(score(nets[p].iloc[tr_lo:tr_hi])))
        seg = nets[best].iloc[te_lo:te_hi]        # winner's UNSEEN test returns
        oos_segments.append(seg)
        picks.append(best)
        te_shr = sharpe(seg)
        bh_shr = sharpe(bh_ret.iloc[te_lo:te_hi])
        span = f"{price.index[te_lo].date()}->{price.index[te_hi - 1].date()}"
        print(f"{k:>4}{span:>26}{label(best):>14}{te_shr:>11.2f}{bh_shr:>9.2f}")

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
    print(f"结论:均值回归 滚动样本外 {verdict} 躺平。")
    print(f"参数漂移:{len(folds)} 个 fold 选了 {len(set(picks))} 种不同参数 "
          f"—— 越少越稳,越乱说明没有稳定最优(危险信号)。")
