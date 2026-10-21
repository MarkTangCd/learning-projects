#!/usr/bin/env python3
"""Replay drill: deliberate practice for the trend-continuation playbook, 2 minutes per rep.

Usage:
  python replay.py              # one rep: random past weekday, cut somewhere inside UTC 12-16
  python replay.py --reps 5     # five reps in a row
  python replay.py --stats      # your drill history: verdict accuracy, rule consistency, drill E

Each rep:
  1. draws a random weekday from the last 120 days and a random cut time inside the window
  2. writes practice/replay.svg (bars from 08:00 UTC to the cut, swings labelled) -- open it in a browser,
     reload after every rep
  3. asks you: verdict? (u/d/r)        -> compared with the rule verdict (L4)
  4. asks you: action? (l/s/n)         -> long / short pullback entry per playbook, or no trade
     stop and target come from the playbook (extreme -/+ k x ATR, default k=1, 2R); exits: stop / target / 16:00 UTC
  5. plays the rest of the session forward and tells you the result in R
  6. appends a row to practice/replay_log.csv
Standard library only. The point is feedback density, not the P&L of the drills.
"""
import argparse
import csv
import random
import statistics
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from binance_data import fetchDay, readKlines
from stop_distance import atrSeries
from structure import findSwings, labelSwings, verdict, writeSvg

LOG_PATH = Path(__file__).with_name("replay_log.csv")
SVG_PATH = Path(__file__).with_name("replay.svg")
LOG_FIELDS = ["when", "symbol", "day", "cutUtc", "userVerdict", "ruleVerdict", "action", "ruleAction",
              "entry", "stop", "target", "exitKind", "resultR"]
CONTEXT_START, WINDOW, TIME_STOP = 8, (12, 15), 16
STRENGTH, TARGET_R = 3, 2.0
K_ATR = 1.0                     # playbook v1.1 (2026-10-20): k in [1, 2] by discretion; drill uses --k, default 1
VERDICT_KEYS = {"u": "UPTREND", "d": "DOWNTREND", "r": "TRADING RANGE (overlap)"}


def hourOf(bar):
    return datetime.fromtimestamp(bar.openTime / 1000, tz=timezone.utc)


def pickSession(symbol, rng, daysBack=120):
    """Random weekday with data; returns (day, bars)."""
    for _ in range(40):
        day = datetime.now(timezone.utc).date() - timedelta(days=rng.randint(2, daysBack))
        if day.weekday() >= 5:
            continue
        path = fetchDay(symbol, day, "5m")
        if path:
            bars = readKlines(path)
            if len(bars) >= 200:
                return day, bars
    raise SystemExit("could not find a session with data")


def ruleVerdict(labeled):
    """Rule verdict with 'not enough swings' folded into RANGE (the rule says: everything else is range)."""
    v = verdict(labeled)
    return VERDICT_KEYS["r"] if v == "not enough swings" else v


def ruleAction(labeled, side):
    """What the playbook allows at this cut: 'l', 's' or 'n'."""
    v = ruleVerdict(labeled)
    last = labeled[-1] if labeled else None
    if v == "UPTREND" and last and last[2] == "L" and last[3] == "HL":
        return "l"
    if v == "DOWNTREND" and last and last[2] == "H" and last[3] == "LH":
        return "s"
    return "n"


def planTrade(bars, cut, labeled, atr, side, k):
    """Entry at the cut close; stop beyond the last pullback extreme; target 2R. None if no valid extreme."""
    extremes = [s for s in labeled if s[2] == ("L" if side == 1 else "H")]
    if not extremes or atr[cut] is None:
        return None
    extreme = extremes[-1][1]
    entry = bars[cut].close
    stop = extreme - side * k * atr[cut]
    dist = (entry - stop) * side
    if dist <= 0:
        return None
    return entry, stop, entry + side * TARGET_R * dist


def playForward(bars, cut, side, entry, stop, target):
    for b in bars[cut + 1:]:
        if hourOf(b).hour >= TIME_STOP:
            return "time", (b.open - entry) * side / ((entry - stop) * side)
        if (b.low <= stop if side == 1 else b.high >= stop):
            return "stop", -1.0
        if (b.high >= target if side == 1 else b.low <= target):
            return "target", TARGET_R
    last = bars[-1].close
    return "time", (last - entry) * side / ((entry - stop) * side)


