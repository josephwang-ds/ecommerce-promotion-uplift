# Personalized Promotion Experiment for Cross-border E-commerce

跨境电商个性化促销实验：用随机实验和 uplift 分析判断促销邮件/优惠券是否真的带来增量转化和 GMV，以及应该发给哪些用户。

## Business Question

A cross-border e-commerce team wants to send promotional emails to past customers.

一个跨境电商团队想给历史购买用户发送类目促销邮件或优惠券。真正的问题不是“发了邮件的人买得更多吗”，而是“邮件是否创造了增量购买”。

The decision is not:

> Which group has the highest conversion rate?

The real Product Data Scientist question is:

> Which customers generate incremental conversion and spend because of the campaign, and which customers should not receive the promotion?

对应中文业务问题：

> 哪些用户是因为促销触达才产生增量转化和 GMV？哪些用户本来就会买，或者触达后没有增量价值，因此不应该被发券/打扰？

## Dataset

Primary dataset:

Hillstrom / MineThatData Email Marketing dataset.

The dataset contains a randomized marketing experiment with:

- a no-email control group.
- a men's email treatment group.
- a women's email treatment group.
- customer history and channel features.
- outcome metrics: visit, conversion, and spend.

这个数据集的价值在于它有 `No E-Mail` holdout control group，所以可以比较促销触达相对“不触达”的增量影响，而不是只做相关性分析。

Current local raw file:

`data/raw/hillstrom_email.csv`

Source URL:

`http://www.minethatdata.com/Kevin_Hillstrom_MineThatData_E-MailAnalytics_DataMiningChallenge_2008.03.20.csv`

## Live Demo

- Streamlit app: `https://josephwang-ecommerce-promotion-uplift.streamlit.app/`
- GitHub repository: `https://github.com/josephwang-ds/ecommerce-promotion-uplift`

## China E-commerce Packaging

Although the dataset is not from a Chinese platform, the business problem maps cleanly to a China/cross-border e-commerce CRM scenario:

- Tmall Global / JD-style old-customer reactivation.
- category-specific coupon campaigns.
- member lifecycle marketing.
- campaign holdout groups for incrementality measurement.
- GMV and conversion lift instead of only click or visit lift.

虽然原始数据不是淘宝/京东/拼多多数据，但业务结构非常接近中国电商里的 CRM 增长问题：

- 老客召回：给过去 12 个月购买过的用户做再营销。
- 类目促销：男装/女装邮件可映射为不同类目 campaign creative。
- 会员运营：根据历史 GMV、购买间隔、渠道做分层触达。
- Holdout 组：保留一部分用户不触达，用来衡量真实增量。
- 决策目标：不是点击率最高，而是增量订单和增量 GMV 最大。

Field mapping:

| Dataset Field | China E-commerce Meaning |
|---|---|
| `segment` | no-contact holdout, men's category campaign, women's category campaign |
| `visit` | return visit after CRM exposure |
| `conversion` | order conversion |
| `spend` | GMV / revenue per targeted customer |
| `history` | historical GMV / customer value |
| `recency` | months since last purchase |
| `channel` | prior purchase channel / customer acquisition source |

Project framing:

This project uses a randomized email marketing dataset as the experimental backbone for a cross-border e-commerce CRM decision: should a category promotion be sent to all past buyers, or only to segments where the campaign creates incremental conversion and GMV?

项目定位：

这个项目使用随机邮件实验作为电商 CRM 决策的分析基础：平台应该给所有历史买家发送类目促销，还是只触达能产生增量转化和 GMV 的用户群？

## Product Framing

This project reframes a marketing campaign as a product decision system:

1. Should we launch a promotion?
2. Which campaign creative should we send?
3. Which customer segments show positive incremental impact?
4. Which segments should be suppressed to avoid wasted discounts or negative uplift?
5. What is the expected incremental conversion and revenue per 100k customers?
6. If the campaign is not strong enough for global rollout, what should the next experiment test?

中文产品框架：

1. 促销是否值得上线？
2. 应该发送哪个类目/创意？
3. 哪些用户群有正向增量？
4. 哪些用户群应该被 suppress，避免浪费优惠券或造成负向 uplift？
5. 每 10 万用户预计带来多少增量订单和 GMV？
6. 如果不适合全量上线，下一轮实验应该测创意、折扣力度还是人群策略？

## Analysis Plan

### 1. Experiment Sanity Checks

- sample size by arm.
- duplicate customer check.
- missing value check.
- covariate balance by treatment arm.
- baseline differences in history, recency, channel, and category preference.

### 2. Average Treatment Effect

Compare each treatment arm against the no-email control:

- visit lift.
- conversion lift.
- spend lift.
- visit-to-conversion quality.
- spend concentration and outlier sensitivity.
- confidence intervals.
- p-values where appropriate.
- incremental conversions and spend per 100k customers.

### 3. Segment Readout

