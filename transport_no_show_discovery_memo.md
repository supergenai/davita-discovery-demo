# Patient Transport No-Show Reduction — Discovery Memo

**Date:** 2026-08-19  
**Scope:** Regional outpatient clinics using contracted NEMT and rideshare  
**Sources reviewed:** 4 Jira issues (project BP2) + 13 Confluence pages (personal space of arsalan hafiz)  

---

## 1. WHAT WE ALREADY KNOW

### Baseline & Target
- The transport no-show rate across regional clinics is **18.4%** (per the Glossary definition), with a range of **11%–27% by site**.  
  _Source: [2024 No-Show Baseline Analysis](https://davita-demo.atlassian.net/wiki/spaces/~71202087d07093cbdf419895df9183abeeea5f/pages/688129)_
- Leadership has asked for a **30% relative reduction** within two quarters.  
  _Source: [Patient Transport No-Show Reduction — Program Charter](https://davita-demo.atlassian.net/wiki/spaces/~71202087d07093cbdf419895df9183abeeea5f/pages/589825)_
- **An earlier analysis reported 24%**, but this used the Ops Dashboard definition (which removes cancellations from the denominator and folds same-day cancels into no-shows). The page explicitly states: "The two numbers are not comparable. Pick one definition before setting the target."  
  _Source: [2024 No-Show Baseline Analysis](https://davita-demo.atlassian.net/wiki/spaces/~71202087d07093cbdf419895df9183abeeea5f/pages/688129)_

### Pilot A — Automated SMS Reminders (completed)
- **Design:** 6 weeks, 2 clinics, automated SMS at T-24h and T-2h vs. control group with no SMS.
- **Result:** No-show rate moved from **17.9% to 16.8%** — a **~6% relative reduction, not statistically significant**. Opt-out rate was 4%.
- **Key finding:** ~22% of numbers on file were invalid or landlines (SMS undeliverable).  
  _Source: [Pilot A — Automated SMS Reminders (results)](https://davita-demo.atlassian.net/wiki/spaces/~71202087d07093cbdf419895df9183abeeea5f/pages/720897)_

### Pilot B — Live Caller Confirmation (completed)
- **Design:** 6 weeks, 2 clinics, staff called each patient at T-24h to confirm and re-book if needed.
- **Result:** No-show rate fell from **18.1% to 12.3%** — a **~32% relative reduction, significant**.
- **Cost:** ~7 staff-minutes per trip.
- **Reach:** 61% of patients reached live; remainder got voicemail.  
  _Source: [Pilot B — Live Caller Confirmation (results)](https://davita-demo.atlassian.net/wiki/spaces/~71202087d07093cbdf419895df9183abeeea5f/pages/753665)_

### Closed Spike — Is SMS-Only Sufficient?
- **Question:** Can SMS-only deliver the 30% no-show reduction target?
- **Finding:** No. Pilot A showed ~6% relative reduction (not significant), capped by ~22% invalid/landline numbers. The target requires live or hybrid contact (Pilot B: ~32%).
- **Recommendation:** "Do NOT pursue SMS-only. Adopt a hybrid: automated reminder + live confirmation for unconfirmed/high-risk trips, and fix phone-number data quality first."
- **Decision:** Spike closed as **Won't Do**.  
  _Sources: [Spike Write-up — SMS-Only Reminder Approach (CLOSED, Won't Do)](https://davita-demo.atlassian.net/wiki/spaces/~71202087d07093cbdf419895df9183abeeea5f/pages/884737)_ and [BP2-2](https://davita-demo.atlassian.net/browse/BP2-2) (Jira, resolution: Done)

### Prior-Art / Literature Scan
- Reminders help most when they enable **action** (easy reschedule/confirm), not just notification.
- Single-channel reminders plateau quickly; multi-touch and live contact outperform.
- Data quality (valid phone numbers) is a common hidden ceiling on messaging approaches.
- Transportation **availability** (accessible vehicles, rural ETA) is a distinct problem from reminders and needs its own track.
- Implication: "Treating no-shows as purely a reminder problem under-scopes it."  
  _Source: [Literature & Prior-Art Scan — No-Show Drivers](https://davita-demo.atlassian.net/wiki/spaces/~71202087d07093cbdf419895df9183abeeea5f/pages/819201)_

### Patient Segments
- **Ambulatory, metro-adjacent:** reminders + rideshare fallback work well.
- **Wheelchair/accessibility-dependent:** blocked by accessible-vehicle supply, not reminders.
- **Rural:** long ETAs; scheduling density is the lever.
- **Low data-quality contacts:** no valid mobile — unreachable by SMS; need address/landline outreach.
- Segment mix varies widely by site; a single channel will not serve all four.  
  _Source: [Patient Segments & Access Barriers](https://davita-demo.atlassian.net/wiki/spaces/~71202087d07093cbdf419895df9183abeeea5f/pages/131074)_

### Correlational Factors (not causal)
- Trips scheduled >7 days out, no confirmed contact number on file, first-time transport users, and pickup windows before 8am are the top associated factors.  
  _Source: [2024 No-Show Baseline Analysis](https://davita-demo.atlassian.net/wiki/spaces/~71202087d07093cbdf419895df9183abeeea5f/pages/688129)_

---

## 2. WHAT'S ALREADY BUILT

### Nothing has been shipped yet.
- The Jira project **BP2 (Brooksource Pod 2)** contains only **one Epic in To Do status** (BP2-1), **one closed spike** (BP2-2), and **two unstarted stories** (BP2-3, BP2-5). No code, dashboard, or service is in production per the ticket descriptions.

### What exists in ticket form:
| Ticket | Status | Summary |
|--------|--------|---------|
| [BP2-1](https://davita-demo.atlassian.net/browse/BP2-1) | **To Do** | Epic: "Automated SMS Reminder Rollout for regional clinic transport" — roll SMS reminders (T-24h, T-2h) as the PRIMARY lever. |
| [BP2-2](https://davita-demo.atlassian.net/browse/BP2-2) | **Done** | Closed spike: SMS-only insufficient; recommend hybrid approach. |
| [BP2-3](https://davita-demo.atlassian.net/browse/BP2-3) | **To Do** | Story: "Validate mobile phone numbers at transport booking entry" — fix root cause of ~22% SMS-undeliverable ceiling. |
| [BP2-5](https://davita-demo.atlassian.net/browse/BP2-5) | **To Do** | Story: "Reconcile the two no-show-rate definitions (Glossary vs Ops Dashboard)" — pick one before reporting target progress. |

### System constraints (unchanged)
- Transport booking lives in a **separate system** from clinical scheduling; sync lag up to 30 minutes.
- Phone number field is **free-text and not validated** at entry — confirmed root cause of the invalid-number ceiling.
- No native hook for T-2h automated messaging; requires middleware.
- Same-day re-booking is manual.  
  _Source: [Scheduling System Constraints](https://davita-demo.atlassian.net/wiki/spaces/~71202087d07093cbdf419895df9183abeeea5f/pages/622613)_

### Rideshare fallback (evaluated, not implemented)
- Two rideshare APIs evaluated for same-day gap coverage.
- Coverage good in metro-adjacent regions, thin in rural sites (>25 min ETA).
- Wheelchair-accessible vehicle availability is the binding constraint; both vendors under-supply it.
- Cost per completed trip competitive vs. NEMT for short urban trips only.
- Read: "Useful as a fallback for ambulatory patients in denser regions; not a primary channel and not a fix for the accessibility segment."  
  _Source: [Rideshare Fallback — Vendor Evaluation](https://davita-demo.atlassian.net/wiki/spaces/~71202087d07093cbdf419895df9183abeeea5f/pages/786433)_

---

## 3. WHAT'S CONTESTED

### 3.1 The Active Epic contradicts its own closed spike and pilot results
- **BP2-1 (Epic, To Do)** assumes: "SMS-only is sufficient and ~95% valid mobile coverage" and claims "25–30% relative reduction in no-show rate from SMS alone."  
  _Source: [EPIC BRIEF — Automated SMS Reminder Rollout (active)](https://davita-demo.atlassian.net/wiki/spaces/~71202087d07093cbdf419895df9183abeeea5f/pages/851969)_
- **BP2-2 (Spike, Done, Won't Do)** explicitly concluded: SMS-only cannot hit the 30% target. Pilot A showed ~6% relative reduction (not significant), capped by ~22% invalid/landline numbers. It recommended: "Do NOT pursue SMS-only. Adopt a hybrid."  
  _Sources: [BP2-2](https://davita-demo.atlassian.net/browse/BP2-2)_ and [Spike Write-up](https://davita-demo.atlassian.net/wiki/spaces/~71202087d07093cbdf419895df9183abeeea5f/pages/884737)_
- **The Epic Brief itself notes the conflict:** "NOTE FOR REVIEWERS: this epic's core assumption conflicts with Pilot A results and the closed spike BP2 below. Reconcile before build."  
  _Source: [EPIC BRIEF](https://davita-demo.atlassian.net/wiki/spaces/~71202087d07093cbdf419895df9183abeeea5f/pages/851969)_
- **Unresolved:** The Epic is still marked ACTIVE / committed for this quarter despite the explicit Won't Do on its core assumption.

### 3.2 Two competing no-show-rate definitions are both in active use
- **Glossary (Analytics):** `no_shows / scheduled_trips`. Same-day cancellations made 2+ hours before pickup are excluded from numerator.  
  _Source: [Glossary — Transport Metrics](https://davita-demo.atlassian.net/wiki/spaces/~71202087d07093cbdf419895df9183abeeea5f/pages/622593)_
- **Ops Dashboard v2:** `no_shows / (completed_trips + no_shows)`. Cancellations removed from denominator entirely. Any same-day cancellation (regardless of notice) is rolled into no-shows.  
  _Source: [Regional Ops Dashboard — Spec v2](https://davita-demo.atlassian.net/wiki/spaces/~71202087d07093cbdf419895df9183abeeea5f/pages/655361)_
- **Impact:** The Baseline Analysis page notes this produced two different baseline figures (18.4% vs. 24%). Managers see the Dashboard number weekly; Analytics reports against the Glossary.  
  _Source: [2024 No-Show Baseline Analysis](https://davita-demo.atlassian.net/wiki/spaces/~71202087d07093cbdf419895df9183abeeea5f/pages/688129)_
- **Status:** BP2-5 exists to reconcile them, but is unassigned and in To Do. The Stakeholders page notes: "Analytics owns the Glossary definition; the Dashboard team maintains a different one. Not yet reconciled."  
  _Sources: [BP2-5](https://davita-demo.atlassian.net/browse/BP2-5)_ and [Stakeholders & Owners](https://davita-demo.atlassian.net/wiki/spaces/~71202087d07093cbdf419895df9183abeeea5f/pages/753685)_

### 3.3 The 30% target may not be achievable with reminders alone for all patient segments
- The Prior-Art Scan states: "Transportation availability (accessible vehicles, rural ETA) is a distinct problem from reminders and needs its own track."  
  _Source: [Literature & Prior-Art Scan](https://davita-demo.atlassian.net/wiki/spaces/~71202087d07093cbdf419895df9183abeeea5f/pages/819201)_
- The Patient Segments page shows that for wheelchair-dependent patients, the barrier is accessible-vehicle supply, not reminders. For rural patients, the barrier is long ETAs / scheduling density.  
  _Source: [Patient Segments & Access Barriers](https://davita-demo.atlassian.net/wiki/spaces/~71202087d07093cbdf419895df9183abeeea5f/pages/131074)_
- **Contest:** The Program Charter scopes the problem as "missed NEMT trips" broadly, but the active Epic (BP2-1) treats it as purely a reminder problem. The pilots and segmentation data suggest a single-channel reminder approach will not serve all segments.

---

## 4. WHAT COULD NOT BE VERIFIED

1. **Pilot sample sizes and statistical methods** — The Pilot A and Pilot B pages report results but do not state sample sizes, confidence intervals, or statistical test details. The claim that Pilot B's 32% reduction was "significant" and Pilot A's 6% was "not statistically significant" cannot be independently verified.
2. **Actual phone number data quality today** — The ~22% invalid/landline figure comes from Pilot A (6 weeks, 2 clinics). Whether this rate is consistent across all regional clinics today is unknown. BP2-3 has not been started.
3. **Cost per no-show** — No source states the dollar cost of a missed transport trip or the total program budget. The Program Charter cites "inflated cost per completed visit" but gives no figure.
4. **Epic BP2-1 has no subtasks or linked issues** — Confirmed via Jira search. It is unclear how "committed for this quarter" an Epic with zero child work can be.
5. **Rideshare vendor names** — The evaluation page names "two rideshare APIs" but does not identify the vendors.
6. **Whether any middleware for T-2h messaging exists** — The Scheduling System Constraints page says it "requires middleware" but does not state whether any has been built or evaluated.
7. **Whether the Ops Dashboard v2 has been built** — The spec page exists, but there is no Jira ticket or Confluence page confirming it is in production.
