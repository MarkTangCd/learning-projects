"""L17+L18: CLOSE THE LOOP, now with RISK-BASED SIZING.

L17 wired the validated signal to the real execution pipe (工位 3 → 工位 4).
L18 replaces the hardcoded $20 order with VOLATILITY TARGETING: each bar the
runner rebalances toward a target dollar exposure computed from your chosen risk
level and the CURRENT market volatility — not a pulled-from-thin-air number.

  fetch closed bars -> regime_switch_signal -> signal 0/1            (BRAIN, L12-16)
    -> vol_target_weight: weight = target_vol / realized_vol         (SIZE, L18)
    -> target_value = signal * weight * allocated_capital
    -> delta vs current holding; skip if within the no-trade band    (L8 discipline)
    -> guarded_create: RISK GATE + intent_cid idempotency            (L9 + L10)
    -> SEND -> fetch_order READ BACK -> RECONCILE filled vs intent    (L11)
    -> ledger from FILLED, never from intended                       (L11 rule)

Honest scope: SPOT testnet cannot SHORT (long/flat) and cannot lever (weight
capped at 1.0). Sizing is against ALLOCATED_CAPITAL — the slice you give this
strategy — so orders stay under the L9 $50 gate, which remains the hard backstop.
The perp venue (short + leverage + real funding) is a later lesson.

Setup: same testnet keys as L9 (BINANCE_TESTNET_KEY / _SECRET).
Run:  python strategy_runner.py                 # signal decides, vol sizes
      python strategy_runner.py --vol 0.22       # set your annualized vol target
      python strategy_runner.py --target 1        # force long to exercise the pipe
      python strategy_runner.py --reset           # wipe the local ledger
"""

import argparse
import json
import os
import time

from execution import connect, guarded_create, show_order, SYMBOL
from strategy import fetch_ohlcv, regime_switch_signal
from sizing import realized_vol, vol_target_weight

TIMEFRAME = "1d"
ALLOCATED_CAPITAL = 40.0    # $ given to this strategy; sizing base (stays < $50 gate)
TARGET_VOL = 0.20           # annualized vol target — YOUR risk dial (--vol overrides)
VOL_WINDOW = 20
MAX_LEVERAGE = 1.0          # SPOT can't lever; the perp venue could
LEDGER = os.path.join(os.path.dirname(__file__), "runner_ledger.json")


def load_ledger():
    if os.path.exists(LEDGER):
        with open(LEDGER) as f:
            return json.load(f)
    return {"coin": 0.0, "weight": 0.0, "last_bar": None, "trades": []}


def save_ledger(led):
    with open(LEDGER, "w") as f:
        json.dump(led, f, indent=2, default=str)


def bar_cid(side, bar_key):
    """Idempotency key from the INTENT (side + which bar), not the clock (L10).
    Re-running the same bar reuses this cid -> the venue rejects the duplicate,
    so a crash-and-restart within one bar cannot double-fill."""
    return f"run-{side}-{bar_key.replace('-', '')}"


def target_from_signal(price_df):
    """BRAIN: the validated regime combo, LONG/FLAT on spot. Read on the LAST
    CLOSED bar — the live form of shift(1). Live uses ONE fixed param set."""
    sig = regime_switch_signal(price_df, er_window=20, er_thresh=0.30)
    return int(sig["signal"].iloc[-1])   # {0, +1}


