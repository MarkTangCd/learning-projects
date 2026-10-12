#!/usr/bin/env python3
"""Trade journal measured in R. Standard library only.

Usage:
  python journal.py demo            # stats on a synthetic sample (writes nothing)
  python journal.py init            # create journal.csv next to this script
  python journal.py add             # interactive: log one trade
  python journal.py stats           # expectancy, per-setup table, mistake tags

Every trade is measured in R: 1R = planned loss = |entry - stop| * qty.
A trade without a stop recorded BEFORE entry has no R and is reported as
"unplanned" -- it cannot be measured, so it cannot be improved.
"""
import argparse
import csv
import random
import statistics
from datetime import datetime, timezone
from pathlib import Path

JOURNAL_PATH = Path(__file__).with_name("journal.csv")
FIELDS = ["id", "openedAt", "symbol", "side", "setup", "entry", "stop",
          "target", "exit", "qty", "feeUsd", "mistake", "note"]
TAKER_FEE = 0.0005          # Binance USDS-M regular tier, per side
DEMO_RISK_USD = 20.0        # 1R in the synthetic sample


# ---------- R arithmetic ----------

def toFloat(value):
    """Empty string -> None, otherwise float."""
    return float(value) if value not in ("", None) else None


def direction(side):
    return 1 if side.lower() == "long" else -1


def stopDist(row):
    """Distance from entry to stop in price units, positive when the stop is on the loss side."""
    entry, stop = toFloat(row["entry"]), toFloat(row["stop"])
    if entry is None or stop is None:
        return None
    dist = (entry - stop) * direction(row["side"])
    return dist if dist > 0 else None


def oneR(row):
    """Planned loss in USD. None when no stop; None when qty is unknown (R still works as a ratio)."""
    dist, qty = stopDist(row), toFloat(row["qty"])
    return dist * qty if dist is not None and qty else None


def plannedR(row):
    """Reward-to-risk written down before entry."""
    dist, entry, target = stopDist(row), toFloat(row["entry"]), toFloat(row["target"])
    if dist is None or target is None:
        return None
    return (target - entry) * direction(row["side"]) / dist


def feeR(row):
    """Fees as a fraction of 1R; 0 when fees or qty were not recorded."""
    r, fee = oneR(row), toFloat(row["feeUsd"])
    return fee / r if r and fee else 0.0


def resultR(row):
    """Realised R net of recorded fees. None when the trade is open or has no stop.
    Works from prices alone: (exit - entry) / (entry - stop), so qty is optional."""
    dist, exitPrice, entry = stopDist(row), toFloat(row["exit"]), toFloat(row["entry"])
    if dist is None or exitPrice is None:
        return None
    grossR = (exitPrice - entry) * direction(row["side"]) / dist
    return grossR - feeR(row)


def hasFee(row):
    return bool(toFloat(row["feeUsd"])) and bool(toFloat(row["qty"]))


# ---------- storage ----------

def readRows(path=JOURNAL_PATH):
    if not path.exists():
        raise SystemExit(f"No journal at {path}. Run: python journal.py init")
    with path.open(newline="") as f:
        rows = list(csv.DictReader(f))
    for i, row in enumerate(rows, start=1):     # tolerate hand-filled rows without ids
        row["id"] = row.get("id") or str(i)
    return rows


def writeRows(rows, path=JOURNAL_PATH):
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def cmdInit(args):
    if JOURNAL_PATH.exists():
        raise SystemExit(f"{JOURNAL_PATH} already exists; not overwriting.")
    writeRows([])
    print(f"Created {JOURNAL_PATH}")
    print("Columns:", ", ".join(FIELDS))


