#!/usr/bin/env python3
"""Shared loader for Binance public kline files (data.binance.vision). Standard library only.

fetchDay(symbol, day, interval) -> cached zip path or None
readKlines(zipPath)             -> list of Kline tuples
fetchLive(symbol, interval, n)  -> last n Kline tuples from the public REST API (no key; honors https_proxy)
atrSeries(bars, length)         -> Wilder ATR per bar (None until warmed up)
"""
import json
import statistics
import csv
import io
import urllib.request
import zipfile
from collections import namedtuple
from pathlib import Path

BASE_URL = "https://data.binance.vision/data/futures/um/daily/klines"
LIVE_URL = "https://fapi.binance.com/fapi/v1/klines"
DATA_DIR = Path(__file__).with_name("data") / "klines"

Kline = namedtuple("Kline", "openTime open high low close volume quoteVolume count takerBuyQuote")


def fetchDay(symbol, day, interval="1m"):
    """Return the cached zip for one UTC day, downloading if needed. None when unavailable."""
    target = DATA_DIR / symbol / interval / f"{symbol}-{interval}-{day.isoformat()}.zip"
    if target.exists():
        return target
    target.parent.mkdir(parents=True, exist_ok=True)
    url = f"{BASE_URL}/{symbol}/{interval}/{target.name}"
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            target.write_bytes(resp.read())
        return target
    except Exception as err:            # 404 for days not yet published, network errors
        print(f"  skip {day} ({interval}): {err}")
        return None


def readKlines(zipPath):
    """Parse one daily zip into Kline tuples (header line skipped)."""
    with zipfile.ZipFile(zipPath) as zf:
        raw = zf.read(zf.namelist()[0]).decode()
    out = []
    for row in csv.reader(io.StringIO(raw)):
        if not row or not row[0].isdigit():
            continue
        out.append(Kline(int(row[0]), float(row[1]), float(row[2]), float(row[3]), float(row[4]),
                         float(row[5]), float(row[7]), int(row[8]), float(row[10])))
    return out


def fetchLive(symbol, interval="5m", limit=300):
    """Most recent bars straight from Binance USDS-M public REST (last bar is still forming)."""
    url = f"{LIVE_URL}?symbol={symbol}&interval={interval}&limit={limit}"
    with urllib.request.urlopen(url, timeout=20) as resp:
        rows = json.loads(resp.read().decode())
    return [Kline(int(r[0]), float(r[1]), float(r[2]), float(r[3]), float(r[4]),
                  float(r[5]), float(r[7]), int(r[8]), float(r[10])) for r in rows]


def atrSeries(bars, length=14):
    """Wilder ATR: first value = simple mean of TR, then smoothed. None while warming up."""
    out, prevClose, atr, trs = [], None, None, []
    for b in bars:
        tr = b.high - b.low if prevClose is None else max(b.high - b.low, abs(b.high - prevClose), abs(b.low - prevClose))
        prevClose = b.close
        if atr is None:
            trs.append(tr)
            atr = statistics.mean(trs) if len(trs) == length else None
        else:
            atr = (atr * (length - 1) + tr) / length
        out.append(atr)
    return out
