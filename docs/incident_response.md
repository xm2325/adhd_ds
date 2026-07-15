# Incident and rollback process

`results/incident_register.csv` converts red service controls, red weekly anomalies, and publication-gate failures into run-linked triage records.

Each record contains:

- incident ID and run ID;
- severity and signal type;
- named owner role;
- investigation playbook;
- rollback trigger;
- current status.

## Minimum response

1. Confirm whether the signal is caused by data, definition, workflow, demand, or capacity.
2. Reconcile source counts and timestamps before assigning cause.
3. Stop publication if a contract or error-level quality gate fails.
4. Revert to the most recent passing run manifest when current outputs cannot be validated.
5. Record the decision, owner, time, evidence, and follow-up.

This portfolio uses CSV and JSON evidence. Production requires an authenticated incident-management system and immutable audit history.
