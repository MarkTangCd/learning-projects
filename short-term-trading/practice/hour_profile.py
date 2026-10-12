#!/usr/bin/env python3
"""Where in the day does BTC actually move? Hour-of-day profile from Binance public data.

Usage:
  python hour_profile.py                       # BTCUSDT perp, last 28 complete days
  python hour_profile.py --symbol ETHUSDT --days 56
  python hour_profile.py --end 2026-10-10      # last day to include

Downloads daily 1-minute kline files from data.binance.vision (free, no key),
caches them under practice/data/, and prints per-UTC-hour medians of:
  move   = sum of |1-minute log returns| in the hour, in bp  (how much price travelled)
  range  = (hour high - hour low) / hour open, in bp         (how far it got)
  volume = quote volume in USD millions
  trades = number of trades in thousands
  buy%   = taker-buy share of volume
Then it recommends the best contiguous 3-hour window by median move.
Standard library only. Honors https_proxy from the environment.
"""
import argparse
import csv
import io
import math
import statistics
import urllib.request
import zipfile
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

BASE_URL = "https://data.binance.vision/data/futures/um/daily/klines"
DATA_DIR = Path(__file__).with_name("data") / "klines"
WINDOW_HOURS = 3
BAR_WIDTH = 28


def dayUrl(symbol, day):
    return f"{BASE_URL}/{symbol}/1m/{symbol}-1m-{day.isoformat()}.zip"


def fetchDay(symbol, day):
    """Return the cached zip path for one day, downloading it if needed. None if unavailable."""
    target = DATA_DIR / symbol / f"{symbol}-1m-{day.isoformat()}.zip"
    if target.exists():
        return target
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        with urllib.request.urlopen(dayUrl(symbol, day), timeout=30) as resp:
            target.write_bytes(resp.read())
        return target
    except Exception as err:            # 404 for days not yet published, network errors
        print(f"  skip {day}: {err}")
        return None


def readMinutes(zipPath):
    """Yield (openTimeMs, open, high, low, close, quoteVolume, count, takerBuyQuote) per minute."""
    with zipfile.ZipFile(zipPath) as zf:
        raw = zf.read(zf.namelist()[0]).decode()
    for row in csv.reader(io.StringIO(raw)):
        if not row or not row[0].isdigit():          # header line or junk
            continue
        yield (int(row[0]), float(row[1]), float(row[2]), float(row[3]), float(row[4]),
               float(row[7]), int(row[8]), float(row[10]))


def hourStats(minutes):
    """Collapse one day of minutes into {hour: dict of raw stats}."""
    buckets = defaultdict(list)
    for m in minutes:
        hour = datetime.fromtimestamp(m[0] / 1000, tz=timezone.utc).hour
        buckets[hour].append(m)
    out = {}
    for hour, rows in buckets.items():
        moveBp = sum(abs(math.log(r[4] / r[1])) for r in rows) * 1e4
        hi, lo, first = max(r[2] for r in rows), min(r[3] for r in rows), rows[0][1]
        quote = sum(r[5] for r in rows)
        out[hour] = {"move": moveBp, "range": (hi - lo) / first * 1e4, "volume": quote / 1e6,
                     "trades": sum(r[6] for r in rows) / 1e3,
                     "buyPct": (sum(r[7] for r in rows) / quote * 100) if quote else 0.0}
    return out


def collect(symbol, days, end):
    """Per-hour lists of daily values, split into weekday/weekend, plus how many days loaded."""
    perHour = defaultdict(lambda: defaultdict(list))
    weekdayMove, weekendMove = [], []
    loaded = 0
    for i in range(days):
        day = end - timedelta(days=i)
        path = fetchDay(symbol, day)
        if path is None:
            continue
        loaded += 1
        stats = hourStats(readMinutes(path))
        dayMove = sum(s["move"] for s in stats.values())
        (weekendMove if day.weekday() >= 5 else weekdayMove).append(dayMove)
        for hour, s in stats.items():
            for key, value in s.items():
                perHour[hour][key].append(value)
    return perHour, weekdayMove, weekendMove, loaded


def medians(perHour):
    return {hour: {k: statistics.median(v) for k, v in stats.items()} for hour, stats in perHour.items()}


def bestWindow(med, key="move", width=WINDOW_HOURS):
    """Best contiguous window (wrapping midnight) by summed median value."""
    best, bestStart = -1.0, 0
    for start in range(24):
        total = sum(med.get((start + k) % 24, {}).get(key, 0.0) for k in range(width))
        if total > best:
            best, bestStart = total, start
    return bestStart, best


def localHour(utcHour):
    offset = datetime.now().astimezone().utcoffset() or timedelta(0)
    return (utcHour + int(offset.total_seconds() // 3600)) % 24


def printTable(med, loaded):
    maxMove = max(s["move"] for s in med.values())
    print(f"\n{'UTC':>3} {'local':>5} {'move bp':>8} {'range bp':>9} {'vol $M':>7} {'trades k':>9} {'buy%':>5}  (medians over {loaded} days)")
    for hour in range(24):
        s = med.get(hour)
        if not s:
            continue
        bar = "#" * int(round(s["move"] / maxMove * BAR_WIDTH))
        print(f"{hour:>3} {localHour(hour):>5} {s['move']:>8.0f} {s['range']:>9.0f} {s['volume']:>7.0f} "
              f"{s['trades']:>9.0f} {s['buyPct']:>5.1f}  {bar}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--symbol", default="BTCUSDT")
    parser.add_argument("--days", type=int, default=28)
    parser.add_argument("--end", type=lambda s: date.fromisoformat(s),
                        default=datetime.now(timezone.utc).date() - timedelta(days=1))
    args = parser.parse_args()

    print(f"{args.symbol} perp, {args.days} days ending {args.end} (UTC). Downloading what is not cached...")
    perHour, weekdayMove, weekendMove, loaded = collect(args.symbol, args.days, args.end)
    if not loaded:
        raise SystemExit("No data loaded. Check network / proxy.")
    med = medians(perHour)
    printTable(med, loaded)

    start, total = bestWindow(med, "move")
    volStart, _ = bestWindow(med, "volume")
    hours = [(start + k) % 24 for k in range(WINDOW_HOURS)]
    print(f"\nBest {WINDOW_HOURS}h window by median move: UTC {start:02d}:00-{(start + WINDOW_HOURS) % 24:02d}:00 "
          f"(local {localHour(start):02d}:00-{localHour(start + WINDOW_HOURS):02d}:00), "
          f"{total:.0f} bp of travel vs {sum(s['move'] for s in med.values()) / 24 * WINDOW_HOURS:.0f} bp for an average 3h")
    print(f"Best {WINDOW_HOURS}h window by volume:      UTC {volStart:02d}:00-{(volStart + WINDOW_HOURS) % 24:02d}:00")
    quietest = min(med, key=lambda h: med[h]["move"])
    print(f"Quietest hour: UTC {quietest:02d} with {med[quietest]['move']:.0f} bp "
          f"({med[quietest]['move'] / med[start]['move']:.0%} of the best hour)")
    if weekdayMove and weekendMove:
        print(f"Whole-day travel: weekday median {statistics.median(weekdayMove):.0f} bp | "
              f"weekend median {statistics.median(weekendMove):.0f} bp")
    print("\nRead it with the lesson: fees are fixed per trade, travel is not -- trade where travel/fee is highest.")


if __name__ == "__main__":
    main()
