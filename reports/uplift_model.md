# T-learner Uplift Model Readout

## Model

Two-model (T-learner) approach using logistic regression.

- Model T: trained on Mens E-Mail group.
- Model C: trained on No E-Mail group.
- Uplift score = P(conversion | treated) - P(conversion | control).

Features: history, recency, mens, womens, newbie, channel, zip_code.

## Uplift By Predicted-Score Decile

Decile 10 = highest predicted uplift (best targets).

| Decile | Avg Score | Conv Lift | Spend Lift | Incr Spend / 100k |
| --- | --- | --- | --- | --- |
| 1 | 0.0042 | 0.22% | $0.316 | $31,643 |
| 2 | 0.0050 | 0.95% | $0.953 | $95,279 |
| 3 | 0.0054 | 0.54% | $1.325 | $132,499 |
| 4 | 0.0056 | 0.52% | $0.498 | $49,823 |
| 5 | 0.0058 | 0.51% | $0.268 | $26,769 |
| 6 | 0.0060 | 0.12% | $0.385 | $38,467 |
| 7 | 0.0062 | 0.62% | $0.520 | $52,012 |
| 8 | 0.0066 | 1.12% | $0.663 | $66,342 |
| 9 | 0.0080 | 0.77% | $1.016 | $101,647 |
| 10 | 0.0150 | 1.42% | $1.710 | $170,964 |

## Model vs Rule-based Comparison (top 30% targeting)

- Top-3-decile model targeting: ~$112,984 avg incremental spend / 100k
- Rule-based target/suppress: ~$41,246 incremental spend vs holdout

Note: decile comparison uses observed uplift within each score band, not a held-out test set.
A proper evaluation would split the data and evaluate on a holdout.

## Business Read

- The top deciles (8-10) show the strongest observed conversion and spend lift.
- The bottom deciles (1-3) show weak or near-zero lift — these customers are less persuadable.
- Targeting the top 30% by uplift score is a more data-driven version of the rule-based segment policy.
- Next step: proper train/test split and Qini curve evaluation.
