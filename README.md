# Healthcare Claims & Prior Authorization Analytics Platform
An end-to-end healthcare analytics project that simulates claims operations, prior authorization monitoring, payer/provider performance, revenue leakage risk, and data quality validation using synthetic data.

---

## Why this project matters

Healthcare analytics roles often ask for more than dashboarding. They expect analysts to:

- Write reliable SQL for operational and executive metrics.
- Validate messy data before reporting it.
- Translate raw claims/authorization data into business-ready marts.
- Explain metric changes to non-technical stakeholders.
- Build repeatable reporting workflows instead of one-off analysis.

This project demonstrates those skills through a reproducible pipeline.

---

## Business problem

A health-tech operations team needs visibility into:

1. Which payers have the highest denial rates?
2. Which providers have unusually high claim volume or unpaid balances?
3. How long prior authorizations take from submission to decision?
4. Which claims should be prioritized due to aging, denial, or high balance?
5. Are reports trustworthy based on data quality checks?

---

## Tech stack

- **Python**: synthetic data generation and pipeline orchestration
- **DuckDB**: local analytical warehouse
- **SQL**: staging, dimensional modeling, marts, KPI tables
- **pandas / NumPy**: data generation and quality reporting
- **Streamlit + Plotly**: interactive dashboard
- **pytest**: testable quality checks

This stack is intentionally lightweight so recruiters/interviewers can run it locally without needing paid cloud tools.

---

## Repository structure

```text
healthcare-claims-prior-auth-analytics/
├── app/
│   └── streamlit_app.py
├── data/
│   ├── raw/                 # generated synthetic CSVs
│   └── processed/           # exported quality report
├── docs/
│   └── INTERVIEW_NOTES.md
├── sql/
│   ├── 01_staging.sql
│   ├── 02_marts.sql
│   └── 03_business_metrics.sql
├── src/
│   ├── config.py
│   ├── data_quality.py
│   ├── generate_synthetic_data.py
│   └── run_pipeline.py
├── tests/
│   └── test_data_quality.py
├── .gitignore
├── requirements.txt
└── README.md
```

---

## How to run

### 1. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate      # Mac/Linux
# .venv\Scripts\activate     # Windows PowerShell
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Generate synthetic data

```bash
python src/generate_synthetic_data.py
```

### 4. Build the local analytics warehouse

```bash
python src/run_pipeline.py
```

### 5. Run tests

```bash
pytest
```

### 6. Launch dashboard

```bash
streamlit run app/streamlit_app.py
```

---
## Dashboard Preview

![Dashboard Overview](assets/dashboard-overview.png)
![Payer Performance](assets/payer-performance.png)
![Prior Authorization Queue](assets/prior-auth-queue.png)
![Data Quality Report](assets/data-quality-report.png)


## Synthetic data model

The project creates six synthetic raw tables:

| Table | Description |
|---|---|
| `patients.csv` | Synthetic patient demographics and location fields |
| `providers.csv` | Provider specialty, facility type, and region |
| `payers.csv` | Commercial, Medicare Advantage, Medicaid, and self-pay plans |
| `encounters.csv` | Patient visits connected to providers |
| `authorizations.csv` | Prior authorization request, decision, turnaround time, and status |
| `claims.csv` | Claim status, charges, payments, denial reason, service date, and balance |

No real patient data is used.

---

## Analytics marts created

| Mart | Purpose |
|---|---|
| `mart_monthly_claim_kpis` | Monthly claim count, denial rate, paid rate, gross charges, allowed amount, paid amount |
| `mart_payer_performance` | Payer-level denial rate, balance, average payment, and claim aging |
| `mart_provider_performance` | Provider-level claim volume, denial rate, paid amount, and average claim age |
| `mart_authorization_turnaround` | Authorization approval/denial rates and turnaround time by payer/specialty |
| `mart_prior_auth_queue` | Operational queue for pending/denied/high-risk authorization cases |
| `mart_claim_aging_buckets` | 0-30, 31-60, 61-90, and 90+ day unpaid claim buckets |

---
## Custom business rules

### Authorization SLA breach rate

An authorization is treated as an SLA breach if it is still pending after 7 days or if an approved/denied authorization took more than 5 days to receive a decision.

### Revenue leakage risk

A claim is classified as higher revenue leakage risk when it has an unpaid balance and is denied, partially paid, or aged into the 90+ day bucket.

### Payer risk score

The payer risk score combines denial rate, open balance, average claim age, and authorization SLA breach rate to assign each payer a low, medium, or high risk tier.


## Data quality checks

The pipeline validates:

- Duplicate primary keys
- Missing required IDs
- Broken foreign keys
- Invalid claim statuses
- Invalid authorization statuses
- Negative charges/payments/balances
- Claim service dates after submission dates
- Authorization decision dates before request dates
- Paid amount greater than allowed amount
- Missing denial reason on denied claims

Results are written to:

```text
data/processed/data_quality_report.csv
```

and also stored inside DuckDB as:

```sql
mart_data_quality_checks
```

---