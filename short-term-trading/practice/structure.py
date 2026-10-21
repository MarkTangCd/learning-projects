#!/usr/bin/env python3
"""Label market structure on a window of 5-minute bars: swing highs/lows, HH/HL/LH/LL, verdict.

Usage:
  python structure.py                                   # yesterday, UTC 12:00-16:00, BTCUSDT 5m
  python structure.py --date 2026-10-10 --start 12 --end 17
  python structure.py --date 2026-10-10 --svg out.svg   # also draw the chart (open in a browser)
  python structure.py --symbol ETHUSDT --strength 4     # swing = highest/lowest of 4 bars each side
  python structure.py --live                            # NOW: last 24h of 5m bars from the public API, window = today 00:00 UTC to now
  python structure.py --live --start 8                  # NOW, but only bars since 08:00 UTC
Columns: leg bp, bars, bp/bar, xATR/bar (= speed for the note), and the last pullback's depth %.

Definitions used (see lesson L4 and reference/structure-card.html):
  swing high  = bar whose high is the highest of STRENGTH bars on both sides (swing low mirrored)
  HH / LH     = this swing high is above / below the previous swing high
  HL / LL     = this swing low is above / below the previous swing low
  uptrend     = the last two swing highs are HH and the last two swing lows are HL
  downtrend   = LH + LL likewise;  otherwise = trading range (overlap)
  impulse     = the leg in the trend direction;  pullback = the leg against it
Standard library only.
"""
import argparse
from datetime import date, datetime, timedelta, timezone

from binance_data import atrSeries, fetchDay, fetchLive, readKlines

DEFAULT_STRENGTH = 3
SVG_W, SVG_H, PAD = 900, 380, 40


def loadWindow(symbol, day, startHour, endHour, interval="5m"):
    path = fetchDay(symbol, day, interval)
    if path is None:
        raise SystemExit("no data for that day")
    bars = readKlines(path)
    return [b for b in bars if startHour <= datetime.fromtimestamp(b.openTime / 1000, tz=timezone.utc).hour < endHour]


def findSwings(bars, strength):
    """Alternating list of (index, price, 'H'|'L'). Consecutive same-type swings keep the more extreme one."""
    raw = []
    for i in range(strength, len(bars) - strength):
        window = bars[i - strength:i + strength + 1]
        if bars[i].high == max(b.high for b in window):
            raw.append((i, bars[i].high, "H"))
        if bars[i].low == min(b.low for b in window):
            raw.append((i, bars[i].low, "L"))
    swings = []
    for s in sorted(raw):
        if swings and swings[-1][2] == s[2]:
            better = s[1] > swings[-1][1] if s[2] == "H" else s[1] < swings[-1][1]
            if better:
                swings[-1] = s
            continue
        swings.append(s)
    return swings


def labelSwings(swings):
    """Attach HH/HL/LH/LL to each swing relative to the previous swing of the same type."""
    lastHigh = lastLow = None
    out = []
    for idx, price, kind in swings:
        if kind == "H":
            tag = "" if lastHigh is None else ("HH" if price > lastHigh else "LH")
            lastHigh = price
        else:
            tag = "" if lastLow is None else ("HL" if price > lastLow else "LL")
            lastLow = price
        out.append((idx, price, kind, tag))
    return out


def verdict(labeled):
    highs = [t for _, _, k, t in labeled if k == "H" and t][-2:]
    lows = [t for _, _, k, t in labeled if k == "L" and t][-2:]
    if len(highs) < 2 or len(lows) < 2:
        return "not enough swings"
    if highs == ["HH", "HH"] and lows == ["HL", "HL"]:
        return "UPTREND"
    if highs == ["LH", "LH"] and lows == ["LL", "LL"]:
        return "DOWNTREND"
    return "TRADING RANGE (overlap)"


def legs(labeled, bars):
    """(fromSwing, toSwing, bp, bars) for every consecutive pair of swings."""
    out = []
    for a, b in zip(labeled, labeled[1:]):
        bp = (b[1] - a[1]) / a[1] * 1e4
        out.append((a, b, bp, b[0] - a[0]))
    return out


def printReport(bars, labeled, day, atr=None):
    atrNow = atr[-1] if atr and atr[-1] else None
    atrBp = atrNow / bars[-1].close * 1e4 if atrNow else None
    print(f"{len(bars)} bars, {len(labeled)} swings  | verdict: {verdict(labeled)}"
          + (f"  | ATR14 now {atrBp:.0f} bp (${atrNow:.0f})" if atrBp else ""))
    print(f"{'time UTC':>9} {'swing':>6} {'price':>10} {'tag':>4} {'leg bp':>8} {'bars':>5} {'bp/bar':>7} {'xATR/bar':>9}")
    prev = None
    for idx, price, kind, tag in labeled:
        t = datetime.fromtimestamp(bars[idx].openTime / 1000, tz=timezone.utc).strftime("%H:%M")
        if prev is None:
            print(f"{t:>9} {kind:>6} {price:>10.1f} {tag:>4}")
        else:
            bp = (price - prev[1]) / prev[1] * 1e4
            n = idx - prev[0]
            a = atr[idx] if atr and atr[idx] else None
            speed = f"{abs(price - prev[1]) / n / a:>9.2f}" if a else f"{'':>9}"
            print(f"{t:>9} {kind:>6} {price:>10.1f} {tag:>4} {bp:>+8.0f} {n:>5} {bp / n:>+7.1f} {speed}")
        prev = (idx, price)
    lg = legs(labeled, bars)
    if len(lg) >= 2:
        a, b = lg[-2], lg[-1]
        retrace = -b[2] / a[2] * 100 if a[2] else float("nan")
        aAtr = atr[a[1][0]] if atr and atr[a[1][0]] else None
        speed = abs(a[1][1] - a[0][1]) / a[3] / aAtr if aAtr else None
        print(f"\nLast impulse {a[2]:+.0f} bp in {a[3]} bars" + (f" = speed {speed:.2f} xATR/bar" if speed else "")
              + f"; last leg {b[2]:+.0f} bp in {b[3]} bars = depth {retrace:.0f}%"
              + (" (pullback-sized)" if 0 < retrace < 100 else " (not a pullback: it went past the start)"))
        if atrBp:
            k4 = 4 * atrBp
            print(f"For the note: atr={atrBp:.0f} k=4 stop>={max(60, k4):.0f}bp depth={retrace:.0f}% speed={speed:.2f}" if speed else "")


