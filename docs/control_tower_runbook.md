# Operations control-tower runbook

## Purpose

The control tower separates a signal from a decision. A red or amber status means that an owner should inspect evidence; it does not identify cause or prescribe a clinical action.

## Daily sequence

1. Confirm that error-level data checks pass.
2. Review the six service-level controls.
3. Review new referral-volume and DNA-rate anomalies.
4. Open the patient-pathway queue only for authorised operational roles.
5. Record an owner, due date, decision note, and escalation route.

## Weekly sequence

1. Review forecast history and interval width.
2. Compare stored capacity scenarios.
3. Set a planning budget in the optimisation workspace.
4. Review the recommended plan and nearby Pareto-efficient alternatives.
5. Confirm staffing, timetable, patient-contact, and governance feasibility outside the model.
6. Record the approved plan and its review measure.

## Status interpretation

- **Green:** within the configured portfolio range.
- **Amber:** review is needed before the next normal control meeting.
- **Red:** named owner and time-bound review are required.
- **Unknown:** the minimum evidence needed for a status is not available.

Thresholds are declared in `config/operations.yaml`. They are demonstration values rather than provider standards.

## Anomaly interpretation

Weekly anomalies use a rolling median and median absolute deviation. They are resistant to a small number of extreme observations but do not adjust for holidays, policy changes, data refresh failures, or service redesign. Every alert requires source and workflow checks before a business explanation is accepted.

## v0.5 audit and service-layer checks

Before the daily huddle, confirm that both the data-contract and coded data-quality gates passed. Record the run ID used in the meeting. If a red control or anomaly is discussed, link the decision to the corresponding incident record. Patient-level API endpoints must be restricted to operational roles and should return only the minimum fields needed for the action.
