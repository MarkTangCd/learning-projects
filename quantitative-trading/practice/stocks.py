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

from backtest import backtest, backtest_next_open
from metrics import cagr, max_drawdown, sharpe
from sizing import realized_vol
from strategy import sma_crossover_signal, zscore_reversion_signal

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


def cmd_size():
    """Challenge (4): the SAME wrong constant, a second victim.

    metrics uses PERIODS_PER_YEAR in the NUMERATOR (sharpe = mean/std * sqrt(P)),
    so 365 on a 252-day calendar INFLATES the score you read.
    sizing uses it inside the DENOMINATOR (weight = target / (std * sqrt(P))),
    so the same 365 SHRINKS the position you actually take. Same constant,
    opposite direction: the report looks better while the machine bets smaller.

    Predicted, before running anything:
        rv     ratio = sqrt(365/252) = 1.204   -> vol over-stated by +20.4%
        weight ratio = 1/1.204      = 0.830    -> position under-sized by -17.0%
        realized portfolio vol = 20% * 0.830   = 16.6%, not the 20% you dialled in
    The measured shrink comes out a touch SMALLER than 17%: whenever
    target/rv exceeds max_leverage both versions are clipped to the same cap,
    and inside the clip the bug is invisible.
    """
    target, window, cap = 0.20, 20, 3.0
    print("④ 同一个常数的第二处伤害:vol targeting 的仓位\n")
    print(f"  target_vol={target:.0%}  window={window}  max_leverage={cap}\n")
    print(f"  {'标的':<7}{'rv@365':>9}{'rv@252':>9}{'rv 虚高':>10}"
          f"{'w@365':>9}{'w@252':>9}{'仓位缩水':>10}{'被 cap 的 bar':>13}")
    for sym in DEMO:
        price = fetch_stock(sym)
        ret = price["close"].pct_change()
        rv365 = realized_vol(ret, window, CRYPTO_DAYS)
        rv252 = realized_vol(ret, window, TRADING_DAYS)
        w365 = (target / rv365).clip(upper=cap)
        w252 = (target / rv252).clip(upper=cap)
        both = pd.concat([w365, w252], axis=1).dropna()
        capped = (both.iloc[:, 1] >= cap).mean()   # cap binding on the HONEST one
        print(f"  {sym:<7}{rv365.mean():>9.1%}{rv252.mean():>9.1%}"
              f"{rv365.mean() / rv252.mean() - 1:>10.1%}"
              f"{w365.mean():>9.2f}{w252.mean():>9.2f}"
              f"{both.iloc[:, 0].mean() / both.iloc[:, 1].mean() - 1:>10.1%}"
              f"{capped:>13.1%}")
    print(f"\n  推导链:rv = std * sqrt(P) —— P 用大了,rv 就大了 sqrt(365/252)"
          f" = {np.sqrt(CRYPTO_DAYS / TRADING_DAYS):.3f}")
    print(f"        weight = target / rv —— rv 在分母,所以仓位反而小了"
          f" 1/{np.sqrt(CRYPTO_DAYS / TRADING_DAYS):.3f}"
          f" = {np.sqrt(TRADING_DAYS / CRYPTO_DAYS):.3f}"
          f"({np.sqrt(TRADING_DAYS / CRYPTO_DAYS) - 1:.1%})")
    print("  夏普那处是【读数虚高】—— 你以为自己更好;这一处是【行为变小】—— 你真的下注更少。")
    print("  后果不是「保守一点没关系」:你把风险刻度盘拧到 20%,实际跑出来的是 16.6%。"
          "\n  那个刻度盘从此不再表示它写着的意思 —— 校准坏了,方向反而是次要的。")


def cmd_calendar():
    """The FIX: one code path, both markets, no constant to remember.

    metrics/sizing no longer default to 365 — they infer the calendar from the
    series' own DatetimeIndex and snap it to a known one (trading_calendar.py).
    Crypto is unchanged (365.2 snaps to the same 365 it always used); stocks are
    now scored on 252 without anyone passing an argument.
    """
    from strategy import fetch_ohlcv
    from trading_calendar import describe

    print("修好之后:同一条代码路径,两个市场,没有要记的常数\n")
    frames = [("BTC/USDT 1d", fetch_ohlcv(symbol="BTC/USDT", since="2021-01-01", limit=1000))]
    frames += [(f"{s} 1d", fetch_stock(s)) for s in DEMO]

    print(f"  {'数据':<14}{'日历推断':<34}{'Sharpe(自动)':>13}{'旧代码(365)':>13}")
    for label, price in frames:
        df = backtest(sma_crossover_signal(price, fast=20, slow=60))
        r = df["strat_ret_net"]
        print(f"  {label:<14}{describe(price.index):<34}"
              f"{sharpe(r):>13.2f}{sharpe(r, CRYPTO_DAYS):>13.2f}")
    print("\n  crypto 两列相同 —— 推断值 365.2 吸附回 365,L5-L22 的所有结论一个字没变。")
    print("  股票两列差 20.4% —— 那正是你一直在读的虚高,现在自动没了。")
    print("\n  三道闸门(trading_calendar.py):")
    print("    · 数 bar,不量间隔 —— 量间隔会给股票也算出 365")
    print("    · 吸附到已知日历 —— 每个 walk-forward 折拿到同一个除数,折间才可比")
    print("    · 对不上就抛 —— 数据有洞会把估计悄悄稀释,那是同一类静默错误")
    print("  跑 `python trading_calendar.py` 看这三道闸门各自的自检。")


