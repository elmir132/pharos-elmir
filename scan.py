"""Self-contained near-miss scan for the VAST workshop VM (stdlib only).
Run on the VM: set -a; . /config/team-*.config; set +a; python3 scan.py [location] [max_chunks]
Reads YOLO sidecars from the VSS backend, tracks objects with IoU matching, finds close approaches.
"""
import json, os, re, sys, urllib.error, urllib.parse as q, urllib.request as u
from itertools import combinations

MOVERS = {"person", "car", "truck", "bus", "motorcycle", "bicycle"}
GAP, CLOSING, SEP = 1.0, 0.8, 0.3


def gap(a, b):
    dx = max(a[0] - b[2], b[0] - a[2], 0.0)
    dy = max(a[1] - b[3], b[1] - a[3], 0.0)
    return (dx * dx + dy * dy) ** 0.5


def size(b):
    return max(b[2] - b[0], b[3] - b[1], 1e-6)


def iou(a, b):
    ix = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    i = ix * iy
    ua = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - i
    return i / ua if ua > 0 else 0.0


def build_tracks(rows):
    """rows: (t, label, bbox). Greedy IoU tracking. Returns [{'id','cls','pts':[(t,bbox)]}]."""
    by_t = {}
    for t, c, b in rows:
        if c in MOVERS:
            by_t.setdefault(t, []).append((c, b))
    tracks = []
    for t in sorted(by_t):
        used = set()
        for c, b in by_t[t]:
            best, bv = None, 0.25
            for i, tr in enumerate(tracks):
                lt, lb = tr["pts"][-1]
                if i in used or tr["cls"] != c or t - lt > 1.0 or t == lt:
                    continue
                v = iou(lb, b)
                if v > bv:
                    best, bv = i, v
            if best is None:
                tracks.append({"id": len(tracks) + 1, "cls": c, "pts": [(t, b)]})
            else:
                tracks[best]["pts"].append((t, b))
                used.add(best)
    return [t for t in tracks if len(t["pts"]) >= 4]


def pair_event(a, b):
    bt = {round(t, 3): bx for t, bx in b["pts"]}
    pairs = [(t, bx, bt[round(t, 3)]) for t, bx in a["pts"] if round(t, 3) in bt]
    if len(pairs) < 4:
        return None
    ts = [p[0] for p in pairs]
    gs = [gap(p[1], p[2]) / min(size(p[1]), size(p[2])) for p in pairs]
    cl = [0.0] + [(gs[i - 1] - gs[i]) / max(ts[i] - ts[i - 1], 1e-6) for i in range(1, len(gs))]
    k = min(range(len(gs)), key=lambda i: gs[i])
    if gs[k] > GAP or max(cl[: k + 1]) < CLOSING or max(gs[k:]) - gs[k] < SEP:
        return None
    kc = max(range(k + 1), key=lambda i: cl[i])
    ttc = gs[kc] / cl[kc] if cl[kc] > 1e-6 else None
    sev = 0.5 * max(0, 1 - gs[k] / GAP) + 0.3 * min(1, max(cl[: k + 1]) / 3) + 0.2 * (max(0, 1 - ttc / 2) if ttc else 0)
    return {"classes": [a["cls"], b["cls"]], "t_closest": round(ts[k], 2), "severity": round(sev, 3),
            "min_gap_body_units": round(gs[k], 2), "peak_closing_body_units_per_s": round(max(cl[: k + 1]), 2),
            "ttc_s": None if ttc is None else round(ttc, 2)}


def find_events(tracks):
    ev = [e for a, b in combinations(tracks, 2) for e in [pair_event(a, b)] if e]
    return sorted(ev, key=lambda e: e["severity"], reverse=True)


def sidecar_rows(d, offset, stride=3, minconf=0.4):
    rows = []
    for fr in d.get("frames", []):
        if fr.get("frame_index", 0) % stride:
            continue
        for x in fr.get("detections", []):
            if x.get("confidence", 1) >= minconf and x.get("bbox"):
                rows.append((offset + fr["time_sec"], x["label"], tuple(x["bbox"])))
    return rows


class API:
    def __init__(self):
        self.b = os.environ["INGRESS_URL"].rstrip("/")
        self.t = self.call("POST", "/api/v1/auth/login", {"username": os.environ["USERNAME"], "password": os.environ["PASSWORD"]})["access_token"]

    def call(self, m, p, body=None):
        h = {"Content-Type": "application/json"}
        if hasattr(self, "t"):
            h["Authorization"] = "Bearer " + self.t
        r = u.Request(self.b + p, data=json.dumps(body).encode() if body else None, method=m, headers=h)
        try:
            return json.loads(u.urlopen(r, timeout=90).read())
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            raise


def main():
    loc = sys.argv[1] if len(sys.argv) > 1 else "new_york"
    maxc = int(sys.argv[2]) if len(sys.argv) > 2 else 12
    api = API()
    chunks = api.call("GET", "/api/v1/videos/explore?scope=all&limit=48&location=" + loc)["chunks"][:maxc]
    print(f"{len(chunks)} chunks for location={loc}")
    allev = []
    for c in chunks:
        prev, total = c["preview_source"], c.get("total_segments", 6)
        rows = []
        for k in range(1, total + 1):
            src = re.sub(r"_segment_\d+_of_", f"_segment_{k:03d}_of_", prev)
            d = api.call("GET", "/api/v1/videos/detections?source=" + q.quote(src, safe=":/"))
            if d:
                rows += sidecar_rows(d, (k - 1) * 5.0)
        evs = find_events(build_tracks(rows))
        for e in evs:
            e.update(video=c["filename"], segment=int(e["t_closest"] // 5) + 1, t_in_chunk=e.pop("t_closest"))
        allev += evs
        print(c["filename"][:34], "samples", len(rows), "events", len(evs))
    allev.sort(key=lambda e: e["severity"], reverse=True)
    json.dump(allev, open("events.json", "w"), indent=1)
    print("\nTOP near misses (location=%s):" % loc)
    for e in allev[:8]:
        print(e["severity"], "+".join(e["classes"]), e["video"][:30], "t=%.1fs" % e["t_in_chunk"], "gap", e["min_gap_body_units"], "closing", e["peak_closing_body_units_per_s"], "ttc", e["ttc_s"])


if __name__ == "__main__":
    main()
