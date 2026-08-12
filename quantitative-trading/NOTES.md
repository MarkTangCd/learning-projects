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
19b. **L19 挑战完成(2026-08-10)**:三档全绿。①0.22→敞口$35买;②0.10→敞口$16**卖**(信号仍做多却下卖单=削回撤发动机由手动拧旋钮触发,证"再平衡≠翻转0/1");③0.30→权重1.2**截到1.0**、敞口顶格$40(现货天花板确证)。里程碑=风控从"事后闸门"升"事前定量"。见 [[0021-l19-sizing-wired-into-runner]]。**待用户选下一岔路(见 20)。**
20. 用户选 **perp 测试网**(老师首选)。拆成三课避免撑爆工作记忆:L20=换 venue+原生做空(隔离摸熟,L9 风格);L21=杠杆;L22=焊进 runner+真 funding。
20a. ✅ L20 换 perp 测试网 · 第一张原生空单:单一胜利=开负持仓(现货物理做不到)。心智切换"我有多少币"→"持仓正/负";flat 时 SELL=开空;平仓=反方向+`reduceOnly`(平空=买)。三新:新 venue+**新密钥**(testnet.binancefuture.com,binanceusdm,与现货两套)、抵押 USDT 不持币、**最小名义 $50**(现货 ~$5)→ 闸门重标定 $200。funding 从 L16 模拟变**真**(本课只预览)。**关键伏笔**:min $50 > 配给 $40 → **杠杆是小账户 perp 下单的前提**(=L21 入口)。新文件 `perp.py`(balance/funding/short/position/close),离线自检 OK。词表 +4。首选源 Binance USDⓈ-M Futures API + ccxt positions。← **已发布**,待用户生成 perp 密钥跑 ③short ⑤close 贴输出。见 [[0022-l20-perp-testnet-native-short]]。
21. 判决后岔路:①**L21 杠杆**(weight>1/set_leverage/保证金/强平价);②**L22 焊进 runner**(perp 接 strategy_runner,信号吐 −1,真 funding 8h 真扣,攒双边 track record);③掉头股票赛道。
21. ✅ L21 杠杆/保证金/强平:**核心反直觉命题=杠杆不是加速器**。恒等式 `杠杆=|名义|/起始保证金` 反读 → `保证金=名义/杠杆`,**杠杆只在保证金那一侧,不在盈亏公式里**;固定名义拧杠杆,每 $1 波动盈亏分毫不变(表 A 最后一列不动),变的只有被锁保证金 + 爆仓距离。杠杆买到的是①容量②爆仓距离,是**准入许可非加速器**。强平推导 `P=P₀(1+1/L)/(1+mmr)`(空),**q 被约掉 → 爆仓价与仓位大小无关**("大小决定伤害,杠杆决定死线");20x 逐仓 ≈4.6% 归零。全仓 vs 逐仓解释了用户实测那个 559 万爆仓价(crossWalletBalance 5000U 垫背)→ **爆仓价是「仓位+抵押品」的属性**。解开 L20 伏笔:$40 配给 1x 下不出单(<最小名义 $50),2x 起可以;**杠杆解除的是"名义≤本金"约束,该开多大仍由 L18 vol 目标决定**。危险点=杠杆让"开大仓"无痛 + **摩擦按名义收**($40 本金开 $800 名义,8bp 来回 = 本金的 160bp)。`perp.py` 新增 `lever [N]`(两张表 + 设置后回读)、`isolated_liq_price()`;词表 +4(杠杆/起始维持保证金率/强平价/全仓逐仓)。首选源 Binance Leverage&Margin FAQ + Change-Initial-Leverage API。← **已发布**,待用户跑 ①lever ④short+position(验 5.0x 且盈亏跳动不变) ⑤close(验 bp 不随杠杆变),并回答②的预测是否猜中。
   - **L20 收尾的两条 meta 教训**(见 [[0023]] [[0024]]):①ccxt 封了期货 testnet(报错在 `sign()` = 库不是场子,`disableFuturesSandboxWarning` 绕过);②**字段缺失≠信息缺失**——v3 不返回 leverage,用恒等式推;`breakEvenPrice` 反推已付开仓费。**我犯的错**:首版 close 只算单边费,把摩擦报少一半(−3.49 vs 真实 −7.49 bp)→ 成本只有双边才有意义。用户实测 taker 4bp 单边 / 来回 8bp 门槛。
