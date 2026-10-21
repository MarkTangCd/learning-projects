#!/usr/bin/env python3
"""How far below the pullback low should the stop go? Measure it instead of guessing.

Usage:
  python stop_distance.py                       # BTCUSDT, 60 days, k in {0.25,0.5,1,1.5,2} x ATR(14, 5m)
  python stop_distance.py --days 90 --target 1.5
  python stop_distance.py --session 12 16       # only signals that fire inside UTC 12:00-16:00
  python stop_distance.py --k 1 2 4 8 --fee 2   # your own k list; maker fee 2 bp/side

Mechanical with-trend pullback, no look-ahead:
  signal  = the bar that CONFIRMS a new swing low tagged HL while the verdict is UP
            (mirror: LH while DOWN). Confirmation = STRENGTH bars after the low, so the
            entry is at that bar's close, not at the low itself.
  stop    = swing low - k * ATR14         target = entry + TARGET_R * (entry - stop)
  exit    = stop, target, or the last bar of the day (time stop); stop checked first.
  one trade at a time; fees = taker both sides, expressed in R via the stop distance.
This is a measurement of noise vs structure, NOT a strategy claim. Standard library only.
"""
import argparse
import statistics
from datetime import date, datetime, timedelta, timezone

from binance_data import atrSeries, fetchDay, readKlines
from structure import findSwings, labelSwings, verdict

STRENGTH = 3
ATR_LEN = 14
K_VALUES = [0.25, 0.5, 1.0, 1.5, 2.0]
TAKER_FEE = 0.0005


def signals(bars, atr):
    """Yield (index, side, swingPrice, atrValue) for confirmed with-trend pullback swings."""
    for i in range(ATR_LEN + 2 * STRENGTH, len(bars)):
        labeled = labelSwings(findSwings(bars[:i + 1], STRENGTH))
        if len(labeled) < 4 or labeled[-1][0] != i - STRENGTH:
            continue                                      # last swing must be confirmed exactly now
        v = verdict(labeled)
        idx, price, kind, tag = labeled[-1]
        if v == "UPTREND" and kind == "L" and tag == "HL":
            yield i, 1, price, atr[i]
        elif v == "DOWNTREND" and kind == "H" and tag == "LH":
            yield i, -1, price, atr[i]


def simulate(bars, i, side, swing, atrValue, k, targetR):
    """Return (resultR, exitKind, stopPct) for one trade entered at bars[i].close."""
    entry = bars[i].close
    stop = swing - side * k * atrValue
    dist = (entry - stop) * side
    if dist <= 0:
        return None
    target = entry + side * targetR * dist
    for b in bars[i + 1:]:
        if (b.low <= stop if side == 1 else b.high >= stop):
            return -1.0, "stop", dist / entry
        if (b.high >= target if side == 1 else b.low <= target):
            return targetR, "target", dist / entry
    last = bars[-1].close
    return (last - entry) * side / dist, "time", dist / entry


def inSession(bar, session):
    if not session:
        return True
    h = datetime.fromtimestamp(bar.openTime / 1000, tz=timezone.utc).hour
    return session[0] <= h < session[1]


def run(symbol, days, end, targetR, session, kValues=K_VALUES):
    results = {k: [] for k in kValues}
    atrBp, atrBpSession, loaded = [], [], 0
    for n in range(days):
        day = end - timedelta(days=n)
        path = fetchDay(symbol, day, "5m")
        if path is None:
            continue
        bars = readKlines(path)
        if len(bars) < 100:
            continue
        loaded += 1
        atr = atrSeries(bars)
        for b, a in zip(bars, atr):
            if a:
                atrBp.append(a / b.close * 1e4)
                if inSession(b, (12, 16)):
                    atrBpSession.append(a / b.close * 1e4)
        busyUntil = -1
        for i, side, swing, a in signals(bars, atr):
            if i <= busyUntil or not inSession(bars[i], session):
                continue
            for k in kValues:
                r = simulate(bars, i, side, swing, a, k, targetR)
                if r:
                    results[k].append(r)
            busyUntil = i + 12                            # crude: no overlapping trades within an hour
    return results, atrBp, atrBpSession, loaded


def printTable(results, targetR, fee=TAKER_FEE):
    print(f"\n{'k x ATR':>8} {'n':>5} {'stop%':>6} {'target%':>8} {'time%':>6} {'stop bp':>8} {'fee R':>6} {'gross E':>8} {'net E':>7}")
    for k, rows in results.items():
        if not rows:
            continue
        n = len(rows)
        stopHit = sum(1 for r in rows if r[1] == "stop") / n
        tgtHit = sum(1 for r in rows if r[1] == "target") / n
        timeHit = sum(1 for r in rows if r[1] == "time") / n
        stopBp = statistics.median(r[2] for r in rows) * 1e4
        feeR = statistics.mean(2 * fee / r[2] for r in rows)
        gross = statistics.mean(r[0] for r in rows)
        print(f"{k:>8.2f} {n:>5} {stopHit:>6.0%} {tgtHit:>8.0%} {timeHit:>6.0%} {stopBp:>8.0f} {feeR:>6.2f} {gross:>+8.2f} {gross - feeR:>+7.2f}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--symbol", default="BTCUSDT")
    parser.add_argument("--days", type=int, default=60)
    parser.add_argument("--end", type=date.fromisoformat, default=datetime.now(timezone.utc).date() - timedelta(days=1))
    parser.add_argument("--target", type=float, default=2.0, help="target in R")
    parser.add_argument("--session", type=int, nargs=2, metavar=("START", "END"), help="UTC hours; only signals inside")
    parser.add_argument("--k", type=float, nargs="+", default=K_VALUES, help="ATR multiples to test")
    parser.add_argument("--fee", type=float, default=TAKER_FEE * 1e4, help="fee per side in bp (taker 5, maker 2)")
    args = parser.parse_args()
    fee = args.fee / 1e4
    results, atrBp, atrBpSession, loaded = run(args.symbol, args.days, args.end, args.target, args.session, args.k)
    print(f"{args.symbol} 5m, {loaded} days ending {args.end}, target {args.target}R, fee {args.fee:.0f} bp/side"
          + (f", signals only in UTC {args.session[0]:02d}-{args.session[1]:02d}" if args.session else ""))
    print(f"ATR14 (5m) median: all hours {statistics.median(atrBp):.0f} bp | UTC 12-16 {statistics.median(atrBpSession):.0f} bp")
    printTable(results, args.target, fee)
    print("\nstop% = stopped out | target% = reached target | time% = still open at day end (exit at close)")
    print("Read with L5: too close and noise takes the stop; too far and the fee share shrinks but the target stops fitting the range.")


if __name__ == "__main__":
    main()
