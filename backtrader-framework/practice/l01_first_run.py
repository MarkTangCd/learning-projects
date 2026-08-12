"""L1 practice — the Cerebro assembly line.

Four commands, each answering one question about backtrader:

    python l01_first_run.py data     # cache BTC + SPY daily bars to CSV
    python l01_first_run.py run      # the 8-component backtest — the main win
    python l01_first_run.py fill     # WHEN and at WHAT PRICE does an order fill?
    python l01_first_run.py sharpe   # what does the free Sharpe analyzer hide?

Everything is cached to CSV on first use, so `run` works offline afterwards.
"""

import os
import sys

import backtrader as bt
import numpy as np
import pandas as pd

# Local proxy (Clash/V2Ray etc.) — ccxt does not read it from the shell env.
PROXY = "http://127.0.0.1:1087"
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


# ---------------------------------------------------------------- data layer
def cache_path(name):
    return os.path.join(DATA_DIR, f"{name}.csv")


def fetch_crypto(symbol="BTC/USDT", timeframe="1d", limit=1000):
    """Same adapter idea as the quantitative-trading course: exchange -> OHLCV frame."""
    import ccxt

    ex = ccxt.binance({"timeout": 30000})
    ex.httpsProxy = PROXY  # ccxt allows exactly ONE proxy setting
    raw = ex.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    df = pd.DataFrame(raw, columns=["ts", "open", "high", "low", "close", "volume"])
    df["ts"] = pd.to_datetime(df["ts"], unit="ms", utc=True)
    # backtrader compares datetimes internally; a tz-naive index avoids the
    # tz-aware vs tz-naive trap already hit in the quant course (L17).
    df.index = df.pop("ts").dt.tz_localize(None)
    return df


def fetch_stock(symbol="SPY", since="2019-01-01"):
    """auto_adjust=True -> split AND dividend adjusted (total return series)."""
    import yfinance as yf

    df = yf.Ticker(symbol).history(start=since, auto_adjust=True)
    if df.empty:
        raise SystemExit(f"没有取到 {symbol} 的数据 —— 代码写错了,或者这个标的已退市。")
    df = df.rename(columns=str.lower)[["open", "high", "low", "close", "volume"]]
    df.index = pd.to_datetime(df.index).tz_localize(None)
    return df


def load(name):
    """Read from cache; fetch and cache on first call."""
    path = cache_path(name)
    if os.path.exists(path):
        return pd.read_csv(path, index_col=0, parse_dates=True)
    os.makedirs(DATA_DIR, exist_ok=True)
    df = fetch_crypto() if name == "BTC" else fetch_stock(name)
    df.to_csv(path)
    print(f"  cached {name}: {len(df)} bars -> {path}")
    return df


def cmd_data():
    for name in ("BTC", "SPY"):
        df = load(name)
        print(f"{name}: {len(df)} bars  {df.index[0].date()} -> {df.index[-1].date()}")


# ------------------------------------------------------- the 8-part assembly
class SmaCross(bt.Strategy):
    """Component #3: the Strategy. Two hooks — __init__ declares, next decides."""

    # Component #3a: params. Read them as self.p.<name> everywhere else.
    params = dict(fast=10, slow=30)

    def __init__(self):
        # Component #4: Indicators. DECLARED here, not computed here.
        # Each is a lazy line object that backtrader evaluates bar by bar.
        fast = bt.ind.SMA(self.data.close, period=self.p.fast)
        slow = bt.ind.SMA(self.data.close, period=self.p.slow)
        # CrossOver emits +1 on an upward cross, -1 on a downward cross, else 0.
        self.cross = bt.ind.CrossOver(fast, slow)
        self.n_orders = 0

    def next(self):
        # Called once per bar, AFTER indicators have a value.
        # [0] is the CURRENT bar; [-1] is the previous one. Opposite of pandas.
        if not self.position and self.cross[0] > 0:
            self.buy()          # sized by the Sizer (component #5)
            self.n_orders += 1
        elif self.position and self.cross[0] < 0:
            self.close()        # flatten whatever we hold
            self.n_orders += 1


def build(df, fast=10, slow=30, bars_per_year=365):
    """Wire all eight components together and return the loaded Cerebro."""
    # 1. Cerebro — the engine that owns everything.
    cerebro = bt.Cerebro()

    # 2. Data Feed — pandas frame in, backtrader lines out.
    cerebro.adddata(bt.feeds.PandasData(dataname=df))

    # 3. Strategy.
    cerebro.addstrategy(SmaCross, fast=fast, slow=slow)

    # 5. Sizer — how big is each order. 95%, leaving room for commission.
    cerebro.addsizer(bt.sizers.PercentSizer, percents=95)

    # 6. Broker — cash and costs. 4bp taker, measured on Binance perp testnet
    #    in the quant course (L20/L21).
    cerebro.broker.setcash(10_000.0)
    cerebro.broker.setcommission(commission=0.0004)

    # 7. Analyzers — the scorecard, for free.
    #    NOTE the explicit timeframe/annualize/factor. The defaults are a trap;
    #    see `sharpe` command below.
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name="sharpe_default")
    cerebro.addanalyzer(
        bt.analyzers.SharpeRatio, _name="sharpe_honest",
        timeframe=bt.TimeFrame.Days, compression=1,
        annualize=True, factor=bars_per_year, riskfreerate=0.0,
    )
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name="dd")
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="trades")
    cerebro.addanalyzer(bt.analyzers.TimeReturn, _name="ret", timeframe=bt.TimeFrame.Days)
    return cerebro


