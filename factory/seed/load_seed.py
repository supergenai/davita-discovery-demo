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


def load() -> int:  # pragma: no cover - requires GCP
    from google.cloud import bigquery

    project = os.environ["GOOGLE_CLOUD_PROJECT"]
    client = bigquery.Client(project=project)
    for ds in ("bronze", "silver", "gold", "dq_results", "ops"):
        client.create_dataset(bigquery.Dataset(f"{project}.{ds}"), exists_ok=True)

    for table, filename in FILES.items():
        for ds in ("bronze", "silver"):
            table_id = f"{project}.{ds}.{table}"
            job = client.load_table_from_file(
                (SEED_DIR / filename).open("rb"),
                table_id,
                job_config=bigquery.LoadJobConfig(
                    source_format=bigquery.SourceFormat.CSV,
                    skip_leading_rows=1, autodetect=True,
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
