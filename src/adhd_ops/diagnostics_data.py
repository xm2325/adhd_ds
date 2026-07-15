from __future__ import annotations

from typing import Any

import pandas as pd


def build_source_freshness(
    tables: dict[str, pd.DataFrame],
    event_columns: dict[str, list[str]] | None = None,
) -> pd.DataFrame:
    mapping = event_columns or {
        "patients": ["created_at"],
        "referrals": ["referral_received_at", "accepted_at", "first_contact_at"],
        "appointments": ["booked_at", "scheduled_start", "cancelled_at"],
        "assessments": ["assessment_started_at", "assessment_completed_at"],
        "treatment_events": ["event_at"],
        "communications": ["sent_at"],
        "clinician_capacity": ["week_start"],
    }
    maxima: dict[str, pd.Timestamp] = {}
    minima: dict[str, pd.Timestamp] = {}
    for table, columns in mapping.items():
        values = []
        for column in columns:
            if table in tables and column in tables[table].columns:
                values.append(pd.to_datetime(tables[table][column], errors="coerce"))
        if values:
            combined = pd.concat(values, ignore_index=True)
            maxima[table] = combined.max()
            minima[table] = combined.min()
    if "referrals" in tables and "referral_received_at" in tables["referrals"].columns:
        reference = pd.to_datetime(tables["referrals"]["referral_received_at"], errors="coerce").max()
    else:
        reference = max(value for value in maxima.values() if pd.notna(value))
    rows = []
    for table, maximum in maxima.items():
        gap = float((reference - maximum).total_seconds() / 86400)
        rows.append(
            {
                "table": table,
                "earliest_event": minima[table],
                "latest_event": maximum,
                "coverage_lag_vs_referral_cutoff_days": max(gap, 0.0),
                "coverage_beyond_referral_cutoff_days": max(-gap, 0.0),
                "freshness_status": "unknown_without_extract_timestamp",
                "freshness_reference": "Event coverage is not extract freshness; production requires source refresh timestamps and SLAs.",
            }
        )
    return pd.DataFrame(rows).sort_values("coverage_lag_vs_referral_cutoff_days", ascending=False).reset_index(drop=True)


def build_missingness_audit(
    tables: dict[str, pd.DataFrame],
    contract_config: dict[str, Any],
) -> pd.DataFrame:
    rows = []
    for table_name, table_contract in contract_config.get("tables", {}).items():
        frame = tables.get(table_name)
        if frame is None:
            continue
        for column, rule in table_contract.get("columns", {}).items():
            if column not in frame.columns:
                continue
            missing_count = int(frame[column].isna().sum())
            rows.append(
                {
                    "table": table_name,
                    "column": column,
                    "row_count": int(len(frame)),
                    "missing_count": missing_count,
                    "missing_rate": float(missing_count / max(len(frame), 1)),
                    "nullable_by_contract": bool(rule.get("nullable", True)),
                    "status": "expected_nullable" if rule.get("nullable", True) else ("pass" if missing_count == 0 else "fail"),
                    "interpretation": "Nullable fields can be structurally missing; review conditional completeness before imputation.",
                }
            )
    return pd.DataFrame(rows).sort_values(["status", "missing_rate"], ascending=[True, False]).reset_index(drop=True)
