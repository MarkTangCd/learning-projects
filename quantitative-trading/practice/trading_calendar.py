"""L23: how many bars are there in a year? MEASURE it, don't assume it.

Every lesson from L5 to L22 carried `BARS_PER_YEAR = 365`, correct for crypto
(7x24) and wrong by sqrt(365/252) = 1.204 on stocks. That constant never raised
— it just inflated every Sharpe by 20.4% and shrank every vol-targeted position
by 17.0%. A wrong constant that cannot crash is worse than one that can.

The fix is NOT to hardcode 252 instead (that only moves the bug to crypto). It
is to infer the calendar from the data's own index. Three things matter:

1. COUNT BARS, DON'T MEASURE SPACING. A stock daily bar is one day apart, same
   as a crypto daily bar — measuring the interval returns 365 for BOTH. What
   differs is that 113 of those days do not exist. Annualization needs the
   number of OBSERVATIONS per year, so: bars / years spanned.

2. SNAP TO A KNOWN CALENDAR. The raw estimate wobbles with the window (a
   90-bar walk-forward fold measures 240-264 for a market that trades 252).
   Returning the raw float would give each fold a slightly different divisor
   and make fold Sharpes non-comparable. Snapping returns one canonical int.
   It also keeps crypto results byte-identical to L5-L22: 365.25 -> 365.

3. REJECT, NEVER GUESS. Auto-inference does not remove the silent-failure mode
   — it relocates it. A 6-month hole in the data (a splice, a halt, a failed
   download) drops the SPY estimate to 209.9, a -16.7% error of exactly the
   kind we are fixing, and just as quiet. Anything that matches no known
   calendar within tolerance raises. So does a non-datetime index.
"""

import pandas as pd

DAYS_PER_YEAR = 365.25          # calendar year incl. leap, for span -> years

# Only calendars this workspace can actually produce. Keep the list SHORT: every
# extra candidate widens the net and weakens requirement 3 (reject, never guess).
KNOWN_CALENDARS = {
    365:  "crypto 日线(7x24)",
    2190: "crypto 4h",
    8760: "crypto 1h",
    252:  "股票日线(美股)",
    1638: "股票 1h(6.5h x 252)",
}

# 10% clears the real wobble with room to spare: a 90-bar walk-forward fold on
# SPY measures 244-258 (±3.0%), a 63-bar one 236-260 (±6.4%). Tightening to 5%
# would start rejecting honest short folds.
TOLERANCE = 0.10
MIN_BARS = 30                   # below this the estimate is noise, not measurement
# A hole in the data dilutes bars/span only in proportion to how much of the
# span it eats — a 6-month gap inside 4 years moves the estimate ~10%, which
# TOLERANCE alone lets through. Spacing catches holes directly instead: SPY's
# widest honest gap is 4 days (Christmas/July-4 weekends) = 4x its 1-day median,
# crypto's is 1x. 10x leaves margin for a real halt and still traps a hole.
MAX_GAP_RATIO = 10


def _check_no_holes(index):
    """Guard the ESTIMATOR's own blind spot: a gap it would silently absorb."""
    spacing = index.to_series().diff().dropna()
    if spacing.empty:
        return
    median, widest = spacing.median(), spacing.max()
    if median > pd.Timedelta(0) and widest / median > MAX_GAP_RATIO:
        at = index[spacing.values.argmax() + 1]
        raise ValueError(
            f"数据里有洞:相邻 bar 最大间隔 {widest} (中位 {median} 的 "
            f"{widest / median:.0f} 倍),出现在 {at.date()} 之前。\n"
            "  缺口会稀释 bar数/跨度 这个估计,而且缺口越小于总跨度、稀释越隐蔽 —— "
            "光靠容差抓不住。\n"
            "  先补数据或截掉缺口那一段;确实是正常长休市就调高 MAX_GAP_RATIO。")


