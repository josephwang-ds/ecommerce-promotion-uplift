# Decision Memo: Hillstrom Promotion Experiment

## Decision

Do not treat this as a simple global "send email to everyone" campaign yet.

The average experiment result supports promotional email as an effective owned-channel growth lever, especially the men's merchandise campaign. The next product decision should be a targeted rollout after segment-level uplift analysis.

After the first-pass segment readout, the recommendation is:

- Use men's email as the primary rollout candidate.
- Prioritize segments with both positive conversion lift and positive spend lift.
- Suppress or retest women's email for segments where spend lift is weak or negative.
- Do not use raw visit lift as a launch criterion.

## Evidence From Initial Readout

Compared with the no-email holdout:

- Men's email increased visit rate from 10.62% to 18.28%.
- Men's email increased conversion rate from 0.57% to 1.25%.
- Men's email increased spend per customer from $0.653 to $1.423.
- Women's email also improved all three metrics, but with a smaller lift.

Per 100k contacted customers:

- Men's email implies about 681 incremental conversions and $76,983 incremental spend.
- Women's email implies about 311 incremental conversions and $42,441 incremental spend.

## Product Interpretation

The campaign creates measurable incremental behavior, but the average result is not enough for a final CRM policy.

Before rollout, the team should answer:

- Which customer segments drive the incremental spend?
- Are high-value customers responding, or is lift concentrated in low-value segments?
- Are recent buyers and lapsed buyers affected differently?
- Does category preference explain why men's email outperforms women's email?
- Are there negative-uplift segments that should be suppressed?

The first segment readout gives a clearer direction:

- Strongest target candidate: customers with both mens and womens history receiving men's email.
- Strong history-based target candidates: `$350-$500`, `$500-$750`, and `$750-$1,000` historical spend bands for men's email.
- Strong channel candidate: multichannel users respond well to both men's and women's email.
- Suppression candidates: some mid-history segments receiving women's email show negative conversion or spend lift.

## Recommended Next Step

Move from rule-based segment readout to uplift modeling and policy simulation.

Use the current segment results to define:

- `target`: send the campaign where incremental conversion and spend are positive.
- `suppress`: avoid groups with weak or negative uplift.
- `retest`: run creative or incentive experiments for ambiguous groups.

Then build an uplift model using:

- historical spend band.
- recency.
- channel.
- prior mens/womens preference.
- new vs existing customer.

The output should be a campaign policy simulation that compares:

- send to all eligible users.
- send men's email only.
- send by segment rule.
- send by modeled uplift score.

## China E-commerce Translation

In a Tmall Global / JD / Pinduoduo-style setting, this maps to:

- no-email group: CRM holdout group.
- men's/women's email: category-specific member campaign.
- conversion: order conversion.
- spend: GMV per targeted customer.
- targeting policy: coupon/member campaign audience rule.

The business goal is not maximum campaign response. The goal is profitable incremental GMV.
