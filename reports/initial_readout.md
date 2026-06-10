# Initial Hillstrom Experiment Readout

## Dataset Snapshot

- Rows: `64,000`
- Columns: `12`
- Exact duplicate feature/outcome rows: `6,562`
- Missing cells: `0`
- Customer identifier: not included in the public CSV, so exact duplicate rows should not be interpreted as duplicate customers.

## Sample Size By Arm

| Segment | Users |
| --- | --- |
| Mens E-Mail | 21,307 |
| No E-Mail | 21,306 |
| Womens E-Mail | 21,387 |

## Average Outcomes By Arm

| Segment | Visit Rate | Conversion Rate | Spend / Customer |
| --- | --- | --- | --- |
| Mens E-Mail | 18.28% | 1.25% | $1.423 |
| No E-Mail | 10.62% | 0.57% | $0.653 |
| Womens E-Mail | 15.14% | 0.88% | $1.077 |

## Treatment Effects vs No E-Mail

### Mens E-Mail

| Metric | Control | Treatment | Absolute Lift | Relative Lift | 95% CI | p-value |
|---|---:|---:|---:|---:|---:|---:|
| Visit rate | 10.62% | 18.28% | 7.66% | 72.14% | [7.00%, 8.32%] | 0.0000 |
| Conversion rate | 0.57% | 1.25% | 0.68% | 118.84% | [0.50%, 0.86%] | 0.0000 |
| Spend per customer | $0.653 | $1.423 | $0.770 | 117.93% | [$0.485, $1.055] | 0.0000 |

Per 100k customers:

- Incremental conversions: `681`
- Incremental spend: `76,983`

### Womens E-Mail

| Metric | Control | Treatment | Absolute Lift | Relative Lift | 95% CI | p-value |
|---|---:|---:|---:|---:|---:|---:|
| Visit rate | 10.62% | 15.14% | 4.52% | 42.61% | [3.89%, 5.16%] | 0.0000 |
| Conversion rate | 0.57% | 0.88% | 0.31% | 54.33% | [0.15%, 0.47%] | 0.0002 |
| Spend per customer | $0.653 | $1.077 | $0.424 | 65.02% | [$0.169, $0.680] | 0.0011 |

Per 100k customers:

- Incremental conversions: `311`
- Incremental spend: `42,441`

## Product Reading

- Treat `conversion` as the primary metric.
- Treat `spend per customer` as the business metric.
- Treat `visit` as a diagnostic metric: more visits are useful only if they translate into profitable conversion or spend.
- Next step: segment the treatment effect by recency, historical spend, channel, and category preference before recommending a global send.
