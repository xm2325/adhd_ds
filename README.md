# adhd_ds

An evidence-backed synthetic healthcare data-science platform showing how an ADHD service could move from source data to trusted metrics, operational diagnosis, prediction, experiments, implementation decisions, incidents and replayable evidence.

> **Synthetic demonstration only.** The repository contains no real patient or company data and is not affiliated with Care ADHD or another provider. All costs, thresholds, effects, identifiers and results are portfolio assumptions.

## v0.7: evidence-backed DS operating handbook

Version 0.7 expands the project from a 42-question scenario lab to a **106-question, 13-category operating handbook**. Each question is attached to:

- a run-specific synthetic answer;
- one or more generated project data products;
- peer-reviewed methods papers, reporting guidelines or official standards;
- an explicit claim type: descriptive, inferential, predictive, scenario, causal, safety, operational, governance or decision;
- a decision-readiness state and evidence gap;
- a named output, risk if wrong and next action.

The build fails when a question has no literature support or no project-data support.

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

## Ten connected dashboard workspaces

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

The tenth workspace includes literature coverage, method selection, KPI uncertainty, subgroup reliability, evidence gaps and official external-data sources.

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
| `reports/operations_dashboard.html` | Self-contained ten-workspace interactive dashboard |

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
- logistic-regression champion PR-AUC of 0.364 and Brier score of 0.095.

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
- Real deployment requires managed identity, clinical safety, information governance, human-factors evaluation and ongoing monitoring.

## Repository map

```text
config/                  contracts, questions, evidence and external-data registries
docs/                    metric, evidence, API, safety and operating guidance
sql/                     Microsoft SQL Server warehouse and diagnostic examples
src/adhd_ops/            analytics, evidence, diagnostics, API and dashboard modules
tests/                   data, evidence, model, API, workflow and dashboard tests
results/                 generated analytical, evidence and audit products
reports/                 generated dashboards, casebooks and management packs
tableau/exports/         generated dashboard-ready extracts
.github/workflows/       test, build and review-pack automation
```
