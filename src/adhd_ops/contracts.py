from __future__ import annotations

import hashlib
from typing import Any

import pandas as pd


def _primary_key_columns(value: str | list[str]) -> list[str]:
    return [value] if isinstance(value, str) else list(value)


def _type_failures(series: pd.Series, expected: str) -> int:
    non_null = series.dropna()
    if expected == "string":
        return int((~non_null.map(lambda value: isinstance(value, str))).sum())
    if expected == "datetime":
        return int(pd.to_datetime(non_null, errors="coerce").isna().sum())
    if expected == "numeric":
        return int(pd.to_numeric(non_null, errors="coerce").isna().sum())
    if expected == "boolean":
        return int((~non_null.isin([True, False, 0, 1])).sum())
    return 0


def validate_data_contracts(
    tables: dict[str, pd.DataFrame], contract_config: dict[str, Any]
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []

    def add(table: str, rule: str, failures: int, expected: str, observed: str) -> None:
        rows.append(
            {
                "table": table,
                "rule": rule,
                "severity": "error",
                "failure_count": int(failures),
                "status": "pass" if int(failures) == 0 else "fail",
                "expected": expected,
                "observed": observed,
            }
        )

    for table_name, spec in contract_config.get("tables", {}).items():
        if table_name not in tables:
            add(table_name, "table_present", 1, "table exists", "missing")
            continue
        frame = tables[table_name]
        add(table_name, "table_present", 0, "table exists", "present")
        bounds = spec.get("row_count", {})
        minimum, maximum = int(bounds.get("min", 0)), int(bounds.get("max", 10**12))
        within = minimum <= len(frame) <= maximum
        add(table_name, "row_count_within_bounds", 0 if within else 1, f"{minimum}..{maximum}", str(len(frame)))

        key_columns = _primary_key_columns(spec["primary_key"])
        missing_keys = [column for column in key_columns if column not in frame.columns]
        add(table_name, "primary_key_columns_present", len(missing_keys), ",".join(key_columns), ",".join(missing_keys) or "present")
        if not missing_keys:
            null_failures = int(frame[key_columns].isna().any(axis=1).sum())
            duplicate_failures = int(frame.duplicated(key_columns).sum())
            add(table_name, "primary_key_not_null", null_failures, "0 null keys", str(null_failures))
            add(table_name, "primary_key_unique", duplicate_failures, "0 duplicate keys", str(duplicate_failures))

        for column, column_spec in spec.get("columns", {}).items():
            present = column in frame.columns
            add(table_name, f"column_present:{column}", 0 if present else 1, "present", "present" if present else "missing")
            if not present:
                continue
            series = frame[column]
            nullable = bool(column_spec.get("nullable", True))
            null_count = int(series.isna().sum())
            add(table_name, f"nullability:{column}", 0 if nullable else null_count, "nullable" if nullable else "not null", str(null_count))
            expected_type = str(column_spec.get("type", "string"))
            type_failures = _type_failures(series, expected_type)
            add(table_name, f"type:{column}", type_failures, expected_type, f"{type_failures} invalid")
            allowed = column_spec.get("allowed")
            if allowed is not None:
                invalid = int((~series.dropna().isin(allowed)).sum())
                add(table_name, f"allowed_values:{column}", invalid, ",".join(map(str, allowed)), f"{invalid} invalid")
    return pd.DataFrame(rows)


def assert_contracts(contract_status: pd.DataFrame) -> None:
    failed = contract_status[contract_status["failure_count"].gt(0)]
    if not failed.empty:
        raise ValueError(f"Data contract gate failed:\n{failed.to_string(index=False)}")


def _fingerprint_frame(frame: pd.DataFrame) -> str:
    canonical = frame.copy()
    canonical = canonical.reindex(sorted(canonical.columns), axis=1)
    canonical = canonical.sort_values(list(canonical.columns), kind="mergesort", na_position="last").reset_index(drop=True)
    hashed = pd.util.hash_pandas_object(canonical.astype(str), index=True).values.tobytes()
    return hashlib.sha256(hashed).hexdigest()


def build_source_profiles(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for name, frame in sorted(tables.items()):
        date_candidates = [column for column in frame.columns if column.endswith("_at") or column in {"week_start", "created_at"}]
        parsed_dates = []
        for column in date_candidates:
            values = pd.to_datetime(frame[column], errors="coerce").dropna()
            if not values.empty:
                parsed_dates.extend([values.min(), values.max()])
        rows.append(
            {
                "table": name,
                "row_count": int(len(frame)),
                "column_count": int(len(frame.columns)),
                "null_cells": int(frame.isna().sum().sum()),
                "min_event_time": min(parsed_dates).isoformat() if parsed_dates else None,
                "max_event_time": max(parsed_dates).isoformat() if parsed_dates else None,
                "sha256_fingerprint": _fingerprint_frame(frame),
                "synthetic": True,
            }
        )
    return pd.DataFrame(rows)