21b. **L21 挑战完成(2026-08-11)**:①③④⑤全绿,杠杆落 5.0x(恒等式推出)、保证金 $2.88→$11.5、盈亏跳动不变。**用户数据抓出我两个 bug**:(a)`abs(slip)` 把有利变动($0.0107)算成成本 → 改有符号;(b)硬编码文案"市价卖单天然低于 last"被数据反驳(实测 +1.86 bp 有利)→ 改中性"参考价漂移",并标注测试网合成盘口量不出真实滑点。**噪声 vs 摩擦实证**:两趟来回毛盈亏 +0.52 / −4.12 bp(变号=噪声),手续费 −8.01 / −8.00 bp(分毫不差=确定性),且**换杠杆不变**(挑战⑤命题成立)。爆仓价 20x→5x 几乎没动(5,597,190 → 5,596,873)=全仓下杠杆旋钮对爆仓价失效,用户无意中做了干净对照。
22. 用户选 **A(先用实测费率重估 L16)**,结果掀翻了路线优先级 → 见 [[0025]]。三发现:①**波动率拖累**:BTC 4bp 下 Sharpe +0.26 但 CAGR −0.06%(算术 +13.39% 被 σ²/2=13.57% 抹平);vol 定量 20% → CAGR +7.0%、MaxDD −14.4%、三档 Sharpe 恒为 0.41(L18 命题二次确证);vol 定量还**降**换手 94→41 次/年。②**参数不稳定性 >> 费率**:费率错 6bp 移动 Sharpe 0.14,网格挪一格移动 **1.85**;钉死参数后费率曲线平缓,陡降真因是选参跳动。③等权平均(0.61)打赢挑最好(0.41)。**我的一处判断被数据纠正**:曾说"最优落在网格边缘=网格划错",推出边界(er_window 3/5/8/15/45)后发现 10 在高原内部,原网格边界没问题。
22a. ✅ L22 参数稳定性(**路线改道**:原定"焊 runner"推迟,因为焊进去=拿真钱赌一个挪一格就变号的数):核心=**walk-forward 消灭前视但没消灭「选择方差」**(7 fold 里 2 个样本内冠军是样本外最差族);核心技能=**分辨高原 vs 尖峰**(看邻居,因为参数一定会漂);四方法对比全部只用样本内信息 → **只有③挑邻域最好(高原)三资产全改善**(BTC .41→.67, ETH −.37→−.05, SOL −.98→−.96),②top3 平均 BTC 最猛(.82)但 SOL 恶化到 −1.39,④等权 ETH/SOL 均恶化。机制:**平均=强制分散(都差时被拖向平均的差);高原=仍在选,只换抗噪统计量**。**最易误用的一句**:集成不制造 edge,只降"拿到哪个参数"的方差 → 均值为负时=更可靠地亏(SOL k 越大越差)。直面**多重检验**:L15 起"BTC 有东西 ETH/SOL 没有"反复出现,唯一正结果指向自身。`param_stability.py`(曲面/四方法/k敏感性)+`fee_sensitivity.py`;词表 +4(选择方差/参数高原尖峰/参数集成/波动率拖累再访)。首选源 Rob Carver + Bailey&López de Prado 伪数学。← **已发布**,待用户跑并回答②③④(尤其④"变好但仍为负算不算改善")。
22b. 下一步岔路:①**多重检验解药**(Deflated Sharpe,给 BTC 的 0.67 一个诚实置信区间);②L23 焊 runner(用方法③而非挑最好);③掉头股票赛道(crypto 日线信号研究边际收益已很薄)。
22c. **L22 挑战 + 留出集判决(2026-08-11)**:见 [[0026]]。用户跑完 L22 后,**开了一段从未被碰过的数据**(2023-10-01 起,测试段 2024-09-30 → 2026-06-21)。判据与用户共同预注册后**只跑一次**。**BTC 方法③ Sharpe 0.17 / CAGR +1.4% / MaxDD −26.9% → 命中"不上钱"区间**(样本内 0.67 掉 0.50,正是多重检验预测的衰减)。
   - **L22 的"交付物"没复现**:四方法排序在三资产上完全打乱,③ 在 ETH 上最差(−0.77)。教训=**方法层结论和策略层结论一样会过拟合**;"三资产一致"不是独立检验,因为它们**共用同一段时间**——换资产 ≠ 换样本,真正的独立检验是**换时间**。
   - **真发现二次复现**:三资产全新数据上,方法③的 CAGR 和 MaxDD **双双优于买入持有**(回撤砍掉 1/2~2/3;SOL 买持 −76.3% vs 策略 −26.9%)。与 [[0017]](L15)逐字相同 = **下跌保护泛化,夏普 edge 不泛化**,两种独立复现方式(跨资产 / 跨时间)都指向它。系统真实身份 = **风险削减 overlay,非 alpha 来源**。
   - 元教训:这次否定结论**在钱进场前**产出 = 系统正常工作。流程(判据先定→数据后开→结果照收)才是资产,不是那个 0.67。
