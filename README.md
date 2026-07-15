# adhd_ds

A synthetic healthcare data-science project that shows how an ADHD service could monitor patient flow, plan clinical capacity, support appointment attendance, record operational decisions, and monitor analytical controls.

> **Synthetic demonstration only.** This repository is not affiliated with Care ADHD or another provider. It contains no real patient or company data. All thresholds, costs, effects, alerts, recommendations, and results are portfolio assumptions.

## What v0.4 adds

Version 0.4 turns the dashboard into an operations control tower:

1. **Service-level control board** — patient access, backlog, pathway completion, data quality, calibration, and forecast error use declared green/amber/red rules.
2. **Robust anomaly triage** — rolling-median and median-absolute-deviation checks flag unusual referral volume and DNA rate without assigning cause.
3. **Budget-constrained resource planning** — enumerates assessment minutes and outreach capacity, identifies Pareto-efficient plans, and recommends the lowest-backlog option under each budget.
4. **Pilot design** — calculates approximate sample size for reminder-effect assumptions and lists patient-experience guardrails.
5. **Champion–challenger registry** — records model status, feature signature, test period, probability quality, and a controlled promotion flag.
6. **Seven connected workspaces** — command centre, pathway, capacity, appointment support, decision impact, optimisation and pilot design, and data/model controls.

## Decision order

```text
source-like data
    → data-quality gate
    → approved metrics
    → service-level and anomaly review
    → patient-pathway analysis
    → demand forecast
    → capacity and outreach scenarios
    → budget-constrained plan
    → controlled intervention pilot
    → owner, due date, and decision record
    → model and service monitoring
```

Machine learning appears after data, metric, and service-flow checks because an appointment model cannot repair a referral-processing or assessment-capacity problem.

## Main outputs

| Output | Purpose |
|---|---|
| `reports/operations_dashboard.html` | Fully self-contained interactive dashboard |
| `docs/index.html` | Smaller CDN-based dashboard build |
| `results/service_level_status.csv` | Green/amber/red operational and analytical controls |
| `results/weekly_anomalies.csv` | Robust weekly anomaly triage |
| `results/resource_optimisation.csv` | Full resource-plan grid and Pareto flag |
| `results/budget_recommendations.csv` | Best enumerated plan under each declared budget |
| `results/experiment_design.csv` | Reminder-pilot sample-size scenarios |
| `results/model_registry.csv` | Champion and challenger metadata |
| `results/champion_challenger_monitoring.csv` | Monthly model comparison |
| `results/operational_action_queue.csv` | Owner, due date, decision, and escalation |
| `reports/weekly_operational_brief.md` | Manager-facing weekly summary |
| `reports/monthly_control_pack.md` | Monthly service and model control pack |

## Current deterministic synthetic run

The fixed-seed build produces:

- 4,911 referrals and 9,869 appointments;
- median referral-to-completed-assessment time of 71.12 days;
- P90 referral-to-completed-assessment time of 93.92 days;
- baseline 12-week backlog of 1,121.6 patients;
- four red service or analytical controls;
- three amber/red weekly anomaly flags;
- 13 Pareto-efficient resource plans from 25 enumerated plans;
- a £10,000 synthetic budget recommendation of 540 extra assessment minutes per week and no additional outreach contacts;
- an approximate total sample size of 9,212 appointments for a conventional two-arm test of the configured 15% relative DNA-reduction assumption;
- logistic-regression champion PR-AUC of 0.364 and Brier score of 0.095 on later synthetic data.

These values test the software and decision logic. They are not provider estimates.

## Run locally

```bash
python -m pip install -e .[dev]
python -m adhd_ops.pipeline --root .
pytest
```

Open:

```text
reports/operations_dashboard.html
```

## Safety boundary

The appointment model may support only reminders, confirmation requests, and easier rescheduling. It must not be used for diagnosis, treatment selection, service eligibility, automatic cancellation, or lower care priority.

Cost fields are planning proxies. Reminder effects are untested assumptions. Scenario differences are sensitivity analyses rather than causal estimates. The role selector is a user-interface demonstration and not an access-control system.

## Repository map

```text
config/                  synthetic parameters, thresholds, costs, budgets, and pilot assumptions
docs/                    metrics, governance, runbooks, experiment and model-promotion policies
sql/                     Microsoft SQL Server-oriented warehouse examples
src/adhd_ops/            executable pipeline and dashboard modules
tests/                   data, model, optimisation, experiment, workflow, and dashboard tests
results/                 analytical products and action records
reports/                 interactive dashboard and management packs
tableau/exports/         dashboard-ready CSV extracts
.github/workflows/       test and build automation
```
