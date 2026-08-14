"""L25 verdict: ONE pre-registered run of the frozen machine on stocks.

The machine was built, tuned and judged entirely on crypto (L12-L22). No stock
data ever influenced any of its knobs. That makes the stock panel an
INDEPENDENT sample for the machine — provided every decision about HOW to run
it there is written down BEFORE the data is opened. This docstring is that
document. It is frozen. Changing it after seeing results voids the test.

===========================================================================
PRE-REGISTRATION  (locked 2026-08-12, before any stock run of this machine)
===========================================================================

THE FROZEN MACHINE (all knobs inherited, none re-tuned for stocks):
  - signal        regime_switch_signal, long_short=True     (L14/L16)
  - grid          GRID = WS(10,20,30) x TS(0.25,0.35,0.45)  (frozen since L14)
  - selection     method ((3)) — best NEIGHBOURHOOD on the train window (L22)
  - sizing        vol target 20%, window 20                 (L18)
  - fills         NEXT OPEN, shift(2)                       (L24)
  - calendar      inferred from the data, snapped           (L23)

VENUE ADAPTATIONS (from rules, not from any stock result):
  - fee           5 bp/side       — the L24 stand-in for spread + slippage
  - carry         0.5%/yr / 252 per bar on |position| — stock borrow stand-in,
                  charged on BOTH sides (an over-charge; biases AGAINST us)
  - max leverage  2.0             — Reg-T margin cap, a venue constraint
                  (crypto used 3.0; we never ran 3.0 on stocks to compare)
  - folds         train 252 / test 63 BARS — same TIME meaning (1y / 1q) as
                  crypto's 365/90; L23: the machine's spec is in time, not bars

UNIVERSE & PERIOD:
  - SPY, AAPL, KO, MSFT, XOM — the L23 demo panel, fixed before any machine
    result on stocks existed (no cherry-picking possible). All survivors, all
    US large caps -> buy-and-hold pass mark is survivorship-inflated, which
    makes H2 HARDER to pass. Bias runs against us: acceptable.
  - since 2015-01-01, through the day this runs.

MULTIPLE-TESTING LEDGER (what has already been seen of this data):
  - L23/L24 printed Sharpe/CAGR of FIXED demo strategies (SMA 20/60, 5/20,
    3/10, zscore 20/1.0) on these 5 tickers. Those looks changed NO machine
    knob — selection is clean — but they soften the blindness of our
    predictions (we know trend roughly works on SPY). Logged, not hidden.

PRE-REGISTERED HYPOTHESES AND READING (three-state, judge method ((3)) only):
  H1 "downside protection generalizes" (the twice-replicated identity):
       |MaxDD of ((3))| <= 2/3 * |MaxDD of buy-and-hold| on >= 3 of 5 tickers
  H2 "the Sharpe edge does NOT generalize":
       median(Sharpe((3)) - Sharpe(BH)) <= 0

  SUPPORTED  H1 pass and H2 pass -> identity confirmed a THIRD independent
             way (cross-asset L15, cross-time L22, cross-market now).
             The system IS a risk-reduction overlay. Stop looking for alpha
             in single-asset timeseries; next stop is cross-sectional.
  REFUTED    H1 fail -> protection was a crypto-era artefact, not an
             identity. Reopen research; do not reuse the machine as-is.
  SURPRISE   Sharpe((3)) > Sharpe(BH) on >= 4 of 5 AND median diff > +0.2
             -> the signal family is underrated on stocks; investigate.
  AMBIGUOUS  anything else -> treat as "do not fund", same as L22.

DISCIPLINE:
  - `run` executes ONCE and drops a marker file. Re-running with different
    settings and keeping the better answer is the exact sin this course has
    spent five lessons naming. The other three method rows are printed as
    background, NOT as judges.
  - Rehearse the mechanics on ALREADY-BURNED crypto data (`rehearsal`).

Run:  python holdout_stocks.py            # show this pre-registration
      python holdout_stocks.py rehearsal  # mechanics check on burned BTC data
      python holdout_stocks.py run        # THE run. Once.
"""

