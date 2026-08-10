"""L20 practice: your first NATIVE SHORT on the PERP (USDT-M futures) TESTNET.

Spot (L9) told one structural lie you could not fix there: "you can only own a
coin, never owe it." On spot your BTC balance is >= 0 — there is no such thing as
a negative holding, so you cannot SHORT. Every short/long-short result from L16
was therefore un-landable on the spot venue.

The perp venue removes that wall. Here you do not hold a coin balance; you hold a
signed POSITION:

    +0.001  = long        0 = flat        -0.001 = short (you OWE BTC)

Selling when flat OPENS a short. Closing a short is a BUY (reduceOnly). The
discipline is the same as L9 — NEVER assume; SEND -> READ BACK -> RECONCILE — but
what you read back is now fetch_positions() (the signed truth), not a coin balance.

Three things that are NEW vs the spot testnet:
  1. Different venue + DIFFERENT KEYS: testnet.binancefuture.com (ccxt binanceusdm),
     NOT testnet.binance.vision. Generate a separate futures-testnet key.
  2. Symbol is BTC/USDT:USDT (a linear USDT-margined swap), not BTC/USDT.
  3. Min notional is ~$50 (vs ~$5 on spot) -> perp orders are chunky; the L9 gate
     is recalibrated here to $200 (still a hard backstop, just venue-calibrated).

Deferred to later lessons (don't add them here — keep working memory small):
  - L21: leverage (weight > 1.0, set_leverage, margin & liquidation).
  - L22: wire perp into strategy_runner + let REAL funding actually accrue over 8h.

Setup (one time):
  1. Go to https://testnet.binancefuture.com/ , log in, generate an API key.
     (This is a SEPARATE testnet from L9's spot testnet.binance.vision.)
  2. export BINANCE_FUTURES_TESTNET_KEY="..."
     export BINANCE_FUTURES_TESTNET_SECRET="..."
  3. python perp.py balance     # confirm you can see futures funny-money (USDT margin)

Run:  python perp.py funding    # the honest new cost (L16), now REAL — preview it
      python perp.py short      # sell-to-open a small short -> READ BACK the position
      python perp.py position   # the signed truth: side / contracts / notional / uPnL
      python perp.py close       # flatten with a reduceOnly order (short close = BUY)
"""

import argparse
import os
import time

import ccxt

SYMBOL = "BTC/USDT:USDT"     # linear USDT-margined perpetual swap (NOT spot BTC/USDT)
PROXY = "http://127.0.0.1:1087"

# Gate recalibrated to this venue: perp min-notional is ~$50, so a $50 spot cap
# would reject every order. Same GATE SHAPE as L9, just calibrated to the venue.
MAX_NOTIONAL_USDT = 200.0
DEMO_NOTIONAL_USDT = 60.0    # a hair above the ~$50 min so the demo short is legal
KILL_FILE = os.path.join(os.path.dirname(__file__), "execution_kill.flag")  # shared急停


def connect():
    """USDT-M futures testnet client. Uses SEPARATE keys from the L9 spot testnet."""
    key = os.getenv("BINANCE_FUTURES_TESTNET_KEY")
    secret = os.getenv("BINANCE_FUTURES_TESTNET_SECRET")
    if not key or not secret:
        raise SystemExit(
            "缺少 perp 测试网密钥(与 L9 现货测试网是两套!)。\n"
            "去 https://testnet.binancefuture.com/ 登录生成 API key,然后:\n"
            '  export BINANCE_FUTURES_TESTNET_KEY="..."\n'
            '  export BINANCE_FUTURES_TESTNET_SECRET="..."')
    ex = ccxt.binanceusdm({"apiKey": key, "secret": secret, "timeout": 30000,
                           "enableRateLimit": True})
    ex.httpsProxy = PROXY
    ex.set_sandbox_mode(True)   # -> testnet.binancefuture.com; keys must be futures-testnet keys
    ex.load_markets()
    # Assume ONE-WAY mode (a single signed position per symbol). Force it, but a
    # "no need to change" error just means it's already one-way — harmless.
    try:
        ex.set_position_mode(False)   # False = one-way (hedgeMode off)
    except ccxt.BaseError:
        pass
    return ex


def pre_trade_check(side, amount, price):
    """Same RISK GATE as L9 (kill switch + max-notional), recalibrated to perp.
    reduceOnly closes are exempt from the notional cap — you must always be able
    to REDUCE risk even if a position somehow grew past the cap."""
    if os.path.exists(KILL_FILE):
        return False, "急停已激活(KILL SWITCH ON)—— 一切新订单被拒。先 execution.py unkill。"
    notional = amount * price
    if notional > MAX_NOTIONAL_USDT:
        return False, f"名义价值 ${notional:,.2f} 超过上限 ${MAX_NOTIONAL_USDT:,.2f}"
    return True, f"通过(名义 ${notional:,.2f} ≤ 上限 ${MAX_NOTIONAL_USDT:,.0f})"


def guarded_create(ex, side, amount, reduce_only=False, cid=None):
    """Market order through the gate, with L10 idempotency (clientOrderId).
    reduce_only=True marks a position-CLOSING order (skips the notional cap)."""
    price = float(ex.fetch_ticker(SYMBOL)["last"])
    if reduce_only:
        ok, reason = (True, "平仓单(reduceOnly)—— 只减风险,免名义上限")
    else:
        ok, reason = pre_trade_check(side, amount, price)
    print(f"  风控: {reason}")
    if not ok:
        return None
    params = {"clientOrderId": cid or f"perp-{side}-{'close' if reduce_only else 'open'}"}
    if reduce_only:
        params["reduceOnly"] = True
    return ex.create_order(SYMBOL, "market", side, amount, None, params)


