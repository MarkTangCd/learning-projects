"""L2 practice — Strategy hooks and custom Indicators.

Four commands, each answering one question:

    python l02_strategy_indicator.py hooks      # WHEN does each Strategy hook fire?
    python l02_strategy_indicator.py minperiod  # an UNUSED indicator changes your P&L
    python l02_strategy_indicator.py er         # write your own Indicator, cross-check it
    python l02_strategy_indicator.py run        # gate the SMA cross with your own ER

Reuses the data cache from l01 (practice/data/*.csv).
"""

import sys

import backtrader as bt
import numpy as np
import pandas as pd

from l01_first_run import load


# =============================================================== experiment 1
# The Strategy lifecycle. Five hooks, and the two you have never heard of
# (prenext / nextstart) are exactly where minperiod hides.
class HookProbe(bt.Strategy):
    params = dict(slow=30)

    def __init__(self):
        # Runs ONCE, before any bar exists. Nothing has a value yet.
        # You DECLARE line objects here; you do not compute anything.
        self.sma = bt.ind.SMA(self.data.close, period=self.p.slow)
        print(f"  __init__     声明完毕。self.sma 现在是个 line 对象,还没有值。"
              f"minperiod={self.sma._minperiod}")

    def start(self):
        # Runs once, after data is attached, before the first bar is delivered.
        print(f"  start()      数据已挂载。策略 minperiod={self._minperiod}")

    def prenext(self):
        # Called for every bar where minperiod is NOT yet satisfied.
        # Default implementation: does nothing. Your next() is NOT called.
        if len(self) in (1, 2, self.p.slow - 1):
            print(f"  prenext()    bar#{len(self)}  指标还没算够 —— next() 不会被调用")

    def nextstart(self):
        # Called EXACTLY ONCE, on the first bar where minperiod is satisfied.
        # Default implementation: calls next(). Override it for one-shot setup.
        print(f"  nextstart()  bar#{len(self)}  date={self.data.datetime.date(0)}  "
              f"sma={self.sma[0]:.2f}  <- 第一根可用的 bar")
        self.next()

    def next(self):
        if len(self) in (self.p.slow, self.p.slow + 1):
            print(f"  next()       bar#{len(self)}  sma[0]={self.sma[0]:.2f}  "
                  f"sma[-1]={self.sma[-1]:.2f}")

    def stop(self):
        # Runs once at the end. Where you stash results for the caller.
        print(f"  stop()       跑完 {len(self)} 根 bar,前 {self._minperiod - 1} 根被 prenext 吃掉了")


def cmd_hooks():
    df = load("BTC").head(60)
    c = bt.Cerebro()
    c.adddata(bt.feeds.PandasData(dataname=df))
    c.addstrategy(HookProbe)
    print("60 根 bar,一个 SMA(30)。看五个钩子分别在什么时候响:\n")
    c.run()
    print("\n问自己:你手搓栈里,前 29 根 bar 是谁在负责扔掉的?你写过这段代码吗?")


# =============================================================== experiment 2
# minperiod is CONTAGIOUS. The strategy's minperiod = max over ALL declared
# indicators — including ones you declared and never read.
class Contagion(bt.Strategy):
    params = dict(fast=10, slow=30, extra=0)

    def __init__(self):
        f = bt.ind.SMA(self.data.close, period=self.p.fast)
        s = bt.ind.SMA(self.data.close, period=self.p.slow)
        self.cross = bt.ind.CrossOver(f, s)
        if self.p.extra:
            # Declared. Never read. Not plotted. Pure dead code.
            self.unused = bt.ind.SMA(self.data.close, period=self.p.extra)
        self.first = None
        self.n = 0

    def next(self):
        if self.first is None:
            self.first = self.data.datetime.date(0)
        if not self.position and self.cross[0] > 0:
            self.buy()
            self.n += 1
        elif self.position and self.cross[0] < 0:
            self.close()
            self.n += 1


def run_contagion(df, extra):
    c = bt.Cerebro()
    c.adddata(bt.feeds.PandasData(dataname=df))
    c.addstrategy(Contagion, extra=extra)
    c.addsizer(bt.sizers.PercentSizer, percents=95)
    c.broker.setcash(10_000.0)
    c.broker.setcommission(commission=0.0004)
    s = c.run()[0]
    return s, c.broker.getvalue()


def cmd_minperiod():
    df = load("BTC")
    print("同一份数据、同一套买卖逻辑。唯一的区别:多声明一个从不使用的 SMA(200)。\n")
    print(f"  {'extra':<8}{'首次 next':<14}{'下单':<7}{'期末资金':>12}{'收益':>9}")
    for extra in (0, 50, 200):
        s, end = run_contagion(df, extra)
        label = "无" if not extra else f"SMA({extra})"
        print(f"  {label:<8}{str(s.first):<14}{s.n:<7}{end:>12,.0f}{end/10_000 - 1:>9.1%}")
    print("\n  声明了就要算,算了就要等。minperiod 会往上传染到整个策略,")
    print("  而策略 minperiod 决定了回测的真实起点 —— 起点变了,一切都变了。")
    print("  没有任何警告。删掉一行死代码,你的回测结论就翻转。")


# =============================================================== experiment 3
# Write your own Indicator. Two styles, then cross-check against pandas.
class EfficiencyRatio(bt.Indicator):
    """Kaufman Efficiency Ratio, declarative style (line arithmetic in __init__).

    ER = |net change over window| / total path length walked
        -> 1 : clean one-way trend
        -> 0 : chop
    Ported from the quant course's `strategy.py:efficiency_ratio`.
    """

    lines = ("er",)                      # names the output line(s)
    params = dict(period=20)
    plotinfo = dict(subplot=True)        # draw in its own pane, not on price

    def __init__(self):
        c = self.data
        net = abs(c - c(-self.p.period))                 # c(-n) = the line, delayed n bars
        total = bt.ind.SumN(abs(c - c(-1)), period=self.p.period)
        self.lines.er = net / total
        # minperiod is inferred automatically from the operands. Print it to see.
        super().__init__()


