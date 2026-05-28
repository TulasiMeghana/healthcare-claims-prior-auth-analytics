"""Data quality checks for the healthcare analytics project."""

from __future__ import annotations

from dataclasses import dataclass

import duckdb
import pandas as pd


@dataclass
class QualityCheck:
    check_name: str
    severity: str
    sql: str
    description: str


CHECKS: list[QualityCheck] = [
    QualityCheck(
        "duplicate_claim_ids",
        "critical",
        """
        SELECT COUNT(*) AS failed_records
        FROM (
            SELECT claim_id
            FROM stg_claims
            GROUP BY claim_id
            HAVING COUNT(*) > 1
        )
        """,
        "Claim IDs should be unique.",
    ),
    QualityCheck(
        "duplicate_authorization_ids",
        "critical",
        """
        SELECT COUNT(*) AS failed_records
        FROM (
            SELECT authorization_id
            FROM stg_authorizations
            GROUP BY authorization_id
            HAVING COUNT(*) > 1
        )
        """,
        "Authorization IDs should be unique.",
    ),
    QualityCheck(
        "claims_missing_required_keys",
        "critical",
        """
        SELECT COUNT(*) AS failed_records
        FROM stg_claims
        WHERE claim_id IS NULL
           OR encounter_id IS NULL
           OR patient_id IS NULL
           OR provider_id IS NULL
           OR payer_id IS NULL
        """,
        "Claims must have required business keys.",
    ),
    QualityCheck(
        "claims_broken_patient_fk",
        "critical",
        """
        SELECT COUNT(*) AS failed_records
        FROM stg_claims c
        LEFT JOIN stg_patients p ON c.patient_id = p.patient_id
        WHERE p.patient_id IS NULL
        """,
        "Every claim patient_id should exist in patients.",
    ),
    QualityCheck(
        "claims_broken_provider_fk",
        "critical",
        """
        SELECT COUNT(*) AS failed_records
        FROM stg_claims c
        LEFT JOIN stg_providers p ON c.provider_id = p.provider_id
        WHERE p.provider_id IS NULL
        """,
        "Every claim provider_id should exist in providers.",
    ),
    QualityCheck(
        "claims_broken_payer_fk",
        "critical",
        """
        SELECT COUNT(*) AS failed_records
        FROM stg_claims c
        LEFT JOIN stg_payers p ON c.payer_id = p.payer_id
        WHERE p.payer_id IS NULL
        """,
        "Every claim payer_id should exist in payers.",
    ),
    QualityCheck(
        "invalid_claim_status",
        "high",
        """
        SELECT COUNT(*) AS failed_records
        FROM stg_claims
        WHERE claim_status NOT IN ('PAID', 'DENIED', 'PENDING', 'PARTIAL')
        """,
        "Claim statuses should match expected values.",
    ),
    QualityCheck(
        "invalid_authorization_status",
        "high",
        """
        SELECT COUNT(*) AS failed_records
        FROM stg_authorizations
        WHERE authorization_status NOT IN ('APPROVED', 'DENIED', 'PENDING', 'CANCELLED')
        """,
        "Authorization statuses should match expected values.",
    ),
    QualityCheck(
        "negative_financial_values",
        "critical",
        """
        SELECT COUNT(*) AS failed_records
        FROM stg_claims
        WHERE charge_amount < 0
           OR allowed_amount < 0
           OR paid_amount < 0
           OR patient_responsibility < 0
           OR balance_amount < 0
        """,
        "Financial values should not be negative.",
    ),
    QualityCheck(
        "paid_exceeds_allowed",
        "high",
        """
        SELECT COUNT(*) AS failed_records
        FROM stg_claims
        WHERE paid_amount > allowed_amount
        """,
        "Paid amount should not exceed allowed amount.",
    ),
    QualityCheck(
        "claim_submission_before_service",
        "medium",
        """
        SELECT COUNT(*) AS failed_records
        FROM stg_claims
        WHERE submitted_date < service_date
        """,
        "Claim submission date should be on/after service date.",
    ),
    QualityCheck(
        "auth_decision_before_request",
        "high",
        """
        SELECT COUNT(*) AS failed_records
        FROM stg_authorizations
        WHERE decision_date IS NOT NULL
          AND decision_date < request_date
        """,
        "Authorization decision date should be on/after request date.",
    ),
    QualityCheck(
        "denied_claim_missing_reason",
        "medium",
        """
        SELECT COUNT(*) AS failed_records
        FROM stg_claims
        WHERE claim_status = 'DENIED'
          AND (denial_reason IS NULL OR TRIM(denial_reason) = '')
        """,
        "Denied claims should include a denial reason.",
    ),
    QualityCheck(
        "denied_auth_missing_reason",
        "medium",
        """
        SELECT COUNT(*) AS failed_records
        FROM stg_authorizations
        WHERE authorization_status = 'DENIED'
          AND (denial_reason IS NULL OR TRIM(denial_reason) = '')
        """,
        "Denied authorizations should include a denial reason.",
    ),
]


def run_quality_checks(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """Run quality checks and return a report DataFrame."""
    rows: list[dict[str, object]] = []
    for check in CHECKS:
        failed_records = int(con.execute(check.sql).fetchone()[0])
        rows.append(
            {
                "check_name": check.check_name,
                "severity": check.severity,
                "status": "PASS" if failed_records == 0 else "FAIL",
                "failed_records": failed_records,
                "description": check.description,
            }
        )
    return pd.DataFrame(rows)
