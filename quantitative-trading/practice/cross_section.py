"""L27: the cross-section — stop asking WHEN, start asking WHO.

Every strategy from L3 to L26 was a TIME-SERIES bet: one symbol, one column of
prices, and the question "is now a good time to be long?". L25/L26 killed that
bet on US stocks: the machine was short during a decade-long bull, and even the
long-flat version lost to buy-and-hold. The climate ate it.

A CROSS-SECTIONAL strategy asks a different question at each instant:
"of everything in front of me RIGHT NOW, who is strongest, who is weakest?"
Long the strong basket, short the weak basket, both legs the same size. The
market's common move — the climate — appears in BOTH legs and CANCELS in the
difference. That is the structural claim this lesson measures.

We measure ONE thing here: exposure, not profit.
  - Survivorship: the universe below is today's DJIA. Companies that fell out
    (or died) are missing, so any RETURN number computed here is contaminated
    upward (L23 `dead`). Beta and correlation are structural — they hold for
    whatever basket you feed in — so those are the only numbers we trust today.
  - No costs are charged. A daily-rebalanced 30-name long/short has real
    turnover. Costs matter the moment we make a profit claim; today we don't.

Run:  python cross_section.py panel     # the shape change: series -> panel
      python cross_section.py rank      # one instant, ranked across names
      python cross_section.py hedge     # the win: beta of each leg vs market
"""

import sys

import numpy as np
import pandas as pd
import yfinance as yf

# Today's DJIA. SURVIVORSHIP-BIASED BY CONSTRUCTION — see module docstring.
UNIVERSE = ("MMM", "AXP", "AMGN", "AMZN", "AAPL", "BA", "CAT", "CVX", "CSCO",
            "KO", "DIS", "GS", "HD", "HON", "IBM", "JNJ", "JPM", "MCD", "MRK",
            "MSFT", "NKE", "NVDA", "PG", "CRM", "SHW", "TRV", "UNH", "VZ",
            "V", "WMT")

SINCE = "2015-01-01"
LOOKBACK = 252       # 12 months of formation window
SKIP = 21            # skip the most recent month (the classic 12-1 momentum)
BASKET = 6           # names per leg: top 6 long, bottom 6 short
TRADING_DAYS = 252

BANNER = "\n" + "=" * 74


def fetch_panel(symbols=UNIVERSE, since=SINCE):
    """Batch form of L23's `fetch_stock`: same auto_adjust=True total-return
    prices, but many names at once, returned WIDE — rows are dates, columns are
    symbols. This transpose IS the lesson: time-series code walks DOWN a column,
    cross-sectional code walks ACROSS a row."""
    raw = yf.download(list(symbols), start=since, auto_adjust=True,
                      progress=False)
    close = raw["Close"].copy()
    close.index = pd.to_datetime(close.index).tz_localize(None)
    return close[list(symbols)].dropna(how="all")


def momentum(close, lookback=LOOKBACK, skip=SKIP):
    """12-1 momentum, computed per column but READ per row.

    The skip month is not decoration: the most recent ~21 days carry short-term
    REVERSAL, which points the opposite way and dilutes the signal. Both facts
    come from the same literature (Jegadeesh & Titman 1993)."""
    return close.shift(skip) / close.shift(lookback) - 1.0


def basket_weights(mom, basket=BASKET):
    """Cross-sectional ranking -> dollar-neutral weights, one row at a time.

    rank(axis=1) is the whole idea: rank ACROSS names within a single day. The
    row is re-ranked every day, so a name's weight depends on its PEERS, never
    on its own absolute level. Weights sum to 0 (dollar neutral) and |weights|
    sum to 2 (one unit long, one unit short)."""
    rank = mom.rank(axis=1, ascending=False)
    n = mom.notna().sum(axis=1)
    long_leg = rank.le(basket).astype(float).div(basket)
    short_leg = rank.gt(n - basket, axis=0).astype(float).div(basket)
    return long_leg - short_leg, long_leg, short_leg


def legs(close):
    """Daily returns of: long basket, short basket (as held, i.e. negated),
    the spread, and the equal-weight market. Weights are shift(1)'d — the L3
    discipline, unchanged since the first signal."""
    ret = close.pct_change()
    mom = momentum(close)
    w, w_long, w_short = basket_weights(mom)
    out = pd.DataFrame({
        "long": (w_long.shift(1) * ret).sum(axis=1),
        "short": -(w_short.shift(1) * ret).sum(axis=1),
        "spread": (w.shift(1) * ret).sum(axis=1),
        "mkt": ret.mean(axis=1),
    })
    return out[w.shift(1).abs().sum(axis=1) > 0].dropna()


