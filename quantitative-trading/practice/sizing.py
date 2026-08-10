"""L18: position sizing — decide HOW MUCH, not just which way.

Everything so far used a full-size position (backtest: position in {-1,0,+1};
runner: a hardcoded $20 notional). That is risk-BLIND: the same notional is a
tiny bet in a calm market and a reckless one in a violent crash. Real systems
size by RISK, not by a round number.

The institutional default is VOLATILITY TARGETING: scale the position so the
strategy's expected volatility hits a fixed target. When the market gets wild,
shrink; when it calms, grow. This directly tames the 'always-in-market double
exposure' that hurt the two-sided combo in L16.

    weight = target_vol / realized_vol   (clipped to a max leverage)

Honesty: our edge is THIN and UNCERTAIN (L16). So we size CONSERVATIVELY — a
modest target and a hard leverage cap. Full Kelly assumes you KNOW your edge;
with a noisy estimate it over-bets and blows up. Vol targeting is also a risk
tool: it caps how much a wrong signal can cost.
"""

PERIODS_PER_YEAR = 365   # crypto trades 24/7; daily bars


def realized_vol(returns, window=20, periods_per_year=PERIODS_PER_YEAR):
    """Annualized rolling realized volatility from per-bar returns."""
    return returns.rolling(window).std() * (periods_per_year ** 0.5)


def vol_target_position(df, target_vol=0.20, window=20, max_leverage=3.0):
    """Turn a {-1,0,+1} position into a risk-sized weight via vol targeting.

    df must already carry a 'position' column (the tradeable, shift(1)'d signal)
    and a 'close'. The vol weight uses volatility known at DECISION time
    (shift(1)) so there is no look-ahead: the size for the bar held at t is set
    from volatility observed through t-1.
    """
    df = df.copy()
    ret = df["close"].pct_change()
    rv = realized_vol(ret, window)
    weight = (target_vol / rv).clip(upper=max_leverage)
    df["rv"] = rv
    df["weight"] = weight.shift(1)                 # size known one bar early
    df["position"] = df["position"] * df["weight"]  # risk-sized position
    return df
