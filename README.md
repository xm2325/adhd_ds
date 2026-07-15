# adhd_ds

A synthetic healthcare data-science project showing how an ADHD service could monitor patient flow, plan clinical capacity, support appointment attendance, record operational decisions, and expose controlled analytical products through a service layer.

> **Synthetic demonstration only.** This repository is not affiliated with Care ADHD or another provider. It contains no real patient or company data. All thresholds, costs, effects, alerts, recommendations, identifiers, and results are portfolio assumptions.

## v0.5: from control tower to auditable service layer

Version 0.5 adds the controls needed to move from an interactive portfolio dashboard toward a production-style analytical service:

1. **Versioned data contracts** — schema, primary-key, row-count, type, nullability, and allowed-value checks run before metric calculation.
2. **Run manifest and source fingerprints** — every build records a run ID, configuration hashes, package version, source-table SHA-256 fingerprints, output hashes, and replay command.
3. **Controlled FastAPI service** — aggregate controls are available through documented endpoints; the appointment-support queue requires an operational role header and returns a minimised field set.
4. **Queue-policy simulation** — compares oldest-first, stage-readiness, funding-route-balanced, and service-group-balanced allocation under the same weekly capacity.
5. **Incident register** — red controls and robust anomalies become run-linked triage records with an owner, playbook, and rollback trigger.
6. **Eighth dashboard workspace** — audit, contract, lineage, incident, queue-policy, and API evidence are shown alongside the existing operating views.

## Decision order

```text
source-like data
    → versioned data-contract gate
    → coded data-quality gate
    → approved metrics
    → service-level and anomaly review
    → patient-pathway analysis
    → demand forecast
    → capacity and outreach scenarios
    → budget-constrained plan
    → queue-policy comparison
    → controlled intervention pilot
    → owner, due date, and decision record
    → incident, model, and service monitoring
    → run manifest and replay evidence
```

Machine learning appears after data, metric, and service-flow checks because an appointment model cannot repair a referral-processing or assessment-capacity problem.

## Eight connected workspaces

1. Operations command centre
2. Patient pathway
3. Demand and capacity
4. Appointment support
5. Decision and service impact
6. Optimisation and pilot design
7. Data and model controls
8. Audit and service API

## Main outputs

| Output | Purpose |
|---|---|
| `reports/operations_dashboard.html` | Fully self-contained interactive dashboard |
| `docs/index.html` | Smaller CDN-based dashboard build |
| `results/data_contract_status.csv` | Versioned source-contract evidence |
| `results/source_profiles.csv` | Row counts, event ranges, and source fingerprints |
| `results/run_manifest.json` | Run ID, config hashes, source profiles, output hashes, and replay command |
| `results/queue_policy_comparison.csv` | Same-capacity operational queue-policy comparison |
| `results/queue_policy_assignments.csv` | Synthetic policy assignments and rank evidence |
| `results/incident_register.csv` | Run-linked signals, owners, playbooks, and rollback triggers |
| `results/data_lineage.csv` | Source-to-transformation-to-decision map |
| `results/service_level_status.csv` | Green/amber/red operational and analytical controls |
| `results/resource_optimisation.csv` | Resource-plan grid and Pareto flag |
| `results/experiment_design.csv` | Reminder-pilot sample-size scenarios |
| `results/model_registry.csv` | Champion and challenger metadata |
| `results/operational_action_queue.csv` | Owner, due date, decision, and escalation |
| `reports/weekly_operational_brief.md` | Manager-facing weekly summary |
| `reports/monthly_control_pack.md` | Monthly service, model, and audit pack |

## Current deterministic synthetic run

The fixed-seed build produces:

- 4,911 patients and referrals;
- 9,869 appointments;
- 200/200 passing data-contract rules;
- median referral-to-completed-assessment time of 71.12 days;
- P90 referral-to-completed-assessment time of 93.92 days;
- baseline 12-week backlog of 1,121.6 patients;
- four red service or analytical controls;
- three amber/red weekly anomaly flags;
- 25 resource plans and 13 Pareto-efficient plans;
- a £10,000 synthetic budget recommendation of 540 extra assessment minutes per week and no additional outreach contacts;
- an approximate total sample size of 9,212 appointments for the configured 15% relative DNA-reduction assumption;
- four queue-allocation policies evaluated under 120 weekly review slots;
- six open or triage incident records linked to the build run ID;
- logistic-regression champion PR-AUC of 0.364 and Brier score of 0.095 on later synthetic data.

These values test software and decision logic. They are not provider estimates.

## Run locally

```bash
python -m pip install -e .[dev]
python -m adhd_ops.orchestrator --root .
pytest
```

Open:

```text
reports/operations_dashboard.html
```

## Run the controlled API

Build the analytical outputs first, then start the service:

```bash
ADHD_DS_ROOT=. adhd-ds-api
```

FastAPI documentation is available locally at:

```text
http://127.0.0.1:8000/docs
```

Examples:

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/v1/service-levels
curl "http://127.0.0.1:8000/v1/budget-recommendation?budget_gbp=10000"
curl -H "X-Role: patient_support" "http://127.0.0.1:8000/v1/appointment-support?limit=20"
```

The role header demonstrates least-privilege behaviour. It is not production identity or authorisation.

## Safety and factual boundaries

- The appointment model may support reminders, confirmation requests, and easier rescheduling only.
- It must not determine diagnosis, treatment, service eligibility, automatic cancellation, or lower care priority.
- Queue-policy simulation allocates operational review capacity; it is not clinical-priority scoring.
- Cost fields are planning proxies.
- Reminder effects are untested assumptions until evaluated in a controlled design.
- Scenario differences are sensitivity analyses rather than causal estimates.
- Browser role views and API headers are demonstrations, not a security system.
- A real deployment needs identity management, database-level permissions, immutable audit logs, incident ownership, retention controls, and clinical/information-governance approval.

## Repository map

```text
config/                  synthetic parameters, thresholds, contracts, budgets, and pilot assumptions
docs/                    metrics, governance, API, contract, incident, and queue-policy runbooks
sql/                     Microsoft SQL Server-oriented warehouse examples
src/adhd_ops/            pipeline, control tower, audit layer, API, and dashboard modules
tests/                   data, contract, API, model, optimisation, workflow, and dashboard tests
results/                 analytical products, manifests, incidents, and action records
reports/                 interactive dashboard and management packs
tableau/exports/         dashboard-ready CSV extracts
.github/workflows/       test and build automation
```
