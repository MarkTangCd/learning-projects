"""L17 practice: CLOSE THE LOOP — the validated signal drives the real
execution pipeline (工位 3 研究 → 工位 4 执行,第一次接通).

Until now the two halves lived apart:
  - the SIGNAL (L12-L16) was proven OFFLINE in the walk-forward gauntlet;
  - the EXECUTION pipe (L9-L11) was exercised by hand via command demos.
This runner is the bridge. One decision cycle wires ALL of it together:

  fetch closed bars -> regime_switch_signal -> target position   (BRAIN, L12-L16)
    -> diff vs ledger (idempotent target-compare)                (L8 discipline 3)
    -> guarded_create: RISK GATE + intent_cid idempotency         (L9 + L10)
    -> SEND -> fetch_order READ BACK -> RECONCILE filled vs intent (L11)
    -> write ledger from FILLED, never from intended              (L11 rule)

Honest scope: Binance SPOT testnet cannot SHORT, so this runs LONG/FLAT
(position in {0,+1}). Executing the two-sided signal for real needs the
PERP venue (funding, L16) — a later lesson. The point HERE is the PIPE, not
the edge: prove the plumbing carries a real (funny-money) order end to end.

Setup: same testnet keys as L9 (BINANCE_TESTNET_KEY / _SECRET).
Run:  python strategy_runner.py            # one tick: signal decides
      python strategy_runner.py --target 1 # OVERRIDE target to exercise the pipe
      python strategy_runner.py --reset    # wipe the local ledger
"""

import argparse
import json
import os
import time

from execution import (connect, guarded_create, show_order, SYMBOL,
                       MAX_NOTIONAL_USDT)
from strategy import fetch_ohlcv, regime_switch_signal

TIMEFRAME = "1d"
ORDER_NOTIONAL = MAX_NOTIONAL_USDT * 0.4   # sized well under the risk-gate cap
LEDGER = os.path.join(os.path.dirname(__file__), "runner_ledger.json")


def load_ledger():
    if os.path.exists(LEDGER):
        with open(LEDGER) as f:
            return json.load(f)
    return {"position": 0, "coin": 0.0, "last_bar": None, "trades": []}


def save_ledger(led):
    with open(LEDGER, "w") as f:
        json.dump(led, f, indent=2, default=str)


def bar_cid(side, bar_key):
    """Idempotency key from the INTENT (side + which bar), not the clock (L10).
    Re-running the same bar reuses this cid -> the venue rejects the duplicate,
    so a crash-and-restart within one bar cannot double-fill. Kept short and
    charset-safe for Binance's clientOrderId limits."""
    return f"run-{side}-{bar_key.replace('-', '')}"


def target_from_signal(price_df):
    """BRAIN: the validated regime combo, LONG/FLAT (long_short=False on spot).
    Live uses ONE fixed param set — walk-forward was to VALIDATE the approach,
    not to re-optimize every bar. Read the signal on the LAST CLOSED bar."""
    sig = regime_switch_signal(price_df, er_window=20, er_thresh=0.30)
    return int(sig["signal"].iloc[-1])   # {0, +1}; the live form of shift(1)


def tick(ex, forced_target=None):
    led = load_ledger()
    # Discipline 1 (L8): the last candle is still forming -> use CLOSED bars only.
    df = fetch_ohlcv(symbol=SYMBOL, timeframe=TIMEFRAME, limit=120).iloc[:-1]
    bar_obj = df.index[-1]
    bar_key = str(bar_obj.date())
    price = float(df["close"].iloc[-1])

    target = forced_target if forced_target is not None else target_from_signal(df)
    tag = "手动覆盖" if forced_target is not None else "信号"
    print(f"[{bar_key}] {SYMBOL} 收盘 ${price:,.2f} | {tag}目标仓位={target} "
          f"当前={led['position']}")

    # Discipline 2 (L8): act only on a STRICTLY NEWER closed bar (block stale/rewound).
    # Compare ISO date STRINGS (bar_key), not Timestamps: last_bar is stored as a
    # naive date string, bar_obj is tz-aware UTC -> comparing them raises. And put
    # forced_target FIRST so an override short-circuits before any compare (--target
    # must never touch this guard). Both were live-plumbing bugs paper trading is
    # exactly meant to catch.
    if forced_target is None and led["last_bar"] is not None and bar_key <= led["last_bar"]:
        print("  同一根收盘K线,已处理过 -> 不动作(防重复触发)。")
        return

    # Discipline 3 (L8) = idempotent target-compare: trade only if target changed.
    if target == led["position"]:
        print("  目标 == 当前,无需下单(账本即真相)。")
        led["last_bar"] = bar_key
        save_ledger(led)
        return

    # A change. Translate the position delta into ONE order, then run it through
    # the SAME guarded pipeline the L9-L11 demos used.
    if target == 1:                                   # flat -> long: BUY
        side = "buy"
        amount = float(ex.amount_to_precision(SYMBOL, ORDER_NOTIONAL / price))
    else:                                             # long -> flat: SELL what we hold
        side = "sell"
        amount = float(ex.amount_to_precision(SYMBOL, led["coin"]))
    if amount <= 0:
        print("  数量为 0(无持仓可平)-> 跳过。")
        led["position"] = target
        led["last_bar"] = bar_key
        save_ledger(led)
        return

    cid = bar_cid(side, bar_key)                      # L10: bar-keyed idempotency
    print(f"  下单意图: {side} {amount} BTC (cid={cid}) -> 过风控闸门:")
    order = guarded_create(ex, "market", side, amount, cid=cid)   # L9 gate inside
    if not order:
        print("  风控拒单,未发送。账本不变。")
        return

    # L11: NEVER trust the create() echo. READ BACK and RECONCILE.
    time.sleep(1)
    done = ex.fetch_order(order["id"], SYMBOL)
    show_order("成交回读", done)
    filled = float(done.get("filled") or 0)
    avg = done.get("average") or price

    # Write the ledger from what ACTUALLY filled, not what we intended (L11).
    if side == "buy":
        led["coin"] = round(led["coin"] + filled, 8)
    else:
        led["coin"] = round(max(0.0, led["coin"] - filled), 8)
    led["position"] = target
    led["last_bar"] = bar_key
    led["trades"].append({"bar": bar_key, "side": side, "intended": amount,
                          "filled": filled, "avg": avg, "cid": cid})
    save_ledger(led)
    print(f"  账本更新: position={led['position']}  coin={led['coin']} BTC  "
          f"(记的是实成 {filled},非意图 {amount})")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="signal -> real execution pipe (testnet)")
    ap.add_argument("--target", type=int, choices=(0, 1),
                    help="override the signal's target to exercise the pipe")
    ap.add_argument("--reset", action="store_true", help="wipe the local ledger")
    args = ap.parse_args()

    if args.reset and os.path.exists(LEDGER):
        os.remove(LEDGER)
        print("账本已重置。")

    print(f"=== L17 signal->execution  regime 组合(long/flat) {SYMBOL} {TIMEFRAME} "
          f"| 单笔名义 ${ORDER_NOTIONAL:,.0f} ===")
    tick(connect(), forced_target=args.target)
