# Tableau implementation specification

The Python pipeline writes CSV extracts to `tableau/exports`. The self-contained HTML dashboard is the reviewable portfolio implementation; the same semantic layers can be rebuilt in Tableau.

## Executive and operations view

Show weekly referrals, acceptance, completed assessments, treatment starts, median and P90 waiting time, attendance, data-gate status, decision owner and review cadence.

## Patient pathway view

Show stage conversion, 30/60/90-day cohort completion, waiting-time distribution, segment comparison and a role-restricted exception queue.

## Demand and capacity view

Show actual demand, forecast interval, stored scenario, assessment minutes, effective throughput, backlog and wait proxy. Scenario assumptions should be displayed beside each result.

## Appointment-support view

Show the capacity-limited queue, predicted probability, suggested non-clinical action, calibration, PR-AUC, Brier score and group monitoring. Patient-level data should not appear on an executive page.

## Required filters

- referral cohort date;
- funding route;
- adult or under-18 service;
- appointment type where relevant.

Metric names and exclusions must match `docs/metric_dictionary.md`.
