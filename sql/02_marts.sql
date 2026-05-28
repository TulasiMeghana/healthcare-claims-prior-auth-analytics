CREATE OR REPLACE TABLE dim_patient AS
SELECT
    patient_id,
    patient_name,
    birth_date,
    patient_age,
    CASE
        WHEN patient_age < 18 THEN '0-17'
        WHEN patient_age BETWEEN 18 AND 34 THEN '18-34'
        WHEN patient_age BETWEEN 35 AND 49 THEN '35-49'
        WHEN patient_age BETWEEN 50 AND 64 THEN '50-64'
        ELSE '65+'
    END AS age_band,
    gender,
    state,
    risk_segment
FROM stg_patients;

CREATE OR REPLACE TABLE dim_provider AS
SELECT
    provider_id,
    provider_name,
    specialty,
    facility_type,
    region,
    network_status
FROM stg_providers;

CREATE OR REPLACE TABLE dim_payer AS
SELECT
    payer_id,
    payer_name,
    payer_type,
    contract_model
FROM stg_payers;

CREATE OR REPLACE TABLE fact_encounter AS
SELECT
    e.encounter_id,
    e.patient_id,
    e.provider_id,
    e.encounter_date,
    e.encounter_type,
    e.diagnosis_group
FROM stg_encounters e;

CREATE OR REPLACE TABLE fact_authorization AS
SELECT
    a.authorization_id,
    a.encounter_id,
    a.patient_id,
    a.provider_id,
    a.payer_id,
    a.specialty,
    a.request_date,
    a.decision_date,
    a.authorization_status,
    a.clinical_priority,
    a.denial_reason,
    a.turnaround_days,
    CASE
        WHEN a.authorization_status = 'PENDING' AND DATE_DIFF('day', a.request_date, CURRENT_DATE) > 7 THEN 1
        WHEN a.authorization_status = 'DENIED' THEN 1
        ELSE 0
    END AS needs_follow_up_flag
FROM stg_authorizations a;

CREATE OR REPLACE TABLE fact_claim AS
SELECT
    c.claim_id,
    c.encounter_id,
    c.authorization_id,
    c.patient_id,
    c.provider_id,
    c.payer_id,
    c.service_date,
    c.submitted_date,
    DATE_TRUNC('month', c.service_date) AS service_month,
    c.claim_status,
    c.cpt_code,
    c.charge_amount,
    c.allowed_amount,
    c.paid_amount,
    c.patient_responsibility,
    c.balance_amount,
    c.denial_reason,
    c.claim_age_days,
    CASE
        WHEN c.claim_status = 'DENIED' THEN 1 ELSE 0
    END AS denied_flag,
    CASE
        WHEN c.claim_status = 'PAID' THEN 1 ELSE 0
    END AS paid_flag,
    CASE
        WHEN c.balance_amount > 0 AND c.claim_age_days <= 30 THEN '0-30'
        WHEN c.balance_amount > 0 AND c.claim_age_days BETWEEN 31 AND 60 THEN '31-60'
        WHEN c.balance_amount > 0 AND c.claim_age_days BETWEEN 61 AND 90 THEN '61-90'
        WHEN c.balance_amount > 0 AND c.claim_age_days > 90 THEN '90+'
        ELSE 'No Open Balance'
    END AS aging_bucket
FROM stg_claims c;
