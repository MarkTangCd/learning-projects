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
9. ✅ L9 真实执行与风控:订单生命周期(open/closed/canceled/partial/rejected)、ccxt 统一订单结构、SEND→READ BACK→RECONCILE、限价 vs 市价/maker-taker、风控闸门(名义上限/最小额)+ 急停 kill switch、testnet(set_sandbox_mode)。脚本 `practice/execution.py`(balance/rest/fill/kill/unkill),参考卡 `execution-recipe.html`,词表 +8 词 ← **已跑通**(挑战③④⑤全过,见 [[0009-execution-lifecycle-on-testnet]])
   - 已验证坑:ccxt 4.5.70 sandbox 仍指 testnet.binance.vision(demo-api.binance.com 也通);两端点公开接口经代理均可达;key 须与端点匹配否则 Invalid API-key。
   - **测试网撒谎两处**(动手抓到):(a)市价单滑点 +0.0 bps —— 合成盘口,测试网测不出真实滑点;(b)手续费在 fills 不在订单头 —— `fetch_order` 的 `fee` 对 Binance 常为 None,须 `fetch_order_trades` 聚合。已补 `fee_from_trades()`。结论:testnet 验代码正确性,不验成本假设准确性。
10. ✅ L10 幂等下单:异步写+超时=双倍单风险;幂等钥匙=意图纯函数(非时钟);超时先 fetch_order 再同 cid 兜底重发。抓到 L9 脚本"假幂等"真 bug(cid 用毫秒时间戳→重试不去重);修 `intent_cid()` + 加 `dup` 命令。首选源 Stripe idempotent-requests ← **已跑通**(dup 挑战通过,见 [[0010-idempotent-orders-verified]])
    - 用户选了路线 **C(先补执行细节)**,L10-L11 为其内容。
11. ✅ L11 部分成交:filled vs intended(账本记事实)、等/撤/追三选一、撤单/成交竞态(撤单也要回读)、TIF(GTC/IOC/FOK)、IOC 原子撤剩余=无竞态、有界追单(IOC 阶梯 -5/0/+5bps + 市价兜底、每腿独立 cid、每腿过闸门)、急迫成本(VWAP vs ref)。`chase` 命令 + recipe 追单块 + 词表 +4(部分成交/TIF/追单/撤单成交竞态)。首选源 Binance enums + freqtrade unfilledtimeout ← **已跑通**(chase + 急停③ 全过,见 [[0011-partial-fills-and-chase-loop]])。抓修真 bug:残量=0 时 `amount_to_precision` 抛 InvalidOrder(边界住在成功路径终点)→ 改为裸数字先判 min_amount。**执行层四件套(生命周期/风控/幂等/部分成交)到此集齐,路线 C 完成。**
12. ✅ L12 均值回归(第二信号族):趋势 vs 回归=相反赌注、regime 决定谁对;z-score 标准化;ffill 状态机(无循环持仓);gauntlet 白捡复用(同 position 接口)。诚实框架:单窗=冒烟测试非判决,lookback/entry=新过拟合面。`strategy.py` +`zscore_reversion_signal`(离线验证过状态机)+`reversion.py` 三方对比。词表 +5。首选源 Chan《Algorithmic Trading》ch2 + QuantStart。← 用户选了**路线 A**;已发布,待用户跑 `reversion.py` 贴三张成绩单。见 [[0012-second-signal-family-mean-reversion]]
    - **L12 动手结果(2026-08-08)**:熊市窗口全员负夏普/全亏;用户三次运行把夏普 −0.83→−0.58,**亲手在单窗口调出过拟合**(本课最值钱体验)。见 [[0013-l12-results-overfitting-felt-on-one-window]]。
13. ✅ L13 均值回归过 walk-forward gauntlet:拆"手挑参数进样本外"陷阱(walk-forward 每窗自选参、人不碰);换信号裁判台一行不改(build_folds/score/sharpe_key 原样 import,只换 RGRID + 信号调用)=L1 接口红利第三次兑现;判决三态(跑输躺平/险胜漂移大/稳赢参数稳);参数漂移读法。`walkforward_reversion.py`(端到端离线验过)。首选源 QuantStart Successful Backtesting + Chan。← 已发布,待用户跑贴输出。
    - **L13 判决(2026-08-09)**:均值回归**跑赢**躺平(Sharpe −0.18 vs −0.28,MaxDD −46% vs −67%)——课程首个非躺平!但夏普仍负=**下跌保护非独立 edge**;fold 5(反弹)输躺平=软肋在单边上涨。参数漂移 4/7 黄灯(lb 20→30 有结构)。见 [[0014-mean-reversion-verdict-downside-protection-not-edge]]。用户选 **A regime 过滤**。
