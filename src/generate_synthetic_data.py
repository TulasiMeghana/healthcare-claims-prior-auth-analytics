"""Generate synthetic healthcare claims and prior authorization data.

The data is fictional and safe to publish. It is designed to preserve realistic
relationships between patients, providers, payers, encounters, authorizations,
and claims for analytics portfolio work.
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

from config import DATA_RAW

SEED = 42
random.seed(SEED)
np.random.seed(SEED)

N_PATIENTS = 2_500
N_PROVIDERS = 180
N_PAYERS = 9
N_ENCOUNTERS = 8_000
N_AUTHORIZATIONS = 4_500
N_CLAIMS = 10_000

FIRST_NAMES = [
    "Avery", "Jordan", "Taylor", "Morgan", "Casey", "Riley", "Skyler", "Parker",
    "Quinn", "Cameron", "Drew", "Reese", "Emerson", "Hayden", "Alex", "Jamie",
]
LAST_NAMES = [
    "Smith", "Johnson", "Garcia", "Brown", "Davis", "Miller", "Wilson", "Moore",
    "Taylor", "Anderson", "Thomas", "Jackson", "Martin", "Lee", "Perez", "White",
]
SPECIALTIES = [
    "Primary Care", "Cardiology", "Orthopedics", "Neurology", "Oncology",
    "Radiology", "Physical Therapy", "Gastroenterology", "Pulmonology", "Dermatology",
]
FACILITY_TYPES = ["Clinic", "Hospital", "Imaging Center", "Surgery Center", "Specialty Clinic"]
REGIONS = ["North Texas", "Central Texas", "Houston Metro", "Austin Metro", "San Antonio", "East Texas"]
PAYER_TYPES = ["Commercial", "Medicare Advantage", "Medicaid", "Self Pay"]
CLAIM_STATUSES = ["PAID", "DENIED", "PENDING", "PARTIAL"]
AUTH_STATUSES = ["APPROVED", "DENIED", "PENDING", "CANCELLED"]
DENIAL_REASONS = [
    "Missing documentation", "Eligibility issue", "Authorization required",
    "Coding mismatch", "Medical necessity not met", "Duplicate claim",
]
CPT_CODES = ["99213", "99214", "93000", "97110", "71046", "80053", "70553", "45378", "27447", "99285"]
DIAGNOSIS_GROUPS = ["Cardiac", "Musculoskeletal", "Neurology", "Preventive", "Respiratory", "Digestive", "Oncology"]


def random_date(start: datetime, end: datetime) -> datetime:
    delta_days = (end - start).days
    return start + timedelta(days=random.randint(0, delta_days))


def make_patients() -> pd.DataFrame:
    patient_ids = [f"PAT-{i:06d}" for i in range(1, N_PATIENTS + 1)]
    rows = []
    for pid in patient_ids:
        birth_year = random.randint(1940, 2010)
        rows.append(
            {
                "patient_id": pid,
                "patient_name": f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
                "birth_date": f"{birth_year}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",
                "gender": random.choice(["F", "M", "Unknown"]),
                "state": random.choice(["TX", "OK", "LA", "AR", "NM"]),
                "risk_segment": random.choices(["Low", "Medium", "High"], weights=[0.55, 0.32, 0.13])[0],
            }
        )
    return pd.DataFrame(rows)


def make_providers() -> pd.DataFrame:
    rows = []
    for i in range(1, N_PROVIDERS + 1):
        rows.append(
            {
                "provider_id": f"PRV-{i:05d}",
                "provider_name": f"{random.choice(LAST_NAMES)} {random.choice(FACILITY_TYPES)} {i}",
                "specialty": random.choice(SPECIALTIES),
                "facility_type": random.choice(FACILITY_TYPES),
                "region": random.choice(REGIONS),
                "network_status": random.choices(["In Network", "Out of Network"], weights=[0.82, 0.18])[0],
            }
        )
    return pd.DataFrame(rows)


def make_payers() -> pd.DataFrame:
    names = [
        "Blue Horizon Health", "Lone Star Choice", "Pioneer Medicare", "Cedar Medicaid",
        "Atlas Commercial", "BrightPath Health", "Summit Self Pay", "Unity Advantage", "ClearCare Plus",
    ]
    rows = []
    for i, name in enumerate(names, start=1):
        rows.append(
            {
                "payer_id": f"PAY-{i:03d}",
                "payer_name": name,
                "payer_type": random.choice(PAYER_TYPES),
                "contract_model": random.choice(["Fee for Service", "Value Based", "Capitated"]),
            }
        )
    return pd.DataFrame(rows)


def make_encounters(patients: pd.DataFrame, providers: pd.DataFrame) -> pd.DataFrame:
    rows = []
    start = datetime(2024, 1, 1)
    end = datetime(2025, 12, 15)
    for i in range(1, N_ENCOUNTERS + 1):
        service_date = random_date(start, end)
        rows.append(
            {
                "encounter_id": f"ENC-{i:07d}",
                "patient_id": random.choice(patients["patient_id"].tolist()),
                "provider_id": random.choice(providers["provider_id"].tolist()),
                "encounter_date": service_date.date().isoformat(),
                "encounter_type": random.choice(["Office Visit", "Emergency", "Imaging", "Procedure", "Therapy", "Telehealth"]),
                "diagnosis_group": random.choice(DIAGNOSIS_GROUPS),
            }
        )
    return pd.DataFrame(rows)


def make_authorizations(encounters: pd.DataFrame, payers: pd.DataFrame, providers: pd.DataFrame) -> pd.DataFrame:
    sampled_encounters = encounters.sample(N_AUTHORIZATIONS, random_state=SEED).reset_index(drop=True)
    provider_specialty = providers.set_index("provider_id")["specialty"].to_dict()
    rows = []
    for i, enc in sampled_encounters.iterrows():
        request_date = datetime.fromisoformat(enc["encounter_date"]) - timedelta(days=random.randint(1, 21))
        status = random.choices(AUTH_STATUSES, weights=[0.66, 0.17, 0.13, 0.04])[0]
        decision_date = None if status == "PENDING" else request_date + timedelta(days=random.randint(0, 14))
        clinical_priority = random.choices(["Routine", "Urgent", "Emergent"], weights=[0.70, 0.25, 0.05])[0]
        rows.append(
            {
                "authorization_id": f"AUTH-{i + 1:07d}",
                "encounter_id": enc["encounter_id"],
                "patient_id": enc["patient_id"],
                "provider_id": enc["provider_id"],
                "payer_id": random.choice(payers["payer_id"].tolist()),
                "specialty": provider_specialty[enc["provider_id"]],
                "request_date": request_date.date().isoformat(),
                "decision_date": None if decision_date is None else decision_date.date().isoformat(),
                "authorization_status": status,
                "clinical_priority": clinical_priority,
                "denial_reason": random.choice(DENIAL_REASONS) if status == "DENIED" else None,
            }
        )
    return pd.DataFrame(rows)


def make_claims(
    encounters: pd.DataFrame,
    payers: pd.DataFrame,
    authorizations: pd.DataFrame,
) -> pd.DataFrame:
    encounter_ids = encounters["encounter_id"].tolist()
    encounter_lookup = encounters.set_index("encounter_id").to_dict("index")
    auth_by_encounter = authorizations.set_index("encounter_id")["authorization_id"].to_dict()

    rows = []
    for i in range(1, N_CLAIMS + 1):
        enc_id = random.choice(encounter_ids)
        enc = encounter_lookup[enc_id]
        service_date = datetime.fromisoformat(enc["encounter_date"])
        submitted_date = service_date + timedelta(days=random.randint(1, 18))
        status = random.choices(CLAIM_STATUSES, weights=[0.62, 0.18, 0.13, 0.07])[0]
        charge_amount = round(float(np.random.gamma(shape=2.8, scale=420) + 80), 2)
        allowed_amount = round(charge_amount * random.uniform(0.42, 0.88), 2)
        if status == "PAID":
            paid_amount = round(allowed_amount * random.uniform(0.82, 1.0), 2)
        elif status == "PARTIAL":
            paid_amount = round(allowed_amount * random.uniform(0.25, 0.75), 2)
        elif status == "DENIED":
            paid_amount = 0.0
        else:
            paid_amount = 0.0
        patient_responsibility = round(max(0, allowed_amount - paid_amount) * random.uniform(0.05, 0.25), 2)
        balance_amount = round(max(0, allowed_amount - paid_amount - patient_responsibility), 2)
        denial_reason = random.choice(DENIAL_REASONS) if status == "DENIED" else None
        rows.append(
            {
                "claim_id": f"CLM-{i:08d}",
                "encounter_id": enc_id,
                "authorization_id": auth_by_encounter.get(enc_id),
                "patient_id": enc["patient_id"],
                "provider_id": enc["provider_id"],
                "payer_id": random.choice(payers["payer_id"].tolist()),
                "service_date": service_date.date().isoformat(),
                "submitted_date": submitted_date.date().isoformat(),
                "claim_status": status,
                "cpt_code": random.choice(CPT_CODES),
                "charge_amount": charge_amount,
                "allowed_amount": allowed_amount,
                "paid_amount": paid_amount,
                "patient_responsibility": patient_responsibility,
                "balance_amount": balance_amount,
                "denial_reason": denial_reason,
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    DATA_RAW.mkdir(parents=True, exist_ok=True)
    patients = make_patients()
    providers = make_providers()
    payers = make_payers()
    encounters = make_encounters(patients, providers)
    authorizations = make_authorizations(encounters, payers, providers)
    claims = make_claims(encounters, payers, authorizations)

    outputs = {
        "patients.csv": patients,
        "providers.csv": providers,
        "payers.csv": payers,
        "encounters.csv": encounters,
        "authorizations.csv": authorizations,
        "claims.csv": claims,
    }
    for filename, df in outputs.items():
        df.to_csv(DATA_RAW / filename, index=False)
        print(f"Wrote {filename}: {len(df):,} rows")


if __name__ == "__main__":
    main()
