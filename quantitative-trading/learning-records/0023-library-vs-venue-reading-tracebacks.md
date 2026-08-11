# 0023 — 库的报错 ≠ 场子的报错:按 traceback 的落点分诊

- **日期**: 2026-08-11
- **触发**: L20 `python perp.py balance` 抛 `ccxt.base.errors.NotSupported: binanceusdm testnet/sandbox mode is not supported for futures anymore`
- **状态**: 已解决(`perp.py::connect()` 加 `options={"disableFuturesSandboxWarning": True}`)

## 发生了什么

ccxt 4.5.x 在 `binance.sign()` 里硬编码了一条拒绝:凡是 URL 命中 `testnet.binancefuture.com`
且开了 sandbox,就直接 `raise NotSupported`。理由是币安官方把期货测试网标记为弃用、改推
demo.binance.com 的 Demo Trading。

但**场子本身没死**。直接 curl 验证:`GET testnet.binancefuture.com/fapi/v1/ping` → 200,
`ticker/price` 正常返回 BTCUSDT 报价。也就是说:**下线的是库的支持,不是服务**。

ccxt 留了逃生开关(源码 `binance.py:11739` 的判断条件里):
`options={"disableFuturesSandboxWarning": True}` → 恢复原来的通路,其余代码一行不改。

## 非显然的教训(本条记录的真正内容)

**看 traceback 的最后一帧停在哪一层,决定了排查方向。**

| 最后一帧 | 含义 | 该查什么 |
|---|---|---|
| `sign()` / 参数校验 | 请求**根本没发出去**,是库的策略或你的用法 | 库版本、changelog、options 开关 |
| `handle_errors()` 且带 `{"code":-2014,...}` | 交易所**真的回话了** | 密钥、权限、IP 白名单、参数、余额 |

这次的 traceback 里**没有任何一帧是网络 IO**——`fetch2` → `sign` 就炸了。这本身就是
"服务可能好好的"的证据。修完后用假密钥复跑,报错变成 `{"code":-2014,"msg":"API-key format
invalid."}`,落点从 `sign()` 变成 `handle_errors()`——**这就是"通道打通了"的验收信号**,
而不是"又一个错"。

推论:**验证依赖是否真的挂了,绕过库直接打一次 HTTP**。库是一层带观点的中间人,它的
"不支持"只是它的意见。

## 迁移路径(如果 testnet 哪天真的关停)

去掉 `set_sandbox_mode(True)`,去 demo.binance.com 生成密钥,改用
`ex.enable_demo_trading(True)`(ccxt 已内置,走 `demo-fapi.binance.com`)。其余代码不动。
注意两者互斥:sandbox 开着时调 `enable_demo_trading` 会直接报错。

## 关联

- 课程: [L20 perp 测试网原生做空](../lessons/0020-perp-testnet-native-short.html)
- 前置: [0009 执行与风控](../lessons/0009-execution-and-risk.html) 的"永不假设——发出 → 回读 → 对账"
  在这里升级为:**连报错也要回读到底是谁在说话**。
