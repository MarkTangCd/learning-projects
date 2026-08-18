# 量化交易读书线 Resources

> 本工作区的主教材是 `resources/` 下的 5 本电子书,目录均已从文件内实际提取核对(2026-08-18)。

## Knowledge(主教材,按学习顺序)

1. [Book: 《Naked Statistics》 — Charles Wheelan](resources/Naked%20Statistics%20(Charles%20Wheelan)%20(z-library.sk,%201lib.sk,%20z-lib.sk).epub)
   EPUB,导言 + 13 章 + 结语。统计直觉零公式入门。**用于:** 补统计地基——相关、概率、CLT、推断、回归及其陷阱。
2. [Book: 《Quantitative Trading》(1st ed., 2009) — Ernest P. Chan](resources/Quantitative%20Trading%20How%20to%20Build%20Your%20Own%20Algorithmic%20Trading%20Business%20(Ernest%20P.%20Chan)%20(z-library.sk,%201lib.sk,%20z-lib.sk).pdf)
   PDF 8 章。个人量化生意全流程:选策略→回测→建业务→执行→资金管理。**用于:** 拿业界清单对照审查实战线已建的系统。注意手上是 **2008 年第 1 版**(例子用 MATLAB,2 版换了 Python/R;方法论不变)。
3. [Book: 《Inside the Black Box》(2nd ed., 2013) — Rishi K. Narang](resources/Inside%20the%20black%20box%20a%20simple%20guide%20to%20quantitative%20and%20high-frequency%20trading%20(Rishi%20K.%20Narang)%20(z-library.sk,%201lib.sk,%20z-lib.sk).pdf)
   PDF 17 章 4 部。机构量化系统的模块化解剖(alpha/风险/成本/组合/执行/数据/研究)。**用于:** 建立机构视角的策略分类学与系统观。
4. [Book: 《Advances in Financial Machine Learning》(2018) — Marcos López de Prado](resources/Advances%20in%20Financial%20Machine%20Learning%20(Marcos%20M.%20López%20de%20Prado)%20(z-library.sk,%201lib.sk,%20z-lib.sk).epub)
   EPUB 22 章 5 部。金融 ML 的严谨方法论。**用于:** 标注、样本权重、purged CV、回测三大危险、Deflated Sharpe。
5. [Book: 《Active Portfolio Management》(2nd ed., 2000) — Grinold & Kahn](resources/Active%20Portfolio%20Management%20A%20Quantitative%20Approach%20for%20Producing%20Superior%20Returns%20and%20Selecting%20Superior%20Returns%20and…%20(Richard%20Grinold,%20Ronald%20Kahn)%20(z-library.sk,%201lib.sk,%20z-lib.sk).pdf)
   PDF 22 章 + 3 附录(扫描版,无书签,正文页码见课程表)。因子模型与组合优化圣经。**用于:** IR、主动管理基本定律、alpha 预测、组合构建。注意书内自带附录 C(收益与统计基础)可作数学急救包。

### 配套(免费一手资料)
- [López de Prado 官方研究站](https://www.quantresearch.org/) — AFML 作者本人论文/讲义/代码。**用于:** AFML 各章的免费配套与延伸。
- [Bailey & López de Prado — Pseudo-Mathematics and Financial Charlatanism (AMS 2014)](https://www.ams.org/notices/201405/rnoti-p458.pdf) — 回测过拟合与多重检验。**用于:** AFML ch11–14 的免费短版导读。
- [Jegadeesh & Titman 1993(动量原始论文)](https://www.jstor.org/stable/2328882) — **用于:** APM 预测章讲横截面动量时的学术源头。

## Wisdom(Communities)
- [r/algotrading](https://www.reddit.com/r/algotrading/) — 独立算法交易者社区。**用于:** 读 Chan 时对照"个人做量化生意"的当代实况(书是 2008 年的)。
- [r/quant](https://www.reddit.com/r/quant/) — 偏机构/学术。**用于:** 读 Narang/APM 时验证机构实践是否仍如书中所述。

## Gaps
- 《Naked Statistics》和 Chan 手上均非最新版(前者无碍;Chan 1 版的工具章节过时,读 ch3/ch5 时由老师补当代对照)。
- APM 为扫描版 PDF,文字层质量一般——如影响阅读,可考虑找更清晰版本。
