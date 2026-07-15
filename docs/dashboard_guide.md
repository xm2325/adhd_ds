# Dashboard operating guide

## 1. What the dashboard is for

The dashboard supports five decisions rather than one general request to “look at the data.”

| Decision | Primary user | Main evidence | Possible action |
|---|---|---|---|
| Where are patients not progressing? | Pathway manager | Stage flow, long-wait queue, cohort completion | Correct referral handling, booking or follow-up process |
| Will demand exceed capacity? | Clinical operations | Forecast range, throughput and backlog scenarios | Change clinics, roster or slot allocation |
| Which appointments need additional support? | Patient-support team | Capacity-limited ranked queue | Reminder, confirmation or easier rescheduling |
| Can the dashboard be published? | Data engineering / metric owner | Data-quality rules and metric definitions | Publish, stop, correct or formally waive |
| Are models still suitable? | Model owner | Forecast error, calibration, group metrics and overrides | Continue, adjust, retrain or suspend |

## 2. Daily process

### 08:00 — data refresh

Inputs are source-like patient, referral, appointment, assessment, communication and capacity tables. The synthetic project uses CSV files; an enterprise system would use controlled database views.

### 08:15 — quality gate

The pipeline checks keys, cross-table links, timestamp order, non-negative capacity and allowed statuses. An error-level failure should stop publication. Passing automated checks does not approve the business meaning of a metric.

### 09:00 — operations huddle

The command centre is read from top to bottom:

1. Confirm the filter scope and refresh time.
2. Read the KPI cards.
3. Review the generated decision queue.
4. Check whether demand, pathway conversion, or capacity is the main issue.
5. Assign an owner and expected review cadence.

The exception queue is not a clinical-priority list. It is a synthetic operational worklist for cases whose recorded pathway has not reached treatment start.

## 3. Weekly capacity review

The team first reviews the validated service-wide forecast and interval. It then compares stored scenarios so the same assumptions can be reproduced in later meetings.

The interactive planner changes:

- referral demand;
- base capacity;
- additional weekly clinic minutes;
- relative reduction in did-not-attend rate.

For each week, the dashboard uses:

\[
B_{t+1}=\max\left(0,B_t+A_t-C_t\right),
\]

where \(B_t\) is backlog, \(A_t\) is new assessment demand, and \(C_t\) is effective assessment throughput. This is a planning equation, not a clinical-outcome model.

After a scenario is discussed, the approved assumptions, owner, date and reason should be recorded in a decision register. Moving sliders is not a decision record.

## 4. Appointment-support process

The model produces a probability for later synthetic appointments. The team then applies an operational policy:

1. Apply service and funding-route filters.
2. Set the weekly contact capacity.
3. Set the minimum probability, if a threshold is required.
4. Review the top queue and permit a human override.
5. Log contact delivery, response, reschedule and attendance.
6. Review calibration and group-level behaviour monthly.

The displayed “observed synthetic DNA” and capture rate use the held-out demonstration data. In production, the queue would contain upcoming appointments whose outcomes are not known.

## 5. Monthly controls

The monthly pack should include:

- forecast WAPE and under-forecast rate;
- appointment-model PR-AUC and Brier score;
- calibration plot;
- group-level observed and predicted rates;
- outreach volume and override reasons;
- data-quality incidents;
- metric or model changes.

A model can be statistically acceptable and still be operationally unsuitable if there is no useful action, contact capacity is too low, or errors create an unacceptable patient impact.

## 6. Data and privacy

The public portfolio dashboard uses synthetic identifiers. A real provider should normally separate:

- aggregated executive reporting;
- operational case queues with restricted access;
- clinical records that are not needed for service operations;
- model-development datasets with approved purpose and retention.

Role-based access, audit logs, data minimisation, retention, versioning and human review are required before a patient-level queue is used.

## 7. Decision and impact workspace

The impact workspace compares stored scenarios using configured resource assumptions. Reviewers should treat the output as an option-comparison tool, not a cost or savings claim.

The decision register lets a reviewer edit owner, due date, status and rationale in the browser. Export is available for demonstration. A production service requires authenticated writes and audit history.

## 8. Role views

Role profiles change the visible workspaces and whether the synthetic patient-level queues are shown. This demonstrates information separation only. Security must be implemented in the application and data platform.

## 9. Monitoring alerts

Monthly attendance-model monitoring excludes small groups from automated alert generation, but still displays them. Rolling forecast checks are dated by forecast origin. Review levels are configuration values and must be approved before production use.
