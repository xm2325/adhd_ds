# Evidence methodology

Version 0.7 separates four questions that are often incorrectly combined:

1. **What does the current dataset show?** — descriptive or inferential evidence from generated project outputs.
2. **Can a model predict a later event?** — temporal validation, calibration, decision utility and subgroup stability.
3. **Did an intervention cause an outcome?** — randomisation or a defensible causal identification strategy.
4. **Is the system safe and ready to operate?** — clinical safety, information governance, human factors, monitoring and rollback.

## Evidence attached to every question

Every row in `results/ds_question_catalog.csv` must contain:

- at least one peer-reviewed methods paper, reporting guideline or official standard;
- at least one run-specific project output;
- an external public-data source where useful for contextual validation;
- a claim type;
- a decision-readiness state;
- an evidence boundary and next action.

The build fails if literature or project-data coverage is missing.

## Evidence is not interchangeable

- A reporting guideline improves transparency but does not prove performance.
- A prediction model can estimate risk but does not identify an intervention effect.
- A scenario model explores assumptions but does not forecast realised policy impact.
- A statistically precise estimate can still be biased by definitions, selection or measurement.
- External aggregate NHS data can contextualise trends but may not be comparable with a specialist provider.

## Statistical uncertainty

`results/kpi_uncertainty.csv` reports Wilson intervals for proportions and patient- or week-level bootstrap intervals for waiting-time and demand summaries. `results/subgroup_reliability.csv` labels small or low-event groups as adequate, review or insufficient rather than treating every subgroup estimate as stable.

## Literature registry

`config/evidence_registry.yaml` records source type, topic, project use and limitations. The registry includes prediction-model guidance, missing-data and survival methods, causal inference, forecasting, queueing, fairness, human factors, clinical safety, privacy and economic evaluation.

## External data registry

`config/external_data_registry.yaml` identifies official NHS and ONS datasets that could support real-world contextual validation. They are not imported into the synthetic build, because their definitions and populations are not automatically comparable.
