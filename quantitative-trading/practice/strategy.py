"""L3 signal logic (renamed from signal.py — 'signal' shadows a stdlib module).

Turn a price table into a position column via an SMA crossover.
Rule: signal is computed from CLOSED candles, and the position only takes
effect on the NEXT bar (shift(1)) — otherwise we'd use future info
(look-ahead bias). This same function is reused by the L4 backtest.
"""

import ccxt
import numpy as np
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


def sma_crossover_signal(df, fast=10, slow=30, long_short=False):
    """Add sma_fast, sma_slow, signal, position columns.

    long_short=False (default): long/flat, signal in {0, +1} — the L3 behavior,
        kept byte-for-byte so every prior lesson still reproduces.
    long_short=True: two-sided, signal in {-1, +1} — SHORT when fast < slow
        instead of sitting flat. Lets the strategy profit in downtrends, not
        just 'lose less'. Same `position` column -> same gauntlet (L1).
    """
    df = df.copy()
    df["sma_fast"] = df["close"].rolling(fast).mean()
    df["sma_slow"] = df["close"].rolling(slow).mean()
    up = df["sma_fast"] > df["sma_slow"]
    df["signal"] = np.where(up, 1, -1) if long_short else up.astype(int)
    df["position"] = df["signal"].shift(1)  # act on the next bar — no look-ahead
    return df


def zscore_reversion_signal(df, lookback=20, entry=1.0, long_short=False):
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
    z = (df["close"] - mean) / std
    df["zscore"] = z
    raw = pd.Series(index=df.index, dtype="float64")   # all NaN
    if long_short:
        # Symmetric, SAME single `entry` knob — no new overfitting surface.
        raw[(np.sign(z) != np.sign(z.shift(1)))] = 0   # crossed the mean -> flat
        raw[z <= -entry] = 1                           # unusually cheap -> long
        raw[z >= entry] = -1                           # unusually rich  -> SHORT
    else:
        raw[z <= -entry] = 1                           # cheap -> enter long
        raw[z >= 0] = 0                                # back to mean -> exit
    df["signal"] = raw.ffill().fillna(0)               # hold between the marks
    df["position"] = df["signal"].shift(1)             # act next bar — no look-ahead
    return df


def efficiency_ratio(close, window=20):
    """Kaufman Efficiency Ratio — a pure measure of 'trendiness', no new lib.

    Of all the distance price traveled over the last `window` bars, how much
    was NET progress?  ER = |net change| / total path length.
        ER -> 1 : a clean one-way trend (net move ≈ total travel)
        ER -> 0 : choppy / range-bound (lots of travel, no net progress)
    This is the axis that separates 'when trend wins' from 'when reversion
    wins' — exactly what fold 5 (L13) showed by losing in a rally.
    """
    net = (close - close.shift(window)).abs()          # net progress over window
    total = close.diff().abs().rolling(window).sum()   # total path length walked
    return net / total


def regime_switch_signal(df, er_window=20, er_thresh=0.3,
                         fast=20, slow=60, lookback=20, entry=1.0,
                         long_short=False):
    """A signal that picks WHICH signal to trust, by market regime.

    Trend-following wins in trends; mean reversion protects on the downside
    and wins in chop. So measure trendiness (Efficiency Ratio) and ROUTE:
        trend regime (ER > thresh) -> SMA signal
        range regime (ER <= thresh) -> reversion signal
    The sub-signals stay at family DEFAULTS; the only NEW knob is er_thresh,
    kept deliberately minimal because every added knob is fresh overfitting
    surface. Same `position` output -> same gauntlet, a third time (L1).
    """
    df = df.copy()
    er = efficiency_ratio(df["close"], er_window)
    trend_sig = sma_crossover_signal(df, fast=fast, slow=slow, long_short=long_short)["signal"]
    revert_sig = zscore_reversion_signal(df, lookback=lookback, entry=entry, long_short=long_short)["signal"]
    is_trend = er > er_thresh
    df["er"] = er
    df["regime"] = np.where(is_trend, "trend", "range")
    df["signal"] = np.where(is_trend, trend_sig, revert_sig)   # route by regime
    df["position"] = df["signal"].shift(1)   # one clean shift — no look-ahead
    return df


if __name__ == "__main__":
    df = sma_crossover_signal(fetch_ohlcv(), fast=10, slow=30)
    print(df[["close", "sma_fast", "sma_slow", "signal", "position"]].tail(10))
    entries = ((df["position"] == 1) & (df["position"].shift(1) == 0)).sum()
    print("进场次数 (fast=10, slow=30):", entries)
