from __future__ import annotations

import sys
from pathlib import Path

import duckdb

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT / "src"))

from config import DB_PATH  # noqa: E402


def test_quality_report_table_exists():
    assert DB_PATH.exists(), "Run `python src/run_pipeline.py` before running tests."
    with duckdb.connect(DB_PATH.as_posix(), read_only=True) as con:
        count = con.execute("SELECT COUNT(*) FROM mart_data_quality_checks").fetchone()[0]
    assert count >= 10


def test_no_critical_quality_failures():
    assert DB_PATH.exists(), "Run `python src/run_pipeline.py` before running tests."
    with duckdb.connect(DB_PATH.as_posix(), read_only=True) as con:
        failures = con.execute(
            """
            SELECT COUNT(*)
            FROM mart_data_quality_checks
            WHERE severity = 'critical'
              AND status = 'FAIL'
            """
        ).fetchone()[0]
    assert failures == 0


def test_core_marts_have_rows():
    assert DB_PATH.exists(), "Run `python src/run_pipeline.py` before running tests."
    tables = [
        "mart_monthly_claim_kpis",
        "mart_payer_performance",
        "mart_provider_performance",
        "mart_authorization_turnaround",
        "mart_prior_auth_queue",
        "mart_claim_aging_buckets",
    ]
    with duckdb.connect(DB_PATH.as_posix(), read_only=True) as con:
        for table in tables:
            row_count = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            assert row_count > 0, f"{table} should have rows"
