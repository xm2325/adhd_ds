/*
  Microsoft SQL Server examples for common healthcare operational questions.
  Table and column names follow the synthetic project and require adaptation.
*/

/* Q1. How do defensible waiting-time definitions differ? */
WITH pathway AS (
    SELECT
        r.referral_id,
        r.referral_received_at,
        r.accepted_at,
        r.first_contact_at,
        a.booked_at,
        s.assessment_completed_at
    FROM dbo.referrals AS r
    LEFT JOIN dbo.first_assessment_appointment AS a
        ON a.referral_id = r.referral_id
    LEFT JOIN dbo.assessments AS s
        ON s.appointment_id = a.appointment_id
)
SELECT
    COUNT(assessment_completed_at) AS completed_n,
    PERCENTILE_CONT(0.5) WITHIN GROUP (
        ORDER BY DATEDIFF_BIG(SECOND, referral_received_at, assessment_completed_at) / 86400.0
    ) OVER () AS median_received_to_assessment_days,
    PERCENTILE_CONT(0.5) WITHIN GROUP (
        ORDER BY DATEDIFF_BIG(SECOND, accepted_at, assessment_completed_at) / 86400.0
    ) OVER () AS median_accepted_to_assessment_days,
    PERCENTILE_CONT(0.5) WITHIN GROUP (
        ORDER BY DATEDIFF_BIG(SECOND, booked_at, assessment_completed_at) / 86400.0
    ) OVER () AS median_booking_to_assessment_days
FROM pathway
WHERE assessment_completed_at IS NOT NULL;

/* Q2. Where does pathway time accumulate? */
SELECT
    referral_id,
    DATEDIFF_BIG(SECOND, referral_received_at, accepted_at) / 86400.0 AS referral_processing_days,
    DATEDIFF_BIG(SECOND, accepted_at, first_contact_at) / 86400.0 AS initial_contact_days,
    DATEDIFF_BIG(SECOND, first_contact_at, booked_at) / 86400.0 AS booking_process_days,
    DATEDIFF_BIG(SECOND, booked_at, scheduled_start) / 86400.0 AS appointment_queue_days,
    DATEDIFF_BIG(SECOND, assessment_completed_at, treatment_started_at) / 86400.0 AS treatment_transition_days
FROM dbo.patient_pathway_mart;

/* Q3. Did non-attendance change, and was the case mix different? */
SELECT
    DATEADD(DAY, -DATEDIFF(DAY, '19000101', scheduled_start) % 7,
            CAST(scheduled_start AS date)) AS week_start,
    appointment_type,
    funding_route,
    service_group,
    CASE
        WHEN DATEDIFF(DAY, booked_at, scheduled_start) <= 7 THEN '≤7d'
        WHEN DATEDIFF(DAY, booked_at, scheduled_start) <= 14 THEN '8–14d'
        WHEN DATEDIFF(DAY, booked_at, scheduled_start) <= 28 THEN '15–28d'
        WHEN DATEDIFF(DAY, booked_at, scheduled_start) <= 56 THEN '29–56d'
        ELSE '>56d'
    END AS lead_time_band,
    COUNT(*) AS eligible_appointments,
    AVG(CASE WHEN appointment_status = 'did_not_attend' THEN 1.0 ELSE 0.0 END) AS dna_rate
FROM dbo.appointments
WHERE appointment_status IN ('attended', 'did_not_attend')
GROUP BY
    DATEADD(DAY, -DATEDIFF(DAY, '19000101', scheduled_start) % 7,
            CAST(scheduled_start AS date)),
    appointment_type,
    funding_route,
    service_group,
    CASE
        WHEN DATEDIFF(DAY, booked_at, scheduled_start) <= 7 THEN '≤7d'
        WHEN DATEDIFF(DAY, booked_at, scheduled_start) <= 14 THEN '8–14d'
        WHEN DATEDIFF(DAY, booked_at, scheduled_start) <= 28 THEN '15–28d'
        WHEN DATEDIFF(DAY, booked_at, scheduled_start) <= 56 THEN '29–56d'
        ELSE '>56d'
    END;

/* Q4. Which records explain a dashboard/source mismatch? */
SELECT
    COALESCE(s.appointment_id, d.appointment_id) AS appointment_id,
    s.appointment_status AS source_status,
    d.appointment_status AS dashboard_status,
    s.scheduled_start AS source_scheduled_start,
    d.scheduled_start AS dashboard_scheduled_start,
    CASE
        WHEN s.appointment_id IS NULL THEN 'dashboard_only'
        WHEN d.appointment_id IS NULL THEN 'source_only'
        WHEN ISNULL(s.appointment_status, '') <> ISNULL(d.appointment_status, '') THEN 'status_mismatch'
        WHEN ISNULL(s.scheduled_start, '19000101') <> ISNULL(d.scheduled_start, '19000101') THEN 'time_mismatch'
        ELSE 'match'
    END AS reconciliation_status
FROM dbo.source_appointments AS s
FULL OUTER JOIN dbo.dashboard_appointments AS d
    ON d.appointment_id = s.appointment_id
WHERE
    s.appointment_id IS NULL
    OR d.appointment_id IS NULL
    OR ISNULL(s.appointment_status, '') <> ISNULL(d.appointment_status, '')
    OR ISNULL(s.scheduled_start, '19000101') <> ISNULL(d.scheduled_start, '19000101');

/* Q5. How many mature cohorts completed assessment within 90 days? */
DECLARE @report_cutoff date = CAST(GETDATE() AS date);

SELECT
    DATEFROMPARTS(YEAR(referral_received_at), MONTH(referral_received_at), 1) AS referral_month,
    COUNT(*) AS referrals,
    AVG(CASE
        WHEN DATEADD(DAY, 90, referral_received_at) <= @report_cutoff
         AND assessment_completed_at <= DATEADD(DAY, 90, referral_received_at)
        THEN 1.0
        WHEN DATEADD(DAY, 90, referral_received_at) <= @report_cutoff
        THEN 0.0
        ELSE NULL
    END) AS assessment_completed_within_90d_rate
FROM dbo.patient_pathway_mart
GROUP BY DATEFROMPARTS(YEAR(referral_received_at), MONTH(referral_received_at), 1)
ORDER BY referral_month;
