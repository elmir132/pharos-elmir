"""Near-miss detection from tracked objects.

The input is a list of tracks (one per object id, with a box per sampled frame).
The output is a list of events, each with the numbers that justify it, so a flag
can always be checked against a measurement and never rests on a model's wording.

Distances are 2D image distances divided by the size of the smaller object
("body units"). Without camera calibration that is only a proxy for real distance,
and the README says so.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations

VEHICLES = {"car", "truck", "bus", "motorcycle", "bicycle"}
MOVERS = VEHICLES | {"person"}

# Thresholds (all in body units unless noted). Tuned on synthetic tracks, not on real data yet.
GAP_NEAR = 1.0          # closest approach under this counts as a near miss
CLOSING_MIN = 0.8       # body units per second the pair must have been closing at
SEPARATE_AFTER = 0.3    # the gap must grow by this much afterwards, otherwise it is a contact
MIN_OVERLAP_S = 0.5     # the two tracks must share at least this much time
TTC_CAP_S = 2.0         # time-to-collision at or above this scores zero


@dataclass
class Box:
    t: float
    x1: float
    y1: float
    x2: float
    y2: float

    @property
    def w(self) -> float:
        return max(self.x2 - self.x1, 1e-6)

    @property
    def h(self) -> float:
        return max(self.y2 - self.y1, 1e-6)

    @property
    def size(self) -> float:
        return max(self.w, self.h)


@dataclass
class Track:
    id: int
    cls: str
    boxes: list[Box] = field(default_factory=list)


@dataclass
class Event:
    pair: tuple[int, int]
    classes: tuple[str, str]
    t_start: float
    t_end: float
    t_closest: float
    severity: float
    evidence: dict
    label: str = "near_miss"


def edge_gap(a: Box, b: Box) -> float:
    """Edge-to-edge distance between two boxes in pixels, 0 when they overlap."""
    dx = max(a.x1 - b.x2, b.x1 - a.x2, 0.0)
    dy = max(a.y1 - b.y2, b.y1 - a.y2, 0.0)
    return (dx * dx + dy * dy) ** 0.5


def _common(a: Track, b: Track, tol: float = 1e-3):
    bt = {round(x.t / tol): x for x in b.boxes}
    out = []
    for x in a.boxes:
        y = bt.get(round(x.t / tol))
        if y is not None:
            out.append((x, y))
    return out


def _clip(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


def pair_event(a: Track, b: Track) -> Event | None:
    if a.cls not in MOVERS or b.cls not in MOVERS:
        return None
    pairs = _common(a, b)
    if len(pairs) < 3 or pairs[-1][0].t - pairs[0][0].t < MIN_OVERLAP_S:
        return None

    ts = [p[0].t for p in pairs]
    gaps = []
    for x, y in pairs:
        scale = min(x.size, y.size)
        gaps.append(edge_gap(x, y) / scale)

    # closing speed in body units per second, from neighbouring samples
    closing = [0.0] * len(gaps)
    for i in range(1, len(gaps)):
        dt = ts[i] - ts[i - 1]
        if dt > 0:
            closing[i] = (gaps[i - 1] - gaps[i]) / dt

    k = min(range(len(gaps)), key=lambda i: gaps[i])
    if gaps[k] > GAP_NEAR:
        return None

    peak_closing = max(closing[: k + 1], default=0.0)
    if peak_closing < CLOSING_MIN:
        return None  # walking together or standing near each other, not an approach

    after = gaps[k:]
    if not after or max(after) - gaps[k] < SEPARATE_AFTER:
        return None  # they never separated again, so it is contact or an occlusion

    # time to collision at the moment of peak closing speed
    kc = max(range(k + 1), key=lambda i: closing[i])
    ttc = gaps[kc] / closing[kc] if closing[kc] > 1e-6 else float("inf")

    closeness = _clip(1 - gaps[k] / GAP_NEAR)
    speed = _clip(peak_closing / 3.0)
    urgency = _clip(1 - ttc / TTC_CAP_S) if ttc != float("inf") else 0.0
    severity = round(0.5 * closeness + 0.3 * speed + 0.2 * urgency, 3)

    first = next((i for i in range(k, -1, -1) if gaps[i] > 2 * GAP_NEAR), 0)
    last = next((i for i in range(k, len(gaps)) if gaps[i] > 2 * GAP_NEAR), len(gaps) - 1)
    x, y = pairs[k]
    return Event(
        pair=(a.id, b.id),
        classes=(a.cls, b.cls),
        t_start=ts[first],
        t_end=ts[last],
        t_closest=ts[k],
        severity=severity,
        evidence={
            "min_gap_body_units": round(gaps[k], 3),
            "min_gap_px": round(edge_gap(x, y), 1),
            "peak_closing_body_units_per_s": round(peak_closing, 2),
            "ttc_s_at_peak_closing": None if ttc == float("inf") else round(ttc, 2),
            "samples": len(gaps),
        },
    )


def find_events(tracks: list[Track]) -> list[Event]:
    events = []
    for a, b in combinations(tracks, 2):
        ev = pair_event(a, b)
        if ev:
            events.append(ev)
    events.sort(key=lambda e: e.severity, reverse=True)
    return events
