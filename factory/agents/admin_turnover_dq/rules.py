"""Admin Turnover reconciliation rules (deterministic, auditable).

Detects mismatches in Facility Admin (FA) / Regional Ops Director (ROD) records
across Oracle MDM (master), Workday (HR truth), and CWOW (role assignments).
The LLM never runs this - it only explains the output.
"""

from __future__ import annotations

from datetime import date, datetime

from agent_factory.business_logic import Mismatch, Severity, index_by

STALE_DAYS = 180


def _is_terminated(wd: dict) -> bool:
    return (str(wd.get("employment_status", "")).strip().lower() == "terminated"
            or bool(wd.get("term_date")))


def _parse(d) -> date | None:
    """Accept ISO strings (CSV path) or date/datetime objects (BigQuery path)."""
    if not d:
        return None
    if isinstance(d, datetime):
        return d.date()
    if isinstance(d, date):
        return d
    try:
        return date.fromisoformat(str(d))
    except ValueError:
        return None


def reconcile(sources: dict[str, list[dict]]) -> list[Mismatch]:
    mdm = sources["mdm"]
    workday = index_by(sources["workday"], "employee_id")
    cwow_by_emp = index_by(sources["cwow"], "employee_id")

    out: list[Mismatch] = []
    for rec in mdm:
        emp = str(rec.get("employee_id", ""))
        fac = str(rec.get("facility_id", ""))
        active = rec.get("status", "").strip().lower() == "active"
        wd = workday.get(emp)
        cw = cwow_by_emp.get(emp)

        # 1) Terminated in Workday but still active admin in MDM (HIGH)
        if active and wd and _is_terminated(wd):
            out.append(Mismatch(
                kind="terminated_but_active", severity=Severity.HIGH,
                employee_id=emp, facility_id=fac,
                detail=f"Employee {emp} is terminated in Workday "
                       f"(term_date={wd.get('term_date') or 'n/a'}) but still an active "
                       f"{rec.get('role')} in MDM for facility {fac}.",
                sources={"mdm": rec, "workday": wd},
            ))

        # 2) Role mismatch between MDM and CWOW (MEDIUM)
        if cw and rec.get("role") and cw.get("assigned_role") \
                and rec["role"].strip().lower() != cw["assigned_role"].strip().lower():
            out.append(Mismatch(
                kind="role_mismatch", severity=Severity.MEDIUM,
                employee_id=emp, facility_id=fac,
                detail=f"MDM role '{rec.get('role')}' != CWOW assigned_role "
                       f"'{cw.get('assigned_role')}' for employee {emp}.",
                sources={"mdm": rec, "cwow": cw},
            ))

        # 3) Active MDM admin with no CWOW assignment (MEDIUM)
        if active and cw is None:
            out.append(Mismatch(
                kind="missing_in_cwow", severity=Severity.MEDIUM,
                employee_id=emp, facility_id=fac,
                detail=f"Active MDM {rec.get('role')} {emp} for facility {fac} has no "
                       f"CWOW role assignment.",
                sources={"mdm": rec},
            ))

        # 4) Stale MDM record vs a newer Workday transfer (LOW)
        eff = _parse(rec.get("effective_date"))
        transfer = _parse(wd.get("transfer_date")) if wd else None
        if eff and transfer and transfer > eff and (transfer - eff).days > STALE_DAYS:
            out.append(Mismatch(
                kind="stale_effective_date", severity=Severity.LOW,
                employee_id=emp, facility_id=fac,
                detail=f"MDM effective_date {eff} predates a Workday transfer on "
                       f"{transfer} by >{STALE_DAYS} days for employee {emp}.",
                sources={"mdm": rec, "workday": wd},
            ))
    return out
