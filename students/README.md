# Students

One folder per student. Each diagnostic attempt is stored as the raw JSON the exam's **Download results JSON** button produces, plus a rendered report.

```
students/<slug>/<YYYY-MM-DD>-diagnostic.json   # raw result (complete response log)
students/<slug>/<YYYY-MM-DD>-report.md         # rendered by diagnostic/report.py
```

To add a new result:

```bash
cp ~/Downloads/series7-diagnostic-result-<date>.json students/<slug>/<date>-diagnostic.json
python3 diagnostic/report.py students/<slug>/<date>-diagnostic.json --name "<Name>" --out students/<slug>/<date>-report.md
```

Ask each student to put their name in the box on the start screen so the file is self-identifying. Results also stay in the student's browser (localStorage) until they click **Start over**.

## Study plans

After filing a result, generate a personal study plan:

```bash
python3 diagnostic/plan.py students/<slug>/<date>-diagnostic.json \
    --exam-date YYYY-MM-DD --name "<Name>" [--sie-passed] \
    [--hours-per-week N] [--notes coach-notes.md] \
    --out students/<slug>/<date>-study-plan.md
```

- Module learn/review/skip is decided per module from the student's per-domain level
  (`diagnostic/curriculum.json` — a public **index** of the 42 modules; the research prose
  stays in the private vault).
- Pass-probability math lives in `diagnostic/irt.py` (the diagnostic's 3PL model; not a
  validated predictor — the readiness gate is).
- `--sie-passed` drops the SIE sitting module (M16). `--hours-per-week` overrides the
  scheduling pace. `--notes FILE` injects a coach's-notes section.
- [`students/cohort.md`](cohort.md) — one-glance summary across all students.