import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from backtest import backtest_next_open
from oos import score, sharpe_key
from param_stability import GRID, neighbourhood
from sizing import realized_vol
from strategy import fetch_ohlcv, regime_switch_signal

FEE = 0.0005                    # 5 bp/side, L24 stand-in
CARRY = 0.005 / 252             # 0.5%/yr borrow stand-in, per bar, both sides
TARGET_VOL = 0.20               # L18 dial, frozen
VOL_WINDOW = 20
MAX_LEVERAGE = 2.0              # Reg-T, a venue constraint (crypto had 3.0)
TRAIN_BARS, TEST_BARS = 252, 63  # 1 year / 1 quarter IN STOCK TIME (L23)
UNIVERSE = ("SPY", "AAPL", "KO", "MSFT", "XOM")
SINCE = "2015-01-01"
PROTECT_RATIO = 2 / 3           # H1: strategy MaxDD <= 2/3 of buy-and-hold's
MARKER = Path(__file__).with_name("holdout_stocks.RAN")

METHODS = (("plateau", "((3)) 挑邻域最好 <- 唯一判据"), ("best", "((1)) 挑样本内最好"),
           ("topk", "((2)) 样本内 top3 平均"), ("all", "((4)) 全网格等权"))


def build_folds(n, train=TRAIN_BARS, test=TEST_BARS):
    start = 0
    while start + train + test <= n:
        yield start, start + train, start + train, start + train + test
        start += test


def nets_for(price):
    """Net return series per grid cell, under the frozen machine + honest fills.

    Sizing happens BEFORE the shift: backtest_next_open lags signal by 2 bars,
    so both the signal and its vol weight are known at close[t-2] — the same
    no-look-ahead alignment vol_target_position used, re-derived for shift(2).
    """
    ret = price["close"].pct_change()
    weight = (TARGET_VOL / realized_vol(ret, VOL_WINDOW)).clip(upper=MAX_LEVERAGE)
    out = {}
    for w, t in GRID:
        sig = regime_switch_signal(price, er_window=w, er_thresh=t, long_short=True)
        sig["signal"] = sig["signal"] * weight
        out[(w, t)] = backtest_next_open(sig, fee=FEE, funding=CARRY)["strat_ret_net"]
    return out


def allocate(folds, nets, mode, k=3):
    """Stitch OOS segments under one selection policy (train-window info only)."""
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


def judge_symbol(sym, price):
    folds = list(build_folds(len(price)))
    lo, hi = folds[0][2], folds[-1][3]
    nets = nets_for(price)
    bh = score(price["close"].pct_change().iloc[lo:hi])

    print(f"{'=' * 62}\n{sym}   {price.index[lo].date()} -> {price.index[hi - 1].date()}"
          f"   ({len(folds)} folds)\n{'=' * 62}")
    print(f"  {'方法':<26}{'Sharpe':>9}{'CAGR':>9}{'MaxDD':>9}")
    s3 = None
    for mode, name in METHODS:
        s = score(allocate(folds, nets, mode))
        if mode == "plateau":
            s3 = s
        print(f"  {name:<24}{s['sharpe']:>9.2f}{s['cagr']:>9.1%}{s['mdd']:>9.1%}")
    print(f"  {'买入持有(及格线)':<22}{bh['sharpe']:>9.2f}{bh['cagr']:>9.1%}{bh['mdd']:>9.1%}\n")
    return s3, bh


