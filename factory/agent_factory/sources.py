"""Data-access layer behind the source skills.

Each enterprise source (Oracle MDM, Workday, CWOW) is read through one function.
In the prototype the connector is MOCKED: offline it reads the seed CSVs, and
with a GCP project it reads the seeded BigQuery `silver` tables. Swapping the
mock for a real GCP Integration Connector is a change here only - no agent code
changes. This is the "connector interface" the plan calls out.
"""

from __future__ import annotations

import csv
from functools import lru_cache
from pathlib import Path
from typing import Any

from .config import offline

SEED_DIR = Path(__file__).resolve().parent.parent / "seed"

# source name -> (seed csv filename, silver table id)
SOURCES: dict[str, tuple[str, str]] = {
    "mdm": ("mdm_admins.csv", "silver.mdm_admins"),
    "workday": ("workday_employees.csv", "silver.workday_employees"),
    "cwow": ("cwow_assignments.csv", "silver.cwow_assignments"),
}


def _read_csv(filename: str) -> list[dict[str, Any]]:
    path = SEED_DIR / filename
    with path.open(newline="") as fh:
        return [dict(row) for row in csv.DictReader(fh)]


@lru_cache(maxsize=None)
def _read_bigquery(table: str) -> tuple[dict[str, Any], ...]:
    from google.cloud import bigquery

    from .settings import get_settings

    s = get_settings()
    client = bigquery.Client(project=s.project)
    fq = f"{s.dataset_prefix}{table}" if s.dataset_prefix else table
    rows = client.query(f"SELECT * FROM `{s.project}`.{fq}").result()
    return tuple(dict(r) for r in rows)


def read_source(name: str) -> list[dict[str, Any]]:
    """Return all rows for a named enterprise source."""
    if name not in SOURCES:
        raise KeyError(f"unknown source '{name}'. known: {sorted(SOURCES)}")
    filename, table = SOURCES[name]
    if offline():
        return _read_csv(filename)
    return [dict(r) for r in _read_bigquery(table)]
