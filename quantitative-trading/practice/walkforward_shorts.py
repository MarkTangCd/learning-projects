"""L16 practice: break the long-only ceiling — let the signals SHORT.

Every strategy in L12-L15 was long/flat. In a multi-year crypto bear that caps
the best case at 'lose less' -> out-of-sample Sharpe stayed <= 0 on all assets.
A two-sided signal can be SHORT in downtrends, so it can actually PROFIT when
price falls. Question: does that finally push Sharpe positive?

Nothing about the judge changes. The backtest already handles shorts (position
* ret inverts; a long<->short flip is 2x turnover). The ONLY honest addition is
FUNDING — perps charge carry to hold either side, so shorting is not free. We
run the SAME frozen walk-forward, now with long_short=True + funding, and put
the two-sided combo next to the long-only combo (L14/L15) and buy & hold.

Read ALL THREE columns (Sharpe / CAGR / MaxDD), not the one-line verdict — L15
taught us a single metric can hide the truth.

Run:  python walkforward_shorts.py                 # BTC, ETH, SOL
      python walkforward_shorts.py --funding 0.0   # turn carry off to compare
"""

import sys

import pandas as pd

from backtest import backtest
from oos import score, sharpe_key                          # reused UNCHANGED
from walkforward import build_folds, TRAIN_BARS, TEST_BARS  # reused UNCHANGED
from strategy import fetch_ohlcv, regime_switch_signal

GGRID = [(w, t) for w in (10, 20, 30) for t in (0.25, 0.35, 0.45)]  # FROZEN
SYMBOLS = ("BTC/USDT", "ETH/USDT", "SOL/USDT")


def stitch(price, long_short, funding, folds):
    """Walk-forward stitch of the regime combo (two-sided if long_short)."""
    nets = {p: backtest(regime_switch_signal(price, er_window=p[0], er_thresh=p[1],
                                             long_short=long_short),
                        funding=funding)["strat_ret_net"]
            for p in GGRID}
    segs, picks = [], []
    for tr_lo, tr_hi, te_lo, te_hi in folds:
        best = max(GGRID, key=lambda p: sharpe_key(score(nets[p].iloc[tr_lo:tr_hi])))
        segs.append(nets[best].iloc[te_lo:te_hi])
        picks.append(best)
    return pd.concat(segs), len(set(picks))


if __name__ == "__main__":
    funding = 0.0001  # ~1 bp/day carry on |position|; --funding X overrides
    if "--funding" in sys.argv:
        funding = float(sys.argv[sys.argv.index("--funding") + 1])

    print(f"双边(做空)regime 组合 vs 只做多组合 vs 躺平  |  funding={funding:.4%}/bar\n")
    print(f"{'资产':<10}{'':<14}{'Sharpe':>9}{'CAGR':>9}{'MaxDD':>9}")

    for sym in SYMBOLS:
        price = fetch_ohlcv(symbol=sym, since="2021-01-01", limit=1000)
        folds = list(build_folds(len(price)))
        ls_oos, ls_drift = stitch(price, True, funding, folds)   # two-sided
        lo_oos, _ = stitch(price, False, 0.0, folds)             # long-only (no carry)
        span_lo, span_hi = folds[0][2], folds[-1][3]
        bh = price["close"].pct_change().iloc[span_lo:span_hi]

        ls, lo, b = score(ls_oos), score(lo_oos), score(bh)
        print(f"{sym:<10}{'双边组合':<12}{ls['sharpe']:>9.2f}{ls['cagr']:>9.1%}{ls['mdd']:>9.1%}"
              f"   漂移 {ls_drift}/{len(folds)}")
        print(f"{'':<10}{'只做多组合':<11}{lo['sharpe']:>9.2f}{lo['cagr']:>9.1%}{lo['mdd']:>9.1%}")
        print(f"{'':<10}{'买入持有':<12}{b['sharpe']:>9.2f}{b['cagr']:>9.1%}{b['mdd']:>9.1%}")
        win = "✓ 转正" if ls["sharpe"] > 0 else ("↑赢只做多" if ls["sharpe"] > lo["sharpe"] else "✗ 没帮上")
        print(f"{'':<10}--> 做空效果:{win}\n")

    print("读法:看 Sharpe 有没有首次 > 0(真 edge),或至少 > 只做多组合(做空有贡献)。")
    print("别忘了读全三列 + funding 敏感性(--funding 0.0 关掉看还剩多少)。")