def verdict(rows):
    """Apply the PRE-REGISTERED reading. No other numbers get a vote."""
    protect = [(sym, abs(s3["mdd"]) <= PROTECT_RATIO * abs(bh["mdd"]))
               for sym, s3, bh in rows]
    diffs = [s3["sharpe"] - bh["sharpe"] for _, s3, bh in rows]
    n_protect = sum(ok for _, ok in protect)
    med = float(np.median(diffs))
    n_beat = sum(d > 0.2 for d in diffs)

    print(f"{'=' * 62}\n预注册判读(判据写于开数据之前,原文见文件头)\n{'=' * 62}")
    print(f"  H1 下跌保护:|MaxDD③| <= 2/3·|MaxDD买持| 达标 "
          f"{n_protect}/{len(rows)}(需 >=3)  "
          f"[{' '.join(sym + ('√' if ok else '×') for sym, ok in protect)}]")
    print(f"  H2 夏普差:中位 (Sharpe③ − Sharpe买持) = {med:+.2f}(预测 <=0),"
          f"跑赢 +0.2 以上 {n_beat}/{len(rows)} 个标的")

    if n_beat >= 4 and med > 0.2:
        print("\n  -> 【惊喜】信号族在股票上被低估 —— 预测被反驳,值得深查。")
    elif n_protect >= 3 and med <= 0:
        print("\n  -> 【支持】身份第三次独立复现(跨资产/跨时间/跨市场):")
        print("     这台机器是【风险削减 overlay】,不是 alpha 来源。")
        print("     单标的时序里别再找 alpha;下一站是横截面。")
    elif n_protect < 3:
        print("\n  -> 【反驳】下跌保护没有跨市场 —— 它是 crypto 时代特征,不是身份。")
        print("     机器不能原样复用,研究重开。")
    else:
        print("\n  -> 【含糊】按「不上钱」处理,同 L22。")
    print("\n  其余三行方法只是背景。事后换判据 = 预注册作废 —— 那正是本课要防的。")


def cmd_rehearsal():
    print("排练 —— 只验机制,不是判决。数据是 L12-L22 早已烧掉的 BTC 窗口,")
    print("这里出现的任何数字都不允许更新你对股票那一跑的预测。\n")
    price = fetch_ohlcv(symbol="BTC/USDT", since="2021-01-01", limit=1000)
    judge_symbol("BTC/USDT(已烧掉)", price)
    print("机制自检通过标准:四行方法 + 及格线都打印、无异常、fold 数 > 5。")
    print("确认无误后,预测写下、判据同意,才轮到:python holdout_stocks.py run")


def cmd_run():
    if MARKER.exists():
        raise SystemExit(f"判决已经跑过一次(见 {MARKER.name}):\n\n{MARKER.read_text()}\n"
                         "重跑并挑更好看的那次 = 预注册作废。若你清楚自己在做什么,"
                         "删掉该文件再来。")
    from stocks import fetch_stock   # yfinance only needed for the real run

    print("留出判决 —— 冻结的机器,第一次也是唯一一次踏上股票。\n")
    # Fetch EVERYTHING first. A data failure must abort the verdict BEFORE any
    # judgment prints — not leave it half-read. Learned the hard way on the
    # first attempt (2026-08-14): Yahoo transiently dropped AAPL after SPY had
    # already been judged. Mechanics fix only; no judging rule changed.
    import time
    prices, err = {}, None
    for sym in UNIVERSE:
        for attempt in range(3):
            try:
                prices[sym] = fetch_stock(sym, since=SINCE)
                break
            except (Exception, SystemExit) as e:
                err = e
                if attempt < 2:
                    time.sleep(5 * (attempt + 1))
        else:
            raise SystemExit(f"{sym} 连续 3 次取不到数据({err})—— 判决整体中止,"
                             "一个标的都不判。稍后重跑 run。")

    rows = []
    for sym in UNIVERSE:
        s3, bh = judge_symbol(sym, prices[sym])
        rows.append((sym, s3, bh))
    verdict(rows)

    lines = [f"ran at {datetime.now():%Y-%m-%d %H:%M}"]
    lines += [f"{sym}: ((3)) sharpe {s3['sharpe']:+.2f} cagr {s3['cagr']:+.1%} "
              f"mdd {s3['mdd']:.1%} | BH sharpe {bh['sharpe']:+.2f} mdd {bh['mdd']:.1%}"
              for sym, s3, bh in rows]
    MARKER.write_text("\n".join(lines) + "\n")
    print(f"\n已落档 {MARKER.name} —— 这次运行从此有据可查。")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "prereg"
    if cmd == "rehearsal":
        cmd_rehearsal()
    elif cmd == "run":
        cmd_run()
    else:
        print(__doc__)
        print("下一步:python holdout_stocks.py rehearsal(机制排练,烧掉的数据)")
        print("然后:  python holdout_stocks.py run     (判决,只跑一次)")
