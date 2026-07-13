# Governance notes

This portfolio project uses deterministic synthetic data only. A real service implementation would require an approved purpose, data minimisation, role-based access, audit logs, retention rules, source reconciliation and named metric owners.

The appointment-support model is limited to operational support such as an extra reminder, confirmation request or easier rescheduling. It must not be used to refuse, delay or lower care priority. Model use requires versioned artefacts, time-based validation, calibration monitoring, group-level checks, override logging, human review and a documented suspension rule.

Executive reporting and patient-level queues should be separate products. Executive reporting should normally be aggregated. A patient-level operational queue should show only the minimum fields needed by the authorised team.
