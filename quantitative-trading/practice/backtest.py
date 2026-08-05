"""L4 practice: a vectorized backtest of the SMA-crossover signal.

Reuses the signal function from L3 (one signal, reused in research — L1 rule).
Computes the strategy equity curve WITH trading costs and compares it to
buy-and-hold. No for-loops — pure column math.
"""

import pandas as pd

from strategy import fetch_ohlcv, sma_crossover_signal

FEE = 0.001  # 0.1% per side — stands in for fees + slippage. Try 0.0 to compare.


def backtest(df, fee=FEE):
    """Add return / cost / equity columns. Assumes df has a 'position' column."""
    df = df.copy()
    df["ret"] = df["close"].pct_change()                  # per-bar asset return
    df["strat_ret"] = df["position"] * df["ret"]          # only earn when holding
    df["trade"] = df["position"].diff().abs()             # 1 on each entry/exit
    df["cost"] = df["trade"] * fee
    df["strat_ret_net"] = df["strat_ret"] - df["cost"]    # net of costs

    df["equity_gross"] = (1 + df["strat_ret"].fillna(0)).cumprod()
    df["equity_net"] = (1 + df["strat_ret_net"].fillna(0)).cumprod()
    df["equity_hold"] = (1 + df["ret"].fillna(0)).cumprod()  # buy & hold benchmark
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


if __name__ == "__main__":
    FAST, SLOW = 10, 30
    df = sma_crossover_signal(fetch_ohlcv(), fast=FAST, slow=SLOW)
    df = backtest(df, fee=FEE)
    report(df, FAST, SLOW, FEE)
