"""L14 practice: run the REGIME-SWITCH signal through the same walk-forward.

Third signal, same judge. The only signal-specific things are (again) the
param GRID and the one signal call. Everything else — folds, scoring — is
imported unchanged from L6/L7.

The honest question this must answer: does routing trend+reversion by regime
beat EITHER standalone family out of sample? If the combo can't clear its own
parts, the extra machinery is just overfitting dressed up. To keep the added
overfitting surface small, we FIX the sub-signals at family defaults and let
walk-forward tune ONLY the regime knobs (er_window, er_thresh) — one new
dimension, not six.

Compare the stitched OOS Sharpe here against:
  - reversion-alone OOS  (L13: Sharpe -0.18, CAGR -14.6%, MaxDD -46.1%)
  - buy & hold same span (Sharpe -0.28, CAGR -27.4%, MaxDD -66.9%)

Run:  python walkforward_regime.py
"""

import pandas as pd

from backtest import backtest
from metrics import sharpe
from oos import score, sharpe_key                         # reused UNCHANGED
from walkforward import build_folds, TRAIN_BARS, TEST_BARS  # reused UNCHANGED
from strategy import fetch_ohlcv, regime_switch_signal

# The ONLY signal-specific thing: regime knobs. Sub-signals stay at defaults.
GGRID = [(w, t) for w in (10, 20, 30) for t in (0.25, 0.35, 0.45)]


def label(p):
    return f"er>{p[1]},w={p[0]}"


if __name__ == "__main__":
    price = fetch_ohlcv(since="2021-01-01", limit=1000)  # bull + bear + recovery
    n = len(price)

    # Backtest each regime-knob combo once (ER + both sub-signals look backward
    # only -> no future leak across the series; same argument as L7/L13).
    nets = {p: backtest(regime_switch_signal(price, er_window=p[0], er_thresh=p[1]))["strat_ret_net"]
            for p in GGRID}
    bh_ret = price["close"].pct_change()

    folds = list(build_folds(n))
    print(f"数据 {price.index[0].date()} -> {price.index[-1].date()}  | rolling "
          f"walk-forward: train {TRAIN_BARS} / test {TEST_BARS}, {len(folds)} folds")
    print(f"\n{'fold':>4}{'test 区间':>26}{'选中参数':>14}"
          f"{'test_Shrp':>11}{'bh_Shrp':>9}")

    oos_segments, picks = [], []
    for k, (tr_lo, tr_hi, te_lo, te_hi) in enumerate(folds, 1):
        best = max(GGRID, key=lambda p: sharpe_key(score(nets[p].iloc[tr_lo:tr_hi])))
        seg = nets[best].iloc[te_lo:te_hi]
        oos_segments.append(seg)
        picks.append(best)
        te_shr = sharpe(seg)
        bh_shr = sharpe(bh_ret.iloc[te_lo:te_hi])
        span = f"{price.index[te_lo].date()}->{price.index[te_hi - 1].date()}"
        print(f"{k:>4}{span:>26}{label(best):>14}{te_shr:>11.2f}{bh_shr:>9.2f}")

    oos = pd.concat(oos_segments)
    span_lo, span_hi = folds[0][2], folds[-1][3]
    bh_span = bh_ret.iloc[span_lo:span_hi]

    wf, bh = score(oos), score(bh_span)
    print(f"\n=== 拼接样本外曲线 {price.index[span_lo].date()} -> "
          f"{price.index[span_hi - 1].date()} ===")
    print(f"regime-switch OOS: Sharpe {wf['sharpe']:+.2f}  "
          f"CAGR {wf['cagr']:+.1%}  MaxDD {wf['mdd']:.1%}")
    print(f"买入持有 同区间  : Sharpe {bh['sharpe']:+.2f}  "
          f"CAGR {bh['cagr']:+.1%}  MaxDD {bh['mdd']:.1%}   <-- 及格线")
    print(f"回归单飞(L13)   : Sharpe -0.18  CAGR -14.6%  MaxDD -46.1%   <-- 要赢的是这个")
    verdict = "跑赢" if wf["sharpe"] > bh["sharpe"] else "跑输"
    print(f"结论:regime 组合 滚动样本外 {verdict} 躺平;"
          f"是否 > 回归单飞(-0.18),看上面一行。")
    print(f"参数漂移:{len(folds)} 个 fold 选了 {len(set(picks))} 种不同参数。")
