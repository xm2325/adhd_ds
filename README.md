# adhd_ds

A synthetic healthcare data-science project that models how an ADHD service could monitor patient flow, plan clinical capacity, and manage appointment-support work.

> **Synthetic demonstration only.** This repository is not affiliated with Care ADHD or another healthcare provider. It contains no real patient or company data. Every operational value, threshold, alert, recommendation, and model result is generated for portfolio use.

## What changed in v0.2

The original report was a static set of charts. The current release is an interactive operations workspace with five connected views:

1. **Operations command centre** — live filters, service KPIs, a decision queue, patient flow, scenario outcomes, and the operating-week control loop.
2. **Patient pathway** — Sankey flow, waiting-time distributions, cohort heatmap, segment comparison, and a synthetic open-case exception queue.
3. **Demand and capacity** — forecast intervals, stored scenarios, an interactive browser-based capacity planner, and a decision table.
4. **Appointment support** — outreach-capacity and risk-threshold controls, model calibration, group monitoring, queue export, and safe-use rules.
5. **Data and model controls** — automated data gates, forecast and appointment-model comparison, ownership, cadence, and change-control evidence.

The dashboard is not only a presentation layer. The pipeline also writes a structured `operational_action_queue.csv` so findings can be assigned to an owner, reviewed on a fixed cadence, and recorded.

## Problem and analysis order

The decision question is:

> How can a service reduce waiting time and unused clinical capacity without reducing fairness or clinical safety?

The analysis follows the order used in an operational team:

```text
source-like data
    → automated data-quality gate
    → approved metric definitions
    → patient pathway and exception queues
    → referral forecast
    → demand/capacity scenarios
    → appointment-support ranking
    → owner, decision and review cadence
```

Machine learning appears late in the process because an appointment model cannot correct a referral-processing or assessment-capacity problem.

## Main outputs

| Output | Purpose |
|---|---|
| `reports/operations_dashboard.html` | Fully self-contained interactive dashboard; opens without a server |
| `docs/index.html` | Smaller CDN-based dashboard build suitable for a web host |
| `results/operational_action_queue.csv` | Structured service-wide decisions and owners |
| `reports/weekly_operational_brief.md` | Manager-facing headline, evidence, recommendation and decision request |
| `reports/data_quality_report.html` | Rule-level data-quality gate |
| `results/` | Pathway, forecast, capacity, model, calibration and queue tables |
| `tableau/exports/` | CSV extracts for a Tableau implementation |

## Dashboard operating flow

The synthetic operating process is documented in [`docs/dashboard_guide.md`](docs/dashboard_guide.md). In summary:

- **Every refresh:** load sources and run blocking data checks.
- **Daily:** review long waits, incomplete pathway stages, and the appointment-support queue.
- **Weekly:** compare demand and capacity assumptions before agreeing the roster.
- **Monthly:** review forecast error, probability calibration, group behaviour, overrides, and metric changes.

Every alert threshold is declared in [`config/operations.yaml`](config/operations.yaml). These are portfolio defaults, not company targets or clinical standards.

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

The pipeline is deterministic because `config/synthetic_data.yaml` fixes the random seed.

## Current deterministic synthetic run

The checked-in demonstration produces:

- 4,911 synthetic referrals;
- 9,869 synthetic appointments;
- median referral-to-completed-assessment time of 71.12 days;
- P90 referral-to-completed-assessment time of 93.92 days;
- baseline simulated backlog of 1,121.6 patients at the 12-week horizon;
- logistic appointment-support model PR-AUC of 0.364 and Brier score of 0.095 on later synthetic data.

These numbers prove that the code runs. They are not estimates for a real provider.

## Safety boundary

The appointment model may support only:

- standard reminder;
- additional reminder;
- confirmation request;
- easier rescheduling.

It must not be used for diagnosis, treatment selection, service eligibility, automatic cancellation, or lower care priority. A real implementation would also require metric approval, source reconciliation, information-governance review, role-based access, external validation, workflow testing, and ongoing monitoring.

## Repository map

```text
config/                  synthetic data, scenarios and operating thresholds
data/synthetic/          generated source-like tables
docs/                    dashboard guide, metrics, governance and decisions
sql/                     MS SQL Server-oriented warehouse examples
src/adhd_ops/            executable analytical pipeline
tests/                   reproducibility, leakage, data, workflow and dashboard tests
results/                 analytical tables and structured action queue
reports/                 self-contained dashboard and management reports
tableau/exports/         dashboard-ready CSV extracts
.github/workflows/       test, build and report-artifact automation
```
