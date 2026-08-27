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
