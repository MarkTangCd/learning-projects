"""L5 -> L6 bridge experiment: does the param ranking survive a regime change?

Run the SAME three SMA param sets on TWO windows:
  - BULL: 400 daily bars from 2020-10-01 (the big BTC run-up)
  - Your earlier BEAR window is the most-recent 400 bars (fetch_ohlcv default)

If the "best" params differ between windows, then picking a winner on one
window is overfitting -- exactly why L6 needs out-of-sample validation.
"""

from backtest import backtest
from metrics import scorecard
from strategy import fetch_ohlcv, sma_crossover_signal

PARAMS = [(5, 20), (10, 30), (20, 60)]
WINDOWS = {
    "BULL 2020-10 -> ~2021": "2020-10-01",  # since date -> 400 bars forward
    "RECENT (default window)": None,         # most recent 400 bars
}


def run_window(name, since):
    price = fetch_ohlcv(since=since)  # fetch once per window
    start, end = price.index[0].date(), price.index[-1].date()
    print(f"\n########## {name}  [{start} -> {end}] ##########")
    for fast, slow in PARAMS:
        df = backtest(sma_crossover_signal(price, fast=fast, slow=slow))
        scorecard(df, f"SMA({fast},{slow})")


if __name__ == "__main__":
    for name, since in WINDOWS.items():
        run_window(name, since)
