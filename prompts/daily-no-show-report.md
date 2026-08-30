# Prompt — Transport No-Show Priority Report (daily)

A generic, source-agnostic business prompt. It names no systems, files, or tickets on purpose:
the agent must route to the right source itself using the AGENTS.md source map + memory. Paste it
into a **fresh** OpenWorker session.

---

**Build me a "Transport No-Show Priority Report" and then set it to run daily.**

Work through these steps and show your reasoning:

1. **Pull the raw numbers.** Find our transport no-show data and aggregate the most recent month
   **per clinic**: total scheduled trips, completed trips, no-shows, and same-day cancellations.

2. **Compute the no-show rate.** Calculate each clinic's no-show rate using our documented
   definition. If more than one official definition exists and they don't agree, compute it each
   way, show them side by side, and flag the discrepancy along with anyone already working on
   resolving it.

3. **Flag priority clinics.** Business rule: any clinic with a no-show rate **above 13%** is a
   **Priority** clinic. Rank all clinics worst-to-best.

4. **Assess SMS-reminder viability.** For each Priority clinic, find our SMS reminder enrollment
   data. Business rule: SMS-only reminders are **NOT viable** for a clinic if its opt-out rate is
   **over 14%** OR its share of invalid/unreachable mobile numbers is **over 10%**. Mark each
   Priority clinic viable / not viable.

5. **Cross-check against the program's direction.** Look at our current plans and any prior
   decisions or analysis on the reminder strategy. Note whether the active plan assumes an
   SMS-only approach, and whether any earlier work contradicts that. Tie your viability findings
   from step 4 to what those plans say.

6. **Write the report.** Produce a one-page brief with: a summary recommendation, a per-clinic
   table (no-show rate(s), priority flag, SMS-viability), any definition conflict called out, and
   any strategy tension called out. Save it as a dated markdown file in your working folder and
   paste the summary in your final message. This is read-only reporting — do not change any of our
   systems or documents.

7. **Automate it.** Once the report looks right, set this up to run **every morning at 7:00 AM** so
   I have a fresh version daily.

---

## Expected result (scorecard)

Thresholds are chosen against the seeded data so a correct run lands on this story:

| Clinic | No-show (Glossary def.) | No-show (Dashboard def.) | Priority? | SMS-only viable? |
|---|---|---|---|---|
| **Pueblo West** | ~13.9% | ~14.8% | ✅ | ❌ Not viable (opt-out 15.4%, invalid 12.1%) |
| **Aurora Regional** | ~13.1% | ~13.7% | ✅ | ⚠️ Borderline |
| Grand Junction | ~10.8% | ~11.5% | No | (viable, not priority) |

**Money conclusion:** the top-priority clinic (Pueblo West) is exactly where SMS-only *fails* the
viability rule — supporting the closed "Won't Do" spike and contradicting the still-active SMS
epic. A good run surfaces that tension AND flags the two conflicting no-show-rate definitions.

## Notes
- The daily automation is **agent-driven** (re-runs the analysis with the model each morning), so
  report quality depends on the model's diligence. Use a strong model for this chain.
- Step 7 triggers a gated `create_scheduled_task` — approve the card to register the `0 7 * * *` job.
