"""How often are the detector's flags right? Reads the CSV files exported from the Review queue.

  python eval_labels.py pharos_labels_A.csv [pharos_labels_B.csv]

One file: precision among the clips you marked real or false, with a 95 percent Wilson interval.
Two files (two reviewers): also agreement and Cohen's kappa, and precision on the clips both agreed on.
Precision here describes only the reviewed sample (spread across the severity ranking), not every flag the
detector would raise, and says nothing about events the detector missed."""
import csv
import math
import sys
from collections import Counter

LABELS = ("real", "false", "uncertain")


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def load(path):
    with open(path, newline="", encoding="utf-8") as fh:
        return {r["id"]: r["label"] for r in csv.DictReader(fh) if r.get("label") in LABELS}


def kappa(a, b):
    ids = sorted(set(a) & set(b))
    n = len(ids)
    if n == 0:
        return 0.0, 0.0
    agree = sum(a[i] == b[i] for i in ids) / n
    ca, cb = Counter(a[i] for i in ids), Counter(b[i] for i in ids)
    pe = sum((ca[l] / n) * (cb[l] / n) for l in LABELS)
    return agree, (agree - pe) / (1 - pe) if pe < 1 else 1.0


def precision(labels):
    c = Counter(labels)
    decided = c["real"] + c["false"]
    lo, hi = wilson(c["real"], decided)
    return c, decided, (c["real"] / decided if decided else 0.0), lo, hi


def show(name, labels):
    c, decided, p, lo, hi = precision(labels)
    print(f"{name}: {len(labels)} reviewed: {c['real']} real, {c['false']} false, {c['uncertain']} uncertain")
    if decided:
        print(f"  precision among decided clips: {p:.0%} ({c['real']} of {decided}), 95% interval {lo:.0%} to {hi:.0%}")
        print(f"  if every unsure clip counted as not real: {c['real'] / len(labels):.0%}")
    else:
        print("  nothing decided yet")


def main(paths):
    sets = [load(p) for p in paths]
    for p, s in zip(paths, sets):
        show(p, list(s.values()))
    if len(sets) >= 2:
        agree, k = kappa(sets[0], sets[1])
        both = sorted(set(sets[0]) & set(sets[1]))
        print(f"\nBoth reviewers saw {len(both)} clips: agreement {agree:.0%}, Cohen's kappa {k:.2f}")
        same = [sets[0][i] for i in both if sets[0][i] == sets[1][i]]
        show("clips both agreed on", same)
        diff = [i for i in both if sets[0][i] != sets[1][i]]
        if diff:
            print(f"Disagreements ({len(diff)}), settle these by discussion:")
            for i in diff[:20]:
                print(" ", i, sets[0][i], "vs", sets[1][i])
    print("\nReminder: this is precision on the reviewed sample only. Do not tune thresholds on the same clips and then quote the result.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    main(sys.argv[1:])
