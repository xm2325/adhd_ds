# adhd_ds

An evidence-backed synthetic healthcare data-science platform showing how an ADHD service could move from source data to trusted metrics, operational diagnosis, prediction, experiments, implementation decisions, incidents and replayable evidence.

> **Synthetic demonstration only.** The repository contains no real patient or company data and is not affiliated with Care ADHD or another provider. All costs, thresholds, effects, identifiers and results are portfolio assumptions.

## v0.8: operational resilience and incident simulation

Version 0.8 turns the evidence-backed handbook into an **operational resilience and incident simulation platform**. It retains the 106-question, 13-category casebook and adds:

- 12 deterministic data, model, fairness, experiment, capacity, service and audit incident exercises;
- P0–P3 acknowledgement, containment and target-resolution decisions;
- fail-closed publication controls and visible non-model degraded modes;
- 1,000-draw Monte Carlo stress tests for five capacity and outreach response policies;
- mean, P90 and CVaR95 backlog risk plus probability of exceeding a declared red threshold;
- an EWMA early-warning exercise with an injected demand shift;
- named owners, escalation routes, rollback paths, human-approval gates and evidence boundaries;
- an eleventh dashboard workspace and resilience API endpoints.

Every incident exercise cites methods or standards already held in the evidence registry. The sources support the control design; they do not validate the injected values, provider-specific impact or portfolio response targets.

## Question coverage

1. Data and metric definitions
2. Patient pathway and waiting time
3. Appointment attendance and predictive support
4. Forecasting and capacity
5. Experimentation
6. Governance and communication
7. Statistical inference and uncertainty
8. Causal inference and policy evaluation
9. Model development and validation
10. Fairness, safety and human factors
11. Production ML and monitoring
12. Privacy, security and information governance
13. Product economics and implementation

## Eleven connected dashboard workspaces

1. Operations command centre
2. Patient pathway
3. Demand and capacity
4. Appointment support
5. Decision and service impact
6. Optimisation and pilot design
7. Data and model controls
8. Audit and service API
9. Data scientist scenario lab
10. Evidence and methods
11. Operational resilience lab

The eleventh workspace adds incident selection, severity and SLA decisions, stress-test risk frontiers, EWMA early warning and a resilience control scorecard.

## Main evidence outputs

| Output | Purpose |
|---|---|
| `reports/ds_question_casebook.md` | 106 run-specific questions, answers, literature, data support and next actions |
| `reports/evidence_backed_ds_handbook.md` | Evidence registry, method-selection matrix and external-data registry |
| `results/ds_question_catalog.csv` | Machine-readable question and decision library |
| `results/evidence_registry.csv` | Peer-reviewed and official evidence sources |
| `results/external_data_registry.csv` | NHS/ONS sources for real-world contextual validation |
| `results/evidence_coverage.csv` | Literature and project-data coverage by category |
| `results/evidence_gap_register.csv` | What remains necessary before real-world decisions are ready |
| `results/method_selection_matrix.csv` | Decision question → method → assumptions → avoid rules |
| `results/kpi_uncertainty.csv` | KPI point estimates with 95% intervals |
| `results/subgroup_reliability.csv` | Sample size, event count, intervals and reliability status |
| `results/incident_simulation_results.csv` | Detection, severity, response, ownership, fallback and evidence boundary for 12 exercises |
| `results/stress_test_summary.csv` | Monte Carlo mean, P90, CVaR95, red-threshold probability and cost proxy by policy |
| `results/early_warning_signals.csv` | EWMA control-limit exercise after an injected demand shift |
| `results/resilience_scorecard.csv` | Control-presence checks for fail-closed, suspension, fallback, ownership and human approval |
| `reports/operations_dashboard.html` | Self-contained eleven-workspace interactive dashboard |

All v0.6 diagnostic, audit, model, capacity and experiment outputs remain.

## Current deterministic synthetic run

The fixed-seed build produces:

- 4,911 patients and referrals;
- 9,869 appointments;
- 200/200 passing source-contract checks;
- 106 evidence-backed questions across 13 categories;
- 35 literature, reporting-guideline or official-standard sources;
- 7 official NHS/ONS external-data sources for contextual validation;
- 106/106 questions with literature support;
- 106/106 questions with run-specific project-data support;
- median referral-to-assessment time of 71.12 days and P90 of 93.92 days;
- capacity pressure as the strongest descriptive diagnostic hypothesis;
- baseline 12-week backlog of approximately 1,122 patients;
- logistic-regression champion PR-AUC of 0.364 and Brier score of 0.095;
- 12 synthetic incident exercises and nine resilience control-presence checks;
- 5,000 stress-test simulations across five response policies;
- a deterministic EWMA warning after the injected referral-demand shift.

These values test the software and analytical logic. They are not estimates for a real provider.

## Evidence hierarchy

```text
source contract and semantic definition
    → descriptive estimate and uncertainty
    → predictive validation and calibration
    → scenario analysis under declared assumptions
    → causal experiment or identification strategy
    → implementation, safety and governance evidence
    → monitored decision with rollback
```

Literature supports method choice. It does not convert synthetic results into provider evidence.

## Run locally

```bash
python -m pip install -e .[dev]
python -m adhd_ops.orchestrator --root .
pytest -q
```

Open:

```text
reports/operations_dashboard.html
reports/ds_question_casebook.md
reports/evidence_backed_ds_handbook.md
```

## API

```bash
ADHD_DS_ROOT=. adhd-ds-api
```

Selected endpoints:

```text
GET /v1/ds-questions
GET /v1/evidence
GET /v1/evidence/coverage
GET /v1/evidence/gaps
GET /v1/statistics/kpi-uncertainty
GET /v1/statistics/subgroup-reliability
GET /v1/resilience/incidents
GET /v1/resilience/stress-tests
GET /v1/resilience/early-warning
GET /v1/resilience/scorecard
GET /v1/diagnostics/root-causes
GET /v1/appointment-support
```

The patient-level endpoint remains restricted to declared operational roles and returns a minimised field set. The role header is a demonstration, not production authentication.

## Evidence boundaries

- Descriptive decomposition is not causal attribution.
- Feature importance is not an intervention effect.
- A narrow confidence interval does not remove systematic bias.
- Recent cohorts may be right-censored.
- Small subgroup estimates may be unreliable even when aggregate performance is stable.
- Scenario savings are conditional planning outputs, not realised financial impact.
- External NHS aggregates are contextual benchmarks, not automatically comparable controls.
- Stress-test distributions, thresholds, costs and response targets are synthetic assumptions rather than forecasts or provider SLAs.
- A control-presence pass is not production assurance; real tabletop, failover, restore and rollback exercises remain necessary.
- Real deployment requires managed identity, clinical safety, information governance, human-factors evaluation and ongoing monitoring.

## Repository map

```text
config/                  contracts, questions, evidence, resilience and external-data registries
docs/                    metric, evidence, API, safety and operating guidance
sql/                     Microsoft SQL Server warehouse and diagnostic examples
src/adhd_ops/            analytics, evidence, diagnostics, resilience, API and dashboard modules
tests/                   data, evidence, model, API, workflow and dashboard tests
results/                 generated analytical, evidence and audit products
reports/                 generated dashboards, casebooks and management packs
tableau/exports/         generated dashboard-ready extracts
.github/workflows/       test, build and review-pack automation
```
