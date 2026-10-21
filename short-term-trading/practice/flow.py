#!/usr/bin/env python3
"""Order flow, two ways: who is hitting the market (taker buys vs sells) and what is resting (book imbalance).

Usage:
  python flow.py --date 2026-10-10                 # offline: 5m delta / CVD for a past session, from klines
  python flow.py --date 2026-10-10 --svg out.svg   # + chart: price on top, CVD below
  python flow.py --live --minutes 10               # live tape: polls aggTrades + depth every 5 s, prints a line each
  python flow.py --live --minutes 60 --every 15

Definitions (Binance USDS-M):
  taker buy  = trade where the BUYER was the taker (aggTrade field m == false) -> someone hit the ask
  taker sell = trade where the buyer was the maker (m == true)                 -> someone hit the bid
  delta      = taker buy volume - taker sell volume (per bar / per interval), in USD
  CVD        = cumulative delta since 00:00 UTC (offline) or since the tape started (live)
  book imbalance = bid size / (bid size + ask size) over the top N levels; 0.5 = balanced
Offline uses kline columns volume & taker_buy_volume (no aggTrades download needed).
Standard library only; honors https_proxy.
"""
import argparse
import csv
import json
import time
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from binance_data import fetchDay, readKlines
from structure import findSwings, labelSwings

FAPI = "https://fapi.binance.com/fapi/v1"
TAPE_LOG = Path(__file__).with_name("tape_log.csv")
SVG_W, SVG_H, PAD = 900, 460, 40


def getJson(url):
    with urllib.request.urlopen(url, timeout=15) as resp:
        return json.loads(resp.read().decode())


# ---------------- offline ----------------

def sessionFlow(bars):
    """Per-bar (close, deltaUsd, cvdUsd) from kline taker-buy columns."""
    out, cvd = [], 0.0
    for b in bars:
        buyQuote = b.takerBuyQuote
        sellQuote = b.quoteVolume - buyQuote
        delta = buyQuote - sellQuote
        cvd += delta
        out.append((b, delta, cvd))
    return out


def divergences(bars, flow, strength=3):
    """Swing highs where price made HH but CVD did not (and mirror for lows)."""
    labeled = labelSwings(findSwings(bars, strength))
    notes = []
    lastHigh = lastLow = None
    for idx, price, kind, tag in labeled:
        c = flow[idx][2]
        if kind == "H":
            if lastHigh and tag == "HH" and c < lastHigh[1]:
                notes.append((idx, "price HH but CVD lower high -> buyers hitting less; absorption / weak push"))
            lastHigh = (price, c)
        else:
            if lastLow and tag == "LL" and c > lastLow[1]:
                notes.append((idx, "price LL but CVD higher low -> sellers hitting less; absorption / weak push"))
            lastLow = (price, c)
    return labeled, notes


def printOffline(bars, flow, labeled, notes, startHour, endHour):
    print(f"{'UTC':>5} {'close':>9} {'delta $k':>9} {'CVD $k':>9} {'swing':>6}")
    swingAt = {idx: tag or kind for idx, _, kind, tag in labeled}
    noteAt = {idx: n for idx, n in notes}
    for i, (b, delta, cvd) in enumerate(flow):
        t = datetime.fromtimestamp(b.openTime / 1000, tz=timezone.utc)
        if not (startHour <= t.hour < endHour):
            continue
        line = f"{t.strftime('%H:%M'):>5} {b.close:>9.1f} {delta / 1e3:>+9.0f} {cvd / 1e3:>+9.0f} {swingAt.get(i, ''):>6}"
        if i in noteAt:
            line += f"   <- {noteAt[i]}"
        print(line)
    print(f"\nSession delta (00:00 -> now): {flow[-1][2] / 1e6:+.1f} $M. {len(notes)} divergence(s) at swing points.")


