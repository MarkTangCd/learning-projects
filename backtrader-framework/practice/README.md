# practice — backtrader 课程动手区

## 环境

独立 venv,与隔壁 `quantitative-trading/practice/venv` 分开(避免 backtrader 的老依赖
污染那边已经跑通的栈)。

```
Python      3.14.2
backtrader  1.9.78.123   # 官方最后一版,2023-04-19
pandas      3.0.5
numpy       2.5.2
matplotlib  3.11.1
ccxt        4.5.73
yfinance    1.5.2
```

实测结论:**这套组合端到端跑通,含 `cerebro.plot()`,不需要打补丁。**
(老教程常说 backtrader 在新版 matplotlib 上绘图会炸——在 3.11.1 上实测没炸。)

## 用法

```bash
cd ~/learning-projects/backtrader-framework/practice

./venv/bin/python l01_first_run.py data     # 拉数据并缓存到 data/*.csv
./venv/bin/python l01_first_run.py run      # 八件套完整回测(主命令)
./venv/bin/python l01_first_run.py fill     # 实验:订单在哪根 bar、什么价成交
./venv/bin/python l01_first_run.py sharpe   # 实验:三个都叫 Sharpe 的数
```

`data` 只需跑一次,之后从 CSV 读,可离线。BTC 走 ccxt(**需要本地代理
`http://127.0.0.1:1087` 开着**),SPY 走 yfinance。

## 重建 venv

```bash
python3 -m venv venv
./venv/bin/pip install backtrader pandas numpy matplotlib ccxt yfinance
```

## 文件

| 文件 | 课 | 内容 |
|---|---|---|
| `l01_first_run.py` | L1 | Cerebro 八件套 + 成交时点实验 + Sharpe 默认值实验 |
| `data/*.csv` | — | 缓存的行情,git 忽略 |
