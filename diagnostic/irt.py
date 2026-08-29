"""3PL IRT helpers shared by plan.py — mirrors the constants in app.template.html.

Pass-probability is a Monte-Carlo over a 125-item form with an assumed difficulty
mix, integrating over the learner's theta uncertainty. It is the diagnostic's own
model extrapolated to a full exam, not a validated predictor — see plan.py's caveat.
"""
import math
import random

A, C = 1.1, 0.15                 # discrimination, pseudo-guessing (IDK offered)
C_REAL = 0.25                    # the real exam has no IDK button
SCORED, PASS_RAW = 125, 90       # 72 equated ≈ 90/125 (approximation, see 01-exam-meta §2)
FORM_MIX = ((0, 0.4), (1, 0.4), (2, 0.2))   # (b, share): core / hard / trap — assumption
LEVEL_B = {1: -2, 2: -1, 3: 0, 4: 1, 5: 2}


def p3(theta, b, c=C):
    return c + (1 - c) / (1 + math.exp(-A * (theta - b)))


def expected_raw(theta, c=C_REAL):
    return sum(SCORED * share * p3(theta, b, c) for b, share in FORM_MIX)


def pass_probability(theta, se, trials=4000, seed=7, c=C_REAL):
    rng = random.Random(seed)
    counts = [round(SCORED * share) for _, share in FORM_MIX]
    counts[0] += SCORED - sum(counts)
    passes = 0
    for _ in range(trials):
        t = rng.gauss(theta, se)
        score = sum(1 for (b, _), k in zip(FORM_MIX, counts) for _ in range(k) if rng.random() < p3(t, b, c))
        passes += score >= PASS_RAW
    return passes / trials


def theta_for_raw(target_raw, c=C_REAL):
    """Smallest theta (0.05 grid) whose expected raw score reaches target_raw."""
    t = -4.0
    while t < 4.0 and expected_raw(t, c) < target_raw:
        t += 0.05
    return round(t, 2)