23. 用户选 **B 换股票赛道**(MISSION 本就写着 crypto → 股票 → AI,不算改使命)。
23a. ✅ L23 换股票·校准时钟:单一胜利=**在自己代码里抓一个 20% 的 bug**。①**接口红利第 8 次**:`fetch_stock` 6 行转接头(yfinance → 同样的 ohlcv 帧),策略代码一行没改;`auto_adjust=True` 给拆股+分红双复权(**yfinance 默认已做拆股复权,所以"拆股假暴跌"那个经典雷在此数据源不存在**——我原计划的 demo 被数据否掉了,改成真雷)。②**真雷=日历常数**:`metrics.BARS_PER_YEAR=365` / `sizing.PERIODS_PER_YEAR=365`,股票实测 **251.4**;夏普恒定虚高 sqrt(365/252)=**1.204**,CAGR 同向虚高(years 算少了)。**关键:不抛异常**。`oos.score()` 加 `bars_per_year` 参数(默认 365 保旧课逐字复现)。③**隔夜跳空**:SPY 隔夜占收益 62%、KO **92.5%**(盘中 −3.2%)→ `shift(1)` 在两个市场表达的不是同一个假设。④**幸存者偏差实证**:SIVBQ/LEHMQ/ENRNQ 全返回空。`stocks.py`(clock/overnight/dead)+ 装了 yfinance;词表 +3。首选源 QuantStart Successful Backtesting + yfinance 文档。← **已发布**,待用户跑并回答①②③④(④=同一常数在 sizing 里的第二处伤害,方向与夏普那处不同)。
23b. 下一步岔路:①L24 预注册的独立检验(冻结机器+正确日历,股票上跑一次——手上唯一干净的独立样本);②先修执行假设(收盘成交 → 次日开盘成交);③**横截面策略**(几百只股票排序做多空,crypto 单标的时序给不了的东西,股票量化真正主场)。用户选 **②**。
24. ✅ L24 诚实成交假设(2026-08-11 完成):`backtest_next_open`(open-to-open + **shift(2) 非 shift(1)**——延迟由收益区间起点决定,留 1 = 亲手引入新前视)。**我的预测错了**(以为隔夜占比 62-92% → 改假设会重伤;实测 ±0.08 夏普)——错因=把「持有期收益的时段分布」和「换仓日跳空成本」当同一个量。公式 `年化损失≈换手×每笔跳空成本` 20 格全中;**跳空=无偏噪声非系统抽水**(10 好 10 坏,均值+0.03%/年),不改期望只放大方差,换手是唯一放大器。backtrader 默认即次日开盘,同根成交开关名叫 `cheat_on_open`。见 [[0028-l24-fill-assumption-is-variance-not-bias]]。
25. ✅ L25 预注册的独立检验(**已发布 2026-08-12,判决未跑**):交付物是文档非代码。检验两次复现过的身份命题(风险削减 overlay 非 alpha 源)第三种独立方式=跨市场。`holdout_stocks.py`:prereg/rehearsal/run 三命令,run 落 `holdout_stocks.RAN` 档案防重跑。判据冻结:H1 |MaxDD③|≤⅔买持 于 ≥3/5;H2 中位夏普差 ≤0;三态判读各接行动、无"再试一次"格。移植决定全部来自规则(fee 5bp、借券 0.5%/yr 双边、杠杆帽 2.0 Reg-T、折长 252/63 时间语义、shift(2)、日历推断);多重检验账本:选择层干净、L23/24 软污染已记录。排练(烧掉的 BTC)已验通:③ 0.92 vs 买持 −0.11,证据价值零。词表 +5(成交假设/预注册/研究者自由度/多重检验账本/三态判读表),新参考卡 `preregistration-checklist.html`。首选源 Nosek PNAS 2018 + AsPredicted。**老师不碰 run,判决权属于用户**;待用户 ①写自己的预测 ②对判据讨价还价(跑前唯一窗口)③rehearsal ④run 一次贴全输出 ⑤按落格执行行动。下一课由数据决定:支持→横截面;反驳→研究重开;惊喜→股票时序深查。见 [[0029-l25-preregistration-locked]]。
