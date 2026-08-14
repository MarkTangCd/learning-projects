"""L26 autopsy: decompose the L25 refutation into named, numbered killers.

MODE SWITCH — read this first. L25 was PREDICTION: criteria locked, one run,
verdict binding ([[0030]]: REFUTED 0/5). This file is POSTDICTION: the verdict
data is open, and we are now legally looking for patterns in it. Both modes are
legitimate; mixing them is the sin (Nosek, PNAS 2018). Concretely:

    An autopsy can NAME SUSPECTS. It cannot ACQUIT OR CONVICT.
    Any "fixed" machine suggested by these numbers is a NEW hypothesis,
    and certifying it on this same data would be the exact move that
    pre-registration exists to prevent.

Three cuts, three commands:

  parts    additive attribution — net return = long side + short side − costs,
           per bar, summing exactly. Which term killed each ticker?
  ladder   counterfactual ladder — two-sided net -> two-sided gross ->
           long/flat net -> buy-and-hold. Each gap isolates one decision.
  climate  the environment transfer — the SAME short trigger (SMA 20<60),
           pulled on crypto-home vs on stocks: what did the market do NEXT?
           Plus time-underwater: long grinding bears vs V-shaped crashes.

Run:  python autopsy.py parts
      python autopsy.py ladder
      python autopsy.py climate
"""

import sys

import numpy as np
import pandas as pd

from backtest import backtest_next_open
from holdout_stocks import (CARRY, FEE, MAX_LEVERAGE, SINCE, TARGET_VOL,
                            UNIVERSE, VOL_WINDOW, build_folds)
from oos import score, sharpe_key
from param_stability import GRID, neighbourhood
from sizing import realized_vol
from stocks import fetch_stock
from strategy import fetch_ohlcv, regime_switch_signal

BANNER = ("尸检 = 生成假设模式。嫌疑人可以指认,判决不能重开;\n"
          "此处冒出的任何『改好』都不得在同一段数据上宣布胜利。\n")


def machine_frames(price, long_short=True):
    """Full backtest frame per grid cell — the L25 machine, byte-identical
    (same weights, fees, carry, fills), except long_short is now a knob so the
    ladder can ask 'what if it never shorted'."""
    ret = price["close"].pct_change()
    weight = (TARGET_VOL / realized_vol(ret, VOL_WINDOW)).clip(upper=MAX_LEVERAGE)
    frames = {}
    for w, t in GRID:
        sig = regime_switch_signal(price, er_window=w, er_thresh=t, long_short=long_short)
        sig["signal"] = sig["signal"] * weight
        frames[(w, t)] = backtest_next_open(sig, fee=FEE, funding=CARRY)
    return frames


def stitch_plateau(price, frames):
    """Reconstruct the exact strategy method ((3)) traded in L25: per fold, pick
    the best train-window NEIGHBOURHOOD, then keep that cell's TEST slice —
    but this time keep the whole frame (position/ret/cost), not just returns."""
    folds = list(build_folds(len(price)))
    segs = []
    for tr_lo, tr_hi, te_lo, te_hi in folds:
        tr = {p: sharpe_key(score(frames[p]["strat_ret_net"].iloc[tr_lo:tr_hi]))
              for p in GRID}
        pick = max(GRID, key=lambda p: np.mean([tr[q] for q in neighbourhood(p)]))
        segs.append(frames[pick].iloc[te_lo:te_hi])
    return pd.concat(segs)


def cmd_parts():
    """Per-bar identity: strat_ret_net = pos·ret[pos>0] + pos·ret[pos<0] − cost.
    Three killers, annualized, summing exactly to the verdict number."""
    print(BANNER)
    print("① 归因恒等式:净收益 = 多头贡献 + 空头贡献 − 成本(逐 bar 相加,分毫不差)\n")
    print(f"  {'标的':<7}{'多头/年':>9}{'空头/年':>9}{'成本/年':>9}{'合计/年':>9}"
          f"{'核对(实际)':>12}{'空仓时间':>9}")
    for sym in UNIVERSE:
        price = fetch_stock(sym, since=SINCE)
        df = stitch_plateau(price, machine_frames(price)).dropna(subset=["position"])
        years = len(df) / 252
        long_c = (df["position"].clip(lower=0) * df["ret"]).sum() / years
        short_c = (df["position"].clip(upper=0) * df["ret"]).sum() / years
        cost_c = -df["cost"].sum() / years
        actual = df["strat_ret_net"].sum() / years
        short_time = (df["position"] < 0).mean()
        print(f"  {sym:<7}{long_c:>9.1%}{short_c:>9.1%}{cost_c:>9.1%}"
              f"{long_c + short_c + cost_c:>9.1%}{actual:>12.1%}{short_time:>9.0%}")
    print("\n  读法:哪一列最负,哪个就是这只票的主凶。合计=核对列 —— 恒等式,")
    print("  不是近似:每一分亏损都必须能指认到多头、空头或成本三者之一。")