def tick(ex, forced_target=None, target_vol=TARGET_VOL):
    led = load_ledger()
    # Discipline 1 (L8): last candle still forming -> use CLOSED bars only.
    df = fetch_ohlcv(symbol=SYMBOL, timeframe=TIMEFRAME, limit=120).iloc[:-1]
    bar_obj = df.index[-1]
    bar_key = str(bar_obj.date())
    price = float(df["close"].iloc[-1])

    signal = forced_target if forced_target is not None else target_from_signal(df)
    # SIZE (L18): weight from CURRENT realized vol; target exposure = signal*weight*capital.
    ret = df["close"].pct_change()
    weight = vol_target_weight(ret, target_vol, VOL_WINDOW, MAX_LEVERAGE)
    target_weight = signal * weight
    target_value = target_weight * ALLOCATED_CAPITAL
    current_value = led["coin"] * price
    delta_value = target_value - current_value

    tag = "手动覆盖" if forced_target is not None else "信号"
    # L23: annualize off the INFERRED calendar, not a hardcoded 365 — this line
    # is what the display shows, so a stale constant here lies to your eyes too.
    rv_ann = realized_vol(ret, VOL_WINDOW).iloc[-1]
    print(f"[{bar_key}] {SYMBOL} ${price:,.2f} | {tag}={signal} 当前波动 {rv_ann:.0%} "
          f"-> 权重 {weight:.2f} 目标仓位 {target_weight:.2f}")
    print(f"  目标敞口 ${target_value:.2f}  当前 ${current_value:.2f}  "
          f"差额 ${delta_value:+.2f}(配给资本 ${ALLOCATED_CAPITAL:.0f}, vol目标 {target_vol:.0%})")

    # Discipline 2 (L8): act only on a STRICTLY NEWER closed bar (forced overrides).
    if forced_target is None and led["last_bar"] is not None and bar_key <= led["last_bar"]:
        print("  同一根收盘K线,已处理过 -> 不动作。")
        return

    # No-trade band (L8 discipline 3, sized version): don't churn on tiny deltas.
    # A rebalance smaller than the exchange min-notional cannot be traded anyway.
    market = ex.market(SYMBOL)
    min_cost = (market.get("limits", {}).get("cost", {}) or {}).get("min") or 5.0
    if abs(delta_value) < min_cost:
        print(f"  差额 ${abs(delta_value):.2f} < 最小下单额 ${min_cost} -> 在不动区间内,不调仓。")
        led["weight"] = target_weight
        led["last_bar"] = bar_key
        save_ledger(led)
        return

    # Rebalance toward target: buy the shortfall / sell the excess.
    side = "buy" if delta_value > 0 else "sell"
    raw_amt = abs(delta_value) / price
    if side == "sell":
        raw_amt = min(raw_amt, led["coin"])          # never sell more than we hold
    amount = float(ex.amount_to_precision(SYMBOL, raw_amt))
    if amount <= 0:
        print("  调仓量为 0 -> 跳过。")
        return

    cid = bar_cid(side, bar_key)                      # L10: bar-keyed idempotency
    print(f"  调仓: {side} {amount} BTC (cid={cid}) -> 过风控闸门:")
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

    # Ledger from what ACTUALLY filled, not what we intended (L11).
    led["coin"] = round(led["coin"] + filled if side == "buy"
                        else max(0.0, led["coin"] - filled), 8)
    led["weight"] = target_weight
    led["last_bar"] = bar_key
    led["trades"].append({"bar": bar_key, "side": side, "intended": amount,
                          "filled": filled, "avg": avg, "cid": cid})
    save_ledger(led)
    print(f"  账本: coin={led['coin']} BTC (${led['coin'] * price:.2f})  "
          f"目标权重={target_weight:.2f}  (记实成 {filled},非意图 {amount})")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="signal -> vol-sized -> real execution")
    ap.add_argument("--vol", type=float, default=TARGET_VOL,
                    help="annualized vol target (your risk dial)")
    ap.add_argument("--target", type=int, choices=(0, 1),
                    help="override the signal to exercise the pipe")
    ap.add_argument("--reset", action="store_true", help="wipe the local ledger")
    args = ap.parse_args()

    if args.reset and os.path.exists(LEDGER):
        os.remove(LEDGER)
        print("账本已重置。")

    print(f"=== L18 signal->vol-sized->execution  regime 组合 {SYMBOL} {TIMEFRAME} "
          f"| 配给 ${ALLOCATED_CAPITAL:.0f}  vol目标 {args.vol:.0%} ===")
    tick(connect(), forced_target=args.target, target_vol=args.vol)
