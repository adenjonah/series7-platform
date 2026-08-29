#!/usr/bin/env python3
"""Turn a diagnostic result into a personal study plan (Markdown).

Usage: plan.py <result.json> --exam-date YYYY-MM-DD [--name X] [--sie-passed]
                [--hours-per-week N] [--notes coach-notes.md] [--out plan.md]

Module selection: per module, the learner's lowest level across the module's
domains decides learn / review / skip (curriculum.json learn_le / review_le).
Any module that teaches a flagged misconception is forced to at least review.
"""
import argparse, datetime, glob, json, pathlib
import irt

ROOT = pathlib.Path(__file__).parent
CUR = json.load(open(ROOT / "curriculum.json"))
LEVEL = {1: "Everyday literacy", 2: "SIE level", 3: "Series 7 core", 4: "Series 7 hard", 5: "Expert / trap"}
DOMAIN = {"foundations": "Foundations & economics", "equity": "Equity & analysis", "debt": "Debt securities",
          "municipal": "Municipal securities", "options": "Options", "packaged": "Funds, annuities, retirement, tax",
          "accounts": "Accounts, suitability, margin", "regulation": "Laws, underwriting, trading"}
# exam share × difficulty-from-zero, same weights the engine uses to pick domains
WEIGHT = {"options": .16, "packaged": .14, "accounts": .14, "foundations": .12, "equity": .12, "debt": .12, "municipal": .12, "regulation": .08}
MIN_MOCK_HOURS = 12          # three fresh full-length mocks + review is the floor for any runway
FEASIBLE_HPW = 25            # above this, the schedule is flagged as not achievable as listed


def load_bank():
    return {i["id"]: i for f in glob.glob(str(ROOT / "items" / "*.json")) for i in json.load(open(f))}


def select_modules(res, sie_passed, fix_modules):
    level = {d["domain"]: d["level"] for d in res["domains"]}
    out = []
    for m in CUR["modules"]:
        if m.get("sie_only") and sie_passed:
            continue
        lv = min((level[d] for d in m["domains"]), default=1)
        mode = "learn" if lv <= m["learn_le"] else ("review" if lv <= m["review_le"] else "skip")
        if mode == "skip" and m["id"] in fix_modules:
            mode = "review"
        hours = m["hours"] if mode == "learn" else (m["hours"] * CUR["review_fraction"] if mode == "review" else 0)
        out.append({**m, "mode": mode, "plan_hours": round(hours, 1), "level": lv})
    return out


def compress_mocks(mods, weeks):
    """M40 is 30 h of mocks at the design pace; on a short runway scale it to the runway but never below the floor."""
    for m in mods:
        if m["id"] == "M40":
            m["plan_hours"] = max(MIN_MOCK_HOURS, min(30, round(4 * weeks, 1)))
    return mods


def schedule(mods, hpw):
    """Lay out active modules in curriculum order at `hpw` per week (a module may span weeks).
    Never truncates to the available runway — if the plan is longer than the runway, the
    extra weeks are returned so the caller can mark them as falling after the exam."""
    active = [m for m in mods if m["mode"] != "skip"]
    weeks_out, cur, cur_h = [], [], 0.0
    for m in active:
        cur.append(m); cur_h += m["plan_hours"]
        while cur_h >= hpw:
            weeks_out.append(cur); cur_h -= hpw
            cur = [{"id": m["id"], "title": "(cont.)", "plan_hours": round(cur_h, 1), "mode": m["mode"]}] if cur_h > 0.05 else []
    if cur and cur_h > 0.05:
        weeks_out.append(cur)
    return weeks_out


def fmt_item(it, r):
    verdict = "wrong" if not r["idk"] else "didn't know"
    return f"- **{it['id']}** ({it['module']}) — {it['topic']} · {verdict}. Key: {it['options'][it['answer']]}"


