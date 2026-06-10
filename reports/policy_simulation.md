# Policy Simulation

## Product Question

If the campaign is effective on average, which rollout policy creates the best expected business outcome?

中文问题：如果促销平均有效，应该全量发、只发某一类目，还是按用户分层定向触达？

## Policy Comparison

| Policy | Contacted | Conv Rate | Spend / Customer | Conv / 100k | Spend / 100k | Contact Cost | Cost-Adj Value | Inc Conv | Inc Spend |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Send all Mens E-Mail | 100.00% | 1.25% | $1.423 | 1,253 | $142,262 | $55,000 | $87,262 | 681 | $76,983 |
| Send all Womens E-Mail | 100.00% | 0.88% | $1.077 | 884 | $107,720 | $55,000 | $52,720 | 311 | $42,441 |
| Rule-based target/suppress | 29.52% | 0.90% | $1.065 | 895 | $106,525 | $16,235 | $90,289 | 323 | $41,246 |
| No campaign holdout | 0.00% | 0.57% | $0.653 | 573 | $65,279 | $0 | $65,279 | 0 | $0 |

## Recommendation

- Best gross spend policy: `Send all Mens E-Mail`.
- Best cost-adjusted policy with `$0.55` contact/incentive cost: `Rule-based target/suppress`.
- Use this rule-based policy as a baseline for future uplift modeling, not as a final production targeting model.
- The next phase should train an uplift model and compare uplift-score targeting against this rule-based baseline.

中文结论：

- 如果只看 gross spend，最优策略是 `Send all Mens E-Mail`。
- 如果考虑每次触达/优惠券成本 `$0.55`，成本调整后最优策略是 `Rule-based target/suppress`。
- 这个规则策略适合作为后续 uplift model 的 baseline，不应包装成最终生产模型。
- 下一步应该训练 uplift model，用模型分数和规则分层策略对比。