def cmd_ladder():
    """Counterfactual ladder. Each rung changes ONE thing; each gap has a name.
    Every rung except the top two is a NEW backtest on opened data —
    hypothesis generation, clearly labeled."""
    print(BANNER)
    print("② 反事实阶梯:每一级只改一件事,级差就是那件事的价格\n")
    for sym in UNIVERSE:
        price = fetch_stock(sym, since=SINCE)
        two = machine_frames(price, long_short=True)
        lf = machine_frames(price, long_short=False)
        df2 = stitch_plateau(price, two)
        dflf = stitch_plateau(price, lf)
        folds = list(build_folds(len(price)))
        lo, hi = folds[0][2], folds[-1][3]
        bh = score(price["close"].pct_change().iloc[lo:hi])

        rows = (("③双边·净(=L25判决)", score(df2["strat_ret_net"])),
                ("③双边·零成本", score(df2["strat_ret"].dropna())),
                ("③长平·净(空头拔掉)", score(dflf["strat_ret_net"])),
                ("买入持有", bh))
        print(f"  {sym}")
        print(f"    {'层级':<22}{'Sharpe':>8}{'CAGR':>9}{'MaxDD':>9}")
        for name, s in rows:
            print(f"    {name:<22}{s['sharpe']:>8.2f}{s['cagr']:>9.1%}{s['mdd']:>9.1%}")
        print()
    print("  级差读法:1→2 = 成本的价格;1→3 = 空头的价格(注意 3 仍远输 4:")
    print("  拔掉空头也救不回来的部分 = 择时本身在赔)。第 3 层是全新回测 = 新假设,")
    print("  它的任何好看之处都要新数据才能算数。")


def _underwater(close):
    eq = (1 + close.pct_change().fillna(0)).cumprod()
    dd = eq / eq.cummax() - 1
    trough = dd.idxmin()
    pre = dd.loc[:trough]
    peak = pre[pre == 0].index[-1]
    post = dd.loc[trough:]
    rec = post[post == 0].index
    to_trough = len(dd.loc[peak:trough]) - 1
    to_rec = (len(dd.loc[trough:rec[0]]) - 1) if len(rec) else None
    spell = (dd < 0).astype(int)
    longest = int(spell.groupby((spell == 0).cumsum()).cumsum().max())
    return dd.min(), to_trough, to_rec, longest


def cmd_climate():
    """The transfer question, made falsifiable: the machine's short TRIGGER is
    the same everywhere (SMA fast<slow, family default 20/60). What the market
    did AFTER the trigger is what differs — that is the climate."""
    print(BANNER)
    print("③ 气候差:同一根扳机,扣动之后市场做了什么?\n")
    frames = [("BTC(机器老家)", fetch_ohlcv(symbol="BTC/USDT", since="2021-01-01",
                                        limit=1000))]
    frames += [(sym, fetch_stock(sym, since=SINCE)) for sym in UNIVERSE]

    print(f"  {'市场':<14}{'扳机激活时间':>10}{'扣动后次bar均值':>14}"
          f"{'最深回撤':>9}{'跌落用时':>9}{'收复用时':>9}{'最长水下':>9}")
    for label, price in frames:
        below = (price["close"].rolling(20).mean()
                 < price["close"].rolling(60).mean())
        fwd = price["close"].pct_change().shift(-1)
        trig = fwd[below].mean() * 1e4
        mdd, to_t, to_r, longest = _underwater(price["close"])
        rec = f"{to_r}根" if to_r is not None else "未收复"
        print(f"  {label:<14}{below.mean():>10.0%}{trig:>12.1f}bp"
              f"{mdd:>9.1%}{f'{to_t}根':>9}{rec:>9}{f'{longest}根':>9}")
    print("\n  「扣动后次bar均值」= SMA(20)<SMA(60) 成立的那些 bar,下一根的平均收益。")
    print("  负 = 做空有肉;正 = 做空在给别人送钱。同一行代码,两种气候,两个符号。")
    print("  「跌落/收复用时」= 最深那次回撤从顶到底、从底回顶各用几根 bar ——")
    print("  长熊(跌得久)喂饱趋势空头;V 型(收复快)绞杀它。")


COMMANDS = {"parts": cmd_parts, "ladder": cmd_ladder, "climate": cmd_climate}

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "parts"
    if cmd not in COMMANDS:
        raise SystemExit(f"用法: python autopsy.py [{'|'.join(COMMANDS)}]")
    COMMANDS[cmd]()
