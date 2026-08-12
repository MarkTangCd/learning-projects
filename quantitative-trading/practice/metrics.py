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
from trading_calendar import bars_per_year_of

BARS_PER_YEAR = 365  # crypto daily. NO LONGER THE DEFAULT (L23) — kept as a
                     # name for scripts that deliberately force this calendar.


def max_drawdown(equity):
    """Deepest peak-to-trough decline of an equity curve (negative number)."""
    roll_max = equity.cummax()               # running high-water mark
    drawdown = equity / roll_max - 1         # distance below the peak (<=0)
    return drawdown.min()


def sharpe(returns, bars_per_year=None):
    """Annualized Sharpe ratio (risk-free rate assumed 0 for simplicity).

    bars_per_year=None INFERS the calendar from the series' own DatetimeIndex
    (L23). It used to default to 365, which was silently wrong by +20.4% on
    every stock. Pass a number to override — stocks.py does exactly that to run
    the same returns under both calendars on purpose.
    """
    r = returns.dropna()
    if r.std() == 0:
        return float("nan")
    return r.mean() / r.std() * (bars_per_year_of(r, bars_per_year) ** 0.5)


def cagr(equity, bars_per_year=None):
    """Compound annual growth rate from an equity curve starting at 1.0.

    Same inference as sharpe(). The 365 bug hit CAGR through a different door:
    years = bars/365 turned 10 years of stock data into 6.9, compressing the
    same total return into fewer years and overstating the annual rate.
    """
    years = len(equity) / bars_per_year_of(equity, bars_per_year)
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
