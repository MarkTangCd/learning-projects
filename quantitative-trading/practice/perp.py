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
      python perp.py raw         # the UNNORMALISED venue response (why leverage is None)
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

# L21. The ration capital from L19 — the number that could NOT trade on perp at 1x,
# because $40 < the ~$50 min notional. Leverage is what unlocks it.
RATION_USDT = 40.0
LEVERAGE_LADDER = (1, 2, 5, 10, 20)
DEFAULT_MMR = 0.004          # maintenance margin rate; real one is read off the position


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
    ex = ccxt.binanceusdm({
        "apiKey": key, "secret": secret, "timeout": 30000, "enableRateLimit": True,
        # ccxt >= 4.4.9 REFUSES to sign futures-testnet requests by default (it raises
        # NotSupported) because Binance deprecated this testnet in favour of "Demo
        # Trading". The venue itself is still up and serving, so we opt back in.
        # If testnet.binancefuture.com ever really dies, the migration is: drop
        # set_sandbox_mode(True), get keys from demo.binance.com, call
        # ex.enable_demo_trading(True) instead. Same code otherwise.
        "options": {"disableFuturesSandboxWarning": True},
    })
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


def derive_leverage(p):
    """Binance's v3 endpoints DROPPED the 'leverage' field, so ccxt reports None.
    But leverage is not a fact you must be told — it is an identity:

        leverage = |notional| / initialMargin

    Same for the two rates that govern liquidation (L21):
        initial margin rate     = initialMargin / |notional| = 1 / leverage
        maintenance margin rate = maintMargin   / |notional|
    Returns (leverage, maint_margin_rate) — either may be None if fields absent."""
    info = p.get("info") or {}
    notional = abs(float(info.get("notional") or 0))
    if not notional:
        return None, None
    init = float(info.get("initialMargin") or 0)
    maint = float(info.get("maintMargin") or 0)
    lev = notional / init if init else None
    return lev, (maint / notional if maint else None)


def entry_fee_from_breakeven(p, signed):
    """The fee you ALREADY paid to open, without re-fetching order history.
    breakEvenPrice is entryPrice shifted by the paid fee — against you: for a
    SHORT it sits BELOW entry (you must buy back cheaper to break even), for a
    LONG above it. The gap times size IS the entry fee."""
    info = p.get("info") or {}
    entry = float(info.get("entryPrice") or 0)
    be = float(info.get("breakEvenPrice") or 0)
    if not entry or not be:
        return 0.0
    return abs(entry - be) * abs(signed)


def show_position(ex, tag="持仓回读"):
    signed, p = read_position(ex)
    if p is None:
        print(f"  [{tag}] 无持仓(flat,仓位=0)。")
        return signed
    label = "多(long)" if signed > 0 else "空(short)"
    notional = abs(float(p.get("notional") or 0))
    lev, maint_rate = derive_leverage(p)
    lev_txt = f"{lev:.1f}x(由 |名义|/起始保证金 推出)" if lev else "未知"
    print(f"  [{tag}] {label}  仓位={signed:+g} BTC  名义≈${notional:,.2f}")
    print(f"        开仓价=${float(p.get('entryPrice') or 0):,.2f}  "
          f"未实现盈亏=${float(p.get('unrealizedPnl') or 0):+,.4f}  杠杆={lev_txt}")
    if maint_rate:
        print(f"        维持保证金率={maint_rate * 100:.3f}%  "
              f"爆仓价=${float(p.get('liquidationPrice') or 0):,.2f}"
              f"(全仓时整个钱包在垫背,所以这个数可能大得离谱)")
    return signed


def read_fill(ex, order_id):
    """READ BACK what the fill actually COST. fetch_order on binanceusdm often
    returns fee=None (futures fees live on the TRADES, not the order), so fall
    back to fetch_my_trades and sum the legs belonging to this order.
    Returns (average_price, fee_usdt, filled_amount)."""
    o = ex.fetch_order(order_id, SYMBOL)
    avg = float(o.get("average") or 0)
    filled = float(o.get("filled") or 0)
    fee = o.get("fee") or {}
    cost = fee.get("cost")
    if cost is None:                      # dig into the trades for the real number
        legs = [t for t in ex.fetch_my_trades(SYMBOL, limit=20)
                if str(t.get("order")) == str(order_id)]
        if legs:
            cost = sum(float((t.get("fee") or {}).get("cost") or 0) for t in legs)
            avg = (sum(float(t["price"]) * float(t["amount"]) for t in legs)
                   / sum(float(t["amount"]) for t in legs))
    return avg, float(cost or 0), filled


def report_fill(ex, order_id, tag="成交回读"):
    avg, fee, filled = read_fill(ex, order_id)
    print(f"  [{tag}] filled={filled:g}  均价=${avg:,.2f}  手续费=${fee:.4f}")
    return avg, fee, filled


