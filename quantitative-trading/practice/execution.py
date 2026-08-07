"""L9 practice: real order execution on Binance SPOT TESTNET (工位 4, 深水区).

Paper trading (L8) told one big lie: "fill is instant, total, and at my price."
Real execution is ASYNCHRONOUS. You SEND an order; the venue decides what
happens. It may rest unfilled, fill partially, fill at a worse price, get
rejected, or time out. The discipline that replaces L8's assumption:

    NEVER assume a fill. SEND -> READ BACK the order object -> RECONCILE.

This script places REAL orders against Binance's test network (no real money),
walks the order lifecycle (open -> canceled, and market -> closed/filled), and
guards every order behind a pre-trade RISK GATE + a KILL SWITCH (急停).

Setup (one time):
  1. Go to https://testnet.binance.vision/ , log in with GitHub, "Generate HMAC Key".
  2. export BINANCE_TESTNET_KEY="..."  and  BINANCE_TESTNET_SECRET="..."
  3. python execution.py balance   # confirm you can see testnet funny-money

Docs: ccxt unified API (create_order / fetch_order / cancel_order / order struct).
"""

import argparse
import os
import time

import ccxt

SYMBOL = "BTC/USDT"
PROXY = "http://127.0.0.1:1087"

# --- Risk config: the whole point is that these are ENFORCED before every send.
MAX_NOTIONAL_USDT = 50.0                       # hard cap on any single order's value
KILL_FILE = os.path.join(os.path.dirname(__file__), "execution_kill.flag")


def connect():
    """Build a testnet-mode client. set_sandbox_mode MUST come before any call."""
    key = os.getenv("BINANCE_TESTNET_KEY")
    secret = os.getenv("BINANCE_TESTNET_SECRET")
    if not key or not secret:
        raise SystemExit(
            "缺少测试网密钥。去 https://testnet.binance.vision/ 用 GitHub 登录生成,然后:\n"
            '  export BINANCE_TESTNET_KEY="..."\n'
            '  export BINANCE_TESTNET_SECRET="..."')
    ex = ccxt.binance({"apiKey": key, "secret": secret, "timeout": 30000,
                       "enableRateLimit": True})
    ex.httpsProxy = PROXY
    ex.set_sandbox_mode(True)   # -> testnet.binance.vision; the keys above must be testnet keys
    ex.load_markets()
    return ex


def pre_trade_check(ex, side, amount, price):
    """The RISK GATE. Returns (ok, reason). No order is sent unless ok is True.

    Two guards here; real systems add more (max position, daily loss, fat-finger
    price bands). The kill switch is deliberately checked FIRST and cheapest."""
    if os.path.exists(KILL_FILE):
        return False, "急停已激活(KILL SWITCH ON)—— 一切新订单被拒。先 `unkill`。"
    notional = amount * price
    if notional > MAX_NOTIONAL_USDT:
        return False, f"名义价值 ${notional:,.2f} 超过上限 ${MAX_NOTIONAL_USDT:,.2f}"
    market = ex.market(SYMBOL)
    min_cost = (market.get("limits", {}).get("cost", {}) or {}).get("min")
    if min_cost and notional < min_cost:
        return False, f"名义价值 ${notional:,.2f} 低于交易所最小下单额 ${min_cost}"
    return True, f"通过(名义 ${notional:,.2f} ≤ 上限 ${MAX_NOTIONAL_USDT:,.0f})"


def show_order(tag, o):
    """Print the fields you MUST read back instead of assuming."""
    print(f"  [{tag}] id={o.get('id')}  status={o.get('status')}  "
          f"type={o.get('type')}/{o.get('side')}")
    print(f"        amount={o.get('amount')}  filled={o.get('filled')}  "
          f"remaining={o.get('remaining')}  average={o.get('average')}  "
          f"cost={o.get('cost')}")


