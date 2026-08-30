# Admin turnover reconciliation

Topic: Facility Admin (FA) and Regional Ops Director (ROD) records.

A FA or ROD is considered "turned over" when Workday shows a termination or transfer that Oracle
MDM or CWOW has not yet reflected. Workday is the source of truth for employment status. When
systems disagree, Workday's employment event wins; MDM/CWOW are corrected to match.

Update SLA: MDM should reflect a Workday employment event within 180 days. Beyond that the record
is flagged as stale.
