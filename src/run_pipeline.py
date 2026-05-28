"""Build the local DuckDB analytics warehouse and run data quality checks."""

from __future__ import annotations

import duckdb

from config import DATA_PROCESSED, DATA_RAW, DB_PATH, SQL_DIR, WAREHOUSE_DIR
from data_quality import run_quality_checks

RAW_TABLES = {
    "raw_patients": DATA_RAW / "patients.csv",
    "raw_providers": DATA_RAW / "providers.csv",
    "raw_payers": DATA_RAW / "payers.csv",
    "raw_encounters": DATA_RAW / "encounters.csv",
    "raw_authorizations": DATA_RAW / "authorizations.csv",
    "raw_claims": DATA_RAW / "claims.csv",
}


def load_raw_tables(con: duckdb.DuckDBPyConnection) -> None:
    for table_name, csv_path in RAW_TABLES.items():
        if not csv_path.exists():
            raise FileNotFoundError(
                f"Missing {csv_path}. Run `python src/generate_synthetic_data.py` first."
            )
        con.execute(
            f"CREATE OR REPLACE TABLE {table_name} AS "
            f"SELECT * FROM read_csv_auto('{csv_path.as_posix()}', HEADER=TRUE)"
        )
        row_count = con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        print(f"Loaded {table_name}: {row_count:,} rows")


def execute_sql_file(con: duckdb.DuckDBPyConnection, filename: str) -> None:
    sql_path = SQL_DIR / filename
    sql = sql_path.read_text(encoding="utf-8")
    con.execute(sql)
    print(f"Executed {filename}")


def main() -> None:
    WAREHOUSE_DIR.mkdir(parents=True, exist_ok=True)
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect(DB_PATH.as_posix())
    try:
        load_raw_tables(con)
        execute_sql_file(con, "01_staging.sql")
        execute_sql_file(con, "02_marts.sql")
        execute_sql_file(con, "03_business_metrics.sql")

        quality_report = run_quality_checks(con)
        quality_report.to_csv(DATA_PROCESSED / "data_quality_report.csv", index=False)
        con.register("quality_report_df", quality_report)
        con.execute("CREATE OR REPLACE TABLE mart_data_quality_checks AS SELECT * FROM quality_report_df")

        print("\nData quality report:")
        print(quality_report.to_string(index=False))
        print(f"\nBuilt warehouse: {DB_PATH}")
    finally:
        con.close()


if __name__ == "__main__":
    main()