def cmd_run():
    for name, bpy in (("BTC", 365), ("SPY", 252)):
        df = load(name)
        cerebro = build(df, bars_per_year=bpy)
        start = cerebro.broker.getvalue()
        strat = cerebro.run()[0]          # 8. run() — the event loop turns over
        end = cerebro.broker.getvalue()

        an = strat.analyzers
        trades = an.trades.get_analysis()
        closed = trades.get("total", {}).get("closed", 0)
        won = trades.get("won", {}).get("total", 0)
        r = pd.Series(an.ret.get_analysis())

        print(f"\n=== {name} ({len(df)} bars, {bpy} bars/year assumed) ===")
        print(f"  资金        {start:,.0f} -> {end:,.0f}   ({end/start-1:+.1%})")
        print(f"  下单次数    {strat.n_orders}   已平仓交易 {closed} (盈利 {won})")
        print(f"  MaxDD       {an.dd.get_analysis()['max']['drawdown']:.2f}%")
        print(f"  Sharpe 默认  {an.sharpe_default.get_analysis()['sharperatio']}"
              "   <- 框架的默认值,注意看它是什么")
        print(f"  Sharpe 诚实  {an.sharpe_honest.get_analysis()['sharperatio']:.4f}"
              f"   (timeframe=Days, factor={bpy})")
        # Cross-check with a hand-rolled Sharpe on backtrader's OWN daily returns.
        hand = r.mean() / r.std(ddof=0) * np.sqrt(bpy)
        print(f"  Sharpe 手算  {hand:.4f}   (对拍: 用上面那条日收益序列自己算)")


# ------------------------------------------------- experiment: when does it fill?
def cmd_fill():
    """A 6-bar toy series where every price is obviously different, so the
    fill price alone tells you which bar you were filled on."""
    idx = pd.date_range("2023-01-01", periods=6, freq="D")
    df = pd.DataFrame(
        {"open": [10, 20, 30, 40, 50, 60], "high": [11, 21, 31, 41, 51, 61],
         "low": [9, 19, 29, 39, 49, 59], "close": [10.5, 20.5, 30.5, 40.5, 50.5, 60.5],
         "volume": [1e6] * 6}, index=idx)

    class Probe(bt.Strategy):
        def next(self):
            if len(self) == 2:
                print(f"  next()  bar#{len(self)}  date={self.data.datetime.date(0)}  "
                      f"close[0]={self.data.close[0]}  -> 调用 buy()")

                self.buy(size=1)

        def notify_order(self, o):
            if o.status == o.Completed:
                print(f"  成交    bar#{len(self)}  date={self.data.datetime.date(0)}  "
                      f"成交价={o.executed.price}  "
                      f"(这根 bar 的 open={self.data.open[0]}, close={self.data.close[0]})")

    c = bt.Cerebro()
    c.adddata(bt.feeds.PandasData(dataname=df))
    c.addstrategy(Probe)
    c.broker.setcash(1000.0)
    print("默认行为 (cheat_on_open=False):")
    c.run()
    print("\n问自己:成交在哪根 bar?用的哪个价?这跟你手搓栈的假设差在哪?")


# ------------------------------------------- experiment: the free Sharpe lies
def cmd_sharpe():
    df = load("BTC")
    cerebro = build(df, bars_per_year=365)
    # Add one more: annualize=True but WITHOUT overriding factor -> backtrader
    # falls back to its hardcoded table.
    cerebro.addanalyzer(
        bt.analyzers.SharpeRatio, _name="sharpe_252",
        timeframe=bt.TimeFrame.Days, compression=1,
        annualize=True, riskfreerate=0.0,
    )
    strat = cerebro.run()[0]
    an = strat.analyzers
    d = an.sharpe_default.get_analysis()["sharperatio"]
    s252 = an.sharpe_252.get_analysis()["sharperatio"]
    s365 = an.sharpe_honest.get_analysis()["sharperatio"]

    print("同一个策略、同一段 BTC 日线,三种叫法都叫 'Sharpe':\n")
    print(f"  A 默认参数                          {d}")
    print(f"  B annualize=True (不指定 factor)    {s252:.4f}")
    print(f"  C annualize=True, factor=365        {s365:.4f}")
    print(f"\n  B / C 的比值 = {s365/s252:.4f}")
    print(f"  sqrt(365/252) = {np.sqrt(365/252):.4f}")
    print("\n  A 为什么是那个值?去读 backtrader/analyzers/sharpe.py 的 params。")
    print("  B 和 C 差的那个常数,你在隔壁课程 0027 里刚亲手赶走过一次。")


if __name__ == "__main__":
    cmds = {"data": cmd_data, "run": cmd_run, "fill": cmd_fill, "sharpe": cmd_sharpe}
    arg = sys.argv[1] if len(sys.argv) > 1 else "run"
    if arg not in cmds:
        raise SystemExit(f"用法: python {sys.argv[0]} [{'|'.join(cmds)}]")
    cmds[arg]()
