"""L12 practice: run the SECOND signal family through the SAME gauntlet.

Mean reversion (zscore_reversion_signal) vs trend (sma_crossover_signal) vs
buy-and-hold, on one daily BTC window. The point is NOT to crown a winner from
one window (L6/L7 taught us a single-window number is a smoke test, not a
verdict) — it's to prove the new signal is a drop-in: a new `position` column,
and every gauntlet tool (backtest, scorecard) reuses unchanged.

Run:  python reversion.py
Next: feed zscore_reversion_signal into oos.py / walkforward.py (L13) for the
real verdict — same skepticism, same gauntlet, new signal.
"""

from backtest import backtest
from metrics import scorecard
from strategy import fetch_ohlcv, sma_crossover_signal, zscore_reversion_signal

LOOKBACK, ENTRY = 20, 1.0   # mean-reversion knobs: window, entry z-threshold


def run(price, label, signal_df):
    df = backtest(signal_df)
    trades = int(df["trade"].sum())
    scorecard(df, f"{label}  (成交 {trades} 笔)")


if __name__ == "__main__":
    price = fetch_ohlcv()   # fetch once, reuse across signals — same window is fair
    start, end = price.index[0].date(), price.index[-1].date()
    print(f"窗口 [{start} -> {end}]  —— 同一窗口下三者对比(单窗 = 冒烟测试,非定论)")

    run(price, f"均值回归 z<{-ENTRY} (lookback={LOOKBACK})",
        zscore_reversion_signal(price, lookback=LOOKBACK, entry=ENTRY))
    run(price, "趋势 SMA(20,60)", sma_crossover_signal(price, fast=20, slow=60))
    # buy & hold is printed inside every scorecard as the 及格线 baseline.