def oneRep(symbol, rng, k):
    day, bars = pickSession(symbol, rng)
    inWindow = [i for i, b in enumerate(bars) if WINDOW[0] <= hourOf(b).hour < WINDOW[1]]
    cut = rng.choice(inWindow)
    shown = [b for b in bars[:cut + 1] if hourOf(b).hour >= CONTEXT_START]
    offset = cut + 1 - len(shown)
    labeled = labelSwings(findSwings(shown, STRENGTH))
    atr = atrSeries(bars)
    writeSvg(shown, labeled, SVG_PATH, f"{symbol} 5m  ?  cut {hourOf(bars[cut]).strftime('%H:%M')} UTC  (date hidden)")
    print(f"\n--- rep: cut at {hourOf(bars[cut]).strftime('%H:%M')} UTC, {len(shown)} bars shown. Reload {SVG_PATH.name} ---")
    userVerdict = VERDICT_KEYS.get(input("verdict? u=uptrend d=downtrend r=range: ").strip().lower(), "?")
    rv = ruleVerdict(labeled)
    print(f"  rule says: {rv}   {'OK' if userVerdict == rv else 'X'}")
    action = input("action? l=long pullback s=short pullback n=no trade: ").strip().lower()
    ra = ruleAction(labeled, None)
    print(f"  playbook allows: {ra}   {'OK' if action == ra else 'X'}")
    row = {"when": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"), "symbol": symbol, "day": day.isoformat(),
           "cutUtc": hourOf(bars[cut]).strftime("%H:%M"), "userVerdict": userVerdict, "ruleVerdict": rv,
           "action": action, "ruleAction": ra, "entry": "", "stop": "", "target": "", "exitKind": "", "resultR": ""}
    if action in ("l", "s"):
        side = 1 if action == "l" else -1
        labeledFull = [(i + offset, p, k, t) for i, p, k, t in labeled]
        plan = planTrade(bars, cut, labeledFull, atr, side, k)
        if plan is None:
            print("  no valid pullback extreme on that side -> no trade")
        else:
            entry, stop, target = plan
            kind, r = playForward(bars, cut, side, entry, stop, target)
            print(f"  entry {entry:.1f} stop {stop:.1f} ({abs(entry - stop) / entry * 1e4:.0f} bp) target {target:.1f} -> {kind} {r:+.2f}R")
            row.update({"entry": f"{entry:.1f}", "stop": f"{stop:.1f}", "target": f"{target:.1f}", "exitKind": kind, "resultR": f"{r:.2f}"})
    print(f"  (it was {day})")
    appendLog(row)


def appendLog(row):
    new = not LOG_PATH.exists()
    with LOG_PATH.open("a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=LOG_FIELDS)
        if new:
            w.writeheader()
        w.writerow(row)


def printStats():
    if not LOG_PATH.exists():
        raise SystemExit("no drills yet")
    rows = list(csv.DictReader(LOG_PATH.open()))
    n = len(rows)
    vOk = sum(1 for r in rows if r["userVerdict"] == r["ruleVerdict"])
    aOk = sum(1 for r in rows if r["action"] == r["ruleAction"])
    trades = [float(r["resultR"]) for r in rows if r["resultR"]]
    withPb = [float(r["resultR"]) for r in rows if r["resultR"] and r["action"] == r["ruleAction"]]
    against = [float(r["resultR"]) for r in rows if r["resultR"] and r["action"] != r["ruleAction"]]
    print(f"Drills: {n} | verdict accuracy {vOk / n:.0%} | action matches playbook {aOk / n:.0%}")
    if trades:
        print(f"Drill trades: {len(trades)} | E {statistics.mean(trades):+.2f}R | "
              f"stopped {sum(1 for t in trades if t <= -0.99) / len(trades):.0%}")
        for name, rs in (("  with playbook", withPb), ("  against playbook", against)):
            if rs:
                print(f"{name:<20} n={len(rs):<3} E {statistics.mean(rs):+.2f}R")
    last = rows[-10:]
    print(f"Last 10: verdict {sum(1 for r in last if r['userVerdict'] == r['ruleVerdict'])}/{len(last)}, "
          f"action {sum(1 for r in last if r['action'] == r['ruleAction'])}/{len(last)}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--symbol", default="BTCUSDT")
    parser.add_argument("--reps", type=int, default=1)
    parser.add_argument("--stats", action="store_true")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--k", type=float, default=K_ATR, help="stop = pullback extreme -/+ k x ATR14(5m)")
    args = parser.parse_args()
    if args.stats:
        return printStats()
    rng = random.Random(args.seed)
    for _ in range(args.reps):
        oneRep(args.symbol, rng, args.k)
    printStats()


if __name__ == "__main__":
    main()
