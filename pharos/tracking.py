"""Turn per-frame detections into tracks. Uses track ids when the detector gives them, else greedy IoU matching."""
from __future__ import annotations

from collections import defaultdict

from .events import MOVERS, Box, Track


def iou(a: tuple, b: tuple) -> float:
    ix = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = ix * iy
    ua = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / ua if ua > 0 else 0.0


def build_tracks(rows: list[tuple], min_iou: float = 0.3, max_gap_s: float = 1.0) -> list[Track]:
    """rows: (t, track_id or None, class, (x1, y1, x2, y2))."""
    rows = [r for r in rows if r[2] in MOVERS]
    by_id: dict[int, Track] = {}
    if rows and all(r[1] is not None for r in rows):
        for t, tid, cls, box in sorted(rows, key=lambda r: r[0]):
            by_id.setdefault(int(tid), Track(int(tid), cls)).boxes.append(Box(t, *box))
        return list(by_id.values())

    frames: dict[float, list[tuple]] = defaultdict(list)
    for t, _tid, cls, box in rows:
        frames[t].append((cls, box))
    tracks: list[Track] = []
    nxt = 1
    for t in sorted(frames):
        used = set()
        for cls, box in frames[t]:
            best, best_iou = None, min_iou
            for i, tr in enumerate(tracks):
                last = tr.boxes[-1]
                if i in used or tr.cls != cls or t - last.t > max_gap_s or t == last.t:
                    continue
                v = iou((last.x1, last.y1, last.x2, last.y2), box)
                if v > best_iou:
                    best, best_iou = i, v
            if best is None:
                tracks.append(Track(nxt, cls, [Box(t, *box)]))
                nxt += 1
            else:
                tracks[best].boxes.append(Box(t, *box))
                used.add(best)
    return tracks
