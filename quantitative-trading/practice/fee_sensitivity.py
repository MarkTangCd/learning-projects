"""L21 follow-up: re-price the L16 two-sided machine at the MEASURED fee.

L4 invented `FEE = 0.001` (10 bp per side) as a stand-in for "fees + slippage".
L20/L21 measured the fee half on a live venue: 4.00 bp per side taker
(0.0231 USDT on 57.69 notional, reproduced twice). So the invented number was
2.5x harsher than the real fee.

This does NOT re-tune anything. The machine is frozen (same GGRID, same folds,
same walk-forward). The ONLY thing that moves is the price of a trade — we sweep
it and look at the SHAPE of the decay, because a single re-run at one new number
is exactly how you fool yourself.

What the shape tells you:
  - flat-ish     -> the edge does not live or die on cost assumptions
  - steep        -> the edge is a cost artefact; 6 bp decides your conclusion
  - sign flip    -> whatever you concluded in L16 was a statement about FEE

Run:  python fee_sensitivity.py            # BTC ETH SOL, fee ladder
      python fee_sensitivity.py BTC/USDT   # one asset
"""

import sys

from backtest import backtest  # noqa: F401  (imported for parity with L16 run)
from oos import score
from walkforward import build_folds
from walkforward_shorts import stitch, SYMBOLS
from strategy import fetch_ohlcv

# bp per SIDE. 4 = measured on the perp venue (L20/L21). 10 = what L4 invented.
FEE_LADDER_BP = (0, 2, 4, 6, 10, 20)
MEASURED_BP = 4
INVENTED_BP = 10
FUNDING = 0.0001          # ~1 bp/day carry, same as the L16 default


def sweep(symbol):
    price = fetch_ohlcv(symbol=symbol, since="2021-01-01", limit=1000)
    folds = list(build_folds(len(price)))
    row = {}
    for bp in FEE_LADDER_BP:
        oos, _ = stitch(price, True, FUNDING, folds, fee=bp / 1e4)
        row[bp] = score(oos)
    return row


if __name__ == "__main__":
    symbols = (sys.argv[1],) if len(sys.argv) > 1 else SYMBOLS
    print("双边 regime 组合:同一台冻结的机器,只改「一笔交易的价格」\n")
    print(f"实测 {MEASURED_BP} bp/边(perp 实盘撮合)  vs  L4 拍脑袋 {INVENTED_BP} bp/边\n")

    head = "".join(f"{bp:>9}bp" for bp in FEE_LADDER_BP)
    print(f"{'资产':<10}{'指标':<8}{head}")
    for sym in symbols:
        row = sweep(sym)
        for metric, fmt in (("sharpe", "{:>11.2f}"), ("cagr", "{:>11.1%}"), ("mdd", "{:>11.1%}")):
            cells = "".join(fmt.format(row[bp][metric]) for bp in FEE_LADDER_BP)
            label = sym if metric == "sharpe" else ""
            print(f"{label:<10}{metric:<8}{cells}")
        d = row[MEASURED_BP]["sharpe"] - row[INVENTED_BP]["sharpe"]
        print(f"{'':<10}--> 实测费率下 Sharpe {row[MEASURED_BP]['sharpe']:+.2f} "
              f"(拍脑袋费率下 {row[INVENTED_BP]['sharpe']:+.2f},差 {d:+.2f})\n")

    print("读法(判据在看数之前就定好了):")
    print("  夏普随费率【陡降】 = edge 是成本假设的产物,脆弱;")
    print("  夏普随费率【平缓】 = 成本不是主要矛盾,信号本身说了算。")
    print(f"  注意:实测的 {MEASURED_BP} bp 只是【手续费】那一半。滑点那一半仍未测量")
    print("  (测试网盘口是合成的,量不出真实滑点)—— 真实成本 >= 这个数。")
