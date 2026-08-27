#!/usr/bin/env python3
"""Render a student's diagnostic result JSON into a Markdown baseline report.

Usage: report.py <result.json> [--name "Student"] [--out students/<slug>/report.md]
The result JSON is the file the diagnostic's "Download results JSON" button produces.
"""
import argparse, glob, json, pathlib, statistics, datetime

ROOT = pathlib.Path(__file__).parent
LEVEL = {1: "Everyday literacy", 2: "SIE level", 3: "Series 7 core", 4: "Series 7 hard", 5: "Expert / trap"}
DOMAIN = {"foundations": "Foundations & economics", "equity": "Equity & analysis", "debt": "Debt securities",
          "municipal": "Municipal securities", "options": "Options", "packaged": "Funds, annuities, retirement, tax",
          "accounts": "Accounts, suitability, margin", "regulation": "Laws, underwriting, trading"}


def load_bank():
    return {i["id"]: i for f in glob.glob(str(ROOT / "items" / "*.json")) for i in json.load(open(f))}


def item_block(it, r):
    verdict = "correct" if r["correct"] else ("didn't know" if r["idk"] else "incorrect")
    chose = "" if r["correct"] or r["idk"] else f"\n  - Chose: {it['options'][r['answer']]}"
    return (f"- **{it['id']}** · {DOMAIN[it['domain']]} · {LEVEL[it['level']]} · {verdict} · {round(r['ms']/1000)}s\n"
            f"  - {it['stem']}\n  - Key: {it['options'][it['answer']]}{chose}\n  - Why: {it['explanation']} *({it['module']})*")


def render(res, name):
    bank = load_bank()
    rs = res["responses"]
    by_id = {r["id"]: r for r in rs}
    n, nc, nidk = len(rs), sum(r["correct"] for r in rs), sum(r["idk"] for r in rs)
    med_s = statistics.median(r["ms"] for r in rs) / 1000
    o = res["overall"]
    per_level = {L: (sum(1 for r in rs if r["level"] == L), sum(1 for r in rs if r["level"] == L and r["correct"])) for L in range(1, 6)}
    fin = datetime.datetime.fromisoformat(res["finishedAt"].replace("Z", "+00:00")).astimezone().strftime("%Y-%m-%d %H:%M")
    lines = [f"# Diagnostic baseline — {name}", "",
             f"Taken {fin} · {n} questions in {res['elapsedMs']/60000:.0f} min (median {med_s:.0f} s/item) · stopped: {res['stopReason']} · build {res['build']}", "",
             f"## Overall: **{o['band']}** (θ {o['theta']:+.2f} ± {o['se']:.2f})", "",
             f"- {nc}/{n} correct, {nidk} “I don't know”.",
             f"- Estimated chance of answering a typical Series 7 core question: **{o['pCoreCorrect']}%**.",
             "- By level: " + ", ".join(f"L{L} {LEVEL[L]} {c}/{t}" for L, (t, c) in per_level.items() if t), "",
             "## By domain", "", "| Domain | θ ± SE | Level | ✓/✗/? | Start at |", "|---|---|---|---|---|"]
    for d in res["domains"]:
        lines.append(f"| {DOMAIN[d['domain']]} | {d['theta']:+.2f} ± {d['se']:.2f} | {LEVEL[d['level']]} | {d['correct']}/{d['wrong']}/{d['idk']} | {d['startAt']} |")
    lines += ["", f"## Confident-but-wrong at or below level ({len(res['misconceptions'])})", ""]
    lines += [item_block(bank[i], by_id[i]) for i in res["misconceptions"]] or ["- none"]
    lines += ["", f"## “I don't know” at level ({len(res['unknownsAtLevel'])})", ""]
    lines += [item_block(bank[i], by_id[i]) for i in res["unknownsAtLevel"]] or ["- none"]
    lines += ["", "## Every question, in order", ""]
    lines += [f"{k+1}. {DOMAIN[r['domain']]} · L{r['level']} · {'✓' if r['correct'] else ('?' if r['idk'] else '✗')} · {round(r['ms']/1000)}s · θ→{r['thetaAfter']:+.2f} · `{r['id']}` {bank[r['id']]['topic']}" for k, r in enumerate(rs)]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("result"); ap.add_argument("--name"); ap.add_argument("--out")
    a = ap.parse_args()
    res = json.load(open(a.result))
    name = a.name or res.get("name") or "student"
    md = render(res, name)
    if a.out:
        p = pathlib.Path(a.out); p.parent.mkdir(parents=True, exist_ok=True); p.write_text(md); print(f"wrote {p}")
    else:
        print(md)