def render(res, name, exam_date, sie_passed, hpw_override, notes):
    bank = load_bank(); by_id = {r["id"]: r for r in res["responses"]}
    today = datetime.date.today(); days = (exam_date - today).days; weeks = max(1, days / 7)
    fix_ids = res["misconceptions"] + res["unknownsAtLevel"]
    fix_modules = {bank[i]["module"] for i in fix_ids}
    mods = compress_mocks(select_modules(res, sie_passed, fix_modules), weeks)
    total = sum(m["plan_hours"] for m in mods)
    hpw_needed = total / weeks; hpw = hpw_override or hpw_needed
    o = res["overall"]; th, se = o["theta"], o["se"]
    p_pass = irt.pass_probability(th, se)
    th50, th90 = irt.theta_for_raw(irt.PASS_RAW), irt.theta_for_raw(irt.PASS_RAW + 12)
    L = [f"# Study plan — {name}", "",
         f"Exam: **{exam_date:%A %Y-%m-%d}** · {days} days / {weeks:.1f} weeks from {today} · baseline {res['finishedAt'][:10]} (θ {th:+.2f} ± {se:.2f}, {o['band']})", "",
         "## Where you stand", "",
         f"- Model estimate of passing **today**: **{p_pass:.0%}** (expected raw {irt.expected_raw(th):.0f}/125; pass ≈ 90). "
         f"Break-even θ ≈ {th50:+.2f}; comfortable (≈102/125) θ ≈ {th90:+.2f}. You are {th50 - th:+.2f} logits from break-even.",
         "- This is the diagnostic's own 3PL model extrapolated to a 125-item form (40% core / 40% hard / 20% trap assumed). "
         "It is not validated against real pass/fail — the readiness gate below is the real test.", "",
         "## Plan at a glance", "",
         f"- **{total:.0f} study hours** selected from the 42-module curriculum → **{hpw_needed:.1f} h/week** to finish by exam day"
         + (f" (scheduled at {hpw:.0f} h/week)" if hpw_override else "") + ".",
         "- " + ("**Not achievable as listed** at that pace — see the triage order below and do modules in that order until time runs out."
                 if hpw_needed > FEASIBLE_HPW else "Achievable at that pace."), "",
         "| Domain | Level | Start at | Weight |", "|---|---|---|---|"]
    L += [f"| {DOMAIN[d['domain']]} | {LEVEL[d['level']]} (θ {d['theta']:+.2f}) | {d['startAt']} | {WEIGHT[d['domain']]:.0%} |" for d in res["domains"]]
    if notes: L += ["", "## Coach's notes", "", notes.strip()]
    L += ["", f"## Fix first — flagged by the diagnostic ({len(fix_ids)})", "",
          "Confidently wrong or “I don't know” at your level. Each is tagged with the module that teaches it; those modules are never skipped."]
    L += [fmt_item(bank[i], by_id[i]) for i in fix_ids] or ["- none"]
    L += ["", "## Modules", "", "| Module | Do | Hours | Why |", "|---|---|---|---|"]
    for m in mods:
        why = ("teaches a flagged miss" if m["id"] in fix_modules else
               f"{'/'.join(DOMAIN[d].split(' ')[0] for d in m['domains']) or 'all'} at {LEVEL[m['level']]}" if m["domains"] else "everyone")
        L.append(f"| {m['id']} {m['title']} | {m['mode']} | {m['plan_hours'] or '—'} | {why} |")
    L += ["", "## Triage order (if time runs short)", "",
          "Highest exam weight per hour first, within the dependency order of the curriculum. Do these in order; stop when the calendar stops."]
    ranked = sorted((m for m in mods if m["mode"] != "skip" and m["domains"]),
                    key=lambda m: -max(WEIGHT[d] for d in m["domains"]) / m["plan_hours"])
    L += [f"{k+1}. {m['id']} {m['title']} ({m['plan_hours']} h)" for k, m in enumerate(ranked[:12])]
    display_hpw = hpw_override or (hpw_needed if hpw_needed <= FEASIBLE_HPW else 15.0)
    wk_list = schedule(mods, display_hpw)
    exam_week = max(1, -(-days // 7))  # ceil(days/7): the week number the exam falls in
    L += ["", f"## Week by week (at {display_hpw:.0f} h/week)", ""]
    if len(wk_list) > exam_week:
        L.append(f"*At {display_hpw:.0f} h/week this plan spans {len(wk_list)} weeks, but your exam is in week {exam_week}. "
                 f"Everything from week {exam_week + 1} on falls after exam day — you will not reach it in time at this pace. "
                 f"Work the triage order above; use this sequence for what to cover first.*\n")
    for k, wk in enumerate(wk_list):
        start = today + datetime.timedelta(days=7 * k)
        tag = "  ← **exam week**" if k + 1 == exam_week else ("  _(after exam date)_" if k + 1 > exam_week else "")
        L.append(f"**Week {k+1}** (from {start:%b %d}){tag}: " + "; ".join(f"{m['id']} {m['title']} {m['plan_hours']}h" for m in wk))
    L += ["", "## Readiness gate (from the curriculum, §6)", "",
          "- Daily 10: 5 options, 3 margin/ledger, 2 accrued-interest/settlement items, every day from now.",
          "- Weekly 40-item mixed quiz in exam proportions (F1 7% / F2 9% / F3 73% / F4 11%); misses go back into review.",
          "- Book the exam only after **three consecutive fresh full-length mocks ≥ 80–85%, no Function < 75%, options and margin ≥ 85%**.",
          "- Last 3–4 days: no new content — mocks and remediation only; three-pass pacing at ~90 s per item."]
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("result"); ap.add_argument("--exam-date", required=True); ap.add_argument("--name")
    ap.add_argument("--sie-passed", action="store_true"); ap.add_argument("--hours-per-week", type=float)
    ap.add_argument("--notes"); ap.add_argument("--out")
    a = ap.parse_args()
    res = json.load(open(a.result))
    notes = open(a.notes).read() if a.notes and pathlib.Path(a.notes).exists() else ""
    md = render(res, a.name or res.get("name") or "student", datetime.date.fromisoformat(a.exam_date), a.sie_passed, a.hours_per_week, notes)
    if a.out: pathlib.Path(a.out).write_text(md); print("wrote", a.out)
    else: print(md)
