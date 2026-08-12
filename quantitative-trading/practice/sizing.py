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

from trading_calendar import bars_per_year_of

PERIODS_PER_YEAR = 365   # crypto daily. NO LONGER THE DEFAULT (L23) — kept as a
                         # name for scripts that deliberately force this calendar.


def realized_vol(returns, window=20, periods_per_year=None):
    """Annualized rolling realized volatility from per-bar returns.

    periods_per_year=None INFERS the calendar from the series' DatetimeIndex.
    The old 365 default did damage here OPPOSITE in sign to the one it did to
    Sharpe: P sits in the numerator of rv, but rv sits in the DENOMINATOR of
    weight = target_vol / rv. So on stocks it over-stated vol by +20.4% and
    therefore UNDER-SIZED every position by 17.0% (measured: `stocks.py size`).
    Sharpe reads too high while the machine actually bets too small — and
    because a constant scaling cancels in mean/std, the under-sizing is
    INVISIBLE in the Sharpe you would use to spot it.
    """
    ann = bars_per_year_of(returns, periods_per_year) ** 0.5
    return returns.rolling(window).std() * ann


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


def vol_target_weight(returns, target_vol=0.20, window=20, max_leverage=1.0):
    """Scalar vol-target weight from the LAST CLOSED bar — the live form of
    vol_target_position for the runner. Uses realized vol through the last
    closed bar to size the position held next (no look-ahead when live).
    max_leverage defaults to 1.0: SPOT cannot lever; the perp venue could."""
    rv = realized_vol(returns, window)
    w = (target_vol / rv).clip(upper=max_leverage)
    return float(w.iloc[-1])
