═══════════════════════════════════════════════════════════════════════════════
PATIENT TRANSPORT NO-SHOW REDUCTION — EXECUTIVE BRIEF
Date: 2026-08-19 | Scope: Regional outpatient clinics, NEMT + rideshare
═══════════════════════════════════════════════════════════════════════════════

THE ASK
  Cut transport no-show rate by 30% within two quarters.

THE BASELINE
  18.4% no-show rate (Glossary definition), 11%–27% by site. NOTE: an alternate
  definition used by the Ops Dashboard reports 24%. These are not comparable.

WHAT WE TRIED
  ┌─────────────────────┬─────────────────────────────────────────────────────┐
  │ Pilot A: SMS-only   │ ~6% reduction (not significant). Capped by ~22%     │
  │                     │ invalid/landline numbers.                           │
  ├─────────────────────┼─────────────────────────────────────────────────────┤
  │ Pilot B: Live caller│ ~32% reduction (significant). Cost: ~7 min/trip.    │
  │                     │ Reached 61% live.                                   │
  ├─────────────────────┼─────────────────────────────────────────────────────┤
  │ Spike: SMS-only?    │ CLOSED WON'T DO. Recommendation: hybrid approach.   │
  └─────────────────────┴─────────────────────────────────────────────────────┘

WHAT'S IN JIRA
  Epic BP2-1 (SMS-only rollout) — To Do, "committed for this quarter."
  Problem: Its core assumption (SMS-only is sufficient) directly contradicts
  the closed spike and Pilot A results. The Epic itself flags this conflict.

WHAT'S BLOCKING US
  • No single definition of "no-show rate." Analytics and Dashboard use
    different formulas. Two baselines = two stories.
  • Phone numbers are free-text, unvalidated. Root cause of SMS undeliverability.
  • No production code, dashboard, or middleware has been shipped.

THE RISK
  If we build BP2-1 as scoped, we will likely spend a quarter delivering a
  single-channel SMS program that the evidence already says will miss the 30%
  target. Meanwhile, wheelchair-dependent and rural patients need vehicle
  supply / scheduling fixes, not reminders.

THE UNASKED QUESTION
  What is the dollar cost of a missed transport trip? Without this, we cannot
  size ROI or stack-rank this initiative against other clinic ops work.

RECOMMENDED NEXT STEPS
  1. HALT BP2-1 until the SMS-only assumption is reconciled with the closed
     spike. Either rescope to hybrid or document why the spike is wrong.
  2. Pick ONE no-show-rate definition before any target reporting.
  3. Size the problem in dollars before committing engineering capacity.
═══════════════════════════════════════════════════════════════════════════════