def cmd_raw(ex):
    """The RAW truth, unnormalised. ccxt hands you a tidy unified dict — but a
    field the venue never sent silently becomes None, and None does not raise.
    This prints what Binance ACTUALLY returned, so you can see which fields are
    genuinely missing vs merely mis-parsed. Also probes the OTHER endpoint:
    ccxt defaults fetchPositions to /fapi/v3/positionRisk; 'account' hits the
    account-info endpoint instead, which may carry fields v3 positionRisk dropped."""
    import json
    for method in ("positionRisk", "account"):
        print(f"\n{'=' * 62}\n端点 method='{method}'\n{'=' * 62}")
        try:
            positions = ex.fetch_positions([SYMBOL], {"method": method})
        except ccxt.BaseError as e:
            print(f"  该端点报错: {type(e).__name__}: {e}")
            continue
        live = [p for p in positions if float(p.get("contracts") or 0) != 0]
        if not live:
            print("  无持仓 —— 先 `python perp.py short` 开个仓再跑本命令。")
            continue
        p = live[0]
        print(f"  ccxt 归一化后 leverage = {p.get('leverage')!r}   "
              f"(None = 这扇窗户没有这个字段)")
        print("  --- 交易所原始返回(info) ---")
        print(json.dumps(p.get("info"), indent=2, ensure_ascii=False))
        has = "leverage" in (p.get("info") or {})
        print(f"  --> 原始响应里{'有' if has else '【没有】'} 'leverage' 字段。")


def isolated_liq_price(entry, lev, mmr, is_short):
    """Where an ISOLATED position dies. Solve for the price P at which the posted
    margin is exactly eaten down to the maintenance requirement:

        margin  −  loss(P)        =  maintenance(P)
        P0·q/L  −  (P−P0)·q       =  mmr·P·q          (short)
      => P = P0·(1 + 1/L) / (1 + mmr)

    Note q cancels: the liquidation PRICE does not depend on position size — only
    on leverage and the maintenance rate. Size decides how much you lose, not when."""
    if not lev:
        return None
    if is_short:
        return entry * (1 + 1 / lev) / (1 + mmr)
    return entry * (1 - 1 / lev) / (1 - mmr)


def cmd_lever(ex, value=None):
    """THE DIAL — and the lesson that leverage is not an accelerator.

    Leverage is the denominator of the identity you derived in L20:
        leverage = |notional| / initialMargin
    Raise it at CONSTANT notional and only the MARGIN moves. Your P&L per $1 of
    BTC movement is unchanged, because that is set by notional alone. What the
    dial really buys is CAPACITY (notional you may carry per unit of capital) —
    and, in isolated margin, it sets how far price may travel before you die."""
    signed, p = read_position(ex)
    mmr = DEFAULT_MMR
    lev_now = None
    if p is not None:
        lev_now, rate = derive_leverage(p)
        mmr = rate or DEFAULT_MMR
    price = float(ex.fetch_ticker(SYMBOL)["last"])
    min_notional = float((ex.market(SYMBOL)["limits"]["cost"] or {}).get("min") or 0)

    if value is not None:                      # SET the dial, then READ IT BACK (L9)
        ex.set_leverage(int(value), SYMBOL)
        print(f"已设置杠杆 -> {int(value)}x。回读确认:")
        if read_position(ex)[1] is not None:
            show_position(ex, tag="持仓回读")
        else:
            print("  (当前无持仓,新杠杆会在下一次开仓时生效。)")
        return

    print(f"当前杠杆 = {f'{lev_now:.1f}x' if lev_now else '无持仓,读不出(杠杆是持仓的属性)'}"
          f"   维持保证金率 = {mmr * 100:.3f}%   参考价 = ${price:,.2f}")
    print(f"最小名义 = ${min_notional:,.2f}   L19 配给资本 = ${RATION_USDT:,.2f}\n")

    # Column A: SAME notional, different dial -> only the margin moves.
    n = DEMO_NOTIONAL_USDT
    print(f"【A】固定名义 ${n:.0f} 不变,只拧杠杆 —— 看什么变了、什么没变:")
    print(f"  {'杠杆':<6}{'占用保证金':>12}{'逐仓爆仓价(空)':>18}{'需涨幅':>10}{'每 $1 波动的盈亏':>18}")
    for lev in LEVERAGE_LADDER:
        liq = isolated_liq_price(price, lev, mmr, is_short=True)
        pnl_per_dollar = n / price          # = position size in BTC; INDEPENDENT of lev
        print(f"  {lev:<4}x{n / lev:>11.2f}{liq:>18,.0f}{(liq / price - 1) * 100:>9.2f}%"
              f"{pnl_per_dollar:>18.6f}")
    print("  ↑ 最后一列全程不动 —— 风险由【名义】决定,不由杠杆决定。")
    print("    动的只有保证金(被锁的钱)和爆仓距离。\n")

    # Column B: the L19 cliffhanger — can the $40 ration trade at all?
    print(f"【B】L19 的 ${RATION_USDT:.0f} 配给资本能不能下出单(最小名义 ${min_notional:.0f}):")
    for lev in LEVERAGE_LADDER:
        cap = RATION_USDT * lev
        ok = "✓ 可以下单" if cap >= min_notional else "✗ 下不出 —— 名义不够最小额"
        print(f"  {lev:<4}x  最大名义 = ${cap:>8,.2f}   {ok}")
    print(f"  ↑ 这就是 L19 那个 weight 被截到 1.0 的天花板被拆掉的地方。")

    print(f"\n用法: python perp.py lever 5   # 把杠杆设成 5x(会回读确认)")


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
    avg, fee, _ = report_fill(ex, o["id"])
    signed_side_is_sell = True          # cmd_short always opens with a SELL
    # Drift from the reference price. Two things are mixed in here: the spread you
    # crossed (always against you) and the price moving between fetch_ticker and the
    # fill (either way). It must stay SIGNED — taking abs() would book a favourable
    # move as a cost. On testnet the synthetic book makes drift dominate the spread,
    # so this number swings both ways and is NOT a clean slippage measurement.
    drift = (avg - price) / price * 1e4 if price else 0
    edge = drift if signed_side_is_sell else -drift   # selling higher is good
    print(f"        参考价漂移 = {drift:+.2f} bp -> 对这张卖单{'有利' if edge > 0 else '不利'}"
          f"(价差 + 读价到成交之间的价格移动;测试网盘口是合成的,量不准真实滑点)")
    print(f"        开仓净成本 ≈ ${fee - edge / 1e4 * avg * amount:+.4f}"
          f"(手续费 {fee:.4f} {'−' if edge > 0 else '+'} 漂移 {abs(edge) / 1e4 * avg * amount:.4f})")
    print("  -> 现在读回持仓,应看到一个【负】仓位(现货永远做不到这一点):")
    show_position(ex)


