# Changelog

## 0.8.0 — operational resilience and incident simulation

- Added 12 synthetic incident exercises covering source freshness, duplicate keys, schema drift, demand surge, capacity loss, calibration drift, feature missingness, subgroup harm signals, experiment guardrails, service latency, audit gaps and unapproved metric changes.
- Added P0–P3 acknowledgement, containment and target-resolution decision matrix.
- Added fail-closed publication, model-suspension, degraded-mode, owner, escalation and rollback records.
- Added 1,000-draw Monte Carlo stress tests per policy across five response strategies.
- Added mean, P90 and CVaR95 backlog risk, red-threshold probability, wait proxy and planning cost outputs.
- Added an EWMA early-warning exercise with an injected referral-demand shift.
- Added an eleventh Operational resilience dashboard workspace.
- Added aggregate resilience API endpoints and a resilience incident runbook.
- Added regression tests for incident completeness, human approval, tail risk, policy trade-offs and shift detection.

## 0.7.0 — evidence-backed DS operating handbook

- Expanded the question library from 42 to 106 questions across 13 categories.
- Added a 34-source literature, reporting-guideline and official-standard registry.
- Added seven official NHS/ONS external-data sources for contextual validation.
- Added claim types, decision-readiness states, evidence boundaries and evidence-gap records.
- Added KPI uncertainty intervals and subgroup reliability classifications.
- Added a method-selection matrix and generated evidence-backed handbook.
- Added a tenth Evidence and methods dashboard workspace.
- Added evidence, coverage, gap and uncertainty API endpoints.
- Added CI gates requiring literature and project-data support for every question.

## 0.6.0 — data scientist scenario lab and diagnostic playbooks

- Added 42 structured healthcare data-science questions with run-specific synthetic answers.
- Added adjacent-period comparison using common source coverage rather than sparse future events.
- Added pathway-stage duration decomposition and waiting-time definition sensitivity.
- Added observed DNA-rate decomposition into composition and within-segment effects.
- Added threshold-versus-workload policy analysis with precision, recall and selection gaps.
- Added predictive feature explanations with an explicit non-causal boundary.
- Added source event-coverage and contract-aware missingness audits.
- Added a root-cause triage scorecard and a generated DS scenario casebook.
- Added a ninth interactive dashboard workspace and aggregate diagnostic API endpoints.
- Expanded automated tests to cover diagnostic reconciliation, question completeness and API outputs.

## 0.5.0 — auditable service layer and data contracts

- Added versioned source-table contracts with blocking schema, key, type, row-count, nullability, and allowed-value rules.
- Added source SHA-256 fingerprints and a run manifest containing config hashes, package version, output hashes, and replay command.
- Added a FastAPI service with aggregate endpoints and a restricted, field-minimised appointment-support endpoint.
- Added four same-capacity operational queue policies and comparison metrics for wait and group-selection gaps.
- Added run-linked incident records with owners, playbooks, and rollback triggers.
- Added source-to-decision lineage evidence.
- Added an Audit and service API dashboard workspace.
- Expanded automated tests to cover contracts, fingerprints, manifests, incidents, queue policies, and API access behaviour.

## 0.4.0 — operations control tower and pilot planning

- Added green/amber/red service-level controls.
- Added robust weekly referral and DNA anomaly triage.
- Added budget-constrained resource-plan enumeration and Pareto frontier.
- Added budget recommendations and backlog sensitivity analysis.
- Added reminder-pilot sample-size scenarios and guardrail specification.
- Added champion–challenger model registry and monthly comparison.
- Added an optimisation and pilot workspace to the interactive dashboard.
- Expanded weekly and monthly management reports.
- Expanded automated tests for controls, optimisation, experimentation, and model governance.

## 0.3.0 — decision controls and role workflows

- Added a sixth Decision and service impact workspace.
- Added an editable browser decision register with owner, due date, status, note, CSV export and print view.
- Added Executive, Operations, Patient support and Data/model role profiles with patient-queue visibility rules.
- Added referral timeline drill-down for synthetic open cases.
- Added scenario resource and cost-proxy comparison plus outreach expected-value analysis.
- Added monthly attendance calibration and dated rolling-origin forecast monitoring.
- Added monitoring rules that create owned operational actions when declared review levels are crossed.
- Added a monthly control pack, role matrix, decision workflow and impact-assumption documentation.
- Added impact, monitoring and shared-build tests and JavaScript syntax checks in CI.

## 0.2.0 — interactive operations dashboard

- Replaced the static four-chart page with five role-based dashboard views.
- Added global funding-route, service and cohort filters.
- Added interactive Plotly charts, pathway Sankey, cohort heatmap and case exception queue.
- Added an in-browser demand and capacity planner using the Python queue-model equation.
- Added appointment-support capacity and threshold controls plus CSV export.
- Added data-quality, forecast, calibration and group-monitoring views.
- Added `config/operations.yaml` for explicit portfolio thresholds and safe-use rules.
- Added a structured `operational_action_queue.csv` with owner, decision and cadence.
- Added dashboard and action-queue tests.
- Added a self-contained report build and a smaller `docs/index.html` build.
