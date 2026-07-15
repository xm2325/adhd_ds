# Operational decision workflow

## Minimum decision record

Each action should record:

1. **Signal** — the metric, threshold, time window, and filter scope.
2. **Evidence** — trend, case review, data-quality status, uncertainty, and model limitation.
3. **Decision** — approved action, owner, due date, rationale, and escalation route.
4. **Delivery** — whether the action was completed and any implementation issue.
5. **Outcome review** — whether the target metric changed and whether another group was adversely affected.

## Dashboard demonstration

The dashboard seeds the decision register from `results/operational_action_queue.csv`. Edits are saved in browser `localStorage`, so a reviewer can demonstrate assignment and status changes without a backend. The export button produces a CSV review record.

## Production replacement

A real implementation should use an authenticated write API, versioned records, immutable audit events, named approvers, timestamps from the service, retention rules, and links to incident or change-management systems.
