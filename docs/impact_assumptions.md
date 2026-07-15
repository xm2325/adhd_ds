# Impact and cost-proxy assumptions

All values in `config/operations.yaml -> planning_cost_proxies` are synthetic planning assumptions.

They answer a narrow portfolio question:

> If a planning team supplied unit-resource assumptions, how would the analytical product compare options consistently?

They do not estimate Care ADHD costs, NHS tariffs, revenue, clinical benefit, or causal intervention effects.

## Scenario impact

The scenario comparison uses the configured clinician-hour proxy and the difference in average weekly clinical minutes from the stored baseline. It reports a 12-week cost proxy and, when backlog improves, a cost per backlog patient avoided.

A backlog patient avoided is a queue-model output, not a patient outcome.

## Outreach impact

The outreach table applies a configured relative DNA-reduction assumption to the sum of predicted probabilities in the selected queue. This is only an expected-value calculation. The reduction must be estimated through a controlled pilot before any operational claim is made.

A suitable pilot would pre-register eligibility, randomisation, primary outcome, subgroup checks, delivery failures, analysis, stopping rules, and data-protection controls.