def writeSvg(bars, labeled, path, title=""):
    """Minimal candle chart with swing labels. No dependencies."""
    lo, hi = min(b.low for b in bars), max(b.high for b in bars)
    span = hi - lo or 1
    n = len(bars)
    x = lambda i: PAD + i * (SVG_W - 2 * PAD) / n
    y = lambda p: SVG_H - PAD - (p - lo) / span * (SVG_H - 2 * PAD)
    w = max(2.0, (SVG_W - 2 * PAD) / n * 0.6)
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {SVG_W} {SVG_H}" '
             f'font-family="system-ui, sans-serif" font-size="12">',
             f'<rect width="{SVG_W}" height="{SVG_H}" fill="white"/>']
    if title:
        parts.append(f'<text x="{PAD}" y="22" font-size="14" fill="#333">{title}</text>')
    for i, b in enumerate(bars):
        cx = x(i) + w / 2
        color = "#2a7f5f" if b.close >= b.open else "#b8341b"
        parts.append(f'<line x1="{cx:.1f}" y1="{y(b.high):.1f}" x2="{cx:.1f}" y2="{y(b.low):.1f}" stroke="{color}" stroke-width="1"/>')
        top, bot = y(max(b.open, b.close)), y(min(b.open, b.close))
        parts.append(f'<rect x="{x(i):.1f}" y="{top:.1f}" width="{w:.1f}" height="{max(1.0, bot - top):.1f}" fill="{color}"/>')
    pts = " ".join(f"{x(i) + w / 2:.1f},{y(p):.1f}" for i, p, _, _ in labeled)
    parts.append(f'<polyline points="{pts}" fill="none" stroke="#1f5f8b" stroke-width="1.5" stroke-dasharray="4 3"/>')
    for i, p, kind, tag in labeled:
        dy = -8 if kind == "H" else 16
        parts.append(f'<text x="{x(i) + w / 2:.1f}" y="{y(p) + dy:.1f}" text-anchor="middle" fill="#1f5f8b" font-weight="700">{tag or kind}</text>')
    parts.append(f'<text x="{SVG_W - PAD}" y="{SVG_H - 12}" text-anchor="end" fill="#777">{lo:.0f} – {hi:.0f}</text>')
    parts.append("</svg>")
    with open(path, "w") as f:
        f.write("\n".join(parts))
    print(f"wrote {path}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--symbol", default="BTCUSDT")
    parser.add_argument("--date", type=date.fromisoformat, default=datetime.now(timezone.utc).date() - timedelta(days=1))
    parser.add_argument("--start", type=int, default=12, help="UTC hour, inclusive")
    parser.add_argument("--end", type=int, default=16, help="UTC hour, exclusive")
    parser.add_argument("--strength", type=int, default=DEFAULT_STRENGTH)
    parser.add_argument("--svg", help="write a chart to this file")
    parser.add_argument("--live", action="store_true", help="use the public REST API for the most recent bars")
    args = parser.parse_args()

    if args.live:
        allBars = fetchLive(args.symbol, "5m", 300)[:-1]           # drop the still-forming bar
        today = datetime.now(timezone.utc).date()
        start = args.start if args.start != 12 else 0            # default for --live: since 00:00 UTC today
        bars = [b for b in allBars if datetime.fromtimestamp(b.openTime / 1000, tz=timezone.utc).date() == today
                and datetime.fromtimestamp(b.openTime / 1000, tz=timezone.utc).hour >= start]
        atrAll = atrSeries(allBars)
        atr = atrAll[len(allBars) - len(bars):]
        label = f"LIVE {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')} UTC, since {start:02d}:00"
    else:
        bars = loadWindow(args.symbol, args.date, args.start, args.end)
        dayBars = readKlines(fetchDay(args.symbol, args.date, "5m"))
        atrDay = atrSeries(dayBars)
        firstIdx = next(i for i, b in enumerate(dayBars) if b.openTime == bars[0].openTime)
        atr = atrDay[firstIdx:firstIdx + len(bars)]
        label = f"{args.date} UTC {args.start:02d}:00-{args.end:02d}:00"
    labeled = labelSwings(findSwings(bars, args.strength))
    print(f"{args.symbol} 5m, {label}, swing strength {args.strength}")
    printReport(bars, labeled, None, atr)
    if args.svg:
        writeSvg(bars, labeled, args.svg, f"{args.symbol} 5m {args.date} UTC {args.start:02d}-{args.end:02d}")


if __name__ == "__main__":
    main()
