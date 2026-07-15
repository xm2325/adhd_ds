# Operational queue-policy simulation

The queue-policy module compares how a fixed weekly review capacity is allocated. It does not assign clinical urgency.

Policies:

- `oldest_first`: longest elapsed wait first;
- `stage_readiness`: later operational pathway stage first, then wait;
- `balanced_funding_route`: round-robin across funding routes while preserving within-group wait order;
- `balanced_service_group`: round-robin across adult and under-18 service groups.

Outputs include selected count, mean and P90 selected wait, overdue cases cleared, maximum remaining wait, and group-selection-rate gaps.

A lower selection-rate gap is not automatically fair, and a lower maximum wait is not automatically preferable. The decision owner must review the intended service objective, capacity constraints, equality implications, patient experience, and clinical safeguards.
