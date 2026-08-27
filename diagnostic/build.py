#!/usr/bin/env python3
"""Inline all items/*.json into app.template.html → diagnostic.html (single self-contained file)."""
import json, pathlib, subprocess, sys, datetime, collections

ROOT = pathlib.Path(__file__).parent
items = []
for p in sorted((ROOT / "items").glob("*.json")):
    r = subprocess.run([sys.executable, ROOT / "validate.py", p], capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"{p.name} failed validation:\n{r.stdout}")
    items += json.load(open(p))
ids = [i["id"] for i in items]
assert len(ids) == len(set(ids)), "duplicate ids across files"
by = collections.Counter((i["domain"], i["level"]) for i in items)
build = datetime.date.today().isoformat()
html = (ROOT / "app.template.html").read_text()
assert "__BANK__" in html and "__BUILD__" in html
out = html.replace("__BANK__", json.dumps(items, ensure_ascii=False)).replace("__BUILD__", json.dumps(f"{build} · {len(items)} items"))
(ROOT / "diagnostic.html").write_text(out)
(ROOT.parent / "index.html").write_text(out)   # served by GitHub Pages
doms = sorted({i["domain"] for i in items})
print(f"built diagnostic/diagnostic.html + index.html: {len(items)} items across {len(doms)} domains")
for d in doms:
    print(f"  {d:12s} " + " ".join(f"L{L}:{by[(d,L)]}" for L in range(1, 6)))
