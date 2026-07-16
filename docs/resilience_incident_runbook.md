# Operational resilience and incident simulation runbook

> All incidents, thresholds, costs, service levels and outcomes in this repository are synthetic portfolio assumptions. They are not Care ADHD controls, provider SLAs, clinical standards or evidence of actual harm.

## Decision structure

Each exercise follows the same sequence:

1. **Detect:** compare a source, metric, model, service or audit signal with a declared trigger.
2. **Classify:** assign P0–P3 severity from the affected decision path, not from model accuracy alone.
3. **Contain:** block publication, suspend model-led ranking or enter a visible degraded mode.
4. **Preserve evidence:** retain source snapshots, configuration, model version, decision events and run hashes.
5. **Escalate:** name the accountable owner, escalation route and response target.
6. **Recover:** restore the last approved state or use a non-model process.
7. **Learn:** reconcile source and output counts, identify the control gap and add a regression test.

## Fail-closed controls

The synthetic exercises block the affected output when any of the following occurs:

- stale referral feed;
- duplicate primary keys;
- unknown appointment status;
- missing decision audit events;
- unapproved KPI-definition change.

A blocking control is scoped to the affected product. It does not imply that every operational activity must stop.

## Model suspension and degraded mode

Calibration drift, high serving-feature missingness and unreliable subgroup performance suspend personalised ranking. The fallback is the standard non-model reminder workflow. The project never uses the attendance score to diagnose, select treatment, determine eligibility, cancel an appointment or lower clinical priority.

## Stress-test interpretation

The Monte Carlo exercise samples demand, capacity and DNA shocks from declared synthetic distributions. It compares five response policies using:

- mean and P90 end backlog;
- CVaR95 end backlog, the mean of the worst 5% of simulations;
- probability of exceeding the declared red backlog threshold;
- mean and P90 wait proxy;
- 12-week planning cost proxy.

The lowest-risk policy is not automatically recommended. Decision makers must review assumptions, affordability, workforce feasibility, patient burden and clinical safety.

## Early warning

The EWMA exercise injects a referral-demand shift after week five. It demonstrates that a sustained moderate change may be detected earlier than waiting for a single extreme week. Control limits are synthetic and must be calibrated to a real data-generating process before use.

## Production gaps

A real deployment would additionally require:

- approved incident severity definitions and service-level objectives;
- identity, authorisation and immutable audit infrastructure;
- tested backup, restore and infrastructure rollback;
- live feature-store and training-serving reconciliation;
- clinical safety case and hazard log where applicable;
- data protection impact assessment and retention controls;
- real tabletop and failover exercises with named participants;
- post-incident review, tracked corrective actions and independent assurance.
