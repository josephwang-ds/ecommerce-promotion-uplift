# Segment Uplift Readout

## Product Question

Which customer segments should receive a category promotion, which should be suppressed, and which need a follow-up experiment?

中文问题：哪些用户应该定向触达，哪些用户应该避免发券/打扰，哪些人群需要继续测试创意或折扣力度？

## Policy Rule

- `target`: positive conversion lift and positive spend lift, with directional statistical support.
- `suppress`: negative conversion lift or negative spend lift.
- `retest`: small sample size or directionally positive but not enough evidence.

This is a first-pass decision rule, not the final model. The next phase will use uplift modeling and policy simulation.

## Top Target Candidates

| Dimension | Segment | Treatment | Policy | N C/T | Conv Lift | Spend Lift | Inc Conv / 100k | Inc Spend / 100k |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| category_history | Both mens and womens | Mens E-Mail | target | 2,149 / 2,181 | 1.50% | $1.825 | 1,499 | $182,499 |
| history_segment | 4) $350 - $500 | Mens E-Mail | target | 2,124 / 2,097 | 0.87% | $1.569 | 873 | $156,894 |
| history_segment | 6) $750 - $1,000 | Mens E-Mail | target | 622 / 644 | 2.00% | $1.534 | 2,002 | $153,415 |
| history_segment | 5) $500 - $750 | Womens E-Mail | target | 1,652 / 1,662 | 1.02% | $1.286 | 1,020 | $128,565 |
| channel | Multichannel | Mens E-Mail | target | 2,606 / 2,577 | 1.02% | $1.209 | 1,017 | $120,913 |
| channel | Multichannel | Womens E-Mail | target | 2,606 / 2,579 | 0.71% | $1.158 | 705 | $115,754 |
| history_segment | 5) $500 - $750 | Mens E-Mail | target | 1,652 / 1,597 | 0.83% | $1.103 | 833 | $110,301 |
| recency_band | 1-3 months | Mens E-Mail | target | 7,438 / 7,469 | 0.73% | $1.048 | 733 | $104,760 |
| customer_type | Newbie | Mens E-Mail | target | 10,695 / 10,686 | 0.74% | $0.960 | 740 | $96,002 |
| channel | Web | Mens E-Mail | target | 9,373 / 9,490 | 0.72% | $0.850 | 720 | $85,045 |

## Suppression Candidates

| Dimension | Segment | Treatment | Policy | N C/T | Conv Lift | Spend Lift | Inc Conv / 100k | Inc Spend / 100k |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| history_segment | 3) $200 - $350 | Womens E-Mail | suppress | 4,044 / 4,155 | -0.07% | $-0.323 | -67 | $-32,314 |
| history_segment | 4) $350 - $500 | Womens E-Mail | suppress | 2,124 / 2,188 | -0.22% | $-0.101 | -216 | $-10,089 |

## Strong Retest Candidates

| Dimension | Segment | Treatment | Policy | N C/T | Conv Lift | Spend Lift | Inc Conv / 100k | Inc Spend / 100k |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| history_segment | 7) $1,000 + | Womens E-Mail | retest | 416 / 428 | 1.13% | $2.507 | 1,128 | $250,678 |
| history_segment | 7) $1,000 + | Mens E-Mail | retest | 416 / 464 | 0.93% | $1.322 | 928 | $132,207 |
| history_segment | 6) $750 - $1,000 | Womens E-Mail | retest | 622 / 593 | 0.87% | $0.648 | 867 | $64,826 |
| zip_code | Rural | Womens E-Mail | retest | 3,139 / 3,181 | 0.33% | $0.515 | 335 | $51,484 |
| category_history | Mens only | Womens E-Mail | retest | 9,638 / 9,622 | 0.06% | $0.278 | 63 | $27,835 |
| channel | Phone | Womens E-Mail | retest | 9,327 / 9,454 | 0.17% | $0.232 | 173 | $23,247 |
| category_history | Both mens and womens | Womens E-Mail | retest | 2,149 / 2,118 | 0.53% | $0.162 | 533 | $16,188 |
| customer_type | Existing | Womens E-Mail | retest | 10,611 / 10,624 | 0.09% | $0.114 | 93 | $11,396 |

## Product Reading

- The global campaign result is positive, but targeting should focus on segments with both conversion and spend lift.
- Some segments show positive visit lift but weaker spend lift; those are not automatic launch candidates.
- Suppression candidates matter because a CRM campaign can waste discounts or attention even when the global average looks good.
- In a China e-commerce setting, this becomes a member campaign audience rule: `target`, `suppress`, or `retest`.