def writeFlowSvg(bars, flow, labeled, path, title):
    n = len(bars)
    lo, hi = min(b.low for b in bars), max(b.high for b in bars)
    cv = [f[2] for f in flow]
    clo, chi = min(cv), max(cv)
    topH = SVG_H * 0.6
    x = lambda i: PAD + i * (SVG_W - 2 * PAD) / n
    yP = lambda p: PAD + (hi - p) / (hi - lo or 1) * (topH - PAD - 10)
    yC = lambda c: topH + 10 + (chi - c) / (chi - clo or 1) * (SVG_H - topH - PAD - 10)
    w = max(2.0, (SVG_W - 2 * PAD) / n * 0.6)
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {SVG_W} {SVG_H}" font-family="system-ui, sans-serif" font-size="12">',
             f'<rect width="{SVG_W}" height="{SVG_H}" fill="white"/>', f'<text x="{PAD}" y="22" font-size="14" fill="#333">{title}</text>']
    for i, b in enumerate(bars):
        cx = x(i) + w / 2
        color = "#2a7f5f" if b.close >= b.open else "#b8341b"
        parts.append(f'<line x1="{cx:.1f}" y1="{yP(b.high):.1f}" x2="{cx:.1f}" y2="{yP(b.low):.1f}" stroke="{color}"/>')
        top, bot = yP(max(b.open, b.close)), yP(min(b.open, b.close))
        parts.append(f'<rect x="{x(i):.1f}" y="{top:.1f}" width="{w:.1f}" height="{max(1.0, bot - top):.1f}" fill="{color}"/>')
    for idx, price, kind, tag in labeled:
        dy = -6 if kind == "H" else 14
        parts.append(f'<text x="{x(idx) + w / 2:.1f}" y="{yP(price) + dy:.1f}" text-anchor="middle" fill="#1f5f8b" font-weight="700">{tag or kind}</text>')
    pts = " ".join(f"{x(i) + w / 2:.1f},{yC(c):.1f}" for i, c in enumerate(cv))
    parts.append(f'<line x1="{PAD}" y1="{topH + 5:.1f}" x2="{SVG_W - PAD}" y2="{topH + 5:.1f}" stroke="#ddd"/>')
    parts.append(f'<polyline points="{pts}" fill="none" stroke="#1f5f8b" stroke-width="1.8"/>')
    parts.append(f'<text x="{PAD}" y="{SVG_H - 12}" fill="#1f5f8b" font-weight="700">CVD = taker buy − taker sell, cumulative since 00:00 UTC (dots = swing points)</text>')
    for idx, price, kind, tag in labeled:
        parts.append(f'<circle cx="{x(idx) + w / 2:.1f}" cy="{yC(cv[idx]):.1f}" r="3" fill="#1f5f8b"/>')
    parts.append("</svg>")
    Path(path).write_text("\n".join(parts))
    print(f"wrote {path}")


# ---------------- live ----------------

def liveTape(symbol, minutes, every, levels=5):
    print(f"{'UTC':>8} {'last':>9} {'buy $k':>7} {'sell $k':>8} {'delta $k':>9} {'CVD $k':>8} {'bid/ask top{levels}':>16} {'imb':>5}")
    lastId, cvd, end = None, 0.0, time.time() + minutes * 60
    newLog = not TAPE_LOG.exists()
    with TAPE_LOG.open("a", newline="") as f:
        w = csv.writer(f)
        if newLog:
            w.writerow(["utc", "symbol", "last", "buyUsd", "sellUsd", "deltaUsd", "cvdUsd", "bidSize", "askSize", "imbalance"])
        while time.time() < end:
            trades = getJson(f"{FAPI}/aggTrades?symbol={symbol}&limit=1000")
            book = getJson(f"{FAPI}/depth?symbol={symbol}&limit={levels}")
            fresh = [t for t in trades if lastId is None or t["a"] > lastId] if lastId is not None else trades[-200:]
            lastId = trades[-1]["a"]
            buy = sum(float(t["p"]) * float(t["q"]) for t in fresh if not t["m"])
            sell = sum(float(t["p"]) * float(t["q"]) for t in fresh if t["m"])
            delta = buy - sell
            cvd += delta
            bid = sum(float(p) * float(q) for p, q in book["bids"])
            ask = sum(float(p) * float(q) for p, q in book["asks"])
            imb = bid / (bid + ask) if bid + ask else 0.5
            last = float(trades[-1]["p"])
            now = datetime.now(timezone.utc)
            print(f"{now.strftime('%H:%M:%S'):>8} {last:>9.1f} {buy / 1e3:>7.0f} {sell / 1e3:>8.0f} {delta / 1e3:>+9.0f} {cvd / 1e3:>+8.0f} "
                  f"{bid / 1e3:>7.0f}/{ask / 1e3:<7.0f} {imb:>5.2f}", flush=True)
            w.writerow([now.strftime("%Y-%m-%d %H:%M:%S"), symbol, last, f"{buy:.0f}", f"{sell:.0f}", f"{delta:.0f}", f"{cvd:.0f}", f"{bid:.0f}", f"{ask:.0f}", f"{imb:.3f}"])
            f.flush()
            time.sleep(every)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--symbol", default="BTCUSDT")
    parser.add_argument("--date", type=date.fromisoformat, default=datetime.now(timezone.utc).date() - timedelta(days=1))
    parser.add_argument("--start", type=int, default=12)
    parser.add_argument("--end", type=int, default=16)
    parser.add_argument("--svg")
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--minutes", type=float, default=10)
    parser.add_argument("--every", type=float, default=5)
    args = parser.parse_args()
    if args.live:
        return liveTape(args.symbol, args.minutes, args.every)
    bars = readKlines(fetchDay(args.symbol, args.date, "5m"))
    flow = sessionFlow(bars)
    window = [i for i, b in enumerate(bars) if args.start <= datetime.fromtimestamp(b.openTime / 1000, tz=timezone.utc).hour < args.end]
    wBars = [bars[i] for i in window]
    wFlow = [flow[i] for i in window]
    labeled, notes = divergences(wBars, wFlow)
    print(f"{args.symbol} 5m, {args.date}, UTC {args.start:02d}-{args.end:02d} (CVD cumulative since 00:00)")
    printOffline(wBars, wFlow, labeled, notes, 0, 24)
    if args.svg:
        writeFlowSvg(wBars, wFlow, labeled, args.svg, f"{args.symbol} 5m {args.date} UTC {args.start:02d}-{args.end:02d}: price + CVD")


if __name__ == "__main__":
    main()
