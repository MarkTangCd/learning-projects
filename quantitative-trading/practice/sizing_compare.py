"""L18 practice: does risk-based sizing beat a full-size bet?

Take the exact two-sided BTC regime combo from L16 and run it two ways over the
same span: (a) RAW full-size position in {-1,0,+1}; (b) VOL-TARGETED position.
Read all three columns (L15 discipline) plus the realized vol each one actually
delivered and how much it traded (turnover has a cost).

target_vol is a RISK CHOICE, not a fitted parameter — we do not optimize it.

Run:  python sizing_compare.py
      python sizing_compare.py --target 0.10   # more conservative
      python sizing_compare.py --target 0.40   # more aggressive
"""

import argparse

from backtest import backtest
from metrics import sharpe
from oos import score
from strategy import fetch_ohlcv, regime_switch_signal
from sizing import vol_target_position, realized_vol, PERIODS_PER_YEAR


def line(tag, net_ret, extra=""):
    s = score(net_ret)
    print(f"{tag:<16}: Sharpe {s['sharpe']:+.2f}  CAGR {s['cagr']:+.1%}  "
          f"MaxDD {s['mdd']:.1%}  {extra}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", type=float, default=0.20, help="annualized vol target")
    ap.add_argument("--maxlev", type=float, default=3.0, help="leverage cap")
    args = ap.parse_args()

    price = fetch_ohlcv(symbol="BTC/USDT", since="2021-01-01", limit=1000)

    # Same signal both ways: two-sided regime combo, family defaults.
    raw = regime_switch_signal(price, er_window=20, er_thresh=0.30, long_short=True)
    sized = vol_target_position(raw.copy(), target_vol=args.target, max_leverage=args.maxlev)

    raw_bt = backtest(raw, funding=0.0001)
    sized_bt = backtest(sized, funding=0.0001)

    ann = PERIODS_PER_YEAR ** 0.5
    raw_vol = raw_bt["strat_ret_net"].std() * ann
    sized_vol = sized_bt["strat_ret_net"].std() * ann
    raw_turn = raw_bt["trade"].sum()
    sized_turn = sized_bt["trade"].sum()

    print(f"BTC 双边 regime 组合  |  vol 目标 {args.target:.0%}/年  杠杆上限 {args.maxlev:.0f}x  "
          f"|  {price.index[0].date()} -> {price.index[-1].date()}\n")
    line("① 满仓(原始)", raw_bt["strat_ret_net"],
         f"实际年化波动 {raw_vol:.0%}  换手 {raw_turn:.0f}")
    line("② 波动率定量", sized_bt["strat_ret_net"],
         f"实际年化波动 {sized_vol:.0%}  换手 {sized_turn:.0f}")
    print(f"\n读法:vol 定量把实际波动拉向目标 {args.target:.0%};看它是否在"
          f"压平波动/回撤的同时,把风险调整后收益(Sharpe)做得不更差甚至更好。")
    print("换手两股力:连续调仓 +换手,仓位常<1 又 -换手;净向哪边看上面的数,别假设。")
