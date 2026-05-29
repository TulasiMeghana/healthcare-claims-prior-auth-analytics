CREATE OR REPLACE TABLE mart_monthly_claim_kpis AS
SELECT
    service_month,
    COUNT(*) AS claim_count,
    ROUND(100.0 * AVG(denied_flag), 2) AS denial_rate_pct,
    ROUND(100.0 * AVG(paid_flag), 2) AS paid_rate_pct,
    ROUND(SUM(charge_amount), 2) AS gross_charges,
    ROUND(SUM(allowed_amount), 2) AS allowed_amount,
    ROUND(SUM(paid_amount), 2) AS paid_amount,
    ROUND(SUM(balance_amount), 2) AS open_balance,
    ROUND(AVG(claim_age_days), 1) AS avg_claim_age_days
FROM fact_claim
GROUP BY service_month
ORDER BY service_month;

CREATE OR REPLACE TABLE mart_payer_performance AS
SELECT
    p.payer_id,
    p.payer_name,
    p.payer_type,
    p.contract_model,
    COUNT(c.claim_id) AS claim_count,
    ROUND(100.0 * AVG(c.denied_flag), 2) AS denial_rate_pct,
    ROUND(100.0 * AVG(c.paid_flag), 2) AS paid_rate_pct,
    ROUND(SUM(c.charge_amount), 2) AS gross_charges,
    ROUND(SUM(c.allowed_amount), 2) AS allowed_amount,
    ROUND(SUM(c.paid_amount), 2) AS paid_amount,
    ROUND(SUM(c.balance_amount), 2) AS open_balance,
    ROUND(AVG(c.claim_age_days), 1) AS avg_claim_age_days
FROM fact_claim c
JOIN dim_payer p ON c.payer_id = p.payer_id
GROUP BY p.payer_id, p.payer_name, p.payer_type, p.contract_model
ORDER BY denial_rate_pct DESC, open_balance DESC;

CREATE OR REPLACE TABLE mart_provider_performance AS
SELECT
    pr.provider_id,
    pr.provider_name,
    pr.specialty,
    pr.facility_type,
    pr.region,
    pr.network_status,
    COUNT(c.claim_id) AS claim_count,
    ROUND(100.0 * AVG(c.denied_flag), 2) AS denial_rate_pct,
    ROUND(SUM(c.paid_amount), 2) AS paid_amount,
    ROUND(SUM(c.balance_amount), 2) AS open_balance,
    ROUND(AVG(c.claim_age_days), 1) AS avg_claim_age_days
FROM fact_claim c
JOIN dim_provider pr ON c.provider_id = pr.provider_id
GROUP BY pr.provider_id, pr.provider_name, pr.specialty, pr.facility_type, pr.region, pr.network_status
HAVING COUNT(c.claim_id) >= 15
ORDER BY denial_rate_pct DESC, open_balance DESC;

CREATE OR REPLACE TABLE mart_authorization_turnaround AS
SELECT
    p.payer_name,
    a.specialty,
    a.clinical_priority,
    COUNT(*) AS authorization_count,
    ROUND(100.0 * AVG(CASE WHEN a.authorization_status = 'APPROVED' THEN 1 ELSE 0 END), 2) AS approval_rate_pct,
    ROUND(100.0 * AVG(CASE WHEN a.authorization_status = 'DENIED' THEN 1 ELSE 0 END), 2) AS denial_rate_pct,
    ROUND(100.0 * AVG(CASE WHEN a.authorization_status = 'PENDING' THEN 1 ELSE 0 END), 2) AS pending_rate_pct,
    ROUND(AVG(a.turnaround_days), 1) AS avg_turnaround_days
FROM fact_authorization a
JOIN dim_payer p ON a.payer_id = p.payer_id
GROUP BY p.payer_name, a.specialty, a.clinical_priority
ORDER BY pending_rate_pct DESC, avg_turnaround_days DESC;

CREATE OR REPLACE TABLE mart_prior_auth_queue AS
SELECT
    a.authorization_id,
    a.request_date,
    a.decision_date,
    a.authorization_status,
    a.clinical_priority,
    a.turnaround_days,
    DATE_DIFF('day', a.request_date, CURRENT_DATE) AS request_age_days,
    p.payer_name,
    pr.provider_name,
    pr.specialty,
    a.denial_reason,
    CASE
        WHEN a.authorization_status = 'PENDING' AND DATE_DIFF('day', a.request_date, CURRENT_DATE) > 10 THEN 'High'
        WHEN a.authorization_status = 'DENIED' THEN 'High'
        WHEN a.clinical_priority IN ('Urgent', 'Emergent') THEN 'Medium'
        ELSE 'Normal'
    END AS queue_priority
FROM fact_authorization a
JOIN dim_payer p ON a.payer_id = p.payer_id
JOIN dim_provider pr ON a.provider_id = pr.provider_id
WHERE a.needs_follow_up_flag = 1
ORDER BY
    CASE queue_priority WHEN 'High' THEN 1 WHEN 'Medium' THEN 2 ELSE 3 END,
    request_age_days DESC;

CREATE OR REPLACE TABLE mart_claim_aging_buckets AS
SELECT
    aging_bucket,
    COUNT(*) AS claim_count,
    ROUND(SUM(balance_amount), 2) AS open_balance,
    ROUND(AVG(balance_amount), 2) AS avg_balance,
    ROUND(AVG(claim_age_days), 1) AS avg_claim_age_days
