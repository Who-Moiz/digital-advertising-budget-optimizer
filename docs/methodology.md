# Analytics and allocation methodology

## Funnel metrics

Calculate ratios after summing counts over the selected group. Do not average
row-level CTR, CPC, CPA, conversion rate or ROAS.

| Metric | Formula | Unit |
| --- | --- | --- |
| CTR | 100 × clicks / impressions | % |
| CPC | spend / clicks | PKR per click |
| CPA | spend / conversions | PKR per conversion |
| Conversion rate | 100 × conversions / clicks | % |
| ROAS | revenue / spend | Multiple |
| Revenue | Sum of attributed revenue | PKR |
| Profit proxy | revenue − spend | PKR; excludes other costs |

For an undefined ratio, retain a missing value. Platform, campaign, date, city,
device, age and gender aggregations all use the same additive totals.

## Simulation

The simulator draws platform, impressions, audience and device, then uses binomial
click and conversion counts to preserve `conversions <= clicks <= impressions`.
Spend uses platform-specific CPC with random variation. Revenue uses conversions
times a lognormal order value. Desktop conversions receive a modest synthetic
multiplier. These parameter choices demonstrate a workflow; they are not measured
claims about the advertising platforms.

A fixed seed and fixed chunk size reproduce identical data. Changing the chunk
size changes the order of random draws and therefore changes the dataset even
with the same seed. Large datasets are generated sequentially in bounded chunks.

## Recommendation model

For platform i, let S_i be historical spend and V_i historical attributed revenue.
The pooled ROAS is R = sum(V_i) / sum(S_i). With prior strength p (default PKR 50,000):

```text
adjusted_roas_i = (V_i + p * R) / (S_i + p)
evidence_weight_i = S_i / (S_i + p)
historical_share_i = S_i / sum(S_i)
scale_i = max(historical_share_i * next_budget, next_budget / platform_count * 0.25)
modeled_revenue_i(x) = adjusted_roas_i * scale_i / a * log(1 + a * x / scale_i)
```

Here a is the positive saturation assumption (default 0.75). This function is
concave and increasing. Its slope falls as spend rises. Response scales are
normalized to the next-budget horizon because historical and proposed budgets
may cover different durations. This is an explicit scenario choice; the model
does not learn horizon, saturation or causal lift from the dataset.

The engine allocates the platform minimum first, then selects the highest modeled
incremental revenue per paisa while respecting maximum shares. The increment is
approximately 1/10,000 of the total budget. This is a discrete greedy approximation,
not an exact continuous solver. Budget is stored as integer paisa; any final
remainder is allocated exactly. Infeasible bounds and budgets too small for
paisa precision are rejected.

The baseline uses historical spend shares with the same response model. A baseline
may violate newly imposed platform caps, so constrained recommendations need not
beat it. Evidence weight describes the shrinkage contribution and is not a
statistical confidence interval. All-zero historical revenue yields tied scores;
tie breaking is deterministic by platform order, not evidence of a preference.

## Interpretation and practical limits

Historical attribution is observational. It does not establish that extra spend
will produce the same return. Seasonality, attribution windows, auction changes,
creative quality, delayed conversions, inventory and product margins are outside
this model. New platforms absent from the history are not automatically added.

Before spending, compare several saturation/prior settings, inspect campaign
quality and recent performance, and validate proposed changes with controlled
incrementality experiments. A future production model could estimate response
curves from randomized spend variation and optimize margin rather than revenue.
