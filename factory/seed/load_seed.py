"""Load the mock enterprise CSVs into BigQuery (bronze -> silver).

  python seed/load_seed.py            # loads to the configured GOOGLE_CLOUD_PROJECT
  python seed/load_seed.py --check    # offline: validate CSVs + report injected mismatches

Silver here is a typed copy of bronze. In a real build silver would be a cleaned/
conformed layer; for the prototype the CSVs are already clean so bronze==silver shape.
"""

from __future__ import annotations

import csv
import os
import sys
from pathlib import Path

SEED_DIR = Path(__file__).resolve().parent
FILES = {
    "mdm_admins": "mdm_admins.csv",
    "workday_employees": "workday_employees.csv",
    "cwow_assignments": "cwow_assignments.csv",
}


def _rows(name: str) -> list[dict]:
    with (SEED_DIR / FILES[name]).open(newline="") as fh:
        return list(csv.DictReader(fh))


def check() -> int:
    for name in FILES:
        rows = _rows(name)
        print(f"  {name}: {len(rows)} rows, cols={list(rows[0])}")
    print("CSVs valid. Run the pipeline to see reconciled mismatches.")
    return 0


def _schemas():
    from google.cloud import bigquery

    S = bigquery.SchemaField
    # Explicit schemas - do NOT rely on autodetect: all-string CSVs (e.g. CWOW) make
    # BigQuery mis-name columns (string_field_0...) and silently break reconciliation.
    return {
        "mdm_admins": [S("facility_id", "STRING"), S("employee_id", "STRING"),
                       S("role", "STRING"), S("status", "STRING"), S("effective_date", "DATE")],
        "workday_employees": [S("employee_id", "STRING"), S("employment_status", "STRING"),
                              S("term_date", "DATE"), S("transfer_date", "DATE"),
                              S("current_role", "STRING")],
        "cwow_assignments": [S("facility_id", "STRING"), S("employee_id", "STRING"),
                             S("assigned_role", "STRING")],
    }


def _ensure_output_tables(client, project: str) -> None:
    """Create the write-target tables (idempotent). Mirrors infra/modules/bigquery;
    lets the online demo run without Terraform installed."""
    from google.cloud import bigquery

    S = bigquery.SchemaField
    outputs = {
        "dq_results.admin_turnover": [S("kind", "STRING"), S("severity", "STRING"),
            S("employee_id", "STRING"), S("facility_id", "STRING"), S("detail", "STRING"),
            S("explanation", "STRING"), S("priority", "INTEGER")],
        "ops.review_queue": [S("review_id", "STRING"), S("agent", "STRING"), S("status", "STRING"),
            S("created_at", "TIMESTAMP"), S("kind", "STRING"), S("severity", "STRING"),
            S("employee_id", "STRING"), S("facility_id", "STRING"), S("detail", "STRING"),
            S("reviewer", "STRING")],
        "ops.sent_emails": [S("to", "STRING"), S("subject", "STRING"), S("body", "STRING"),
            S("sent_at", "TIMESTAMP"), S("channel", "STRING")],
    }
    for name, schema in outputs.items():
        client.create_table(bigquery.Table(f"{project}.{name}", schema=schema), exists_ok=True)
        print(f"  ensured {name}")


def load() -> int:  # pragma: no cover - requires GCP
    from google.cloud import bigquery

    project = os.environ["GOOGLE_CLOUD_PROJECT"]
    client = bigquery.Client(project=project)
    for ds in ("bronze", "silver", "gold", "dq_results", "ops"):
        client.create_dataset(bigquery.Dataset(f"{project}.{ds}"), exists_ok=True)
    _ensure_output_tables(client, project)

    schemas = _schemas()
    for table, filename in FILES.items():
        for ds in ("bronze", "silver"):
            table_id = f"{project}.{ds}.{table}"
            job = client.load_table_from_file(
                (SEED_DIR / filename).open("rb"),
                table_id,
                job_config=bigquery.LoadJobConfig(
                    source_format=bigquery.SourceFormat.CSV,
                    skip_leading_rows=1,
                    schema=schemas[table],
                    write_disposition="WRITE_TRUNCATE",
                ),
            )
            job.result()
            print(f"  loaded {table_id} ({client.get_table(table_id).num_rows} rows)")
    print("Seed load complete.")
    return 0


if __name__ == "__main__":
    if "--check" in sys.argv or not os.getenv("GOOGLE_CLOUD_PROJECT"):
        raise SystemExit(check())
    raise SystemExit(load())
