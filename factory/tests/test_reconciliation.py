"""The deterministic core: assert every injected mismatch is caught and nothing else."""

from __future__ import annotations

from agent_factory.business_logic import Severity
from agent_factory.sources import read_source
from agents.admin_turnover_dq.rules import reconcile


def _run():
    sources = {name: read_source(name) for name in ("mdm", "workday", "cwow")}
    return reconcile(sources)


def test_finds_exactly_the_injected_mismatches():
    kinds = sorted(m.kind for m in _run())
    assert kinds == [
        "missing_in_cwow",
        "role_mismatch",
        "stale_effective_date",
        "terminated_but_active",
    ]


def test_terminated_but_active_is_high_and_correct_employee():
    m = [x for x in _run() if x.kind == "terminated_but_active"]
    assert len(m) == 1
    assert m[0].severity == Severity.HIGH
    assert m[0].employee_id == "E101"
    assert m[0].facility_id == "F002"


def test_inactive_mdm_record_is_not_flagged_terminated():
    # E105 is Inactive in MDM though Terminated in Workday -> must NOT flag.
    assert not any(x.employee_id == "E105" and x.kind == "terminated_but_active"
                   for x in _run())


def test_role_mismatch_employee():
    m = [x for x in _run() if x.kind == "role_mismatch"]
    assert len(m) == 1 and m[0].employee_id == "E102" and m[0].severity == Severity.MEDIUM


def test_missing_in_cwow_employee():
    m = [x for x in _run() if x.kind == "missing_in_cwow"]
    assert len(m) == 1 and m[0].employee_id == "E103"


def test_stale_effective_date_employee():
    m = [x for x in _run() if x.kind == "stale_effective_date"]
    assert len(m) == 1 and m[0].employee_id == "E104" and m[0].severity == Severity.LOW