def cmdAdd(args):
    rows = readRows()
    nextId = len(rows) + 1
    row = {"id": str(nextId), "openedAt": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")}
    prompts = [("symbol", "Symbol (e.g. BTC/USDT:USDT)"), ("side", "Side long/short"),
               ("setup", "Setup name"), ("entry", "Entry price"), ("stop", "Stop price"),
               ("target", "Target price"), ("qty", "Quantity"), ("exit", "Exit price (blank if open)"),
               ("feeUsd", "Fees paid USD (blank if open)"), ("mistake", "Mistake tag (blank if none)"),
               ("note", "Note")]
    for key, label in prompts:
        row[key] = input(f"{label}: ").strip()
    if stopDist(row) is None:
        print("WARNING: no stop on the loss side -> this trade is UNPLANNED and will not be measured.")
    else:
        usd = f"1R = ${oneR(row):.2f}  " if oneR(row) else "1R = ? (no qty)  "
        print(f"{usd}planned {plannedR(row):.2f}R  fee {feeR(row):.2f}R", end="")
        print(f"  result {resultR(row):+.2f}R" if resultR(row) is not None else "  (open)")
    rows.append(row)
    writeRows(rows)
    print(f"Saved trade #{nextId}")


# ---------- statistics ----------

def summarize(rValues):
    """Expectancy table for a list of realised R values."""
    wins = [r for r in rValues if r > 0]
    losses = [r for r in rValues if r <= 0]
    n = len(rValues)
    return {
        "n": n,
        "winRate": len(wins) / n if n else 0.0,
        "avgWin": statistics.mean(wins) if wins else 0.0,
        "avgLoss": statistics.mean(losses) if losses else 0.0,
        "expectancy": statistics.mean(rValues) if n else 0.0,
        "total": sum(rValues),
    }


def maxConsecutiveLosses(rValues):
    worst = run = 0
    for r in rValues:
        run = run + 1 if r <= 0 else 0
        worst = max(worst, run)
    return worst


def printStats(rows):
    closed = [r for r in rows if resultR(r) is not None]
    openTrades = [r for r in rows if stopDist(r) is not None and resultR(r) is None]
    unplanned = [r for r in rows if stopDist(r) is None]
    print(f"Trades: {len(closed)} closed | {len(openTrades)} open | "
          f"{len(unplanned)} UNPLANNED (no stop -> cannot be measured, excluded)")
    if not closed:
        return
    rs = [resultR(r) for r in closed]
    s = summarize(rs)
    fees = [feeR(r) for r in closed]
    noFee = sum(1 for r in closed if not hasFee(r))
    print(f"Win rate {s['winRate']:.0%} | avg win {s['avgWin']:+.2f}R | avg loss {s['avgLoss']:+.2f}R | "
          f"expectancy {s['expectancy']:+.2f}R/trade | total {s['total']:+.1f}R")
    print(f"Fees: avg {statistics.mean(fees):.2f}R per trade -> gross expectancy "
          f"{s['expectancy'] + statistics.mean(fees):+.2f}R, net {s['expectancy']:+.2f}R")
    if noFee:
        print(f"      ({noFee} trades have no qty/fee recorded -> their fee drag is counted as 0R; real net is lower)")
    planned = [plannedR(r) for r in closed if plannedR(r) is not None]
    if planned:
        print(f"Planned R: avg {statistics.mean(planned):.2f}R | min {min(planned):.2f}R | max {max(planned):.2f}R")
    print(f"Max consecutive losses: {maxConsecutiveLosses(rs)} | best {max(rs):+.2f}R | worst {min(rs):+.2f}R")
    printExecution(closed)
    printGroup(closed, "setup", "By setup")
    tagged = [r for r in closed if r["mistake"]]
    if tagged:
        printGroup(tagged, "mistake", "By mistake tag")


def executionBucket(row):
    """Where did the trade actually end relative to its plan?"""
    r, target = resultR(row), plannedR(row)
    if r < -1.05:
        return "beyond stop (slippage or stop moved)"
    if r <= -0.9:
        return "at stop"
    if r <= 0:
        return "small loss, closed early"
    if target is not None and r >= 0.9 * target:
        return "to target"
    return "profit taken early"


def printExecution(closed):
    print("\nExecution (where trades actually ended):")
    counts = {}
    for row in closed:
        counts.setdefault(executionBucket(row), []).append(resultR(row))
    for name, rs in sorted(counts.items(), key=lambda kv: -len(kv[1])):
        print(f"  {name:<38}{len(rs):>3}   avg {statistics.mean(rs):+.2f}R")


def printGroup(rows, key, title):
    print(f"\n{title}:")
    print(f"  {'name':<14}{'n':>4}{'win%':>7}{'E(R)':>8}{'total':>8}")
    groups = {}
    for r in rows:
        groups.setdefault(r[key] or "(none)", []).append(resultR(r))
    for name, rs in sorted(groups.items(), key=lambda kv: -sum(kv[1])):
        s = summarize(rs)
        print(f"  {name:<14}{s['n']:>4}{s['winRate']:>7.0%}{s['expectancy']:>+8.2f}{s['total']:>+8.1f}")


def cmdStats(args):
    printStats(readRows())


# ---------- synthetic sample ----------

DEMO_SETUPS = {
    # name: (win probability, mean win R, mean stop distance as fraction of price)
    "pullback": (0.46, 1.9, 0.0045),
    "breakout": (0.36, 1.5, 0.0030),
    "fomo": (0.30, 1.2, 0.0020),
}


def demoRows(count=60, seed=7):
    """Deterministic fake trades so the stats output has something to show."""
    rng = random.Random(seed)
    rows = []
    for i in range(1, count + 1):
        setup = rng.choice(list(DEMO_SETUPS))
        winProb, meanWin, stopFrac = DEMO_SETUPS[setup]
        side = rng.choice(["long", "short"])
        d = direction(side)
        entry = 60000 + rng.uniform(-1500, 1500)
        stopDist = entry * stopFrac * rng.uniform(0.7, 1.3)
        stop = entry - d * stopDist
        target = entry + d * stopDist * rng.uniform(1.5, 2.5)
        qty = DEMO_RISK_USD / stopDist
        won = rng.random() < winProb
        moveR = rng.uniform(0.6, 1.4) * meanWin if won else -rng.uniform(0.8, 1.15)
        exitPrice = entry + d * stopDist * moveR
        feeUsd = qty * (entry + exitPrice) * TAKER_FEE
        mistake = "chased" if setup == "fomo" else ("early-exit" if won and moveR < 0.8 else "")
        rows.append({"id": str(i), "openedAt": f"2026-10-{(i % 28) + 1:02d} 14:{rng.randint(0, 59):02d}",
                     "symbol": "BTC/USDT:USDT", "side": side, "setup": setup,
                     "entry": f"{entry:.1f}", "stop": f"{stop:.1f}", "target": f"{target:.1f}",
                     "exit": f"{exitPrice:.1f}", "qty": f"{qty:.5f}", "feeUsd": f"{feeUsd:.3f}",
                     "mistake": mistake, "note": ""})
    rows.append({**rows[-1], "id": str(count + 1), "stop": "", "note": "no stop written down"})
    return rows


def cmdDemo(args):
    print("Synthetic sample -- nothing is written to disk.\n")
    printStats(demoRows())


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    for name, fn in [("demo", cmdDemo), ("init", cmdInit), ("add", cmdAdd), ("stats", cmdStats)]:
        sub.add_parser(name).set_defaults(fn=fn)
    args = parser.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