def intent_cid(side, price, tag="l9"):
    """Idempotency key derived from the TRADE INTENT, not the wall clock.

    A retry after a timed-out SEND must reuse the SAME key, or the venue treats
    it as a brand-new order and you double-fill. So the key must be a pure
    function of what the trade IS (side + price bucket), never time.time().
    In the L8 tick loop the natural intent id is (symbol, side, bar_ts)."""
    return f"{tag}-{side}-{str(price).replace('.', '_')}"


def guarded_create(ex, otype, side, amount, price=None, cid=None):
    """Every order goes through the gate. Idempotency via a clientOrderId.
    If cid is None a per-intent key is derived so retries are safe by default."""
    check_price = price if price is not None else float(ex.fetch_ticker(SYMBOL)["last"])
    ok, reason = pre_trade_check(ex, side, amount, check_price)
    print(f"  风控: {reason}")
    if not ok:
        return None
    cid = cid or intent_cid(side, check_price)
    params = {"clientOrderId": cid}
    if otype == "limit":
        return ex.create_order(SYMBOL, "limit", side, amount, price, params)
    return ex.create_order(SYMBOL, "market", side, amount, None, params)


def cmd_balance(ex):
    bal = ex.fetch_balance()
    print("测试网余额:")
    for coin in ("USDT", "BTC"):
        info = bal.get(coin, {})
        print(f"  {coin}: free={info.get('free')}  used={info.get('used')}  "
              f"total={info.get('total')}")


def cmd_rest(ex):
    """Lifecycle demo #1 (safe): a limit BUY far BELOW market rests unfilled.
    Shows status=open, filled=0 -> then we cancel -> status=canceled.
    This is the reality L8 pretended away: an order can just sit there."""
    price = float(ex.fetch_ticker(SYMBOL)["last"])
    limit = ex.price_to_precision(SYMBOL, price * 0.80)   # 20% below -> won't fill
    amount = ex.amount_to_precision(SYMBOL, MAX_NOTIONAL_USDT * 0.5 / float(limit))
    print(f"下一张限价买单 @ ${limit}(市价 ${price:,.2f} 的 80%,不会成交):")
    o = guarded_create(ex, "limit", "buy", float(amount), float(limit))
    if not o:
        return
    show_order("下单返回", o)
    time.sleep(1)
    fetched = ex.fetch_order(o["id"], SYMBOL)     # READ BACK the truth
    show_order("回读", fetched)
    canceled = ex.cancel_order(o["id"], SYMBOL)   # end the lifecycle
    print(f"  撤单 -> status={ex.fetch_order(o['id'], SYMBOL)['status']}")


def cmd_fill(ex):
    """Lifecycle demo #2 (the punchline): a MARKET buy actually fills.
    Then RECONCILE: what you assumed vs what the venue actually gave you."""
    assumed = float(ex.fetch_ticker(SYMBOL)["last"])
    amount = ex.amount_to_precision(SYMBOL, MAX_NOTIONAL_USDT * 0.4 / assumed)
    print(f"市价买入 {amount} BTC(下单前假设价 ${assumed:,.2f}):")
    o = guarded_create(ex, "market", "buy", float(amount))
    if not o:
        return
    time.sleep(1)
    filled = ex.fetch_order(o["id"], SYMBOL)      # never trust the create() echo alone
    show_order("成交回读", filled)
    avg = filled.get("average") or assumed
    slip_bps = (avg - assumed) / assumed * 1e4

    # RECONCILE FEES — Binance's order object does NOT carry commission; the fee
    # lives in the individual fills. Read the trades and aggregate. This is the
    # honest cost of the trade, not the (empty) fee field on the order header.
    fee_cost, fee_ccy = fee_from_trades(ex, o["id"])
    fee_bps = (fee_cost / filled["cost"] * 1e4) if fee_cost and filled.get("cost") else None
    fee_str = f"{fee_cost} {fee_ccy}" + (f"({fee_bps:+.1f} bps)" if fee_bps else "")
    print(f"  对账: 假设 ${assumed:,.2f} -> 实际均价 ${avg:,.2f}  "
          f"滑点 {slip_bps:+.1f} bps  手续费 {fee_str}")
    if slip_bps == 0.0:
        print("  注:测试网盘口是合成的,滑点常为 0 —— 真实成本要到实盘/真实盘口才测得出。")


