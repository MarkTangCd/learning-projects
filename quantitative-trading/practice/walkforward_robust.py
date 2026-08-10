"""L15 practice: robustness — run the SAME frozen machine on a DIFFERENT asset.

The regime combo cleared its BTC gauntlet (L14: OOS Sharpe -0.02, beat both
reversion-solo -0.18 and buy&hold -0.28, and patched the fold-5 rebound). But
one asset over one span is one draw. The scariest failure mode in quant is an
"edge" that is really just overfitting to BTC-2022's exact wiggles.

The only honest test: FREEZE everything and re-run on another asset. Same folds,
same grids, same fixed sub-signal defaults — nothing re-tuned for the new symbol.
If we hand-tune for ETH, we've just overfit asset #2 and learned nothing.

We print, on the given asset, three stitched OOS curves so the combo has to beat
its own parts AND buy & hold on a market it has never seen:
    regime combo   vs   reversion-solo   vs   buy & hold

The question is NOT "is the number identical to BTC" (it won't be). It's:
does the SHAPE hold? — combo still beats both parts, still beats hold, drift not
wildly worse. Shape holds -> edge more likely real. Shape breaks -> BTC was luck.

Run:  python walkforward_robust.py            # default ETH/USDT
      python walkforward_robust.py BTC/USDT   # re-run BTC as the anchor
      python walkforward_robust.py SOL/USDT   # try a third
"""

import sys

import pandas as pd

from backtest import backtest
from metrics import sharpe
from oos import score, sharpe_key                          # reused UNCHANGED
from walkforward import build_folds, TRAIN_BARS, TEST_BARS  # reused UNCHANGED
from strategy import fetch_ohlcv, regime_switch_signal, zscore_reversion_signal

# Both grids are FROZEN at their L13/L14 values. Do not touch them per asset.
GGRID = [(w, t) for w in (10, 20, 30) for t in (0.25, 0.35, 0.45)]  # regime knobs
RGRID = [(lb, e) for lb in (10, 20, 30) for e in (1.0, 1.5, 2.0)]   # reversion knobs


def stitch_oos(nets, grid, folds):
    """Walk-forward: each train window self-picks its best param; splice the
    out-of-sample test segments. Returns (stitched_net_returns, picks)."""
    segments, picks = [], []
    for tr_lo, tr_hi, te_lo, te_hi in folds:
        best = max(grid, key=lambda p: sharpe_key(score(nets[p].iloc[tr_lo:tr_hi])))
        segments.append(nets[best].iloc[te_lo:te_hi])
        picks.append(best)
    return pd.concat(segments), picks


if __name__ == "__main__":
    symbol = sys.argv[1] if len(sys.argv) > 1 else "ETH/USDT"
    price = fetch_ohlcv(symbol=symbol, since="2021-01-01", limit=1000)
    n = len(price)
    folds = list(build_folds(n))

    # Backtest every combo once per family (all look backward only -> no leak).
    regime_nets = {p: backtest(regime_switch_signal(price, er_window=p[0], er_thresh=p[1]))["strat_ret_net"]
                   for p in GGRID}
    rev_nets = {p: backtest(zscore_reversion_signal(price, lookback=p[0], entry=p[1]))["strat_ret_net"]
                for p in RGRID}
    bh_ret = price["close"].pct_change()

    print(f"资产 {symbol}  |  数据 {price.index[0].date()} -> {price.index[-1].date()}  |  "
          f"train {TRAIN_BARS} / test {TEST_BARS}, {len(folds)} folds  (machine FROZEN)")

    reg_oos, reg_picks = stitch_oos(regime_nets, GGRID, folds)
    rev_oos, rev_picks = stitch_oos(rev_nets, RGRID, folds)
    span_lo, span_hi = folds[0][2], folds[-1][3]
    bh_span = bh_ret.iloc[span_lo:span_hi]

    reg, rev, bh = score(reg_oos), score(rev_oos), score(bh_span)
    print(f"\n=== 拼接样本外 {price.index[span_lo].date()} -> {price.index[span_hi - 1].date()} ===")

    def line(tag, s, note=""):
        print(f"{tag:<16}: Sharpe {s['sharpe']:+.2f}  CAGR {s['cagr']:+.1%}  "
              f"MaxDD {s['mdd']:.1%}  {note}")

    line("regime 组合", reg, "<-- 复杂策略")
    line("回归单飞", rev, "<-- 要赢的零件之一")
    line("买入持有", bh, "<-- 及格线")

    # Verdict: the SHAPE test. Both must hold for the edge to look transferable.
    beats_hold = reg["sharpe"] > bh["sharpe"]
    beats_part = reg["sharpe"] > rev["sharpe"]
    shape = "保持" if (beats_hold and beats_part) else "破了"
    print(f"\n形状判决:组合 {'>' if beats_hold else '<='} 躺平 且 "
          f"{'>' if beats_part else '<='} 回归单飞  ->  {shape}")
    print(f"参数漂移:regime {len(set(reg_picks))}/{len(folds)} 种  |  "
          f"回归 {len(set(rev_picks))}/{len(folds)} 种")
    print("\n对照 BTC(L14):组合 -0.02 > 回归 -0.18 > 躺平 -0.28,漂移 5/7。")
    print("读法:形状'保持'= edge 更可能是真的;'破了'= BTC 那次八成是过拟合花衣裳。")
