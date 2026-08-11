"""L6 practice: honest out-of-sample validation via a train/test split.

Grid-search SMA params on the TRAIN slice only, lock the in-sample winner,
then judge it ONCE on the TEST slice it never saw. The gap between train and
test performance = the overfitting tax -- your honest estimate of the future.

Reuses L4 backtest() + L5 metrics. One signal, reused everywhere (L1 rule).
"""

import math

from backtest import backtest
from metrics import BARS_PER_YEAR, cagr, max_drawdown, sharpe
from strategy import fetch_ohlcv, sma_crossover_signal

TRAIN_FRAC = 0.7
GRID = [(f, s) for f in (5, 10, 20, 30) for s in (40, 60, 90, 120) if f < s]


def score(net_returns, bars_per_year=BARS_PER_YEAR):
    """Scorecard for a slice, rebuilt from its own per-bar net returns.

    bars_per_year defaults to 365 (crypto trades 7x24), which keeps every lesson
    L5-L22 byte-identical. STOCKS TRADE ~252 DAYS A YEAR — leaving this at 365
    inflates Sharpe by sqrt(365/252) = 1.20 and misstates CAGR. Pass the right
    calendar when you leave crypto (see stocks.py).
    """
    r = net_returns.dropna()
    equity = (1 + r).cumprod()
    return {"sharpe": sharpe(r, bars_per_year), "cagr": cagr(equity, bars_per_year),
            "mdd": max_drawdown(equity)}


def evaluate(price, fast, slow, split):
    """Backtest one param set on the full series, then score train/test slices.

    An SMA on any day only looks at PAST bars, so computing across the split
    leaks no future. The one thing kept out of sample is WHICH params we pick
    -- and that decision is made on train alone (see __main__).
    """
    net = backtest(sma_crossover_signal(price, fast=fast, slow=slow))["strat_ret_net"]
    return score(net.iloc[:split]), score(net.iloc[split:])


def sharpe_key(val):
    """Sort key that pushes all-cash (nan-Sharpe) slices to the bottom."""
    return -math.inf if math.isnan(val["sharpe"]) else val["sharpe"]


if __name__ == "__main__":
    price = fetch_ohlcv(since="2021-01-01", limit=1000)  # spans bull + bear
    split = int(len(price) * TRAIN_FRAC)
    print(f"数据 {price.index[0].date()} -> {price.index[-1].date()}  "
          f"| train {split} 根 / test {len(price) - split} 根 "
          f"(切点 {price.index[split].date()})")

    rows = [(f, s, *evaluate(price, f, s, split)) for f, s in GRID]

    # Buy & hold benchmark -- the real pass mark (L5 rule: always compare to doing nothing).
    bh_ret = price["close"].pct_change()
    bh_tr, bh_te = score(bh_ret.iloc[:split]), score(bh_ret.iloc[split:])

    # Rank by TRAIN sharpe -- as if train were the only data we had to choose from.
    rows.sort(key=lambda x: sharpe_key(x[2]), reverse=True)

    print(f"\n{'params':>10}{'train_Shrp':>12}{'test_Shrp':>11}"
          f"{'train_CAGR':>12}{'test_CAGR':>11}")
    for f, s, tr, te in rows:
        print(f"{f'({f},{s})':>10}{tr['sharpe']:>12.2f}{te['sharpe']:>11.2f}"
              f"{tr['cagr']:>12.1%}{te['cagr']:>11.1%}")
    print(f"{'-' * 56}")
    print(f"{'买入持有':>8}{bh_tr['sharpe']:>12.2f}{bh_te['sharpe']:>11.2f}"
          f"{bh_tr['cagr']:>12.1%}{bh_te['cagr']:>11.1%}   <-- 及格线")

    # Honest verdict: the train winner, judged on unseen test data.
    bf, bs, btr, bte = rows[0]
    best_test = max(rows, key=lambda x: sharpe_key(x[3]))  # only knowable in hindsight

    print(f"\n=== train 冠军 SMA({bf},{bs}) ===")
    print(f"样本内 train: Sharpe {btr['sharpe']:+.2f}  "
          f"CAGR {btr['cagr']:+.1%}  MaxDD {btr['mdd']:.1%}")
    print(f"样本外 test : Sharpe {bte['sharpe']:+.2f}  "
          f"CAGR {bte['cagr']:+.1%}  MaxDD {bte['mdd']:.1%}   <-- 诚实的未来估计")
    print(f"过拟合税 (train−test Sharpe 落差): {btr['sharpe'] - bte['sharpe']:+.2f}")

    # The honesty gut-check: a positive test Sharpe means nothing vs the benchmark.
    verdict = "跑赢" if bte["sharpe"] > bh_te["sharpe"] else "跑输"
    print(f"\n对照及格线 买入持有(test): Sharpe {bh_te['sharpe']:+.2f}  CAGR {bh_te['cagr']:+.1%}")
    print(f"结论:train 冠军样本外 {verdict} 躺平 "
          f"(Sharpe {bte['sharpe']:+.2f} vs {bh_te['sharpe']:+.2f}  |  "
          f"CAGR {bte['cagr']:+.1%} vs {bh_te['cagr']:+.1%})")
    print(f"\n事后诸葛:test 上真正最优其实是 SMA({best_test[0]},{best_test[1]}) "
          f"(test Sharpe {best_test[3]['sharpe']:+.2f}) —— 你在 train 上根本选不到它。")
