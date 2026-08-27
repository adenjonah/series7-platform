#!/usr/bin/env python3
"""Validate a diagnostic item file. Usage: validate.py items/<domain>.json"""
import json, sys, collections, re

REQ = {"id": str, "domain": str, "level": int, "topic": str, "module": str,
       "stem": str, "options": list, "answer": int, "explanation": str, "calc": bool, "source": str}
BANNED = re.compile(r"all of the above|none of the above|both a and b", re.I)

def main(path):
    items = json.load(open(path))
    errs = []
    if not isinstance(items, list): sys.exit("top level must be a list")
    ids = collections.Counter(i.get("id") for i in items)
    for n, it in enumerate(items):
        tag = it.get("id", f"#{n}")
        for k, t in REQ.items():
            if k not in it: errs.append(f"{tag}: missing {k}"); continue
            if not isinstance(it[k], t): errs.append(f"{tag}: {k} should be {t.__name__}")
        if not (1 <= it.get("level", 0) <= 5): errs.append(f"{tag}: level must be 1-5")
        opts = it.get("options", [])
        if len(opts) != 4: errs.append(f"{tag}: need exactly 4 options")
        if len(set(o.strip().lower() for o in opts)) != len(opts): errs.append(f"{tag}: duplicate options")
        if not (0 <= it.get("answer", -1) < 4): errs.append(f"{tag}: answer must be 0-3")
        if any(re.match(r"^\s*[A-Da-d][\.\)]\s", o) for o in opts): errs.append(f"{tag}: options must not start with letter labels")
        if any(BANNED.search(o) for o in opts): errs.append(f"{tag}: banned option wording")
        if len(it.get("stem", "")) < 25: errs.append(f"{tag}: stem too short")
        if len(it.get("explanation", "")) < 30: errs.append(f"{tag}: explanation too short")
        if ids[it.get("id")] > 1: errs.append(f"{tag}: duplicate id")
        if not re.match(r"^M\d{1,2}$", it.get("module", "")): errs.append(f"{tag}: module must look like M21")
    per_level = collections.Counter(i.get("level") for i in items)
    for L in range(1, 6):
        if per_level[L] < 5: errs.append(f"level {L}: only {per_level[L]} items (need >= 5)")
    if errs:
        print("\n".join(errs)); print(f"\nFAILED: {len(errs)} problem(s) in {len(items)} items"); sys.exit(1)
    print(f"OK: {len(items)} items, per level {dict(sorted(per_level.items()))}, answer key distribution {dict(collections.Counter(i['answer'] for i in items))}")

if __name__ == "__main__":
    main(sys.argv[1])
