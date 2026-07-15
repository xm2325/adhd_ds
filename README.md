# adhd_ds

A synthetic healthcare data-science project showing how an ADHD service could move from source data to trusted metrics, operational diagnosis, predictive support, controlled experiments, decisions, incidents, and replayable evidence.

> **Synthetic demonstration only.** This repository is not affiliated with Care ADHD or another provider. It contains no real patient or company data. All thresholds, costs, effects, alerts, recommendations, identifiers, and results are portfolio assumptions.

## v0.6: data scientist scenario lab

Version 0.6 is designed around the questions a healthcare data scientist is asked in real work rather than around isolated model outputs.

It adds:

1. **42 stakeholder questions with run-specific answers** — each question identifies the stakeholder, why it is asked, analysis method, inputs, output, risk if wrong, and next action.
2. **Root-cause triage** — combines demand, capacity, administrative delay, attendance, pathway and data-reliability evidence without presenting diagnostic hypotheses as causal conclusions.
3. **Pathway-stage decomposition** — separates referral processing, initial contact, booking, appointment queue, assessment delivery, and treatment transition.
4. **Metric-definition sensitivity** — shows how referral-received, accepted, contacted, and booking-based waiting-time definitions answer different decisions.
5. **DNA change decomposition** — separates observed case-mix change from within-segment rate change across appointment type, lead time, reminder pattern, funding route, service group, and weekday.
6. **Threshold and workload policy grid** — evaluates probability thresholds and weekly outreach capacity using precision, recall, expected synthetic recoveries, and group-selection gaps.
7. **Predictive explanation with a causal boundary** — exposes the largest fitted coefficients or importances while explicitly stating that prediction is not intervention evidence.
8. **Ninth dashboard workspace** — an interactive DS scenario lab with a question selector, diagnostic scorecard, stage chart, rate decomposition, policy heatmap, and evidence boundaries.

## Decision order

```text
source-like data
    → versioned data-contract gate
    → coded data-quality gate
    → approved metric definitions
    → adjacent-period and source-coverage review
    → pathway-stage and root-cause diagnosis
    → demand forecast and capacity scenarios
    → appointment-support model and threshold policy
    → budget-constrained plan
    → controlled intervention pilot
    → owner, due date, decision and incident record
    → model and service monitoring
    → run manifest, casebook and replay evidence
```

Machine learning appears after data, metric and service-flow checks because an appointment model cannot repair a referral-processing or assessment-capacity problem.

## Nine connected workspaces

1. Operations command centre
2. Patient pathway
3. Demand and capacity
4. Appointment support
5. Decision and service impact
6. Optimisation and pilot design
7. Data and model controls
8. Audit and service API
9. Data scientist scenario lab

## Main v0.6 outputs

| Output | Question answered |
|---|---|
| `reports/ds_question_casebook.md` | What will clinical, operational, product, finance, engineering and governance colleagues ask, and how should the DS answer? |
| `results/ds_question_catalog.csv` | Structured question, method, evidence, risk and next-action library |
| `results/root_cause_scorecard.csv` | Which hypotheses should be investigated first? |
| `results/period_comparison.csv` | What changed compared with the previous 12-week operating period? |
| `results/stage_duration_decomposition.csv` | Where does pathway time accumulate? |
| `results/metric_definition_sensitivity.csv` | Why do defensible waiting-time definitions differ? |
| `results/dna_change_decomposition.csv` | Which observed case-mix and within-segment changes explain the DNA-rate movement? |
| `results/threshold_policy_grid.csv` | What threshold and workload trade-off follows from finite outreach capacity? |
| `results/model_feature_effects.csv` | Which terms drive the fitted prediction, without claiming causality? |
| `results/source_freshness.csv` | What event coverage exists, and why is extract freshness still unknown without refresh metadata? |
| `results/missingness_audit.csv` | Which missing fields are structural, investigatory or blocking? |
| `reports/operations_dashboard.html` | Fully self-contained nine-workspace interactive dashboard |

Existing v0.5 outputs remain, including contracts, source fingerprints, run manifest, incidents, queue policies, resource optimisation, experiment design, model registry, operational actions, weekly brief and monthly control pack.

## Current deterministic synthetic run

The fixed-seed build produces:

- 4,911 patients and referrals;
- 9,869 appointments;
- 200/200 passing data-contract rules;
- 42 run-specific stakeholder questions;
- median referral-to-completed-assessment time of 71.12 days;
- P90 referral-to-completed-assessment time of 93.92 days;
- appointment-queue time as the largest complete-pathway stage;
- capacity pressure as the strongest diagnostic hypothesis;
- baseline 12-week backlog of 1,121.6 patients;
- a £10,000 synthetic plan of 540 additional assessment minutes per week and no additional outreach contacts;
- an approximate sample size of 9,212 appointments for the configured 15% relative DNA-reduction assumption;
- logistic-regression champion PR-AUC of 0.364 and Brier score of 0.095 on later synthetic data.

These values test the software and decision logic. They are not provider estimates.

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
```

## Run the controlled API

```bash
ADHD_DS_ROOT=. adhd-ds-api
```

Local API documentation:

```text
http://127.0.0.1:8000/docs
```

Example endpoints:

```bash
curl http://127.0.0.1:8000/v1/ds-questions
curl "http://127.0.0.1:8000/v1/ds-questions?category=appointment_and_model"
curl http://127.0.0.1:8000/v1/diagnostics/root-causes
curl "http://127.0.0.1:8000/v1/diagnostics/threshold-policy?weekly_capacity=100"
curl http://127.0.0.1:8000/v1/diagnostics/metric-sensitivity
curl -H "X-Role: patient_support" "http://127.0.0.1:8000/v1/appointment-support?limit=20"
```

The role header demonstrates least-privilege behaviour. It is not production identity or authorisation.

## Evidence boundaries

- Descriptive decomposition is not causal attribution.
- Model coefficients and feature importance are not intervention effects.
- Recent cohorts can be right-censored and require maturity controls.
- Queue policies allocate operational review capacity; they are not clinical-priority scoring.
- Cost fields are planning proxies rather than provider finance data.
- Reminder effects remain assumptions until evaluated with a defensible causal design.
- Event coverage is not source refresh freshness; production needs extract timestamps and SLAs.
- Browser role views and API headers are demonstrations rather than security controls.
- A real deployment needs managed identity, database permissions, immutable audit logs, retention controls, clinical review and information-governance approval.

## Repository map

```text
config/                  synthetic parameters, contracts, thresholds, questions and pilot assumptions
docs/                    metrics, governance, API, scenario, incident and queue-policy runbooks
sql/                     Microsoft SQL Server-oriented warehouse and diagnostic examples
src/adhd_ops/            pipeline, diagnostics, casebook, API and dashboard modules
tests/                   data, contract, diagnostic, API, model, workflow and dashboard tests
results/                 analytical products, questions, manifests, incidents and action records
reports/                 interactive dashboard, casebook and management packs
tableau/exports/         dashboard-ready CSV extracts
.github/workflows/       test and build automation
```
