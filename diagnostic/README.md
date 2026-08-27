# Series 7 adaptive diagnostic

A single-file, offline, computer-adaptive baseline exam. Open `diagnostic.html` in any browser — no server, no install. It places a learner on the path from "no financial background" to "Series 7 ready" across eight domains in ~30–50 minutes and tells the curriculum (`../research/00-curriculum.md` §3) where to start.

## Files

| File | Role |
|---|---|
| `diagnostic.html` | **The deliverable.** Built artifact — engine + 200-item bank inlined. Send this file to the learner. |
| `app.template.html` | Engine source (HTML/CSS/JS, no dependencies). `__BANK__` / `__BUILD__` are replaced at build time. |
| `items/<domain>.json` | Item bank, 25 items per domain, 5 per difficulty level. Edit these, never the built file. |
| `validate.py` | Schema/shape checks for one item file (4 options, key in range, ≥5 per level, no letter labels, no "all of the above"…). |
| `build.py` | Validates every item file, inlines them, writes `diagnostic.html`. Run after any edit: `python3 build.py`. |

## Item format

```json
{"id":"opt-L4-02","domain":"options","level":4,"topic":"credit-put-spread-breakeven","module":"M21",
 "stem":"…","options":["…","…","…","…"],"answer":2,"explanation":"…","calc":true,"source":"06-options.md §3.4"}
```

`answer` is the 0-based index of the key. `module` is the curriculum module that teaches the item. Levels are defined uniformly:

| Level | Meaning | Logit difficulty *b* |
|---|---|---|
| 1 | Everyday financial literacy — answerable with no finance jargon | −2 |
| 2 | SIE level — definitions, roles, basic product features | −1 |
| 3 | Series 7 core — standard application, single-step calculation | 0 |
| 4 | Series 7 hard — multi-step calculation, two-fact scenarios, thresholds | +1 |
| 5 | Expert / trap — fine distinctions a strong candidate still misses | +2 |

Every bank was authored from the research reports and then independently **key-verified** by a second agent that solved each item blind before comparing to the key (see the verification notes in the session log). Items must not hinge on any fact flagged † in `00-curriculum.md` §7.

## How the adaptive engine works

- **Model:** 3-parameter logistic IRT, `P(correct) = c + (1−c) / (1 + e^(−a(θ−b)))` with `a = 1.1`, `c = 0.15` (pseudo-guessing is below 1/4 because "I don't know" is offered and scored as incorrect). `b` comes from the level table above.
- **Ability estimate:** EAP (expected a posteriori) on a θ grid from −4 to +4, prior N(0, 1.5²). Per-domain estimates use only that domain's items with a prior centred on the global estimate (sd 1.0), so 4–7 items per domain give a usable but wide reading.
- **Item selection:** pick the domain furthest below its target share (weights: options .16, packaged .14, accounts .14, foundations/equity/debt/municipal .12 each, regulation .08 — roughly the exam's emphasis × difficulty-from-zero), tie-breaking toward the most uncertain domain; within the domain, the unseen item with maximum Fisher information at the current domain estimate, with a small penalty for a topic already seen. The first item is always a foundations SIE-level question.
- **Stop rule:** after ≥30 items, stop when the global SE ≤ 0.38 and every domain has ≥3 items; hard caps at 45 items and 60 minutes (soft warning at 45 min).
- **No feedback during the test, no going back** — it is a measurement, not a lesson. Full review with explanations is shown at the end.
- **State** autosaves to `localStorage`, so a closed tab can resume.

Simulated respondents at true θ ∈ {−2.5 … +2.5} were recovered within ~0.5 logits in 32–39 items (one extreme case hit the 45 cap).

## What the results page gives you

- Overall band (Pre-foundations / Foundations / SIE-ready / Series 7 core / Series 7 ready), θ ± SE, and the probability of answering a typical Series 7 core item.
- Per-domain θ ± SE, level, item counts (✓/✗/?), and the **module to start at**.
- Ability trajectory chart (θ after each question with ±1 SE band).
- **Priority fixes:** items at or below the learner's level answered confidently wrong — misconceptions to clear first.
- **Gaps:** items at the learner's level answered "I don't know".
- Full review of every item with the key and explanation.
- **Download results JSON** (complete response log — feed this to the platform) and **Copy text summary**.

## Test hook

`window.__diag` exposes `start(name)`, `current()`, `answer(index, idk)`, `reset()`, `state`, `p3`, `eap` for automated runs. Example simulation: reload the page, then in the console

```js
const D = __diag; D.start('sim');
while (!D.state.finished) { const it = D.current(); D.answer(Math.random() < D.p3(0.5, {1:-2,2:-1,3:0,4:1,5:2}[it.level]) ? it.answer : (it.answer+1)%4); }
```
