CREATE OR REPLACE TABLE stg_patients AS
SELECT
    patient_id::VARCHAR AS patient_id,
    patient_name::VARCHAR AS patient_name,
    TRY_CAST(birth_date AS DATE) AS birth_date,
    gender::VARCHAR AS gender,
    state::VARCHAR AS state,
    risk_segment::VARCHAR AS risk_segment,
    DATE_DIFF('year', TRY_CAST(birth_date AS DATE), CURRENT_DATE) AS patient_age
FROM raw_patients;

CREATE OR REPLACE TABLE stg_providers AS
SELECT
    provider_id::VARCHAR AS provider_id,
    provider_name::VARCHAR AS provider_name,
    specialty::VARCHAR AS specialty,
    facility_type::VARCHAR AS facility_type,
    region::VARCHAR AS region,
    network_status::VARCHAR AS network_status
FROM raw_providers;

CREATE OR REPLACE TABLE stg_payers AS
SELECT
    payer_id::VARCHAR AS payer_id,
    payer_name::VARCHAR AS payer_name,
    payer_type::VARCHAR AS payer_type,
    contract_model::VARCHAR AS contract_model
FROM raw_payers;

CREATE OR REPLACE TABLE stg_encounters AS
SELECT
    encounter_id::VARCHAR AS encounter_id,
    patient_id::VARCHAR AS patient_id,
    provider_id::VARCHAR AS provider_id,
    TRY_CAST(encounter_date AS DATE) AS encounter_date,
    encounter_type::VARCHAR AS encounter_type,
    diagnosis_group::VARCHAR AS diagnosis_group
FROM raw_encounters;

CREATE OR REPLACE TABLE stg_authorizations AS
SELECT
    authorization_id::VARCHAR AS authorization_id,
    encounter_id::VARCHAR AS encounter_id,
    patient_id::VARCHAR AS patient_id,
    provider_id::VARCHAR AS provider_id,
    payer_id::VARCHAR AS payer_id,
    specialty::VARCHAR AS specialty,
    TRY_CAST(request_date AS DATE) AS request_date,
    TRY_CAST(decision_date AS DATE) AS decision_date,
    authorization_status::VARCHAR AS authorization_status,
    clinical_priority::VARCHAR AS clinical_priority,
    denial_reason::VARCHAR AS denial_reason,
    CASE
        WHEN decision_date IS NULL THEN NULL
        ELSE DATE_DIFF('day', TRY_CAST(request_date AS DATE), TRY_CAST(decision_date AS DATE))
    END AS turnaround_days
FROM raw_authorizations;

CREATE OR REPLACE TABLE stg_claims AS
SELECT
    claim_id::VARCHAR AS claim_id,
    encounter_id::VARCHAR AS encounter_id,
    authorization_id::VARCHAR AS authorization_id,
    patient_id::VARCHAR AS patient_id,
    provider_id::VARCHAR AS provider_id,
    payer_id::VARCHAR AS payer_id,
    TRY_CAST(service_date AS DATE) AS service_date,
    TRY_CAST(submitted_date AS DATE) AS submitted_date,
    claim_status::VARCHAR AS claim_status,
    cpt_code::VARCHAR AS cpt_code,
    TRY_CAST(charge_amount AS DOUBLE) AS charge_amount,
    TRY_CAST(allowed_amount AS DOUBLE) AS allowed_amount,
    TRY_CAST(paid_amount AS DOUBLE) AS paid_amount,
    TRY_CAST(patient_responsibility AS DOUBLE) AS patient_responsibility,
    TRY_CAST(balance_amount AS DOUBLE) AS balance_amount,
    denial_reason::VARCHAR AS denial_reason,
    DATE_DIFF('day', TRY_CAST(service_date AS DATE), CURRENT_DATE) AS claim_age_days
FROM raw_claims;