Estimate treatment effects by:

- historical spend bands.
- recency bands.
- channel.
- zip code type.
- new versus existing customers.
- prior mens/womens purchase preference.

### 4. Uplift Modeling

Start simple before adding complexity:

- treatment interaction logistic regression.
- two-model uplift approach.
- uplift ranking by decile.
- policy simulation for targeted send.

### 5. Decision Memo

The final deliverable should answer:

- ship to all customers?
- target only selected segments?
- choose men's email, women's email, or no email?
- suppress any negative-uplift segments?
- retest if the result is directionally positive but not practically meaningful?
- which metric should be monitored after launch?
- what follow-up experiment should be run?

## Current Status

Data download, global treatment readout, segment uplift analysis, and policy simulation are complete.

Artifacts:

- `notebooks/hillstrom_promotion_uplift_analysis.ipynb`
- `reports/initial_readout.md`
- `reports/segment_uplift.md`
- `reports/policy_simulation.md`
- `reports/decision_memo.md`
- `figures/global_experiment_readout.png`
- `figures/top_segment_uplift.png`
- `figures/policy_simulation_value.png`
- `src/download_data.py`
- `src/hillstrom_readout.py`
- `src/segment_uplift.py`
- `src/policy_simulation.py`
- `src/run_pipeline.py`
- `scripts/create_hillstrom_notebook.py`
- `scripts/export_figures.py`
- `data/processed/segment_uplift.csv`
- `data/processed/policy_simulation.csv`

Initial global finding:

- Men's email increased conversion from 0.57% to 1.25% versus no email.
- Men's email increased spend per customer from $0.653 to $1.423.
- Women's email also improved conversion and spend, but with smaller lift.
- Segment-level uplift and policy simulation are complete; the notebook shows code, tables, chart outputs, and business conclusions.

初步中文结论：

- 相比不发邮件，男装类目邮件把转化率从 `0.57%` 提升到 `1.25%`。
- 每用户 spend 从 `$0.653` 提升到 `$1.423`。
- 女装类目邮件也有提升，但幅度小于男装邮件。
- 分层 uplift 和 policy simulation 已完成；当前版本已经对比了全量发送、规则分层发送和不发送策略。

Segment uplift finding:

- Top target candidate: customers with both mens and womens history receiving men's email.
- Strong target candidates also include multichannel users and several higher historical spend bands.
- Suppression candidates appear in some mid-history segments for women's email, where conversion or spend lift turns negative.
- Policy simulation shows that cost-adjusted value can favor targeted rollout even when gross spend favors a broader send.

分层 uplift 结论：

- 最强 target 候选：历史上同时购买过男装和女装的用户，收到男装邮件时增量 spend 最高。
- Multichannel 用户和部分高历史消费档也适合优先触达。
- 女装邮件在部分中等历史消费档出现 negative uplift，需要 suppress 或重新测试创意。
- Policy simulation 显示：如果考虑触达/优惠券成本，成本调整后的最优策略可能不是简单全量发送。

## Skills Covered

This single project covers product experimentation skills beyond a basic campaign readout:

- metric design: primary metric, business metric, and guardrails.
- experiment quality checks before reading outcomes.
- statistical uncertainty: p-values, confidence intervals, and practical significance.
- no-ship / target / retest decision logic.
- segment-level product judgment.
- follow-up experiment planning.
- productized readout through a Streamlit experiment analyzer.

中文技能点：

- 指标设计：primary metric、business metric、guardrail metric。
- 实验质量检查：样本量、分流、缺失值、组间可比性。
- 统计判断：p-value、置信区间、实际业务意义。
- 产品决策：不是只看显著性，而是决定全量发、定向发、暂不发、还是继续实验。
- 用户分层：根据历史 GMV、购买间隔、渠道、类目偏好判断谁值得触达。
- Uplift 思维：不是预测谁会买，而是预测“谁会因为促销才买”。

## Deliverables

- `notebooks/hillstrom_promotion_uplift_analysis.ipynb`
- `reports/initial_readout.md`
- `reports/segment_uplift.md`
- `reports/policy_simulation.md`
- `reports/decision_memo.md`
- `figures/global_experiment_readout.png`
- `figures/top_segment_uplift.png`
- `figures/policy_simulation_value.png`
- `app/streamlit_app.py`
- `src/run_pipeline.py`

## Project Positioning

This project combines:

- e-commerce business context.
- randomized experiment analysis.
- conversion and revenue metrics.
- segment-level product judgment.
- uplift modeling.
- actionable launch recommendation.

## How to Run

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the full analysis pipeline:

```bash
python src/run_pipeline.py
```

Regenerate the executed notebook:

```bash
python scripts/create_hillstrom_notebook.py
```

Export static PNG figures:

```bash
python scripts/export_figures.py
```

Launch the Streamlit demo locally:

```bash
streamlit run app/streamlit_app.py
```