def raw_bars_per_year(index):
    """Unsnapped estimate: bars per calendar year, measured from the index.

    Uses len-1 over the span because the span covers n-1 intervals, not n. Skip
    that and a 63-bar window reads 256 instead of 252 — a 1.6% fencepost bias
    that grows as the window shrinks (63/62 = 1.016).
    """
    if not isinstance(index, pd.DatetimeIndex):
        raise TypeError(
            f"无法推断日历:索引是 {type(index).__name__},不是 DatetimeIndex。"
            " 显式传入 bars_per_year,或者修好上游的索引 —— 绝不静默退回 365。")
    if len(index) < MIN_BARS:
        raise ValueError(f"只有 {len(index)} 根 bar,不足 {MIN_BARS} 根,推断不出日历。")
    span_days = (index[-1] - index[0]).total_seconds() / 86400
    if span_days <= 0:
        raise ValueError("索引跨度为 0 —— 数据只有一个时点,或者索引没排序。")
    _check_no_holes(index)
    return (len(index) - 1) / (span_days / DAYS_PER_YEAR)


def infer_bars_per_year(index):
    """Measure the calendar from `index` and snap it to a known one, or raise."""
    raw = raw_bars_per_year(index)
    best = min(KNOWN_CALENDARS, key=lambda k: abs(raw / k - 1))
    if abs(raw / best - 1) > TOLERANCE:
        known = ", ".join(f"{k}({v})" for k, v in sorted(KNOWN_CALENDARS.items()))
        raise ValueError(
            f"实测 {raw:.1f} bar/年,离每一个已知日历都超过 {TOLERANCE:.0%}"
            f"(最近的是 {best})。已知:{known}。\n"
            "  最常见的原因不是「新市场」,而是【数据有洞】:拼接过的序列、长期停牌、"
            "下载中断 —— 缺口拉长了跨度而 bar 数不变,估计值就会塌下来。\n"
            "  先去查数据;确实是新市场就把它加进 KNOWN_CALENDARS。")
    return best


def bars_per_year_of(obj, override=None):
    """Resolve the annualization constant for a Series/DataFrame/DatetimeIndex.

    `override` short-circuits inference — that is how stocks.py runs the same
    strategy under both calendars to measure the damage on purpose.
    """
    if override is not None:
        return override
    return infer_bars_per_year(obj if isinstance(obj, pd.DatetimeIndex) else obj.index)


def describe(index):
    """One-line human summary — useful when a script should SHOW its calendar."""
    raw = raw_bars_per_year(index)
    snapped = infer_bars_per_year(index)
    return f"实测 {raw:.1f} bar/年 -> {snapped}({KNOWN_CALENDARS[snapped]})"


if __name__ == "__main__":
    print("日历推断自检\n")
    cases = [
        ("crypto 日线", pd.date_range("2021-01-01", periods=1000, freq="D")),
        ("crypto 4h", pd.date_range("2021-01-01", periods=1000, freq="4h")),
        ("crypto 1h", pd.date_range("2021-01-01", periods=1000, freq="h")),
        ("股票日线", pd.bdate_range("2015-01-01", periods=2000)),
    ]
    for label, idx in cases:
        print(f"  {label:<14}{describe(idx)}")

    print("\n  应该抛异常的:")
    bad = pd.bdate_range("2015-01-01", periods=500).append(
        pd.bdate_range("2017-06-01", periods=500))    # 中间真的缺了半年(无重叠)
    for label, thunk in (
            ("数据有 6 个月缺口", lambda: infer_bars_per_year(bad)),
            ("整数索引", lambda: infer_bars_per_year(pd.RangeIndex(500))),
            ("bar 数太少", lambda: infer_bars_per_year(pd.date_range("2021-01-01", periods=5))),
    ):
        try:
            thunk()
            print(f"  {label:<20}-> 没抛 —— 这是个 bug")
        except (TypeError, ValueError) as e:
            print(f"  {label:<20}-> {type(e).__name__}: {str(e).splitlines()[0]}")
