# Champion–challenger promotion policy

## Registered evidence

Each candidate records:

- model version;
- champion or challenger status;
- feature signature;
- training and test periods;
- PR-AUC;
- Brier score;
- top-capacity precision and recall.

## Promotion rule

The demonstration flag requires the challenger to improve recent mean Brier score by at least the configured margin without reducing recent mean PR-AUC beyond the configured tolerance.

A true promotion also requires:

1. reproducible training and scoring;
2. leakage and time-split checks;
3. calibration review;
4. subgroup review;
5. workflow and latency testing;
6. approved rollback plan;
7. named model owner;
8. decision record and effective date.

The dashboard flag is advisory. It cannot promote a model automatically.
