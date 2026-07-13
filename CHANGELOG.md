# Changelog

## 0.2.0 — interactive operations dashboard

- Replaced the static four-chart page with five role-based dashboard views.
- Added global funding-route, service and cohort filters.
- Added interactive Plotly charts, pathway Sankey, cohort heatmap and case exception queue.
- Added an in-browser demand and capacity planner using the Python queue-model equation.
- Added appointment-support capacity and threshold controls plus CSV export.
- Added data-quality, forecast, calibration and group-monitoring views.
- Added `config/operations.yaml` for explicit portfolio thresholds and safe-use rules.
- Added a structured `operational_action_queue.csv` with owner, decision and cadence.
- Added dashboard and action-queue tests.
- Added a self-contained report build and a smaller `docs/index.html` build.
