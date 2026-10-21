#!/usr/bin/env python3
"""Where did the pullback come back to? Group the L5 mechanical pullback trades by location.

Usage:
  python location.py                      # BTCUSDT, 60 days, k=4, target 2R
  python location.py --days 120 --near 1.0
  python location.py --symbol ETHUSDT
  python location.py --by depth           # group by how deep the pullback retraced the prior impulse
  python location.py --by speed           # group by how fast the prior impulse was (ATR per bar)
  python location.py --by session         # signal fired inside the trading window (UTC 12-16) or not
  python location.py --by htf             # whole-day structure (strength 8) agrees with the trade side or not

Levels tested for each pullback extreme (the HL in an uptrend / LH in a downtrend):
  VWAP   = session VWAP from 00:00 UTC   (sum(quoteVolume) / sum(volume))
  PDH/PDL = previous UTC day's high / low (whichever is on the pullback side)
  SWING  = the previous swing of the opposite type (for a long: the last swing HIGH
           before this low = the top of the prior range / start of the last impulse)
A pullback is "near" a level when |extreme - level| <= NEAR x ATR14. When several
levels are near, the closest wins. Everything else is "none".
Then every group is traded exactly as in L5 (k x ATR stop, target R, day-end time stop).
Standard library only. Measurement, not a strategy claim.
"""
import argparse
import statistics
from datetime import date, datetime, timedelta, timezone

from binance_data import fetchDay, readKlines
from stop_distance import ATR_LEN, STRENGTH, TAKER_FEE, atrSeries, simulate
from structure import findSwings, labelSwings, verdict


def vwapSeries(bars):
    out, q, v = [], 0.0, 0.0
    for b in bars:
        q += b.quoteVolume
        v += b.volume
        out.append(q / v if v else b.close)
    return out


def pullbackSignals(bars, atr):
    """Like stop_distance.signals but also returns the prior impulse: (prevOpposite, impulseStart, impulseBars)."""
    for i in range(ATR_LEN + 2 * STRENGTH, len(bars)):
        labeled = labelSwings(findSwings(bars[:i + 1], STRENGTH))
        if len(labeled) < 4 or labeled[-1][0] != i - STRENGTH:
            continue
        v = verdict(labeled)
        idx, price, kind, tag = labeled[-1]
        impulse = (labeled[-2][1], labeled[-3][1], labeled[-2][0] - labeled[-3][0])   # end, start, bars
        if v == "UPTREND" and kind == "L" and tag == "HL":
            yield i, 1, price, atr[i], impulse
        elif v == "DOWNTREND" and kind == "H" and tag == "LH":
            yield i, -1, price, atr[i], impulse


def depthGroup(extreme, impulse):
    end, start, _ = impulse
    depth = (end - extreme) / (end - start) if end != start else float("nan")
    if depth < 0.38:
        return "shallow<38%"
    return "mid38-62%" if depth <= 0.62 else "deep>62%"


SESSION_UTC = (12, 16)
HTF_STRENGTH = 8


def sessionGroup(bar):
    """Signal fired inside the trading window or not."""
    hour = datetime.fromtimestamp(bar.openTime / 1000, tz=timezone.utc).hour
    return "in-session" if SESSION_UTC[0] <= hour < SESSION_UTC[1] else "out-of-session"


def htfGroup(bars, i, side):
    """Coarser structure (strength 8 on everything seen so far today) vs the trade side."""
    v = verdict(labelSwings(findSwings(bars[:i + 1], HTF_STRENGTH)))
    if v == "not enough swings":
        return "htf-unknown"
    aligned = (v == "UPTREND" and side == 1) or (v == "DOWNTREND" and side == -1)
    return "htf-aligned" if aligned else "htf-against-or-range"


def speedGroup(impulse, atrValue):
    end, start, nBars = impulse
    speed = abs(end - start) / max(nBars, 1) / atrValue
    if speed < 0.5:
        return "slow<0.5ATR/bar"
    return "mid0.5-1" if speed <= 1.0 else "fast>1ATR/bar"