def cmd_position(ex):
    show_position(ex, tag="持仓")


def cmd_close(ex):
    """Flatten whatever we hold with a reduceOnly market order in the OPPOSITE
    direction. Closing a SHORT is a BUY; closing a LONG is a SELL. reduceOnly
    guarantees the order can only shrink the position, never accidentally flip it."""
    signed, p = read_position(ex)
    if signed == 0:
        print("  已经是 flat,无需平仓。")
        return
    # Grab BEFORE closing — both vanish the moment the position goes flat.
    entry = float(p.get("entryPrice") or 0)
    entry_fee = entry_fee_from_breakeven(p, signed)
    side = "buy" if signed < 0 else "sell"     # close short = BUY, close long = SELL
    amount = float(ex.amount_to_precision(SYMBOL, abs(signed)))
    print(f"当前仓位 {signed:+g} BTC -> reduceOnly 市价 {side} {amount} 平仓"
          f"(平空是买回,平多是卖出):")
    o = guarded_create(ex, side, amount, reduce_only=True)
    if not o:
        return
    time.sleep(1)
    exit_avg, exit_fee, filled = report_fill(ex, o["id"])
    # Gross PnL on a SHORT is (entry - exit); on a LONG it is (exit - entry).
    # Only the NET number (gross minus fees) is the one that hits your balance.
    gross = (entry - exit_avg) * filled if signed < 0 else (exit_avg - entry) * filled
    notional = entry * filled
    net = gross - entry_fee - exit_fee      # BOTH legs — a one-sided figure lies
    print(f"\n  === 这趟来回的真实账单 ===")
    print(f"  开仓价 ${entry:,.2f} -> 平仓价 ${exit_avg:,.2f}   "
          f"毛盈亏 = ${gross:+.4f}({gross / notional * 1e4:+.2f} bp)")
    print(f"  开仓手续费 = ${entry_fee:.4f}(由 breakEvenPrice 反推,你早就付过了)")
    print(f"  平仓手续费 = ${exit_fee:.4f}")
    print(f"  净盈亏 = ${net:+.4f}  = 名义的 {net / notional * 1e4:+.2f} bp")
    print(f"  --> 来回固定门槛 ≈ {(entry_fee + exit_fee) / notional * 1e4:.2f} bp:"
          f"信号必须先赚够这么多才开始赚钱。")
    print("  这就是 L4 回测里你手填的那个摩擦参数的真身 —— 现在它是实测值。\n")
    show_position(ex)


COMMANDS = {"balance": cmd_balance, "funding": cmd_funding, "short": cmd_short,
            "position": cmd_position, "close": cmd_close, "raw": cmd_raw,
            "lever": cmd_lever}

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Binance USDT-M perp testnet: short + leverage")
    ap.add_argument("cmd", choices=COMMANDS, help="balance|funding|short|position|close|raw|lever")
    ap.add_argument("value", nargs="?", default=None, help="lever 的可选参数,如 `lever 5`")
    args = ap.parse_args()
    ex = connect()
    cmd_lever(ex, args.value) if args.cmd == "lever" else COMMANDS[args.cmd](ex)