FILL_FEE = 0.0005           # 5 bp/side stand-in for US equity spread + slippage
PANEL = ("SPY", "AAPL", "KO", "MSFT", "XOM")
STRATS = (("SMA(20,60)", lambda p: sma_crossover_signal(p, 20, 60)),
          ("SMA(5,20)", lambda p: sma_crossover_signal(p, 5, 20)),
          ("SMA(3,10)", lambda p: sma_crossover_signal(p, 3, 10)),
          ("zscore(20,1.0)", lambda p: zscore_reversion_signal(p, 20, 1.0)))


def gap_slippage(price, sig):
    """Per-trade cost of moving the fill from close[t] to open[t+1].

    Positive = the honest fill is WORSE. Buying into a gap up costs you; selling
    into a gap down costs you. Direction matters, so sign the gap by the trade.
    """
    change = sig["signal"].diff().fillna(0)
    gap = price["open"].shift(-1) / price["close"] - 1     # close[t] -> open[t+1]
    return (np.sign(change) * gap)[change != 0].dropna()


def cmd_fill():
    """L24: replace the fill assumption you cannot execute, then MEASURE it.

    shift(1) on close-to-close says 'compute at the close, fill at that close'.
    On a stock the exchange is shut when the signal exists. The honest version
    fills at the NEXT OPEN — and needs shift(2), not shift(1) (backtest.py).
    """
    print("① 换掉成交假设:收盘成交 -> 次日开盘成交\n")
    print(f"  SMA(20,60)  fee={FILL_FEE:.2%}/边")
    print(f"  {'标的':<7}{'夏普(收盘)':>12}{'夏普(次日开盘)':>15}{'差':>8}"
          f"{'CAGR(收盘)':>12}{'CAGR(开盘)':>12}{'笔数':>7}")
    for sym in DEMO:
        price = fetch_stock(sym)
        sig = sma_crossover_signal(price, fast=20, slow=60)
        a = backtest(sig, fee=FILL_FEE)
        b = backtest_next_open(sig, fee=FILL_FEE)
        print(f"  {sym:<7}{sharpe(a['strat_ret_net']):>12.2f}"
              f"{sharpe(b['strat_ret_net']):>15.2f}"
              f"{sharpe(b['strat_ret_net']) - sharpe(a['strat_ret_net']):>8.2f}"
              f"{cagr(a['equity_net']):>12.1%}{cagr(b['equity_net']):>12.1%}"
              f"{int(b['trade'].sum()):>7}")
    print("\n  和直觉相反:几乎没损失。L23 量到 SPY 62%、KO 92% 的收益在隔夜段,"
          "\n  但那衡量的是【持有】—— 持有时你照样吃到跳空。跳空只在【换仓那天】"
          "\n  才影响你,而这个策略 11 年只换 47 次。")

    print("\n\n② 那到底什么决定损失?一条可检验的公式\n")
    print("  年化损失 ≈ 换手/年 × 每笔跳空成本\n")
    print(f"  {'标的':<6}{'策略':<16}{'换手/年':>8}{'每笔成本':>10}"
          f"{'公式预测':>10}{'实测':>9}{'误差':>8}")
    cells = []
    for sym in PANEL:
        price = fetch_stock(sym)
        years = len(price) / TRADING_DAYS
        for name, make in STRATS:
            sig = make(price)
            slip = gap_slippage(price, sig)
            turnover = len(slip) / years
            predicted = -turnover * slip.mean()
            actual = (cagr(backtest_next_open(sig, fee=FILL_FEE)["equity_net"])
                      - cagr(backtest(sig, fee=FILL_FEE)["equity_net"]))
            cells.append(actual)
            print(f"  {sym:<6}{name:<16}{turnover:>8.1f}{slip.mean():>10.3%}"
                  f"{predicted:>10.2%}{actual:>9.2%}{actual - predicted:>8.2%}")

    cells = np.array(cells)
    print(f"\n  20 个格子全中,误差几乎都 <0.2% —— 换手是唯一的放大器。")
    print(f"\n\n③ 但看清楚那一列的【符号】\n")
    print(f"  变差的格子 {int((cells < 0).sum())} 个,变好的 {int((cells >= 0).sum())} 个"
          f" —— 掷硬币。")
    print(f"  面板均值 {cells.mean():+.2%}/年(≈0),但单格从 {cells.min():+.1%}"
          f" 到 {cells.max():+.1%}。")
    print("  跳空对你的信号来说是【无偏噪声】,不是系统性抽水:它不改变期望,只放大方差。")
    print("\n  所以换掉这个假设,不是为了省下一笔可预测的成本 —— 是因为")
    print("  【你原来那个数里有一部分是运气,而你分不清是哪部分】。")
    print("  真正危险的是换手高的策略:同一个无偏噪声,抽的次数越多,单次回测偏离期望越远。")


COMMANDS = {"clock": cmd_clock, "overnight": cmd_overnight, "dead": cmd_dead,
            "size": cmd_size, "calendar": cmd_calendar, "fill": cmd_fill}

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "clock"
    if cmd not in COMMANDS:
        raise SystemExit(f"用法: python stocks.py [{'|'.join(COMMANDS)}]")
    COMMANDS[cmd]()