def nearestLevel(extreme, side, atrValue, vwap, pdh, pdl, prevSwing, near):
    """Return (groupName, distanceInAtr) for the closest level within NEAR x ATR, else ('none', min)."""
    candidates = {"VWAP": vwap, "SWING": prevSwing, "PD": pdl if side == 1 else pdh}
    best, bestDist = "none", float("inf")
    for name, level in candidates.items():
        d = abs(extreme - level) / atrValue
        if d <= near and d < bestDist:
            best, bestDist = name, d
    return best, bestDist


def run(symbol, days, end, k, targetR, near, by="location"):
    groups = {}
    loaded = 0
    for n in range(days):
        day = end - timedelta(days=n)
        path, prevPath = fetchDay(symbol, day, "5m"), fetchDay(symbol, day - timedelta(days=1), "5m")
        if path is None or prevPath is None:
            continue
        bars, prevBars = readKlines(path), readKlines(prevPath)
        if len(bars) < 100 or len(prevBars) < 100:
            continue
        loaded += 1
        pdh, pdl = max(b.high for b in prevBars), min(b.low for b in prevBars)
        atr, vwap = atrSeries(bars), vwapSeries(bars)
        busyUntil = -1
        for i, side, extreme, a, impulse in pullbackSignals(bars, atr):
            if i <= busyUntil:
                continue
            r = simulate(bars, i, side, extreme, a, k, targetR)
            if not r:
                continue
            if by == "depth":
                name = depthGroup(extreme, impulse)
            elif by == "speed":
                name = speedGroup(impulse, a)
            elif by == "session":
                name = sessionGroup(bars[i])
            elif by == "htf":
                name = htfGroup(bars, i, side)
            else:
                name, _ = nearestLevel(extreme, side, a, vwap[i], pdh, pdl, impulse[0], near)
            groups.setdefault(name, []).append(r)
            busyUntil = i + 12
    return groups, loaded


def printGroups(groups, fee):
    allRows = [r for rows in groups.values() for r in rows]
    print(f"\n{'group':>16} {'n':>5} {'stop%':>6} {'target%':>8} {'time%':>6} {'gross E':>8} {'net E':>7}  {'±se':>5}")
    for name, rows in sorted(groups.items(), key=lambda kv: -len(kv[1])) + [("ALL", allRows)]:
        n = len(rows)
        if not n:
            continue
        rs = [r[0] for r in rows]
        gross = statistics.mean(rs)
        feeR = statistics.mean(2 * fee / r[2] for r in rows)
        se = statistics.pstdev(rs) / n ** 0.5 if n > 1 else float("nan")
        print(f"{name:>16} {n:>5} {sum(1 for r in rows if r[1] == 'stop') / n:>6.0%} "
              f"{sum(1 for r in rows if r[1] == 'target') / n:>8.0%} {sum(1 for r in rows if r[1] == 'time') / n:>6.0%} "
              f"{gross:>+8.2f} {gross - feeR:>+7.2f}  {se:>5.2f}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--symbol", default="BTCUSDT")
    parser.add_argument("--days", type=int, default=60)
    parser.add_argument("--end", type=date.fromisoformat, default=datetime.now(timezone.utc).date() - timedelta(days=1))
    parser.add_argument("--k", type=float, default=4.0)
    parser.add_argument("--target", type=float, default=2.0)
    parser.add_argument("--near", type=float, default=1.0, help="'near' = within this many ATR of the level")
    parser.add_argument("--fee", type=float, default=TAKER_FEE * 1e4, help="bp per side")
    parser.add_argument("--by", choices=["location", "depth", "speed", "session", "htf"], default="location")
    args = parser.parse_args()
    if args.by != "location" and args.near != 1.0:
        print(f"note: --near only affects --by location; it is ignored for --by {args.by}")
    groups, loaded = run(args.symbol, args.days, args.end, args.k, args.target, args.near, args.by)
    print(f"{args.symbol} 5m, {loaded} days ending {args.end}, stop {args.k} x ATR, target {args.target}R, "
          f"grouped by {args.by}" + (f", near = {args.near} ATR" if args.by == "location" else "") + f", fee {args.fee:.0f} bp/side")
    printGroups(groups, args.fee / 1e4)
    print("\n±se = standard error of gross E. Differences smaller than ~2 se are noise.")


if __name__ == "__main__":
    main()
