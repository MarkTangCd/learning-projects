"""L5 practice: turn an equity curve into a scorecard.

Three risk-adjusted numbers that total return hides:
  - Max Drawdown : the worst peak-to-trough drop (can you hold it?)
  - Sharpe       : return per unit of volatility (is it worth holding?)
  - CAGR         : compound annual growth rate (how fast, per year?)

Reuses the L4 backtest() + the L3 signal — one signal, reused everywhere.
"""

import pandas as pd

from backtest import backtest
from strategy import fetch_ohlcv, sma_crossover_signal

BARS_PER_YEAR = 365  # daily crypto candles trade 7x24 -> ~365 bars/year


def max_drawdown(equity):
    """Deepest peak-to-trough decline of an equity curve (negative number)."""
    roll_max = equity.cummax()               # running high-water mark
    drawdown = equity / roll_max - 1         # distance below the peak (<=0)
    return drawdown.min()


def sharpe(returns, bars_per_year=BARS_PER_YEAR):
    """Annualized Sharpe ratio (risk-free rate assumed 0 for simplicity)."""
    r = returns.dropna()
    if r.std() == 0:
        return float("nan")
    return r.mean() / r.std() * (bars_per_year ** 0.5)


def cagr(equity, bars_per_year=BARS_PER_YEAR):
    """Compound annual growth rate from an equity curve starting at 1.0."""
    years = len(equity) / bars_per_year
    return equity.iloc[-1] ** (1 / years) - 1


def scorecard(df, label):
    """Print the three-number scorecard for a backtested df, plus buy & hold."""
    print(f"\n=== {label} ===")
    print(f"{'':10}{'MaxDD':>9}{'Sharpe':>9}{'CAGR':>9}")
    print(f"{'策略':10}{max_drawdown(df['equity_net']):>9.1%}"
          f"{sharpe(df['strat_ret_net']):>9.2f}{cagr(df['equity_net']):>9.1%}")
    print(f"{'买入持有':8}{max_drawdown(df['equity_hold']):>9.1%}"
          f"{sharpe(df['ret']):>9.2f}{cagr(df['equity_hold']):>9.1%}")


if __name__ == "__main__":
    price = fetch_ohlcv()  # fetch once, reuse across param sets
    for fast, slow in [(5, 20), (10, 30), (20, 60)]:
        df = sma_crossover_signal(price, fast=fast, slow=slow)
        df = backtest(df)
        scorecard(df, f"SMA({fast},{slow})")
