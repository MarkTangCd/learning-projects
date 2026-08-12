# 计量金融 Resources

选材原则:**代码优先、数学随需补给**(见 [MISSION.md](./MISSION.md))。凡是要求测度论前置的资源一律标注,不作为主线。

## Knowledge

### 主线教材

- **[Options, Futures, and Other Derivatives — John C. Hull](https://www.pearson.com/en-us/subject-catalog/p/options-futures-and-other-derivatives/P200000005938)**
  衍生品领域的标准第一本书,覆盖定价模型与风险管理,**刻意回避重数学**。多个来源一致把它列为"没有测度论背景时的第一本"。
  Use for: 期权机制、Black-Scholes 的应用侧、希腊字母、对冲实务。**本课程的主线教材。**

- **[Paul Wilmott Introduces Quantitative Finance](https://www.wiley.com/en-us/Paul+Wilmott+Introduces+Quantitative+Finance%2C+2nd+Edition-p-9780470319581)**
  比 Hull 数学重,比 Shreve 直觉强——**Hull 与严肃数学之间的那座桥**。覆盖 Black-Scholes、波动率、数值方法。
  Use for: 当 Hull 说"可以证明……"而你想知道为什么的时候。

- **[Stochastic Calculus for Finance I & II — Steven Shreve](https://math.cmu.edu/users/math/nw0z/abstracts/shreve2)**
  金工硕士的标准教材。**Vol I 用二叉树在离散世界里讲完所有核心概念,不需要测度论**——这是本课程唯一会正面用到的一卷。Vol II 需要实分析+测度论,列在这里是路标不是任务。
  Use for: 想把"无套利/复制/风险中性"这三件事真正弄清楚时,读 Vol I。

### 免费的高质量材料

- **[Mathematical Finance Lecture Notes — Daniel Ocone, Rutgers (Math 621/622)](https://sites.math.rutgers.edu/~ocone/mathfinancenotes.html)**
  跟随 Shreve I & II 的免费大学讲义。
  Use for: 想要教材同款内容但不想买书时;也可用来对照检查我讲的东西。

- **[QuantEcon: Monte Carlo and Option Pricing](https://intro.quantecon.org/monte_carlo.html)**
  高质量开源经济学教材,用 Python 从头做蒙特卡洛期权定价,**明确采用风险中性定价并直说"忽略投资者风险偏好"**。代码优先,与本课程口味完全一致。
  Use for: L1 的首选精读源;后续做方差缩减、路径依赖期权时回来看。

- **[QuantStart: Quant Reading List — Derivative Pricing](https://www.quantstart.com/articles/Quant-Reading-List-Derivative-Pricing/)**
  分层书单(入门 → 中级 → 研究级),说清每本书的数学前置。
  Use for: 每学完一块,判断下一本该读哪本。隔壁量化交易课已多次用过这个站。

### 待补(见 Gaps)

## Wisdom (Communities)

- **[Quantitative Finance Stack Exchange](https://quant.stackexchange.com/)**
  问题质量要求高、有人认真回答定价与模型问题。**衍生品定价问题的最佳去处**。
  Use for: "我的 Delta 对冲 P&L 不收敛,是模型问题还是实现问题?"这类可复现的技术问题。

- **[Wilmott Forum](https://forum.wilmott.com/)**
  从业者的老牌聚集地,数学讨论深。
  Use for: 实务与理论的落差(模型在真实市场怎么失效)。

- **[r/quant](https://reddit.com/r/quant)**
  节奏快,职业+技术混杂。
  Use for: 行业现状、什么模型还在用什么已经死了。信噪比不如前两个,交叉验证着看。

> 用户尚未表态是否愿意参与社区。**待确认**——若不愿,记录到此并停止推荐。

## Gaps(缺口,驱动后续搜索)

- **数学补给的中文/低门槛资源**:用户数学基本清零,需要"金融用得上的微积分与概率"这一层的好材料,尚未找到满意的。目前策略是我按需自制补给块 + 用代码验证。
- **Delta 对冲的交互式可视化**:能拖动参数看 P&L 收敛的现成材料,尚未找到,倾向自建组件(`assets/mc-pricer.js` 已是第一个)。
- **中文术语对照**:期权术语中英混用严重,已在 [reference/glossary.html](./reference/glossary.html) 自建,以它为准。
