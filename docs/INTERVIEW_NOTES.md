# Interview Notes

Use these notes to defend the project in interviews.

## What I built

I built a local healthcare analytics platform using synthetic patient, provider, payer, claim, encounter, and prior authorization data. The project simulates the reporting work a healthcare data analyst would do for operations, payer performance, claims aging, denial analysis, and authorization turnaround.

## Why I chose this project

Healthcare data analyst roles often require SQL, Python, data quality, dashboarding, documentation, and the ability to explain trends to non-technical stakeholders. This project demonstrates all of those skills without using protected health information.

## Why synthetic data

Healthcare data is sensitive and regulated. I used synthetic data so the project is public and safe for GitHub while still preserving realistic relationships between patients, encounters, authorizations, claims, providers, and payers.

## Main tables

- `raw_claims`: claim-level financial and status data
- `raw_authorizations`: prior authorization request and decision data
- `raw_encounters`: visit-level data
- `raw_patients`: synthetic patient demographics
- `raw_providers`: provider specialty/facility data
- `raw_payers`: payer type and plan data

## Modeling approach

I used a simple warehouse pattern:

1. Raw CSVs loaded into DuckDB.
2. Staging tables clean data types and standardize field names.
3. Fact and dimension tables organize the analytical model.
4. Mart tables answer business questions.
5. Data quality checks run after mart creation.

## KPIs included

- Claim denial rate
- Paid rate
- Average claim age
- Unpaid balance
- 30/60/90+ aging buckets
- Prior authorization approval rate
- Prior authorization turnaround time
- Payer-level and provider-level performance

## Quality checks I implemented

- Duplicate IDs
- Missing required keys
- Invalid statuses
- Broken foreign-key relationships
- Negative financial values
- Paid amount greater than allowed amount
- Date logic violations
- Denied claims missing denial reasons

## How I would improve it next

- Add dbt for lineage and documentation.
- Deploy the dashboard publicly.
- Add GitHub Actions to run tests on every push.
- Add anomaly detection for sudden denial-rate increases.
- Add a PDF client report export.
- Compare payer/provider performance over rolling 3-month windows.

## Strong interview explanation

The biggest value of this project is not just the dashboard. It is the full workflow: generating realistic synthetic data, building clean SQL models, validating data quality, documenting metric logic, and creating a dashboard that a business user could actually use to prioritize operational work.
