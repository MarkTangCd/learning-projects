"""L22 practice: the parameter you pick is a bigger bet than the fee you assume.

L21 measured the real trading fee (4 bp/side) and re-priced the L16 machine. The
by-product was more important than the answer:

    filling the FEE in wrong by 6 bp  ->  Sharpe moves 0.14
    stepping ONE cell on the grid     ->  Sharpe moves 1.85

Walk-forward already removed look-ahead: each fold picks its parameters using
only its TRAIN window. What it did NOT remove is SELECTION VARIANCE — the noise
you inherit from the act of choosing a single winner out of nine noisy estimates.
On 2 of 7 folds the in-sample winner was the worst out-of-sample family.

This script does not invent a new signal. It asks one question about the machine
you already have: HOW SHOULD YOU USE A GRID OF PARAMETERS?

  ① pick the single in-sample best      (what every lesson has done so far)
  ② average the in-sample top k         (partial diversification)
  ③ pick the best NEIGHBOURHOOD         (a plateau, not a peak)
  ④ average all of them, equally        (no selection at all)

All four use TRAIN-window information only, so all four are honest.

Run:  python param_stability.py            # grid map + 4 methods + k-sweep
      python param_stability.py ETH/USDT   # one asset
"""

import sys

import numpy as np
import pandas as pd

from backtest import backtest
from oos import score, sharpe_key
from sizing import vol_target_position
from strategy import fetch_ohlcv, regime_switch_signal
from walkforward import build_folds

WS = (10, 20, 30)                     # FROZEN since L14 — do not tune
TS = (0.25, 0.35, 0.45)
GRID = [(w, t) for w in WS for t in TS]
WIDE_WS = (3, 5, 8, 10, 15, 20, 30, 45)   # exploratory only — see the caveat printed below

FEE = 0.0004        # MEASURED on the perp venue in L20/L21 (4 bp/side taker)
FUNDING = 0.0001    # ~1 bp/day carry
TARGET_VOL = 0.20   # L18 risk dial; kills the vol drag that ate the CAGR in L21
SYMBOLS = ("BTC/USDT", "ETH/USDT", "SOL/USDT")


def build(price, params):
    """Net return series per parameter cell. Frozen machine — only the grid varies."""
    out = {}
    for w, t in params:
        df = regime_switch_signal(price, er_window=w, er_thresh=t, long_short=True)
        df = vol_target_position(df, target_vol=TARGET_VOL, max_leverage=3.0)
        out[(w, t)] = backtest(df, fee=FEE, funding=FUNDING)["strat_ret_net"]
    return out


def neighbourhood(p):
    """Grid cells within one step of p (Chebyshev), including p. A parameter whose
    NEIGHBOURS also score well is sitting on a plateau; one that scores well alone
    is a peak — and peaks are usually noise that will not be there next quarter."""
    i, j = WS.index(p[0]), TS.index(p[1])
    return [(WS[a], TS[b])
            for a in range(max(0, i - 1), min(len(WS), i + 2))
            for b in range(max(0, j - 1), min(len(TS), j + 2))]


def allocate(folds, nets, mode, k=3):
    """Stitch the out-of-sample segments under one selection policy.
    Every mode ranks parameters on the TRAIN slice only — no look-ahead."""
    segs = []
    for tr_lo, tr_hi, te_lo, te_hi in folds:
        tr = {p: sharpe_key(score(nets[p].iloc[tr_lo:tr_hi])) for p in GRID}
        if mode == "best":
            sel = [max(GRID, key=tr.get)]
        elif mode == "topk":
            sel = sorted(GRID, key=tr.get, reverse=True)[:k]
        elif mode == "plateau":
            sel = [max(GRID, key=lambda p: np.mean([tr[q] for q in neighbourhood(p)]))]
        else:                                   # "all" — equal weight, zero selection
            sel = GRID
        segs.append(pd.concat([nets[p].iloc[te_lo:te_hi] for p in sel], axis=1).mean(axis=1))
    return pd.concat(segs)


def map_grid(price, folds):
    """Print the OOS Sharpe surface. Are the good cells CLUSTERED (plateau, real
    structure) or SCATTERED (peaks, noise)? Read the shape, not the maximum."""
    lo, hi = folds[0][2], folds[-1][3]
    nets = build(price, [(w, t) for w in WIDE_WS for t in TS])
    print("样本外 Sharpe 曲面(含原网格之外的探索行):")
    print(f"  {'er_window':<11}" + "".join(f"{t:>9}" for t in TS) + f"{'行均值':>11}")
    for w in WIDE_WS:
        row = [score(nets[(w, t)].iloc[lo:hi])["sharpe"] for t in TS]
        tag = "  <- 冻结网格" if w in WS else ""
        print(f"  {w:<11}" + "".join(f"{v:>9.2f}" for v in row)
              + f"{np.mean(row):>11.2f}{tag}")
    print("  注意:这张表是【样本外】结果。看完它再去挑参数区间 = 用样本外数据做选择,")
    print("       那一刻它就不再是样本外的了。它只能用来判断【形状】,不能用来选参。\n")


def compare(price, folds):
    nets = build(price, GRID)
    print("同一台冻结机器,4 种「怎么用这 9 组参数」(全部只用样本内信息):")
    print(f"  {'方法':<24}{'Sharpe':>9}{'CAGR':>9}{'MaxDD':>9}")
    for mode, name in (("best", "① 挑样本内最好(现状)"), ("topk", "② 样本内 top3 平均"),
                       ("plateau", "③ 挑邻域最好(高原)"), ("all", "④ 全网格等权")):
        s = score(allocate(folds, nets, mode))
        print(f"  {name:<22}{s['sharpe']:>9.2f}{s['cagr']:>9.1%}{s['mdd']:>9.1%}")
    return nets


def sweep_k(nets_by_symbol):
    """k=1 is 'pick the best'; k=9 is 'equal-weight everything'. If the gain only
    appears at one k, it is luck. If it appears across k AND across assets, it is
    a property of the method. Spoiler: it is not."""
    print("\nk 敏感性 × 换资产 —— 集成到底是不是普遍有效?")
    print(f"  {'资产':<11}" + "".join(f"{'k=' + str(k):>8}" for k in range(1, 10)))
    for sym, (folds, nets) in nets_by_symbol.items():
        cells = "".join(f"{score(allocate(folds, nets, 'topk', k))['sharpe']:>8.2f}"
                        for k in range(1, 10))
        print(f"  {sym:<11}{cells}")
    print("  (k=1 = 挑最好,k=9 = 全网格等权)")


if __name__ == "__main__":
    symbols = (sys.argv[1],) if len(sys.argv) > 1 else SYMBOLS
    print(f"参数稳定性  |  fee={FEE:.2%}/边(实测)  funding={FUNDING:.2%}/bar  "
          f"vol目标={TARGET_VOL:.0%}\n")

    store = {}
    for sym in symbols:
        price = fetch_ohlcv(symbol=sym, since="2021-01-01", limit=1000)
        folds = list(build_folds(len(price)))
        print(f"{'=' * 64}\n{sym}\n{'=' * 64}")
        if sym == symbols[0]:
            map_grid(price, folds)
        store[sym] = (folds, compare(price, folds))
        print()
    sweep_k(store)

    print("\n读法:")
    print("  ①→④ 的差距 = 【选择方差】的代价,和信号本身无关。")
    print("  但换资产看:集成【不制造 edge】,它只降低「你拿到哪个参数」的方差。")
    print("  均值是负的时候,降方差 = 更可靠地亏钱。")
