# NOTES — 教学工作笔记

## 用户画像(2026-08-01 建立)
- 核心目标:**构建交易系统**(工程导向,非求职、非纯理论)
- 技术背景:会编程;数学一般(统计/概率/线代需边学边补)
- 切入方向:**Crypto 优先**,后续 → 传统股票 → AI 量化
- 编辑器 Cursor;终端 zsh;偏好 async/await;2 空格缩进;camelCase / UPPER_SNAKE_CASE

## 教学偏好
- 中文讲解,代码/注释用英文
- 解释简洁直接,不铺垫
- 每节课:短、单一目标、可快速完成、有一个"看得见的胜利"
- 工程导向:能动手就动手,少空谈

## 已确认(2026-08-01)
- 主力语言:**Python 熟练**;但**没用过 pandas** → 数据分析库需边用边教(从 L2 起顺带 pandas 入门)。
- **网络/代理**:用户走本地代理 **`http://127.0.0.1:1087`**(Clash/V2Ray 类)。Python 的 requests 不认 .zshrc 里的代理 → **所有拉数据脚本必须在 ccxt 里显式设代理**:`exchange.httpsProxy = "http://127.0.0.1:1087"`(只设一个,设 httpProxy+httpsProxy 会报 InvalidProxySettings)。配上代理后 **binance 可用**,无需换所。

## 待确认
- 学习节奏 / 每周可投入时间?

## 课程路线(草案,随进展修订)
1. ✅ L1 量化系统解剖(五段式流水线心智模型)
2. ✅ L2 Crypto 数据管道:用 CCXT 拉真实行情(已跑通,含代理排障)
3. ✅ L3 第一个信号 + pandas 计算(SMA 交叉,含 shift 防前视偏差)
4. ✅ L4 诚实的回测:收益−成本(手续费/滑点),向量化 equity 曲线
5. ✅ L5 读懂成绩单:最大回撤 / 夏普 / CAGR,首点过拟合
6. ✅ L6 样本外验证:train/test 切分、数据泄漏/窥探、过拟合税
7. ✅ L7 滚动前进验证(walk-forward):拼接样本外曲线、参数漂移
8. ✅ L8 纸上交易:tick 事件循环、三纪律 + 收尾压力测试(抓到并修掉"时间戳倒退误成交"+"账本不分周期串味"两 bug;闸门改比时间序、state 按 tf 命名空间)← 完成
9. ✅ L9 真实执行与风控:订单生命周期(open/closed/canceled/partial/rejected)、ccxt 统一订单结构、SEND→READ BACK→RECONCILE、限价 vs 市价/maker-taker、风控闸门(名义上限/最小额)+ 急停 kill switch、testnet(set_sandbox_mode)。脚本 `practice/execution.py`(balance/rest/fill/kill/unkill),参考卡 `execution-recipe.html`,词表 +8 词 ← 已发布,待用户拿 testnet key 跑动手挑战
   - 已验证坑:ccxt 4.5.70 sandbox 仍指 testnet.binance.vision(demo-api.binance.com 也通);两端点公开接口经代理均可达;key 须与端点匹配否则 Invalid API-key。
10. 小资金实盘(paper/testnet 稳定后)← 下一课候选 A
11. (扩展)传统股票 / AI 量化;或回 gauntlet 给信号找 edge(regime 过滤/均值回归)← 候选 B
10. Paper trading 稳定后 → 小资金实盘
11. (扩展)传统股票 / AI 量化(SMA 单族无 edge → 待引入均值回归/波动率过滤/regime 过滤等第二类信号,复用 gauntlet)
