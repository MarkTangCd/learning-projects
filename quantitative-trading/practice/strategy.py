"""L3 signal logic (renamed from signal.py — 'signal' shadows a stdlib module).

Turn a price table into a position column via an SMA crossover.
Rule: signal is computed from CLOSED candles, and the position only takes
effect on the NEXT bar (shift(1)) — otherwise we'd use future info
(look-ahead bias). This same function is reused by the L4 backtest.
"""

import ccxt
import pandas as pd

PROXY = "http://127.0.0.1:1087"


def fetch_ohlcv(symbol="BTC/USDT", timeframe="1d", limit=400):
    """Pull clean OHLCV into a time-indexed DataFrame (from L2)."""
    exchange = ccxt.binance({"timeout": 30000})
    exchange.httpsProxy = PROXY
    raw = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    df = pd.DataFrame(raw, columns=["ts", "open", "high", "low", "close", "volume"])
    df["ts"] = pd.to_datetime(df["ts"], unit="ms", utc=True)
    return df.set_index("ts")


def sma_crossover_signal(df, fast=10, slow=30):
    """Add sma_fast, sma_slow, signal, position columns (long/flat only)."""
    df = df.copy()
    df["sma_fast"] = df["close"].rolling(fast).mean()
    df["sma_slow"] = df["close"].rolling(slow).mean()
    df["signal"] = (df["sma_fast"] > df["sma_slow"]).astype(int)
    df["position"] = df["signal"].shift(1)  # act on the next bar — no look-ahead
    return df


if __name__ == "__main__":
    df = sma_crossover_signal(fetch_ohlcv(), fast=10, slow=30)
    print(df[["close", "sma_fast", "sma_slow", "signal", "position"]].tail(10))
    entries = ((df["position"] == 1) & (df["position"].shift(1) == 0)).sum()
    print("进场次数 (fast=10, slow=30):", entries)