def read_position(ex):
    """READ BACK the signed truth. Returns (signed_contracts, raw_position_dict).
    fetch_positions gives an UNSIGNED 'contracts' + a 'side' string; the sign is
    what makes short vs long a single number: long=+, short=-, flat=0."""
    positions = ex.fetch_positions([SYMBOL])
    for p in positions:
        contracts = float(p.get("contracts") or 0)
        if contracts == 0:
            continue
        signed = contracts if p.get("side") == "long" else -contracts
        return signed, p
    return 0.0, None


def show_position(ex, tag="持仓回读"):
    signed, p = read_position(ex)
    if p is None:
        print(f"  [{tag}] 无持仓(flat,仓位=0)。")
        return signed
    label = "多(long)" if signed > 0 else "空(short)"
    print(f"  [{tag}] {label}  仓位={signed:+g} BTC  名义≈${abs(float(p.get('notional') or 0)):,.2f}")
    print(f"        开仓价=${float(p.get('entryPrice') or 0):,.2f}  "
          f"未实现盈亏=${float(p.get('unrealizedPnl') or 0):+,.4f}  "
          f"杠杆={p.get('leverage')}x")
    return signed


def cmd_balance(ex):
    bal = ex.fetch_balance()
    info = bal.get("USDT", {})
    print("perp 测试网保证金余额(USDT):")
    print(f"  free={info.get('free')}  used={info.get('used')}  total={info.get('total')}")
    print("  (perp 里你抵押的是 USDT 保证金,不再持有 BTC 币本身。)")


def cmd_funding(ex):
    """The honest new cost from L16, now REAL. On perp you pay/receive funding
    every 8h (3x/day) while a position is open — long pays when rate>0. In L16
    this was a SIMULATED carbon tax; here it is the venue's live number."""
    fr = ex.fetch_funding_rate(SYMBOL)
    rate = float(fr.get("fundingRate") or 0)
    print(f"{SYMBOL} 当前资金费率:")
    print(f"  每 8h 费率 = {rate * 100:+.4f}%   ->  折合每日 ≈ {rate * 3 * 100:+.4f}%")
    print(f"  下次结算: {fr.get('fundingDatetime')}")
    sign = "多头付给空头" if rate > 0 else "空头付给多头" if rate < 0 else "持平"
    print(f"  费率{'>' if rate > 0 else '<' if rate < 0 else '='}0 -> {sign}。"
          f"这就是 L16 里那笔'碳税',现在是真的。持仓期间每 8h 收/付一次。")


def cmd_short(ex):
    """THE WIN: open a native SHORT — a sell-to-open — the thing spot cannot do.
    Flat + market SELL => you now OWE BTC => position goes NEGATIVE. Then the L9
    discipline: don't trust the echo, READ BACK the signed position."""
    signed = read_position(ex)[0]
    if signed != 0:
        print(f"  已有持仓 {signed:+g} BTC。先 `python perp.py close` 平掉再演示开空。")
        return
    price = float(ex.fetch_ticker(SYMBOL)["last"])
    amount = float(ex.amount_to_precision(SYMBOL, DEMO_NOTIONAL_USDT / price))
    print(f"当前 flat。市价【卖出开空】{amount} BTC(名义≈${amount * price:,.2f},参考价 ${price:,.2f}):")
    print("  注意:flat 时的 SELL = 开空,不是'卖掉手里的币'(你手里没有币)。")
    o = guarded_create(ex, "sell", amount)
    if not o:
        print("  风控拒单,未开空。")
        return
    time.sleep(1)
    done = ex.fetch_order(o["id"], SYMBOL)
    print(f"  [成交回读] id={done.get('id')} status={done.get('status')} "
          f"filled={done.get('filled')} average={done.get('average')}")
    print("  -> 现在读回持仓,应看到一个【负】仓位(现货永远做不到这一点):")
    show_position(ex)


def cmd_position(ex):
    show_position(ex, tag="持仓")


def cmd_close(ex):
    """Flatten whatever we hold with a reduceOnly market order in the OPPOSITE
    direction. Closing a SHORT is a BUY; closing a LONG is a SELL. reduceOnly
    guarantees the order can only shrink the position, never accidentally flip it."""
    signed, _ = read_position(ex)
    if signed == 0:
        print("  已经是 flat,无需平仓。")
        return
    side = "buy" if signed < 0 else "sell"     # close short = BUY, close long = SELL
    amount = float(ex.amount_to_precision(SYMBOL, abs(signed)))
    print(f"当前仓位 {signed:+g} BTC -> reduceOnly 市价 {side} {amount} 平仓"
          f"(平空是买回,平多是卖出):")
    o = guarded_create(ex, side, amount, reduce_only=True)
    if not o:
        return
    time.sleep(1)
    done = ex.fetch_order(o["id"], SYMBOL)
    print(f"  [成交回读] id={done.get('id')} status={done.get('status')} filled={done.get('filled')}")
    show_position(ex)


COMMANDS = {"balance": cmd_balance, "funding": cmd_funding, "short": cmd_short,
            "position": cmd_position, "close": cmd_close}

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Binance USDT-M perp testnet: first native short")
    ap.add_argument("cmd", choices=COMMANDS, help="balance|funding|short|position|close")
    args = ap.parse_args()
    COMMANDS[args.cmd](connect())
