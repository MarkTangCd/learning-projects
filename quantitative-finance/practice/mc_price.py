"""L1 practice: price a European call option WITHOUT stochastic calculus.

Three ideas, in code:

  1. price = discounted average payoff over many simulated futures
  2. the naive version needs a drift mu -- your forecast of the stock
  3. ...and the answer changes wildly with mu, which is the whole problem

The resolution (mu := r, the risk-free rate) is not an assumption about
investor psychology. It falls out of a replication argument -- that is L2.

Only dependency is numpy. The normal CDF comes from math.erf so that the
Black-Scholes benchmark needs no scipy.

Usage:
    python mc_price.py bs                 # closed-form benchmark
    python mc_price.py mc [MU]            # one Monte Carlo price
    python mc_price.py drift              # THE EXPERIMENT: sweep mu
    python mc_price.py converge           # MC -> BS as paths grow
"""

import math
import sys

import numpy as np

# ---------------------------------------------------------------------------
# The contract we are pricing, fixed across every command so numbers compare.
# A European CALL: the right (not obligation) to buy 1 share at K on date T.
# ---------------------------------------------------------------------------
S0 = 100.0     # spot price today
K = 100.0      # strike price
T = 1.0        # years to expiry
R = 0.05       # risk-free rate (continuously compounded)
SIGMA = 0.20   # annualized volatility of the stock
SEED = 42      # fixed so your run reproduces the lesson's numbers exactly


def terminal_prices(mu, n_paths, rng):
    """Simulate n_paths possible values of the stock at time T.

    The model is Geometric Brownian Motion. One line, and every piece of it
    is something you can name:

        S_T = S0 * exp( (mu - sigma^2/2) * T  +  sigma * sqrt(T) * Z )
                          ^^^^^^^^^^^^^         ^^^^^^^^^^^^^^^^^^^^^
                          where the middle          the spread around it
                          of the cloud sits         (Z is standard normal)

    That -sigma^2/2 is not decoration. It is the SAME volatility drag you
    measured empirically in the trading course (learning record 0025):
    geometric return = arithmetic return - sigma^2/2. Here it is the
    correction that makes E[S_T] come out to exactly S0 * exp(mu * T).
    """
    z = rng.standard_normal(n_paths)
    return S0 * np.exp((mu - 0.5 * SIGMA**2) * T + SIGMA * math.sqrt(T) * z)


def mc_call_price(mu, n_paths=200_000, seed=SEED):
    """Monte Carlo price of the European call. Returns (price, std_error).

    Three steps, no calculus:
      1. simulate where the stock could end up
      2. compute what the option pays in each of those futures
      3. average, then discount that average back to today
    """
    rng = np.random.default_rng(seed)
    s_t = terminal_prices(mu, n_paths, rng)
    payoff = np.maximum(s_t - K, 0.0)        # a call pays only if S_T > K
    discounted = math.exp(-R * T) * payoff   # money at T is worth less today
    price = discounted.mean()
    std_err = discounted.std(ddof=1) / math.sqrt(n_paths)
    return price, std_err


def norm_cdf(x):
    """P(Z <= x) for a standard normal, via the error function in stdlib."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def bs_call_price():
    """Black-Scholes closed form. Used here ONLY as a benchmark to check
    the simulator against -- the formula itself is L3, not L1."""
    d1 = (math.log(S0 / K) + (R + 0.5 * SIGMA**2) * T) / (SIGMA * math.sqrt(T))
    d2 = d1 - SIGMA * math.sqrt(T)
    return S0 * norm_cdf(d1) - K * math.exp(-R * T) * norm_cdf(d2)


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_bs():
    print(f"contract: call  S0={S0}  K={K}  T={T}y  r={R}  sigma={SIGMA}")
    print(f"Black-Scholes price = {bs_call_price():.4f}")


def cmd_mc(argv):
    mu = float(argv[0]) if argv else R
    price, se = mc_call_price(mu)
    print(f"drift mu = {mu:+.2%}")
    print(f"MC price = {price:.4f}   (+/- {1.96 * se:.4f} at 95% confidence)")
    print(f"BS price = {bs_call_price():.4f}   <- benchmark")


def cmd_drift():
    """THE EXPERIMENT. Price the same option under different forecasts."""
    print("Same contract. Same volatility. Only my FORECAST of the stock changes.\n")
    print(f"{'my view (mu)':>14} | {'MC price':>9} | {'vs r=5% case':>13}")
    print("-" * 44)
    base, _ = mc_call_price(R)
    for mu in [-0.20, -0.10, 0.0, 0.05, 0.10, 0.20, 0.40]:
        price, _ = mc_call_price(mu)
        tag = "  <- mu = r" if abs(mu - R) < 1e-12 else ""
        print(f"{mu:>13.0%} | {price:>9.4f} | {price / base - 1:>+12.1%}{tag}")
    print()
    print(f"Black-Scholes (the price the market actually trades) = {bs_call_price():.4f}")
    print()
    print("Two bearish traders and two bullish traders would quote four different")
    print("prices for the identical contract. Markets do not work that way.")
    print("Notice WHICH row matches Black-Scholes -- that is the lesson.")


def cmd_converge():
    """Monte Carlo error shrinks like 1/sqrt(N): 100x paths, 10x accuracy."""
    exact = bs_call_price()
    print(f"target (Black-Scholes) = {exact:.4f}\n")
    print(f"{'paths':>10} | {'MC price':>9} | {'error':>8} | {'std err':>8}")
    print("-" * 44)
    for n in [100, 1_000, 10_000, 100_000, 1_000_000]:
        price, se = mc_call_price(R, n_paths=n)
        print(f"{n:>10,} | {price:>9.4f} | {price - exact:>+8.4f} | {se:>8.4f}")
    print()
    print("Error falls ~10x per 100x paths. Slow, but it works on ANY payoff --")
    print("including the exotic ones that have no closed-form formula at all.")


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "drift"
    rest = sys.argv[2:]
    if cmd == "bs":
        cmd_bs()
    elif cmd == "mc":
        cmd_mc(rest)
    elif cmd == "drift":
        cmd_drift()
    elif cmd == "converge":
        cmd_converge()
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
