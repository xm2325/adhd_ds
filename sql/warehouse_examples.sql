-- Microsoft SQL Server examples for the synthetic warehouse design.
-- Source names are placeholders and must be mapped to approved source views.

-- 1. Typed referral staging view.
select
    cast(referral_id as varchar(64)) as referral_id,
    cast(patient_id as varchar(64)) as patient_id,
    cast(referral_received_at as datetime2(0)) as referral_received_at,
    cast(accepted_at as datetime2(0)) as accepted_at,
    cast(first_contact_at as datetime2(0)) as first_contact_at,
    cast(funding_route as varchar(50)) as funding_route,
    cast(service_group as varchar(50)) as service_group,
    cast(referral_status as varchar(50)) as referral_status,
    cast(source_system as varchar(100)) as source_system
from dbo.raw_referrals
where referral_id is not null
  and patient_id is not null;

-- 2. Patient pathway mart.
with first_assessment as (
    select referral_id, appointment_id, scheduled_start, appointment_status
    from (
        select
            referral_id,
            appointment_id,
            scheduled_start,
            appointment_status,
            row_number() over (
                partition by referral_id
                order by scheduled_start, appointment_id
            ) as sequence_number
        from dbo.stg_appointments
        where appointment_type = 'assessment'
    ) ranked
    where sequence_number = 1
),
first_treatment as (
    select referral_id, min(event_at) as treatment_started_at
    from dbo.stg_treatment_events
    where event_type = 'titration_started'
    group by referral_id
)
select
    r.referral_id,
    r.patient_id,
    r.funding_route,
    r.service_group,
    r.referral_received_at,
    r.accepted_at,
    r.first_contact_at,
    a.scheduled_start as first_assessment_at,
    a.appointment_status as first_assessment_status,
    s.assessment_completed_at,
    t.treatment_started_at,
    datediff(day, r.referral_received_at, r.first_contact_at) as referral_to_contact_days,
    datediff(day, r.referral_received_at, s.assessment_completed_at) as referral_to_assessment_days
from dbo.stg_referrals r
left join first_assessment a on r.referral_id = a.referral_id
left join dbo.stg_assessments s on a.appointment_id = s.appointment_id
left join first_treatment t on r.referral_id = t.referral_id;

-- 3. Weekly demand and capacity mart.
-- 1900-01-01 was a Monday, so this expression is independent of SET DATEFIRST.
with weekly_demand as (
    select
        dateadd(day, -datediff(day, '19000101', cast(referral_received_at as date)) % 7,
                cast(referral_received_at as date)) as week_start,
        count_big(*) as referrals_received
    from dbo.stg_referrals
    group by dateadd(day, -datediff(day, '19000101', cast(referral_received_at as date)) % 7,
                     cast(referral_received_at as date))
),
weekly_capacity as (
    select
        cast(week_start as date) as week_start,
        sum(case when service_type = 'assessment' then available_minutes else 0 end) as assessment_minutes
    from dbo.stg_clinician_capacity
    group by cast(week_start as date)
)
select
    coalesce(d.week_start, c.week_start) as week_start,
    coalesce(d.referrals_received, 0) as referrals_received,
    coalesce(c.assessment_minutes, 0) as assessment_minutes
from weekly_demand d
full outer join weekly_capacity c on d.week_start = c.week_start;
