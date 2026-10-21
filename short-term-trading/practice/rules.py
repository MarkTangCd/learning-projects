#!/usr/bin/env python3
"""Rules v1 compliance check. Reads journal.csv and reports every rule violation.

Usage:
  python rules.py            # check the real journal
  python rules.py --demo     # check the synthetic sample from journal.py

Edit the constants below when your rules change; the lesson explains each one.
Standard library only; reuses journal.py for the R arithmetic.
"""
import argparse
import statistics
from datetime import datetime, timedelta

from journal import demoRows, executionBucket, readRows, resultR, stopDist

# ---- Rules v1 (your numbers; change here, nowhere else) ----
SESSION_UTC = (12, 15)        # entries allowed when 12:00 <= UTC hour < 15:00, weekdays only (2026-10-20)
TIME_STOP_UTC = 16            # if neither stop nor target was hit, be flat by this UTC hour
DAY_STOP_R = -3.0             # stop opening trades for the day once the day's total is below this
MAX_CONSEC_LOSSES = 3         # stop opening trades for the day after this many losses in a row
SLIPPAGE_TOLERANCE_R = 0.05   # a loss worse than -(1 + this) R means the stop was not resting on the exchange
TIME_FORMAT = "%Y-%m-%d %H:%M"
NOTE_VOCAB = ({"UP", "DOWN", "RANGE"}, {"cont", "term", "hold", "break"},
              {"in-pullback", "after-impulse", "at-edge", "in-breakout"})   # 判决 / 格子 / 腿


def parseTime(text):
    try:
        return datetime.strptime(text.strip(), TIME_FORMAT)
    except (ValueError, AttributeError):
        return None


def inSession(openedAt):
    """None when unknown, else True/False."""
    t = parseTime(openedAt)
    if t is None:
        return None
    return t.weekday() < 5 and SESSION_UTC[0] <= t.hour < SESSION_UTC[1]


def checkTrade(row):
    """Return the list of rule violations for one closed trade."""
    found = []
    r = resultR(row)
    if r < -(1 + SLIPPAGE_TOLERANCE_R):
        found.append(f"R1 beyond stop ({r:+.2f}R): stop was not resting on the exchange, or was moved")
    session = inSession(row["openedAt"])
    if session is False and row["mistake"] != "outside-session":
        found.append("R2 opened outside session and not tagged outside-session")
    bucket = executionBucket(row)
    closed = parseTime(row["closedAt"])
    timeStopped = closed is not None and closed.hour >= TIME_STOP_UTC
    if bucket in ("profit taken early", "small loss, closed early") and not timeStopped \
            and row["mistake"] != "time-stop":
        found.append(f"R3 discretionary exit ({bucket}, {r:+.2f}R): only stop, target or time-stop may close a trade")
    return found


def checkDays(closed):
    """Day-level rules: daily stop and consecutive losses. Needs openedAt."""
    found = []
    byDay = {}
    for row in closed:
        t = parseTime(row["openedAt"])
        if t is not None:
            byDay.setdefault(t.date(), []).append((t, row))
    for day, items in sorted(byDay.items()):
        total, streak = 0.0, 0
        for t, row in sorted(items, key=lambda x: x[0]):
            if total <= DAY_STOP_R:
                found.append(f"R4 {day}: trade #{row['id']} opened after the day was already at {total:+.1f}R")
            if streak >= MAX_CONSEC_LOSSES:
                found.append(f"R5 {day}: trade #{row['id']} opened after {streak} consecutive losses")
            r = resultR(row)
            total += r
            streak = streak + 1 if r <= 0 else 0
    return found


def holdHours(closed):
    hours = []
    for row in closed:
        a, b = parseTime(row["openedAt"]), parseTime(row["closedAt"])
        if a and b and b > a:
            hours.append((b - a) / timedelta(hours=1))
    return hours


def structureNote(row):
    """Parse '判决/格子/腿' from note; returns the tuple or None when absent/malformed."""
    parts = row["note"].strip().split("/")
    if len(parts) < 3:
        return None
    parts = tuple(p.strip() for p in parts[:3])
    return parts if all(p in vocab for p, vocab in zip(parts, NOTE_VOCAB)) else None


def printStructureNotes(closed):
    noted = [structureNote(r) for r in closed]
    valid = [n for n in noted if n]
    print(f"Structure note (判决/格子/腿): {len(valid)}/{len(closed)} trades written in the vocabulary")
    against = sum(1 for v in valid if (v[0] == "RANGE" and v[1] == "break") or (v[0] in ("UP", "DOWN") and v[1] == "term"))
    if valid:
        print(f"  with-trend pullbacks (cont/in-pullback): {sum(1 for v in valid if v[1] == 'cont' and v[2] == 'in-pullback')} | "
              f"against the 80% (RANGE/break or trend/term): {against}")


def report(rows):
    closed = [r for r in rows if stopDist(r) is not None and resultR(r) is not None]
    print(f"Rules v1: session UTC {SESSION_UTC[0]:02d}-{SESSION_UTC[1]:02d} weekdays | time-stop {TIME_STOP_UTC:02d}:00 UTC | "
          f"day stop {DAY_STOP_R:+.0f}R | max {MAX_CONSEC_LOSSES} losses in a row")
    print(f"Closed trades checked: {len(closed)}")
    unknownTime = sum(1 for r in closed if parseTime(r["openedAt"]) is None)
    if unknownTime:
        print(f"  {unknownTime} trades have no openedAt -> R2/R4/R5 cannot be checked for them (log the time!)")
    clean = 0
    for row in closed:
        found = checkTrade(row)
        clean += not found
        for f in found:
            print(f"  #{row['id']:<3} {f}")
    for f in checkDays(closed):
        print(f"  {f}")
    if closed:
        print(f"\nCompliance: {clean}/{len(closed)} trades with zero violations ({clean / len(closed):.0%})")
    printStructureNotes(closed)
    hours = holdHours(closed)
    if hours:
        print(f"Hold time: median {statistics.median(hours):.1f}h | max {max(hours):.1f}h  ({len(hours)} trades with both times)")
    else:
        print("Hold time: unknown -- fill openedAt and closedAt")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--demo", action="store_true")
    args = parser.parse_args()
    report(demoRows() if args.demo else readRows())


if __name__ == "__main__":
    main()
