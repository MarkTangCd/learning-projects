# L20:换到 perp 测试网 —— 第一张原生空单(拆掉现货的做空墙)

用户在 L19 挑战后从四条岔路里选了 **perp 测试网**(老师首选)。承接 [[0021-l19-sizing-wired-into-runner]](现货 runner 按风险下注跑通,但 honest scope 写死 long/flat:现货余额 ≥0,物理做不了空)+ [[0018-l16-shorting-breaks-ceiling-on-btc-but-not-free]](做空在回测里顶出全课首个正样本外夏普,但一直落不了地)。

## 教学要点(隔离摸熟新 venue,L9 风格;不焊 runner)
- **单一胜利**:在 perp 测试网开出第一张**原生空单**,读回一个**负持仓**——现货物理打印不出这一行。
- **心智切换**:现货"我有多少币(≥0)" → perp"我的持仓是正是负(带符号)"。`fetch_positions()` 读回带符号真相 = L9"别假设,读回对账"在 perp 上的样子(真相多一个符号位)。
- **flat 时 SELL = 开空**(建负持仓/"欠"币),不是卖手里的币。平仓永远是持仓符号的**反**方向:平空=**买**、平多=卖,且带 `reduceOnly`(只缩不反向开)。
- **三样新东西**:①新 venue+**新密钥**(`testnet.binancefuture.com`,ccxt `binanceusdm`,与现货测试网两套账户;混用报 Invalid API-key)②抵押 USDT 保证金、不持币 ③**最小名义 ≈$50**(现货 ~$5)→ 单子块头大,L9 的 $50 闸门卡死,按 venue 重标定到 $200(闸门形状不变、校准值随场子)。
- **funding 从模拟变真**:L16 的"碳税"现在是 perp 真费率,每 8h 收付一次;本课只**预览**(`perp.py funding`),L22 再让它随持仓真扣。

## 关键伏笔(为什么 perp 上杠杆是"必需"非"可选")
- perp 最小名义 $50 **> 用户 L19 配给资本 $40** → 1x 杠杆下小账户根本下不出合规单 → **杠杆成了小账户在 perp 下单的前提**,不是加速器。= L21 入口。本课演示单用 $60(略高于 $50 min),杠杆用测试网默认(~20x)不碰。

## 代码(离线自检:编译 OK + 无密钥优雅报错;网络路径需用户 perp 密钥才能真跑,同 L9)
- 新文件 `practice/perp.py`(对照 `execution.py` 教学风格):`connect()`=binanceusdm+sandbox+代理+set_position_mode(False) one-way(try/except 吞"无需改")。命令 `balance`(USDT 保证金)/`funding`(费率预览,×3 折日)/`short`(flat→市价卖开空→回读订单→`show_position` 打负仓)/`position`(带符号+名义+uPnL+杠杆)/`close`(reduceOnly 反方向平回 0)。
- 复用:同一 KILL_FILE(急停跨脚本);guarded_create 同 L9 gate 形状(kill+名义上限),reduceOnly 豁免上限。
- ccxt 4.5.70 已验:binanceusdm/set_sandbox_mode→testnet.binancefuture.com;`BTC/USDT:USDT` linear swap,limits.cost.min=50、amount.min=0.0001、contractSize=1。

## 待办 / 岔路
- 用户去 testnet.binancefuture.com 生成密钥 export,跑 ①balance ②funding ③short ④position ⑤close,贴 ③⑤ 输出 → 确认真开真平一张现货下不出的单。
- 下一步:①**L21 杠杆**(weight>1、set_leverage、保证金/强平价=小账户 perp 下单前提)②**L22 焊进 runner**(perp 接 strategy_runner,信号能吐 −1,真 funding 随持仓 8h 真扣,攒双边 track record)③股票赛道。见 [[0021-l19-sizing-wired-into-runner]]。