def fee_from_trades(ex, order_id):
    """Where the fee actually lives: the fills, not the order header.

    Returns (total_cost, currency). Sums commission across all fills of the
    order. Falls back to (None, None) if the venue exposes nothing."""
    try:
        trades = ex.fetch_order_trades(order_id, SYMBOL)
    except Exception:
        return None, None
    total, ccy = 0.0, None
    for t in trades:
        fee = t.get("fee") or {}
        if fee.get("cost") is not None:
            total += float(fee["cost"])
            ccy = fee.get("currency") or ccy
    return (round(total, 8), ccy) if ccy else (None, None)


def cmd_dup(ex):
    """Idempotency demo (L10): send the SAME clientOrderId twice — the venue
    rejects the duplicate, so a timed-out-then-retried SEND cannot double-fill.
    Uses a far-below-market limit (won't fill) so nothing actually double-buys.

    The recovery pattern real systems use: on a timeout, DON'T blind-retry
    create_order. First fetch_order(cid) to learn if it already went through;
    resend with the SAME cid only if it didn't."""
    price = float(ex.fetch_ticker(SYMBOL)["last"])
    limit = ex.price_to_precision(SYMBOL, price * 0.80)   # won't fill
    amount = ex.amount_to_precision(SYMBOL, MAX_NOTIONAL_USDT * 0.5 / float(limit))
    cid = intent_cid("buy", limit)                        # SAME key both sends
    print(f"用同一个 clientOrderId 发两次 @ ${limit}(cid={cid}):")

    print("  第一次发送:")
    o1 = guarded_create(ex, "limit", "buy", float(amount), float(limit), cid=cid)
    if not o1:
        return
    show_order("第一次", o1)

    print("  第二次发送(模拟断网后重试,同一个 cid):")
    try:
        o2 = guarded_create(ex, "limit", "buy", float(amount), float(limit), cid=cid)
        if o2:
            show_order("重试", o2)
            same = o2.get("id") == o1.get("id")
            print(f"  交易所返回{'同一张单(id 相同)' if same else '新单!幂等失效'} "
                  f"-> {'没有下重单 ✅' if same else '账户被下了两单 ❌'}")
    except ccxt.DuplicateOrderId as e:
        print(f"  交易所拒绝重复 clientOrderId ✅ —— 幂等生效,账户没被下重单。({e})")
    except ccxt.InvalidOrder as e:
        print(f"  交易所拒绝重复单 ✅(InvalidOrder)——幂等生效。({e})")

    ex.cancel_order(o1["id"], SYMBOL)                     # cleanup
    print(f"  撤单 -> status={ex.fetch_order(o1['id'], SYMBOL)['status']}")


def cmd_kill(_):
    open(KILL_FILE, "w").close()
    print("急停已激活。所有新订单将被风控闸门拒绝。解除:python execution.py unkill")


def cmd_unkill(_):
    if os.path.exists(KILL_FILE):
        os.remove(KILL_FILE)
    print("急停已解除。")


COMMANDS = {"balance": cmd_balance, "rest": cmd_rest, "fill": cmd_fill,
            "dup": cmd_dup, "kill": cmd_kill, "unkill": cmd_unkill}

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Binance testnet order-lifecycle demo")
    ap.add_argument("cmd", choices=COMMANDS, help="balance|rest|fill|dup|kill|unkill")
    args = ap.parse_args()

    # kill/unkill are local-only switches; they must NOT need network or keys.
    if args.cmd in ("kill", "unkill"):
        COMMANDS[args.cmd](None)
    else:
        COMMANDS[args.cmd](connect())
