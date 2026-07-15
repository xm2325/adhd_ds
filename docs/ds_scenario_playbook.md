# Data scientist scenario playbook

## Purpose

The scenario lab is organised around four questions:

1. **What happened?** — validated descriptive metrics and adjacent-period comparison.
2. **Why might it have happened?** — diagnostic decomposition and competing hypotheses.
3. **What should the service do?** — capacity, queue, outreach and budget options.
4. **How will we know whether the action worked?** — controlled experiment or defensible causal evaluation.

The analysis must identify its evidence class:

| Evidence class | Appropriate claim |
|---|---|
| Descriptive | What was recorded and how it changed |
| Predictive | Which cases are more likely to have an outcome |
| Scenario | What the declared model produces under changed assumptions |
| Causal | What would change because of an intervention, under stated assumptions |

## Standard answer structure

Every answer should follow:

```text
Decision question
→ current evidence
→ method and assumptions
→ options
→ recommendation
→ risk if wrong
→ named owner and next review
```

## Root-cause workflow

When a stakeholder asks “why did this KPI change?”:

1. Verify data contracts, source coverage and metric definitions.
2. Check whether the change exceeds normal variation.
3. Separate composition change from within-group rate change.
4. Review concurrent operational or policy changes.
5. Form competing hypotheses rather than a single story.
6. Identify the analysis or experiment that could distinguish them.

Feature importance must not be used as root-cause evidence.

## Waiting-time workflow

Always show the start and end event. Recommended paired measures:

- referral received → completed assessment: patient-experience access measure;
- referral accepted → completed assessment: post-acceptance operational measure;
- booking created → completed assessment: appointment-queue measure.

For recent cohorts, use fixed-horizon outcomes or survival analysis rather than eventual completion rates.

## Appointment-support workflow

Select threshold and workload jointly:

- maximum weekly outreach capacity;
- minimum probability;
- precision and recall at that capacity;
- calibration;
- funding-route and service-group selection gaps;
- permitted action and patient-experience guardrails.

The queue can support reminders, confirmation and easier rescheduling only.

## Experiment workflow

Before launch, specify:

- eligible population;
- assignment mechanism;
- primary estimand;
- outcome timing;
- sample size and recruitment duration;
- delivery, complaint, opt-out and equality guardrails;
- stopping and rollback rules;
- intention-to-treat analysis.

A small feasibility pilot may validate delivery and workload without being powered for an outcome effect.

## Communication by audience

### Executive

Lead with conclusion, evidence, implication, options and decision needed. Avoid model architecture unless it changes risk.

### Operations

Show queue volume, timing, owner, staffing implications and what can be changed this week.

### Clinical team

State intended use, error consequences, human review, patient-safety boundary and evidence limitations.

### Data engineering

Provide source, grain, key, refresh, lineage, contract failure and reproducible example records.

### Product

Define user action, experiment, success metric, guardrails and adoption measurement.

### Governance

Provide purpose, minimum fields, lawful access process, audit evidence, retention, incidents and rollback.
