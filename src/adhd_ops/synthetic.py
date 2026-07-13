from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


def _prob(x: float) -> float:
    return float(np.clip(1.0 / (1.0 + np.exp(-x)), 0.01, 0.95))


def generate_synthetic_data(config: dict, output_dir: str | Path | None = None) -> dict[str, pd.DataFrame]:
    """Generate deterministic source-like tables. All records are synthetic."""
    rng = np.random.default_rng(int(config["seed"]))
    start = pd.Timestamp(config["start_date"])
    week_starts = pd.date_range(start, periods=int(config["weeks"]), freq="W-MON")

    patients, referrals, appointments = [], [], []
    assessments, treatments, communications = [], [], []
    p_count = a_count = s_count = t_count = m_count = 0

    for week_index, week_start in enumerate(week_starts):
        seasonal = 1 + 0.12 * np.sin(2 * np.pi * week_index / 52) - 0.10 * (week_start.month == 12)
        trend = 1 + float(config["weekly_growth_rate"]) * week_index
        n = int(rng.poisson(float(config["base_weekly_referrals"]) * seasonal * trend))

        for _ in range(n):
            p_count += 1
            patient_id, referral_id = f"P{p_count:06d}", f"R{p_count:06d}"
            funding = "private" if rng.random() < float(config["private_share"]) else "nhs_right_to_choose"
            service = "adult" if rng.random() < float(config["adult_share"]) else "under_18"
            age_band = (
                rng.choice(["18-29", "30-44", "45-59", "60+"], p=[0.31, 0.38, 0.24, 0.07])
                if service == "adult"
                else rng.choice(["6-11", "12-17"], p=[0.34, 0.66])
            )
            region = rng.choice(["London", "Midlands", "North", "South", "East"], p=[0.28, 0.20, 0.18, 0.20, 0.14])
            received = week_start + pd.Timedelta(days=int(rng.integers(0, 7)), hours=int(rng.integers(8, 18)))
            accept_rate = float(config["acceptance_rate_private"] if funding == "private" else config["acceptance_rate_nhs"])
            accepted = rng.random() < accept_rate
            accepted_at = received + pd.Timedelta(days=float(rng.gamma(1.7, 1.6))) if accepted else pd.NaT
            rejected_at = received + pd.Timedelta(days=float(rng.gamma(1.5, 1.4))) if not accepted else pd.NaT
            first_contact = accepted_at + pd.Timedelta(days=float(rng.gamma(1.5, 1.8))) if accepted else pd.NaT

            patients.append({
                "patient_id": patient_id,
                "age_band": age_band,
                "service_group": service,
                "funding_route": funding,
                "region_group": region,
                "created_at": received,
                "synthetic_record": True,
            })
            referrals.append({
                "referral_id": referral_id,
                "patient_id": patient_id,
                "referral_received_at": received,
                "referral_source": "Private self-referral" if funding == "private" else rng.choice(["NHS e-RS", "GP letter"]),
                "funding_route": funding,
                "service_group": service,
                "referral_status": "accepted" if accepted else "rejected",
                "accepted_at": accepted_at,
                "rejected_at": rejected_at,
                "first_contact_at": first_contact,
                "rejection_reason": None if accepted else rng.choice(["incomplete_information", "outside_scope", "duplicate"]),
                "source_system": "synthetic_referral_system",
            })
            if not accepted:
                continue

            wait_days = (
                (18 if funding == "private" else 48)
                + (18 if service == "under_18" else 0)
                + 0.22 * week_index
                + rng.gamma(3.0, 6.0)
            )
            booked = first_contact + pd.Timedelta(days=float(rng.uniform(0.5, 4.0)))
            scheduled = accepted_at + pd.Timedelta(days=float(max(wait_days, 5)))
            if scheduled <= booked:
                scheduled = booked + pd.Timedelta(days=2)

            def add_appointment(appt_type: str, booked_at: pd.Timestamp, scheduled_at: pd.Timestamp, prior_dna: int = 0) -> tuple[str, str]:
                nonlocal a_count, m_count
                a_count += 1
                appt_id = f"A{a_count:07d}"
                r7, r1 = rng.random() < 0.92, rng.random() < 0.95
                lead = max((scheduled_at - booked_at).total_seconds() / 86400, 0)
                logit = -3.25 + 0.026 * lead + 0.62 * (service == "under_18") + 0.42 * (funding != "private")
                logit += 1.10 * prior_dna - 0.90 * (r7 and r1) + 0.30 * (scheduled_at.day_name() == "Monday")
                dna = _prob(logit)
                u = rng.random()
                if u < 0.025:
                    status = "cancelled_provider"
                elif u < 0.105:
                    status = "cancelled_patient"
                elif u < 0.105 + dna:
                    status = "did_not_attend"
                else:
                    status = "attended"
                duration = int(config["assessment_duration_minutes"] if appt_type == "assessment" else config["follow_up_duration_minutes"])
                appointments.append({
                    "appointment_id": appt_id,
                    "patient_id": patient_id,
                    "referral_id": referral_id,
                    "appointment_type": appt_type,
                    "booked_at": booked_at,
                    "scheduled_start": scheduled_at,
                    "scheduled_end": scheduled_at + pd.Timedelta(minutes=duration),
                    "clinician_id": f"C{int(rng.integers(1, 17)):03d}",
                    "appointment_status": status,
                    "cancelled_at": scheduled_at - pd.Timedelta(days=float(rng.uniform(0.2, 5))) if status.startswith("cancelled") else pd.NaT,
                    "cancellation_reason": rng.choice(["patient_unavailable", "illness", "provider_unavailable"]) if status.startswith("cancelled") else None,
                    "service_group": service,
                    "funding_route": funding,
                    "age_band": age_band,
                    "region_group": region,
                    "reminder_7d_delivered": r7,
                    "reminder_1d_delivered": r1,
                    "source_system": "synthetic_scheduling_system",
                })
                for offset, delivered in [(7, r7), (1, r1)]:
                    m_count += 1
                    communications.append({
                        "communication_id": f"M{m_count:08d}",
                        "patient_id": patient_id,
                        "appointment_id": appt_id,
                        "channel": rng.choice(["sms", "email"], p=[0.82, 0.18]),
                        "sent_at": scheduled_at - pd.Timedelta(days=offset),
                        "delivery_status": "delivered" if delivered else "failed",
                        "response_status": rng.choice(["confirmed", "no_response"], p=[0.45, 0.55]) if delivered else "not_delivered",
                    })
                return appt_id, status

            assessment_appt, assessment_status = add_appointment("assessment", booked, scheduled)
            if assessment_status != "attended":
                continue

            s_count += 1
            completed = scheduled + pd.Timedelta(minutes=int(config["assessment_duration_minutes"]))
            eligible = rng.random() < 0.76
            assessments.append({
                "assessment_id": f"S{s_count:07d}",
                "appointment_id": assessment_appt,
                "patient_id": patient_id,
                "assessment_started_at": scheduled,
                "assessment_completed_at": completed,
                "assessment_status": "completed",
                "next_step": "titration" if eligible else "follow_up_or_discharge",
            })
            if not eligible:
                continue

            t_count += 1
            treatment_start = completed + pd.Timedelta(days=float(rng.gamma(2.6, 6.5)))
            treatments.append({
                "treatment_event_id": f"T{t_count:07d}",
                "patient_id": patient_id,
                "referral_id": referral_id,
                "event_type": "titration_started",
                "event_at": treatment_start,
                "status": "completed",
            })
            prior_dna = 0
            for follow_index in range(int(rng.integers(1, 4))):
                follow_booked = treatment_start + pd.Timedelta(days=follow_index * 25 + float(rng.uniform(0, 5)))
                follow_scheduled = treatment_start + pd.Timedelta(days=(follow_index + 1) * 28 + float(rng.normal(0, 3)))
                if follow_scheduled <= follow_booked:
                    follow_scheduled = follow_booked + pd.Timedelta(days=5)
                _, follow_status = add_appointment("follow_up", follow_booked, follow_scheduled, prior_dna)
                prior_dna += int(follow_status == "did_not_attend")

    tables = {
        "patients": pd.DataFrame(patients),
        "referrals": pd.DataFrame(referrals),
        "appointments": pd.DataFrame(appointments),
        "assessments": pd.DataFrame(assessments),
        "treatment_events": pd.DataFrame(treatments),
        "communications": pd.DataFrame(communications),
    }

    appts = tables["appointments"].sort_values(["patient_id", "scheduled_start"]).reset_index(drop=True)
    indicators = {
        "previous_attended_count": appts["appointment_status"].eq("attended").astype(int),
        "previous_dna_count": appts["appointment_status"].eq("did_not_attend").astype(int),
        "previous_cancel_count": appts["appointment_status"].str.startswith("cancelled").astype(int),
    }
    for column, indicator in indicators.items():
        cumulative = indicator.groupby(appts["patient_id"]).cumsum()
        appts[column] = cumulative - indicator
    appts["reschedule_count"] = appts.groupby("patient_id").cumcount().clip(upper=3)
    tables["appointments"] = appts

    capacity_rows = []
    for i, week in enumerate(pd.date_range(start, periods=int(config["weeks"]) + int(config["forecast_horizon_weeks"]), freq="W-MON")):
        seasonal = 1 - 0.12 * (week.month == 12) + 0.04 * np.sin(2 * np.pi * i / 52)
        for service_type, base in [
            ("assessment", float(config["base_assessment_capacity_minutes"])),
            ("follow_up", float(config["base_follow_up_capacity_minutes"])),
        ]:
            absence = max(0.0, rng.normal(0.035, 0.025))
            available = max(0.0, base * seasonal * (1 - absence) + rng.normal(0, base * 0.035))
            capacity_rows.append({
                "week_start": week,
                "service_type": service_type,
                "available_minutes": round(available, 1),
                "absence_minutes": round(base * absence, 1),
                "source_system": "synthetic_roster_system",
            })
    tables["clinician_capacity"] = pd.DataFrame(capacity_rows)

    if output_dir is not None:
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        for name, frame in tables.items():
            frame.to_csv(out / f"{name}.csv", index=False)
    return tables
