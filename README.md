# Series 7 platform

Zero-to-Series-7 learning platform, built for one learner at a time.

- **Live diagnostic:** https://adenjonah.github.io/series7-platform/ — a 30–50 minute adaptive baseline exam (200 verified items, 8 domains, 5 difficulty levels). See [`diagnostic/README.md`](diagnostic/README.md) for how it works and how to rebuild it.

Rebuild after editing any item file:

```bash
python3 diagnostic/build.py   # validates items/*.json, writes diagnostic/diagnostic.html and index.html
```