FROM fact_claim
GROUP BY aging_bucket
ORDER BY
    CASE aging_bucket
        WHEN '0-30' THEN 1
        WHEN '31-60' THEN 2
        WHEN '61-90' THEN 3
        WHEN '90+' THEN 4
        ELSE 5
    END;

CREATE OR REPLACE TABLE mart_denial_reasons AS
SELECT
    denial_reason,
    COUNT(*) AS denied_claims,
    ROUND(SUM(allowed_amount), 2) AS denied_allowed_amount,
    ROUND(SUM(balance_amount), 2) AS denied_open_balance
FROM fact_claim
WHERE claim_status = 'DENIED'
GROUP BY denial_reason
ORDER BY denied_claims DESC;
 
CREATE OR REPLACE TABLE mart_authorization_sla AS
WITH auth_base AS (
    SELECT
        p.payer_name,
        a.specialty,
        a.clinical_priority,
        a.authorization_status,
        a.turnaround_days,
        DATE_DIFF('day', a.request_date, CURRENT_DATE) AS request_age_days,
        CASE
            WHEN a.authorization_status = 'PENDING'
                 AND DATE_DIFF('day', a.request_date, CURRENT_DATE) > 7
                 THEN 1

            WHEN a.authorization_status IN ('APPROVED', 'DENIED')
                 AND a.turnaround_days > 5
                 THEN 1

            ELSE 0
        END AS sla_breached_flag
    FROM fact_authorization a
    JOIN dim_payer p
        ON a.payer_id = p.payer_id
)

SELECT
    payer_name,
    specialty,
    clinical_priority,
    COUNT(*) AS total_authorizations,
    SUM(sla_breached_flag) AS sla_breached_count,
    ROUND(100.0 * AVG(sla_breached_flag), 2) AS sla_breach_rate_pct
FROM auth_base
GROUP BY payer_name, specialty, clinical_priority
ORDER BY sla_breach_rate_pct DESC, total_authorizations DESC;


CREATE OR REPLACE TABLE mart_revenue_leakage_risk AS
SELECT
    c.claim_id,
    c.patient_id,
    pr.provider_name,
    p.payer_name,
    pr.specialty,
    c.claim_status,
    c.service_date,
    c.submitted_date,
    c.aging_bucket,
    c.charge_amount,
    c.allowed_amount,
    c.paid_amount,
    c.balance_amount,
    c.denial_reason,

    CASE
        WHEN c.balance_amount > 500
             AND c.claim_status = 'DENIED'
             THEN 'High - Denied High Balance'

        WHEN c.balance_amount > 500
             AND c.aging_bucket = '90+'
             THEN 'High - Aged High Balance'

        WHEN c.balance_amount BETWEEN 250 AND 500
             AND c.claim_status IN ('DENIED', 'PARTIALLY_PAID')
             THEN 'Medium'

        ELSE 'Low'
    END AS revenue_leakage_risk,

    CASE
        WHEN c.balance_amount > 500
             AND c.claim_status = 'DENIED'
             THEN 1

        WHEN c.balance_amount > 500
             AND c.aging_bucket = '90+'
             THEN 2

        WHEN c.balance_amount BETWEEN 250 AND 500
             AND c.claim_status IN ('DENIED', 'PARTIALLY_PAID')
             THEN 3

        ELSE 4
    END AS risk_sort_order

FROM fact_claim c
JOIN dim_provider pr
    ON c.provider_id = pr.provider_id
JOIN dim_payer p
    ON c.payer_id = p.payer_id
WHERE c.balance_amount > 0
ORDER BY risk_sort_order, c.balance_amount DESC;


CREATE OR REPLACE TABLE mart_payer_risk_score AS
WITH auth_sla_by_payer AS (
    SELECT
        payer_name,
        ROUND(AVG(sla_breach_rate_pct), 2) AS auth_sla_breach_rate_pct
    FROM mart_authorization_sla
    GROUP BY payer_name
),

payer_score AS (
    SELECT
        p.payer_name,
        p.claim_count,
        p.denial_rate_pct,
        p.open_balance,
        p.avg_claim_age_days,
        COALESCE(a.auth_sla_breach_rate_pct, 0) AS auth_sla_breach_rate_pct,

        ROUND(
            (p.denial_rate_pct * 0.40)
            + (LEAST(p.open_balance / 10000, 10) * 2.5)
            + (LEAST(p.avg_claim_age_days / 10, 10) * 2.0)
            + (COALESCE(a.auth_sla_breach_rate_pct, 0) * 0.25),
            2
        ) AS payer_risk_score

    FROM mart_payer_performance p
    LEFT JOIN auth_sla_by_payer a
        ON p.payer_name = a.payer_name
)

SELECT
    payer_name,
    claim_count,
    denial_rate_pct,
    open_balance,
    avg_claim_age_days,
    auth_sla_breach_rate_pct,
    payer_risk_score,

    CASE
        WHEN payer_risk_score >= 50 THEN 'High Risk'
        WHEN payer_risk_score >= 25 THEN 'Medium Risk'
        ELSE 'Low Risk'
    END AS payer_risk_tier

FROM payer_score
ORDER BY payer_risk_score DESC;