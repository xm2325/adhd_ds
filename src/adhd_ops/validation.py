from __future__ import annotations

from pathlib import Path

import pandas as pd


def validate_tables(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []

    def add(table: str, rule: str, count: int, detail: str = "") -> None:
        rows.append({"table": table, "rule": rule, "failure_count": int(count), "severity": "error", "detail": detail})

    p, r, a = tables["patients"], tables["referrals"], tables["appointments"]
    s, c = tables["assessments"], tables["clinician_capacity"]
    add("patients", "patient_id_not_null", p["patient_id"].isna().sum())
    add("patients", "patient_id_unique", p["patient_id"].duplicated().sum())
    add("referrals", "referral_id_unique", r["referral_id"].duplicated().sum())
    add("appointments", "appointment_id_unique", a["appointment_id"].duplicated().sum())
    add("referrals", "patient_foreign_key", (~r["patient_id"].isin(p["patient_id"])).sum())
    add("appointments", "patient_foreign_key", (~a["patient_id"].isin(p["patient_id"])).sum())
    add("appointments", "referral_foreign_key", (~a["referral_id"].isin(r["referral_id"])).sum())
    add("assessments", "appointment_foreign_key", (~s["appointment_id"].isin(a["appointment_id"])).sum())
    accepted = r[r["referral_status"].eq("accepted")]
    add("referrals", "accepted_timestamp_present", accepted["accepted_at"].isna().sum())
    add("referrals", "accepted_after_received", (accepted["accepted_at"] < accepted["referral_received_at"]).sum())
    add("referrals", "contact_after_acceptance", (accepted["first_contact_at"] < accepted["accepted_at"]).sum())
    add("appointments", "booked_before_scheduled", (a["booked_at"] > a["scheduled_start"]).sum())
    add("appointments", "end_after_start", (a["scheduled_end"] <= a["scheduled_start"]).sum())
    add("assessments", "completion_after_start", (s["assessment_completed_at"] < s["assessment_started_at"]).sum())
    add("clinician_capacity", "nonnegative_available_minutes", (c["available_minutes"] < 0).sum())
    valid = {"attended", "cancelled_patient", "cancelled_provider", "did_not_attend"}
    add("appointments", "known_status", (~a["appointment_status"].isin(valid)).sum())
    return pd.DataFrame(rows)


def assert_valid(validation: pd.DataFrame) -> None:
    failed = validation[(validation["severity"] == "error") & (validation["failure_count"] > 0)]
    if not failed.empty:
        raise ValueError(f"Synthetic data validation failed:\n{failed.to_string(index=False)}")


def write_validation_report(validation: pd.DataFrame, path: str | Path) -> None:
    failed = validation[validation["failure_count"] > 0]
    state = "PASS" if failed.empty else "FAIL"
    html = f"""<html><head><meta charset='utf-8'><title>Data quality</title>
<style>body{{font-family:Arial;margin:32px}}table{{border-collapse:collapse;width:100%}}th,td{{padding:8px;border:1px solid #ddd}}th{{background:#f3f4f6}}</style></head>
<body><h1>Synthetic data quality report</h1><p><strong>{state}</strong>: {len(failed)} failing rules.</p>{validation.to_html(index=False)}</body></html>"""
    Path(path).write_text(html, encoding="utf-8")