14. ✅ L14 regime 过滤:ER(效率比)检测趋势/震荡→路由 SMA/回归;组合=路由器照样吐 position(gauntlet 复用第4次);核心纪律=奥卡姆剃刀(6 旋钮大过拟合面,钉死子信号只调 regime,组合须样本外打赢零件单飞)。`strategy.py`+efficiency_ratio/regime_switch_signal(离线验路由),`walkforward_regime.py`(三行并排比,端到端跑通)。首选源 QuantStart HMM + Chan。← 已发布,待用户跑贴输出。判据:组合 Sharpe 须 > −0.18 且看 fold 5 是否被扳回。见 [[0015-regime-filter-built]]。
14b. **L14 判决(2026-08-10)**:regime 组合**成立**——OOS Sharpe −0.02 > 回归单飞 −0.18 > 躺平 −0.28,fold 5 从输 2.0 补到只差 0.04(命门被扳回)。但两条 caveat:Sharpe 仍 ≈0(非正 edge,是"基本不亏");**参数漂移变差 5/7**(6 旋钮警告兑现)。用户选**路线 B → 换资产复现**。见 [[0016-l14-verdict-regime-combo-beats-parts-but-drift-worse]]。
15. ✅ L15 稳健性/换资产复现:冻结机器(GGRID/RGRID FROZEN)搬到 ETH,只改 symbol 一个字符串(L1 红利第 5 次);核心纪律=**不许为新资产重调参**(否则过拟合 asset #2);读法=**看形状不看数字**(相对排名保持 vs 破)。首选源 López de Prado《Pseudo-Mathematics and Financial Charlatanism》(回测过拟合/多重检验)+ QuantStart Successful Backtesting。`walkforward_robust.py`(symbol 走 argv,三行并排 组合/回归单飞/躺平 + 形状判决 + 漂移)。词表 +5(稳健性检验/形状判决/多重检验/回测过拟合)。← **已发布**。**老师已跑 ETH:形状保持**(组合 −0.25 > 回归 −0.40 > 躺平 −0.30,漂移 regime 5/7、回归 4/7)——互补关系不是 BTC 独有。待用户自跑 BTC 锚点 + SOL 试金石(先预测后验证)贴输出。见 [[0016-l14-verdict-regime-combo-beats-parts-but-drift-worse]]。
15b. **L15 判决(2026-08-10)**:换资产复现(BTC/ETH/SOL,冻结机器)。**下跌保护身份三资产全泛化**(少亏+回撤更浅,连 SOL −94% 都成立)=非 BTC 过拟合;但**"夏普 edge"没泛化**(SOL 夏普翻车),且三资产夏普全 ≤ 0。元教训:别信脚本 Sharpe-only 的"形状破了",**读全三列**。根因锁定=**所有信号只做多**。用户选 **A 引入做空**。见 [[0017-l15-robustness-verdict-protection-generalizes-sharpe-edge-doesnt]]。
16. ✅ L16 引入做空(打穿 long-only 天花板):position 放开到 {−1,0,+1};回测**零改**天生支持(`position*ret` 自动取反 + `diff().abs()` 双倍换手 = L1 红利第 6 次);唯一诚实新增=**资金费率 funding**(perp 持仓碳税,`|position|*funding`);信号加 `long_short` 开关(默认 False 保证旧课逐字复现,已验证)。`strategy.py`/`backtest.py`/`walkforward_shorts.py`。词表 +6。首选源 Binance Funding Rates + Chan long-short。← **已发布 + 老师已跑**:**BTC 双边 Sharpe +0.12 = 全课首个正样本外夏普**,回撤最浅;但 funding 3bp/天就归零(edge 薄),ETH 双边反而更差(空头被扫损),SOL 夏普改善但回撤更深 → **做空能打穿天花板但不免费、不泛化**。见 [[0018-l16-shorting-breaks-ceiling-on-btc-but-not-free]]。
16b. **L16 挑战完成(2026-08-10)**:用户亲跑 funding 三档确认。**BTC 双边 +0.12 = 全课首个正样本外夏普**但薄(3bp→+0.01);funding 对双边单调惩罚(ETH/SOL 越加越差)。合并六课结论=crypto 日线上只抠得出"下跌保护+薄做空 edge",信号研究边际递减。用户选 **接执行层跑纸上交易**。见 [[0018-l16-shorting-breaks-ceiling-on-btc-but-not-free]]。
17. ✅ L17 闭环(capstone / 使命里程碑):`strategy_runner.py` 一次 tick 串起 L12–L16 信号 + L8 三纪律 + L9 闸门 + L10 幂等(cid 绑 bar)+ L11 回读对账 + 账本记实成。**诚实边界**:现货测试网不能做空 → 桥先 long/flat,双边(做空)需 perp 测试网(接 L16 funding,留后课);**纸上交易验管路非验 edge,分开别混**。复用 execution.py + strategy.py;`--target` 覆盖逼管路点火,`--reset` 清账本。离线自检 brain 路径 OK(信号当前 target=0)。词表 +3。首选源 freqtrade dry-run + ccxt orders。← **已发布**,待用户用 L9 testnet 密钥实跑 ①点火 ③平仓 ⑤拒单 贴输出。见 [[0019-l17-loop-closed-signal-drives-execution]]。
17b. **L17 挑战完成(2026-08-10)**:①③⑤全绿 —— 开仓/平仓/急停拒单都在真实撮合上跑通,**闭环验证 = 使命"回测→纸上交易"打勾**。抓到并修掉一个 tz-naive vs tz-aware 比较 bug(只有活循环暴露,回测撞不到)。见 [[0019-l17-loop-closed-signal-drives-execution]]。用户选 **仓位管理**。
18. ✅ L18 仓位管理(波动率目标定量):`weight=target_vol/realized_vol` 截断杠杆;**vol 目标=风险旋钮,不改 edge**(拧目标 Sharpe≈不动 0.35,回撤/收益同步缩放);按**能扛的最大回撤**反推目标非最大 CAGR;edge 薄→保守下注,全 Kelly 危险。纯叠加 position 列不碰信号(L1 接口第 7 次)。`sizing.py`+`sizing_compare.py`;真实跑:vol 定量把 BTC 双边回撤 −59%→−25%@20%、Sharpe 微升、CAGR 反升(少被波动率拖累)。词表 +4。首选源 López de Prado AFML Bet Sizing + QuantStart Kelly。← **已发布 + 老师已跑**,待用户跑三档 + 回答"目标定几"。见 [[0020-l18-position-sizing-vol-targeting]]。
18b. **L18 挑战完成(2026-08-10)**:用户 vol 目标选 30%(理由=30% 回撤不会逼我手动干预,锚点满分)。修正:**vol 目标≠MaxDD**(30% 目标实测 −36% 回撤),要回撤落 30% 目标≈25%;且未来>回测,守红线应留缓冲→建议 20–22%。用户选 **vol 定量接进 runner**。见 [[0020-l18-position-sizing-vol-targeting]]。
19. ✅ L19 vol 定量接进 runner(系统集成):单量=signal×weight×配给资本,weight=vol目标/当下波动,硬编码 $20 消失。三新决定:①**向目标再平衡**(非翻转 0/1;持仓中波动涨就减仓=削回撤发动机)②**不动区间**(差额<最小额不动,防 churn)③对**配给资本**($40)下注非全部身家(单量落 L9 闸门内,闸门硬后备)。现货天花板:权重截到 1.0,高 vol 目标要上 perp 杠杆。`sizing.py`+`vol_target_weight`,`strategy_runner.py` 重写(`--vol`/`--target`/`--reset`)。离线自检 OK。词表 +4。首选源 Rob Carver《Systematic Trading》。← **已发布**,待用户跑 ①`--reset --target 1 --vol 0.22` ③`--vol 0.10 vs 0.30` 贴输出。见 [[0021-l19-sizing-wired-into-runner]]。
20. 判决后岔路:①**perp 测试网**(双边+杠杆+实测 funding,收敛 L16/L18/L19 现货落不了地的部分)= 老师首选;②循环攒按真实风险下注的 track record;③多资产 vol 标准化合仓;④**掉头股票赛道**。
