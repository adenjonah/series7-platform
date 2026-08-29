# Cohort overview

Generated from each student's diagnostic by `diagnostic/plan.py`. "Pass today" is the
diagnostic's own 3PL IRT model extrapolated to a 125-item form (40% core / 40% hard /
20% trap assumed, real-exam guessing c=0.25), integrated over the θ uncertainty band.
It is **not** validated against real FINRA pass/fail — the readiness gate in each plan
(three fresh mocks ≥ 80–85%, no Function < 75%) is the real test. All four have passed
the SIE, so Phase 2's SIE sitting (M16) is dropped.

| Student | Baseline band | θ ± SE | Pass today (model) | Exam date | Plan hours | Pace to finish | Reachable by date? |
|---|---|---|---|---|---|---|---|
| [Sydni](sydni/2026-08-28-study-plan.md) | Series 7 ready | +2.43 ± 0.38 | ~99% | 2026-10-20 | 86 (mostly review) | 11 h/wk | **Yes** — comfortable |
| [Jojo](jojo/2026-08-28-study-plan.md) | Series 7 core | +0.84 ± 0.38 | ~14% | 2026-09-14 | 132 | 55 h/wk | **No** — needs ~9 wk at 15 h/wk |
| [Jonah](jonah/2026-08-28-study-plan.md) | Foundations | −0.95 ± 0.38 | ~0% | 2027-02-05 *(recommended, not booked)* | 266 | 12 h/wk | **Yes** — full runway |
| [Adam](adam/2026-08-28-study-plan.md) | Pre-foundations | −1.58 ± 0.38 | ~0% | 2026-09-14 | 252 | 104 h/wk | **No** — needs ~17 wk at 15 h/wk |

## What each plan contains

Per-student `<date>-study-plan.md`: current standing + model pass-probability; the
module list with each module marked **learn / review / skip** (chosen from the student's
per-domain level via `curriculum.json`); a **fix-first** list of the exact diagnostic
misses tagged to the module that teaches each; a **triage order** (highest exam-weight
per hour, for short runways); a **week-by-week** schedule that marks where the exam date
falls; and the readiness gate.

## The two date problems

Jojo and Adam are booked for **Sept 14** (17 days out). The model says neither reaches
ready by then — Jojo would need ~55 study-hours/week, Adam ~104. Their plans still lay
out the correct sequence and a triage order for maximum coverage before the date, but the
honest call is to **push those two exam dates** (FINRA lets you reschedule > 10 business
days out for the standard fee). Sydni (Oct) and Jonah (open) are well-paced.
