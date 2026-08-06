"""L8 practice: a minimal paper-trading loop (工位 4 执行).

Backtest was OFFLINE and VECTORIZED -- whole-column math over frozen history.
Live is an ONLINE EVENT LOOP: poll the latest CLOSED candle, compute the signal
on data-so-far, compare desired vs current position, and simulate an order only
when it changes. No real money -- but every wire is the same as live trading.

This realizes L1's "one signal, two runtimes" on the LIVE side. The strategy
(SMA crossover) has no proven edge -- here it's just a vehicle for the plumbing.
"""

import argparse
import json
import os
import time

import pandas as pd

from strategy import fetch_ohlcv

SYMBOL = "BTC/USDT"
FAST, SLOW = 10, 30
FEE = 0.001
START_CASH = 10_000.0


def state_path(tf):
    """Namespace the ledger by (symbol, timeframe): switching --tf must NOT
    mix a 4h ledger with 1d bars -- that's what caused the backwards-bar sell."""
    key = SYMBOL.replace("/", "")
    return os.path.join(os.path.dirname(__file__), f"paper_state_{key}_{tf}.json")


def load_state(path):
    """Live trading is a loop WITH MEMORY: reload the portfolio each tick."""
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {"cash": START_CASH, "coin": 0.0, "position": 0,
            "entry": 0.0, "last_ts": None, "trades": []}


def save_state(state, path):
    with open(path, "w") as f:
        json.dump(state, f, indent=2, default=str)


def tick(state, tf="1d"):
    """One decision cycle: poll -> signal -> compare -> maybe trade -> persist."""
    # Discipline 1: the last candle is still FORMING -> drop it, use closed bars only.
    df = fetch_ohlcv(symbol=SYMBOL, timeframe=tf, limit=SLOW + 40).iloc[:-1]
    bar_ts_obj = df.index[-1]
    bar_ts = str(bar_ts_obj)
    price = float(df["close"].iloc[-1])

    # Live signal = crossover on the LAST CLOSED bar -- the live form of shift(1).
    fast = df["close"].rolling(FAST).mean().iloc[-1]
    slow = df["close"].rolling(SLOW).mean().iloc[-1]
    desired = int(fast > slow)

    # Discipline 2: act only on a STRICTLY NEWER closed bar. Comparing ordering
    # (not ==) blocks both the repeat tick AND a backwards/stale timestamp --
    # e.g. a stale ledger or a rewound feed must never make us "trade the past".
    last_obj = pd.Timestamp(state["last_ts"]) if state["last_ts"] else None
    if last_obj is not None and bar_ts_obj <= last_obj:
        equity = state["cash"] + state["coin"] * price
        print(f"[{bar_ts}] 无更新收盘K线,持仓不变 | position={state['position']} "
              f"equity=${equity:,.2f}")
        return state

    # Discipline 3: idempotent -- trade only if the target differs from current.
    if desired != state["position"]:
        if desired == 1:  # buy: all cash -> coin, pay the fee
            state["coin"] = state["cash"] * (1 - FEE) / price
            state["cash"] = 0.0
            state["entry"] = price
            action = f"BUY  {state['coin']:.6f} BTC @ ${price:,.2f}"
        else:             # sell: all coin -> cash, pay the fee
            state["cash"] = state["coin"] * price * (1 - FEE)
            state["coin"] = 0.0
            action = f"SELL @ ${price:,.2f}"
        state["position"] = desired
        state["trades"].append({"ts": bar_ts, "action": action})
        print(f"[{bar_ts}] 成交: {action}")
    else:
        print(f"[{bar_ts}] 新K线,目标仓位={desired} 与当前一致,不动作")

    state["last_ts"] = bar_ts
    equity = state["cash"] + state["coin"] * price  # mark-to-market
    print(f"          现金=${state['cash']:,.2f}  持币={state['coin']:.6f} BTC  "
          f"标记市值=${equity:,.2f}")
    return state


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="minimal BTC paper-trading loop")
    ap.add_argument("--loop", type=int, metavar="SEC", help="repeat every SEC seconds")
    ap.add_argument("--reset", action="store_true", help="wipe portfolio, start fresh")
    ap.add_argument("--tf", default="1d", help="timeframe: 1d (default) / 4h / 1h")
    args = ap.parse_args()

    state_file = state_path(args.tf)
    if args.reset and os.path.exists(state_file):
        os.remove(state_file)
        print("状态已重置。")

    state = load_state(state_file)
    print(f"=== paper trading  SMA({FAST},{SLOW}) {SYMBOL} {args.tf}  "
          f"起始资金 ${START_CASH:,.0f} ===")

    if args.loop:
        print(f"每 {args.loop}s 一次 tick(Ctrl-C 停止)\n")
        try:
            while True:
                state = tick(state, tf=args.tf)
                save_state(state, state_file)
                time.sleep(args.loop)
        except KeyboardInterrupt:
            print("\n已停止,状态已保存。")
    else:
        state = tick(state, tf=args.tf)
        save_state(state, state_file)
