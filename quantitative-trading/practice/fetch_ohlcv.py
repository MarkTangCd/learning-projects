"""L2 practice: pull real BTC/USDT candles into a clean pandas DataFrame."""

import ccxt
import pandas as pd

# Local proxy (Clash/V2Ray etc.). ccxt's requests backend does NOT read the
# proxy from .zshrc automatically — we must pass it explicitly here.
PROXY = "http://127.0.0.1:1087"

# 1) Pick an exchange. No API key needed for public market data.
exchange = ccxt.binance({"timeout": 30000})
exchange.httpsProxy = PROXY   # ccxt allows only ONE proxy setting — HTTPS only
# If a given exchange still won't connect, try another:
#   exchange = ccxt.kraken({"timeout": 30000})     # then set the two proxies again
#   exchange = ccxt.coinbase({"timeout": 30000})   # use symbol "BTC/USD" below

# 2) Fetch OHLCV candles: symbol, timeframe, how many.
#    Returns a list of [timestamp, open, high, low, close, volume].
raw = exchange.fetch_ohlcv("BTC/USDT", timeframe="1d", limit=90)

# 3) Load into a pandas DataFrame — a labeled table.
df = pd.DataFrame(raw, columns=["ts", "open", "high", "low", "close", "volume"])
df["range"] = df["high"] - df["low"]
# 4) The timestamp is Unix milliseconds. Turn it into real UTC datetimes,
#    then make it the row index so every row is stamped in time.
df["ts"] = pd.to_datetime(df["ts"], unit="ms", utc=True)
df = df.set_index("ts")

print(df.tail())          # last 5 rows
print(df.shape)           # (rows, columns
print(df["range"].describe())

# ---- Cleaning checks (should be: 0 duplicates, True for monotonic) ----
print("duplicates:", df.index.duplicated().sum())
print("monotonic:", df.index.is_monotonic_increasing)

# 1) 两条均线
df["sma_fast"] = df["close"].rolling(10).mean()
df["sma_slow"] = df["close"].rolling(30).mean()

# 2) 原始信号:快线在慢线之上 → 想持有(1),否则空仓(0)
df["signal"] = (df["sma_fast"] > df["sma_slow"]).astype(int)

# 3) 关键一步:把信号后移一根,才是"能真正执行"的仓位
df["position"] = df["signal"].shift(1)

print(df[["close","sma_fast","sma_slow","signal","position"]].tail(10))

# 数一数:一共给出了多少次"进场"(从空仓变持有)?
entries = ((df["position"] == 1) & (df["position"].shift(1) == 0)).sum()
print("进场次数:", entries)

# ---- Challenge (uncomment and try) ----
# df["range"] = df["high"] - df["low"]
# print(df["range"].describe())
