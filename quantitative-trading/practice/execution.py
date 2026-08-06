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


def guarded_create(ex, otype, side, amount, price=None):
    """Every order goes through the gate. Idempotency via a clientOrderId,
    echoing L8: the same tick must not send the same order twice."""
    check_price = price if price is not None else float(ex.fetch_ticker(SYMBOL)["last"])
    ok, reason = pre_trade_check(ex, side, amount, check_price)
    print(f"  风控: {reason}")
    if not ok:
        return None
    cid = f"l9-{int(time.time() * 1000)}"
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
    fee = filled.get("fee") or {}
    print(f"  对账: 假设 ${assumed:,.2f} -> 实际均价 ${avg:,.2f}  "
          f"滑点 {slip_bps:+.1f} bps  手续费 {fee.get('cost')} {fee.get('currency')}")


def cmd_kill(_):
    open(KILL_FILE, "w").close()
    print("急停已激活。所有新订单将被风控闸门拒绝。解除:python execution.py unkill")


def cmd_unkill(_):
    if os.path.exists(KILL_FILE):
        os.remove(KILL_FILE)
    print("急停已解除。")


COMMANDS = {"balance": cmd_balance, "rest": cmd_rest, "fill": cmd_fill,
            "kill": cmd_kill, "unkill": cmd_unkill}

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Binance testnet order-lifecycle demo")
    ap.add_argument("cmd", choices=COMMANDS, help="balance|rest|fill|kill|unkill")
    args = ap.parse_args()

    # kill/unkill are local-only switches; they must NOT need network or keys.
    if args.cmd in ("kill", "unkill"):
        COMMANDS[args.cmd](None)
    else:
        COMMANDS[args.cmd](connect())
