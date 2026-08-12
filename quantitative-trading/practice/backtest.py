"""L4 practice: a vectorized backtest of the SMA-crossover signal.

Reuses the signal function from L3 (one signal, reused in research — L1 rule).
Computes the strategy equity curve WITH trading costs and compares it to
buy-and-hold. No for-loops — pure column math.
"""

import matplotlib.pyplot as plt
import pandas as pd

from strategy import fetch_ohlcv, sma_crossover_signal

FEE = 0.001  # 0.1% per side — stands in for fees + slippage. Try 0.0 to compare.
# Perp funding: you PAY carry to hold a leveraged position, either side. This is
# the cost that makes shorting NOT a free lunch. Long-only backtests left it 0;
# a two-sided strategy that is always in the market must pay it every bar.
# ~1 bp/day ≈ 3.7%/yr — a conservative stand-in for average BTC/ETH perp funding.
FUNDING = 0.0  # default 0 keeps every prior long-only lesson byte-identical


def backtest(df, fee=FEE, funding=FUNDING):
    """Add return / cost / equity columns. Assumes df has a 'position' column.

    `position` may now be -1 (short), 0 (flat) or +1 (long). The math already
    handles shorts: position*ret inverts the return, and a +1->-1 flip counts as
    2 units of turnover in `trade` (close long + open short) -> double fee.
    `funding` charges carry on |position| every bar (perp holding cost).
    """
    df = df.copy()
    df["ret"] = df["close"].pct_change()                  # per-bar asset return
    df["strat_ret"] = df["position"] * df["ret"]          # short (-1) earns when price falls
    df["trade"] = df["position"].diff().abs()             # turnover: 2 on a long<->short flip
    df["cost"] = df["trade"] * fee + df["position"].abs() * funding  # fees + carry
    df["strat_ret_net"] = df["strat_ret"] - df["cost"]    # net of costs

    df["equity_gross"] = (1 + df["strat_ret"].fillna(0)).cumprod()
    df["equity_net"] = (1 + df["strat_ret_net"].fillna(0)).cumprod()
    df["equity_hold"] = (1 + df["ret"].fillna(0)).cumprod()  # buy & hold benchmark
    return df


def backtest_next_open(df, fee=FEE, funding=FUNDING):
    """L24: the same backtest under an HONEST stock fill — next open, not this close.

    `backtest()` above assumes you compute the signal at a bar's close and get
    filled at THAT close. Crypto never closes, so that is defensible. A stock
    exchange is shut when the signal exists; the earliest you can trade is the
    NEXT OPEN, and L23 measured that the skipped overnight window is where most
    of the return lives (SPY 62%, KO 92%).

    Two things change together, and the second one is the trap:

      1. Accounting moves to OPEN-to-OPEN. `open.pct_change()` at row t is the
         return from open[t-1] to open[t].
      2. The lag becomes shift(2), NOT shift(1). To earn the open[t-1]->open[t]
         move you must already be positioned AT open[t-1], so the decision has
         to be made with data available before it — at close[t-2]. Reusing
         shift(1) here would fill you at an open using a signal computed at the
         close that comes AFTER it: a brand-new look-ahead bug, introduced by
         the very change meant to make the backtest more honest.

    Takes `signal` (not `position`) because the lag is this function's business.
    """
    df = df.copy()
    df["ret"] = df["open"].pct_change()                   # open[t-1] -> open[t]
    df["position"] = df["signal"].shift(2)                # see docstring
    df["strat_ret"] = df["position"] * df["ret"]
    df["trade"] = df["position"].diff().abs()
    df["cost"] = df["trade"] * fee + df["position"].abs() * funding
    df["strat_ret_net"] = df["strat_ret"] - df["cost"]

    df["equity_gross"] = (1 + df["strat_ret"].fillna(0)).cumprod()
    df["equity_net"] = (1 + df["strat_ret_net"].fillna(0)).cumprod()
    df["equity_hold"] = (1 + df["ret"].fillna(0)).cumprod()
    return df


def report(df, fast, slow, fee):
    total_net = df["equity_net"].iloc[-1] - 1
    total_gross = df["equity_gross"].iloc[-1] - 1
    total_hold = df["equity_hold"].iloc[-1] - 1
    trades = int(df["trade"].sum())
    print(f"\n=== SMA({fast},{slow})  fee={fee:.3%} ===")
    print(f"策略 含成本 总收益: {total_net:+.1%}")
    print(f"策略 零成本 总收益: {total_gross:+.1%}   (成本拖累 {total_gross-total_net:.1%})")
    print(f"买入持有 总收益:   {total_hold:+.1%}   <-- 及格线")
    print(f"总成交笔数:        {trades}")


def plot_equity(df, fast, slow, out="equity.png"):
    """Recipe plot: strategy (net) vs buy-and-hold equity curves."""
    df[["equity_net", "equity_hold"]].plot(figsize=(10, 5))
    plt.title(f"SMA({fast},{slow}) equity — net vs buy & hold")
    plt.ylabel("equity (start = 1.0)")
    plt.tight_layout()
    plt.savefig(out, dpi=120)  # headless: save instead of plt.show()
    print(f"图已保存: {out}")


if __name__ == "__main__":
    FAST, SLOW = 20, 60
    df = sma_crossover_signal(fetch_ohlcv(), fast=FAST, slow=SLOW)
    df = backtest(df, fee=FEE)
    report(df, FAST, SLOW, FEE)
    plot_equity(df, FAST, SLOW)
