"""L23 practice: move the machine to stocks — and recalibrate the CLOCK.

The whole research machine (signals, backtest, walk-forward, vol targeting,
plateau selection) reads a DataFrame with an open/high/low/close/volume shape
and a datetime index. `fetch_stock` below returns exactly that. So the machine
transfers with ZERO changes — the L1 interface dividend, cashed a 8th time.

What does NOT transfer is the CALENDAR, and it is wired into constants you have
been carrying since L5:

    metrics.BARS_PER_YEAR = 365      # crypto trades 7x24
    sizing.PERIODS_PER_YEAR = 365

Stocks trade ~252 days a year. Leaving 365 in place does not crash anything —
it silently inflates every Sharpe by sqrt(365/252) = 1.20 (+20%) and makes the
vol-targeting dial under-size positions by the same factor. A wrong constant
that never raises is far more dangerous than one that does.

Run:  python stocks.py clock            # the 365-vs-252 damage, measured
      python stocks.py overnight        # where stock returns actually happen
      python stocks.py dead             # what the data source cannot show you
"""

import sys

import numpy as np
import pandas as pd
import yfinance as yf

from backtest import backtest
from metrics import cagr, max_drawdown, sharpe
from strategy import sma_crossover_signal

TRADING_DAYS = 252          # the honest stock calendar
CRYPTO_DAYS = 365           # what every lesson up to L22 assumed
DEMO = ("SPY", "AAPL", "KO")


def fetch_stock(symbol="SPY", since="2015-01-01", until=None):
    """Adapter: yfinance -> the SAME frame shape `fetch_ohlcv` returns.

    auto_adjust=True gives split- AND dividend-adjusted prices, i.e. a TOTAL
    RETURN series. Without it you would be modelling price return only, and for
    a dividend payer that is a large, one-directional error.
    """
    df = yf.Ticker(symbol).history(start=since, end=until, auto_adjust=True)
    if df.empty:
        raise SystemExit(f"没有取到 {symbol} 的数据 —— 代码写错了,或者这个标的已经退市。")
    df = df.rename(columns=str.lower)[["open", "high", "low", "close", "volume"]]
    df.index = pd.to_datetime(df.index).tz_localize(None)
    return df


def bars_per_year(df):
    """Measure the calendar instead of assuming it."""
    span_years = (df.index[-1] - df.index[0]).days / 365.25
    return len(df) / span_years


def cmd_clock():
    """Score the SAME strategy under both calendars. Nothing about the strategy
    changes — only the number you divide by. The gap is pure measurement error."""
    print("同一个策略,同一段数据,只换年化常数:\n")
    print(f"  {'标的':<7}{'实测 bar/年':>12}{'Sharpe@365':>13}{'Sharpe@252':>13}"
          f"{'虚高':>9}{'CAGR@365':>11}{'CAGR@252':>11}")
    for sym in DEMO:
        price = fetch_stock(sym)
        df = backtest(sma_crossover_signal(price, fast=20, slow=60))
        r, eq = df["strat_ret_net"], df["equity_net"]
        s365, s252 = sharpe(r, CRYPTO_DAYS), sharpe(r, TRADING_DAYS)
        c365, c252 = cagr(eq, CRYPTO_DAYS), cagr(eq, TRADING_DAYS)
        print(f"  {sym:<7}{bars_per_year(price):>12.1f}{s365:>13.2f}{s252:>13.2f}"
              f"{s365 / s252 - 1:>9.1%}{c365:>11.1%}{c252:>11.1%}")
    print(f"\n  虚高倍数是常数:sqrt(365/252) = {np.sqrt(CRYPTO_DAYS / TRADING_DAYS):.3f}"
          f" —— 与策略、与标的无关,纯粹是除错了数。")
    print("  CAGR 同向虚高,原因不同:years = bar数/365 把 10 年数据当成 6.9 年,"
          "\n  同样的总收益被摊进更少的年份 -> 年化速度被高估。两个指标一起骗你。")
    print("  没有任何报错。一个不会抛异常的错误常数,比会抛的危险得多。")


def cmd_overnight():
    """Decompose total return into the part you can trade and the part you cannot.
    Crypto never closes, so this split does not exist there. In stocks a large
    share of the drift arrives while the market is SHUT — you hold through it,
    you cannot react to it, and any entry timed at the open has already missed it."""
    print("收益到底在哪段时间产生?(隔夜 = 你无法交易的那段)\n")
    print(f"  {'标的':<7}{'总累计':>11}{'只吃隔夜':>11}{'只吃盘中':>11}{'隔夜占比':>11}")
    for sym in DEMO:
        df = fetch_stock(sym)
        overnight = (df["open"] / df["close"].shift(1) - 1).dropna()
        intraday = (df["close"] / df["open"] - 1).dropna()
        tot = (1 + df["close"].pct_change().dropna()).prod() - 1
        on, it = (1 + overnight).prod() - 1, (1 + intraday).prod() - 1
        share = overnight.mean() / (overnight.mean() + intraday.mean())
        print(f"  {sym:<7}{tot:>11.1%}{on:>11.1%}{it:>11.1%}{share:>11.1%}")
    print("\n  含义:你从 L3 起用的 `signal.shift(1)` 假设「收盘算信号、按收盘价成交」。")
    print("  crypto 里这成立(永不收市)。股票里信号在收盘后才算得出来,最早只能在")
    print("  【次日开盘】成交 —— 中间那道跳空,正是上表里收益最集中的地方。")


def cmd_dead():
    """Survivorship, demonstrated rather than asserted: ask the data source for
    companies that no longer exist. What comes back is the whole problem."""
    print("幸存者偏差:向数据源索要已经死掉的公司\n")
    for sym, note in (("SPY", "活着 —— 作为对照"), ("SIVBQ", "硅谷银行,2023 倒闭"),
                      ("LEHMQ", "雷曼兄弟,2008 倒闭"), ("ENRNQ", "安然,2001 倒闭")):
        try:
            df = yf.Ticker(sym).history(start="2015-01-01", auto_adjust=True)
            got = f"{len(df)} 根 bar" if not df.empty else "空 —— 什么都没有"
        except Exception as e:
            got = f"报错 {type(e).__name__}"
        print(f"  {sym:<8}{note:<22}-> {got}")
    print("\n  你今天能列举出来的标的,已经全部是【活下来的】那批。")
    print("  用它们做出来的回测,天然继承了「这家公司没倒闭」这个未来信息。")
    print("  crypto 上你也有这个问题(退市的币更多),只是当时没人提醒你。")


COMMANDS = {"clock": cmd_clock, "overnight": cmd_overnight, "dead": cmd_dead}

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "clock"
    if cmd not in COMMANDS:
        raise SystemExit(f"用法: python stocks.py [{'|'.join(COMMANDS)}]")
    COMMANDS[cmd]()
