# Practice — 代码练习区

课程配套的动手代码都放这里。每节课一个(或几个)脚本。

## 一次性设置(首次)

```bash
cd /Users/marktang/learning-projects/quantitative-trading/practice
python -m venv venv          # 建虚拟环境
source venv/bin/activate     # 激活(zsh)—— 命令行前会出现 (venv)
pip install ccxt pandas      # 装依赖
```

## 以后每次写代码前

```bash
cd /Users/marktang/learning-projects/quantitative-trading/practice
source venv/bin/activate     # 每开一个新终端都要先激活
```

## 运行

```bash
python fetch_ohlcv.py
```

## 脚本清单
- `fetch_ohlcv.py` — L2:拉真实 BTC/USDT K 线,清洗成 pandas 表。
- `strategy.py` — L3:SMA 均线交叉信号,输出 position 列(含防前视偏差的 shift)。
  (原名 signal.py;`signal` 与 Python 标准库同名会冲突,故改名。)
- `backtest.py` — L4:向量化回测,含成本,对比买入持有。复用 strategy.py。
