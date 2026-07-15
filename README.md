# adhd_ds

A synthetic healthcare data-science project that demonstrates how an ADHD service could monitor patient flow, plan clinical capacity, support appointments, and record operational decisions.

> **Synthetic demonstration only.** This repository is not affiliated with Care ADHD or another healthcare provider. It contains no real patient or company data. Every threshold, cost proxy, alert, recommendation, model result, and identifier is generated for portfolio use.

## v0.3: from dashboard to operating workspace

The project now models the full path from data refresh to an owned decision:

```text
source-like data
    → blocking data-quality gate
    → approved metric definitions
    → patient pathway and exception review
    → referral forecast
    → demand/capacity scenarios
    → appointment-support ranking
    → resource and impact comparison
    → owner, due date, status and decision rationale
    → monthly model and forecast monitoring
```

The interactive HTML contains six connected workspaces:

1. **Operations command centre** — filtered service KPIs, pathway conversion, backlog scenarios, and a rule-based decision queue.
2. **Patient pathway** — Sankey flow, wait distributions, cohort heatmap, segment comparison, exception queue, and referral timeline drill-down.
3. **Demand and capacity** — forecast intervals, stored scenarios, interactive queue planning, and comparable scenario outputs.
4. **Appointment support** — capacity-limited ranking, calibration, group monitoring, queue export, and safe-use controls.
5. **Decision and service impact** — resource/cost proxies, outreach assumptions, editable decision register, role matrix, CSV export, and print view.
6. **Data and model controls** — quality gates, model comparison, monthly calibration monitoring, rolling-origin forecast monitoring, ownership, and change control.

## What v0.3 adds

### Decision ownership and audit path

`results/operational_action_queue.csv` now records:

- signal and source metric;
- evidence;
- owner and escalation route;
- created and due dates;
- status and decision note;
- review cadence;
- synthetic-data flag.

The browser dashboard lets a reviewer edit owner, due date, status, and rationale. These changes are saved in browser `localStorage` and can be exported as CSV. This is a front-end demonstration; a production system would use an authenticated API and immutable audit history.

### Role-based workflow simulation

The dashboard provides Executive, Operations, Patient support, and Data/model role profiles. Each profile has an allowed view set and a patient-level access flag. Patient queues are hidden from aggregate-only roles.

This is a UI simulation, not a security boundary. Real access control must be enforced by the application and data platform.

### Resource and impact analysis

`results/scenario_impact.csv` compares stored capacity scenarios using:

- end backlog and wait proxy;
- change from baseline;
- weekly clinical-minute change;
- 12-week cost proxy;
- backlog patients avoided;
- cost per backlog patient avoided when applicable.

`results/outreach_impact.csv` compares outreach capacity using a declared relative DNA-reduction assumption. It reports expected appointments recovered and synthetic resource-value proxies. These values are not causal estimates or provider costs.

### Monitoring that creates actions

`results/attendance_monitoring.csv` reports monthly:

- sample size;
- observed DNA rate;
- mean predicted probability;
- calibration gap;
- Brier score.

`results/forecast_monitoring.csv` attaches dates to rolling-origin forecast errors. Review levels are declared in `config/operations.yaml`. When a reliable monitoring period crosses a review level, the pipeline adds an owned action to the operational register.

## Main outputs

| Output | Purpose |
|---|---|
| `reports/operations_dashboard.html` | Fully self-contained interactive workspace; opens without a server |
| `docs/index.html` | Smaller CDN-based build for a controlled static host |
| `results/operational_action_queue.csv` | Owned action and decision register seed |
| `results/scenario_impact.csv` | Scenario resource and cost-proxy comparison |
| `results/outreach_impact.csv` | Outreach capacity and assumed-impact comparison |
| `results/attendance_monitoring.csv` | Monthly appointment-model monitoring |
| `results/forecast_monitoring.csv` | Dated rolling-origin forecast monitoring |
| `reports/weekly_operational_brief.md` | Manager-facing headline, evidence, recommendation and decision request |
| `reports/data_quality_report.html` | Rule-level publication gate |
| `tableau/exports/` | Tableau-ready analytical extracts |

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

The checked-in configuration produces:

- 4,911 synthetic referrals;
- 9,869 synthetic appointments;
- median referral-to-completed-assessment time of 71.12 days;
- P90 referral-to-completed-assessment time of 93.92 days;
- baseline simulated backlog of 1,121.6 patients at the 12-week horizon;
- logistic appointment-support model PR-AUC of 0.364 and Brier score of 0.095;
- four open operational/model-review actions plus one recorded data-quality gate;
- `add_one_assessment_clinic` as the stored scenario with the lowest synthetic end backlog.

These numbers prove that the code and workflow run. They are not estimates for a real provider.

## Decision and safety boundaries

The appointment model may support only:

- standard reminder;
- additional reminder;
- confirmation request;
- easier rescheduling.

It must not be used for diagnosis, treatment selection, service eligibility, automatic cancellation, or lower care priority.

A real implementation would also require source reconciliation, metric approval, clinical and operational review, information-governance approval, role-based access, external validation, workflow testing, equality-impact review, audit logging, incident management, and ongoing monitoring.

## Repository map

```text
config/                  synthetic data, scenarios, thresholds, roles and cost proxies
data/synthetic/          generated source-like tables
docs/                    operating guide, metrics, governance, roles and decisions
sql/                     MS SQL Server-oriented warehouse examples
src/adhd_ops/            executable analytical and dashboard pipeline
tests/                   reproducibility, leakage, workflow, impact and monitoring tests
results/                 analytical tables, monitoring and action register
reports/                 self-contained dashboard and management reports
tableau/exports/         dashboard-ready CSV extracts
.github/workflows/       test, build and review-pack automation
```