def _beta(y, x):
    """OLS slope of y on x — 'how many units does y move per unit of market'."""
    return float(np.cov(y, x)[0, 1] / np.var(x, ddof=1))


def cmd_panel():
    """Shape first. Everything else follows from the transpose."""
    print(BANNER)
    print("① 面板:一列变一张表\n")
    close = fetch_panel()
    print(f"  形状: {close.shape[0]} 行(交易日) × {close.shape[1]} 列(标的)")
    print(f"  区间: {close.index[0]:%Y-%m-%d} → {close.index[-1]:%Y-%m-%d}")
    print(f"  缺口: {int(close.isna().sum().sum())} 个空格"
          f"(上市晚/停牌;横截面排序会自动跳过 NaN)\n")
    corner = close.iloc[-3:, :5].round(2)
    print(corner.to_string())
    print("\n  ↓ 竖着看一列 = 时序:AAPL 这三天怎么走的(L3-L26 全部住在这里)")
    print("  → 横着看一行 = 横截面:2026 年某一天,这些公司互相之间谁强谁弱")
    print("  同一张表,两种读法。换的不是数据,是提问的方向。")


def cmd_rank():
    """One instant, sorted. Makes 'relative' concrete."""
    print(BANNER)
    print("② 一个瞬间,横着排一次序\n")
    close = fetch_panel()
    mom = momentum(close)
    day = mom.dropna(how="all").index[-1]
    row = mom.loc[day].dropna().sort_values(ascending=False)
    print(f"  日期 {day:%Y-%m-%d} · 12-1 动量(跳过最近 {SKIP} 天)\n")
    print(f"  {'腿':<6}{'排名':>4}  {'标的':<6}{'形成期涨幅':>10}")
    for i, (sym, v) in enumerate(row.items(), start=1):
        if i <= BASKET:
            print(f"  {'做多':<5}{i:>5}  {sym:<7}{v:>10.1%}")
        elif i == BASKET + 1:
            print(f"  {'—':<5}{'':>5}  {'…中间 ' + str(len(row) - 2 * BASKET) + ' 只不碰…':<20}")
        elif i > len(row) - BASKET:
            print(f"  {'做空':<5}{i:>5}  {sym:<7}{v:>10.1%}")
    print(f"\n  注意排名是相对的:第 1 名不是「涨了」,是「比另外 {len(row)-1} 个都强」。")
    print("  熊市里第 1 名可能是 −30%,照买不误——因为另外 29 个跌得更惨。")


def cmd_hedge():
    """THE WIN: the climate lives in both legs and cancels in the difference."""
    print(BANNER)
    print("③ 气候被对冲掉了吗?——量一量,别猜\n")
    close = fetch_panel()
    df = legs(close)
    print(f"  样本 {df.index[0]:%Y-%m-%d} → {df.index[-1]:%Y-%m-%d},"
          f"{len(df)} 个交易日\n")
    print(f"  {'组合':<14}{'与市场相关':>11}{'对市场beta':>11}{'年化波动':>10}")
    for name, label in [("long", "只做多头篮"), ("short", "只做空头篮"),
                        ("spread", "多空价差")]:
        r = df[name]
        print(f"  {label:<12}{r.corr(df['mkt']):>11.2f}"
              f"{_beta(r, df['mkt']):>11.2f}"
              f"{r.std() * TRADING_DAYS ** 0.5:>10.1%}")
    r = df["mkt"]
    print(f"  {'等权市场':<12}{1.0:>11.2f}{1.0:>11.2f}"
          f"{r.std() * TRADING_DAYS ** 0.5:>10.1%}")

    worst = df.nsmallest(5, "mkt")
    print(f"\n  市场最惨的 5 天,价差组合在干什么:\n")
    print(f"  {'日期':<12}{'市场':>9}{'多头篮':>9}{'空头篮':>9}{'价差':>9}")
    for d, row in worst.iterrows():
        print(f"  {d:%Y-%m-%d}{row['mkt']:>9.1%}{row['long']:>9.1%}"
              f"{row['short']:>9.1%}{row['spread']:>9.1%}")
    print("\n  读法:beta≈0 = 市场整体涨跌不再决定你的盈亏。这不是收益,是**免疫**。")
    print("  L25 杀死的那台机器 beta 在 −1 到 +1 之间来回跳,赌的正是市场方向。")
    print("  ⚠ 本表不含成本、且 universe 是幸存者 —— 所以只读 beta,不读收益。")


COMMANDS = {"panel": cmd_panel, "rank": cmd_rank, "hedge": cmd_hedge}

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "panel"
    if cmd not in COMMANDS:
        raise SystemExit(f"用法: python cross_section.py [{'|'.join(COMMANDS)}]")
    COMMANDS[cmd]()