class EfficiencyRatioLoop(bt.Indicator):
    """Same thing, imperative style — you fill the line yourself, bar by bar."""

    lines = ("er",)
    params = dict(period=20)

    def __init__(self):
        # You must declare the warm-up yourself in this style.
        self.addminperiod(self.p.period + 1)

    def next(self):
        n = self.p.period
        c = self.data
        net = abs(c[0] - c[-n])
        total = sum(abs(c[-i] - c[-i - 1]) for i in range(n))
        self.lines.er[0] = net / total if total else 0.0


def pandas_er(close, window=20):
    """The reference implementation from the quant course — the thing to match."""
    net = (close - close.shift(window)).abs()
    total = close.diff().abs().rolling(window).sum()
    return net / total


class ErDump(bt.Strategy):
    params = dict(period=20)

    def __init__(self):
        self.a = EfficiencyRatio(self.data.close, period=self.p.period)
        self.b = EfficiencyRatioLoop(self.data.close, period=self.p.period)
        self.rows = []

    def next(self):
        self.rows.append((self.data.datetime.date(0), self.a[0], self.b[0]))


def cmd_er():
    df = load("BTC").head(200)
    c = bt.Cerebro()
    c.adddata(bt.feeds.PandasData(dataname=df))
    c.addstrategy(ErDump)
    s = c.run()[0]

    got = pd.DataFrame(s.rows, columns=["date", "declarative", "loop"]).set_index("date")
    ref = pandas_er(df["close"], 20)
    ref.index = ref.index.date
    got["pandas"] = ref.reindex(got.index)

    print(f"三种写法的 ER,前 5 行与后 3 行(BTC 前 200 根):\n")
    print(got.head(5).to_string(float_format=lambda v: f"{v:.6f}"))
    print("   ...")
    print(got.tail(3).to_string(float_format=lambda v: f"{v:.6f}"))

    d1 = (got["declarative"] - got["pandas"]).abs().max()
    d2 = (got["loop"] - got["pandas"]).abs().max()
    print(f"\n  声明式 vs pandas 最大偏差   {d1:.2e}")
    print(f"  循环式 vs pandas 最大偏差   {d2:.2e}")
    print(f"  第一个有值的 bar: {got.index[0]}  (pandas 那边前 20 个是 NaN,backtrader 这边直接不给你)")
    print("\n  对拍通过 = 你可以把手搓栈的任何指标搬进来,而且能验证它搬对了。")


# =============================================================== experiment 4
# Use the custom indicator for real: gate the SMA cross by regime.
class GatedCross(bt.Strategy):
    params = dict(fast=10, slow=30, er_period=20, er_thresh=0.0)

    def __init__(self):
        f = bt.ind.SMA(self.data.close, period=self.p.fast)
        s = bt.ind.SMA(self.data.close, period=self.p.slow)
        self.cross = bt.ind.CrossOver(f, s)
        self.er = EfficiencyRatio(self.data.close, period=self.p.er_period)
        self.n = 0

    def next(self):
        trending = self.er[0] > self.p.er_thresh
        if not self.position and self.cross[0] > 0 and trending:
            self.buy()
            self.n += 1
        elif self.position and self.cross[0] < 0:
            self.close()
            self.n += 1


def cmd_run():
    for name, bpy in (("BTC", 365), ("SPY", 252)):
        df = load(name)
        print(f"\n=== {name} ===")
        print(f"  {'er_thresh':<12}{'下单':<7}{'期末资金':>12}{'收益':>9}{'MaxDD':>9}{'Sharpe':>9}")
        for th in (0.0, 0.2, 0.3, 0.4):
            c = bt.Cerebro()
            c.adddata(bt.feeds.PandasData(dataname=df))
            c.addstrategy(GatedCross, er_thresh=th)
            c.addsizer(bt.sizers.PercentSizer, percents=95)
            c.broker.setcash(10_000.0)
            c.broker.setcommission(commission=0.0004)
            c.addanalyzer(bt.analyzers.DrawDown, _name="dd")
            c.addanalyzer(bt.analyzers.TimeReturn, _name="ret",
                          timeframe=bt.TimeFrame.Days)
            s = c.run()[0]
            end = c.broker.getvalue()
            r = pd.Series(s.analyzers.ret.get_analysis())
            sd = r.std(ddof=0)
            # Never trade -> zero variance -> Sharpe is undefined, not zero.
            sharpe = r.mean() / sd * np.sqrt(bpy) if sd > 0 else float("nan")
            label = "0.0 (off)" if th == 0.0 else f"{th}"
            print(f"  {label:<12}{s.n:<7}{end:>12,.0f}{end/10_000 - 1:>9.1%}"
                  f"{s.analyzers.dd.get_analysis()['max']['drawdown']:>8.1f}%{sharpe:>9.2f}")
    print("\n  注意:er_thresh 是一个新旋钮。四个值里最好的那个,是发现还是过拟合?")
    print("  隔壁 L22 的答案:这是选择方差。别看这张表最右边那一列就下结论。")


if __name__ == "__main__":
    cmds = {"hooks": cmd_hooks, "minperiod": cmd_minperiod,
            "er": cmd_er, "run": cmd_run}
    arg = sys.argv[1] if len(sys.argv) > 1 else "hooks"
    if arg not in cmds:
        raise SystemExit(f"用法: python {sys.argv[0]} [{'|'.join(cmds)}]")
    cmds[arg]()
