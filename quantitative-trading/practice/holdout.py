"""L22 verdict: ONE run on data no lesson has ever touched.

Every number from L1 to L22 was measured on 2021-01-01 -> 2023-09-27. Across
those lessons the grid was searched, the fee was recalibrated, the OOS surface
was read twice, and three assets were tried. You cannot count those looks, so
you cannot correct for them with a Deflated-Sharpe-style penalty.

A segment of data that has never been opened needs no correction at all.

The machine is welded shut BEFORE this file runs:
  - grid          GGRID, frozen since L14
  - selection     method ③ — pick the best NEIGHBOURHOOD on the train window
  - fee           4 bp/side, measured on the live perp venue in L20/L21
  - vol target    20%, chosen in L18 from a max-drawdown red line
  - funding       1 bp/day

PRE-REGISTERED reading (agreed before the data was opened):
  BTC Sharpe > 0.4 and CAGR > 0  -> real signal; proceed to a small live wiring
  BTC Sharpe 0 .. 0.4            -> probably an artefact of 2021-23; do not fund
  BTC Sharpe < 0                 -> the 0.67 was multiple testing; change course
  ETH or SOL turns positive      -> surprise; the signal family was underrated

Run ONCE. Do not re-run with different settings and keep the better answer.
"""

import numpy as np
import pandas as pd

from backtest import backtest
from oos import score, sharpe_key
from param_stability import GRID, neighbourhood, FEE, FUNDING, TARGET_VOL, SYMBOLS
from sizing import vol_target_position
from strategy import fetch_ohlcv, regime_switch_signal
from walkforward import build_folds

HOLDOUT_START = "2023-10-01"      # the day after the last bar any lesson has seen
METHODS = (("plateau", "③ 挑邻域最好 <- 判据"), ("best", "① 挑样本内最好"),
           ("topk", "② 样本内 top3 平均"), ("all", "④ 全网格等权"))


def nets_for(price):
    out = {}
    for w, t in GRID:
        df = regime_switch_signal(price, er_window=w, er_thresh=t, long_short=True)
        df = vol_target_position(df, target_vol=TARGET_VOL, max_leverage=3.0)
        out[(w, t)] = backtest(df, fee=FEE, funding=FUNDING)["strat_ret_net"]
    return out


def allocate(folds, nets, mode, k=3):
    segs = []
    for tr_lo, tr_hi, te_lo, te_hi in folds:
        tr = {p: sharpe_key(score(nets[p].iloc[tr_lo:tr_hi])) for p in GRID}
        if mode == "best":
            sel = [max(GRID, key=tr.get)]
        elif mode == "topk":
            sel = sorted(GRID, key=tr.get, reverse=True)[:k]
        elif mode == "plateau":
            sel = [max(GRID, key=lambda p: np.mean([tr[q] for q in neighbourhood(p)]))]
        else:
            sel = GRID
        segs.append(pd.concat([nets[p].iloc[te_lo:te_hi] for p in sel], axis=1).mean(axis=1))
    return pd.concat(segs)


if __name__ == "__main__":
    print("留出集判决 —— 这段数据在此之前从未被任何一课打开过\n")
    for sym in SYMBOLS:
        price = fetch_ohlcv(symbol=sym, since=HOLDOUT_START, limit=1000)
        folds = list(build_folds(len(price)))
        lo, hi = folds[0][2], folds[-1][3]
        nets = nets_for(price)
        bh = score(price["close"].pct_change().iloc[lo:hi])

        print(f"{'=' * 60}\n{sym}   {price.index[lo].date()} -> {price.index[hi - 1].date()}"
              f"   ({len(folds)} folds)\n{'=' * 60}")
        print(f"  {'方法':<22}{'Sharpe':>9}{'CAGR':>9}{'MaxDD':>9}")
        for mode, name in METHODS:
            s = score(allocate(folds, nets, mode))
            print(f"  {name:<20}{s['sharpe']:>9.2f}{s['cagr']:>9.1%}{s['mdd']:>9.1%}")
        print(f"  {'买入持有(及格线)':<18}{bh['sharpe']:>9.2f}{bh['cagr']:>9.1%}{bh['mdd']:>9.1%}\n")

    print("判决只读【方法③】那一行。其余三行是背景信息,不是判据 —— 事后改判据")
    print("等于把预注册作废,那正是本课要防的东西。")
