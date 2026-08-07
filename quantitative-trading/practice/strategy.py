"""L3 signal logic (renamed from signal.py — 'signal' shadows a stdlib module).

Turn a price table into a position column via an SMA crossover.
Rule: signal is computed from CLOSED candles, and the position only takes
effect on the NEXT bar (shift(1)) — otherwise we'd use future info
(look-ahead bias). This same function is reused by the L4 backtest.
"""

import ccxt
import pandas as pd

PROXY = "http://127.0.0.1:1087"


def fetch_ohlcv(symbol="BTC/USDT", timeframe="1d", limit=400, since=None):
    """Pull clean OHLCV into a time-indexed DataFrame (from L2).

    since: optional ISO date like "2020-10-01" -> start the window there.
           None (default) = most recent `limit` bars.
    """
    exchange = ccxt.binance({"timeout": 30000})
    exchange.httpsProxy = PROXY
    since_ms = exchange.parse8601(f"{since}T00:00:00Z") if since else None
    raw = exchange.fetch_ohlcv(symbol, timeframe=timeframe, since=since_ms, limit=limit)
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


def zscore_reversion_signal(df, lookback=20, entry=1.0):
    """A SECOND signal family: mean reversion (the OPPOSITE bet to SMA).

    SMA bets price CONTINUES; mean reversion bets price SNAPS BACK to its
    average. We standardize distance-from-mean into a z-score (how many std
    devs is price from its rolling mean), then:
        z <= -entry  -> price unusually CHEAP  -> go long
        z >=  0      -> reverted to the mean    -> exit (flat)
    Long/flat only, so it drops straight into the L4 backtest — same
    `position` column, same gauntlet. That's L1's 'one interface' dividend.

    The ffill trick: mark only the entry/exit BARS, leave the rest NaN, then
    forward-fill to 'hold the last decision' between them. This is the
    vectorized way to express a stateful hold without a Python loop.
    """
    df = df.copy()
    mean = df["close"].rolling(lookback).mean()
    std = df["close"].rolling(lookback).std()
    df["zscore"] = (df["close"] - mean) / std
    raw = pd.Series(index=df.index, dtype="float64")   # all NaN
    raw[df["zscore"] <= -entry] = 1                     # cheap -> enter long
    raw[df["zscore"] >= 0] = 0                          # back to mean -> exit
    df["signal"] = raw.ffill().fillna(0)               # hold between the marks
    df["position"] = df["signal"].shift(1)             # act next bar — no look-ahead
    return df


if __name__ == "__main__":
    df = sma_crossover_signal(fetch_ohlcv(), fast=10, slow=30)
    print(df[["close", "sma_fast", "sma_slow", "signal", "position"]].tail(10))
    entries = ((df["position"] == 1) & (df["position"].shift(1) == 0)).sum()
    print("进场次数 (fast=10, slow=30):", entries)
