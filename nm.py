"""PharOs near-miss agent, single file, stdlib only, for the VAST workshop VM.

  set -a; . /config/team-*.config; set +a
  python3 nm.py scan [location] [filename_filter] [max_chunks]   # writes events.json
  python3 nm.py serve [port]                                      # web page with clips
Distances are approximate metres from the ground-contact point of each box, scaled by typical object height.
"""
import json, math, os, re, sys, urllib.error, urllib.parse as q, urllib.request as u
from itertools import combinations
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

REF_H = {"person": 1.7, "bicycle": 1.7, "motorcycle": 1.5, "car": 1.5, "truck": 3.0, "bus": 3.2}
VRU, VEH = {"person", "bicycle", "motorcycle"}, {"car", "truck", "bus"}
NEAR_M, CLOSE_MPS, SEP_M = 2.0, 1.5, 0.8
MAX_CLOSE_MPS, MIN_VEH_MPS, DEPTH_LO, DEPTH_HI = 12.0, 1.5, 0.6, 1.6


def iou(a, b):
    ix = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    i = ix * iy
    ua = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - i
    return i / ua if ua > 0 else 0.0


def build_tracks(rows):
    by_t = {}
    for t, c, b in rows:
        if c in REF_H:
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
                tracks.append({"cls": c, "pts": [(t, b)]})
            else:
                tracks[best]["pts"].append((t, b))
                used.add(best)
    return [t for t in tracks if len(t["pts"]) >= 6]


def dist_m(ca, ba, cb, bb):
    ga, gb = ((ba[0] + ba[2]) / 2, ba[3]), ((bb[0] + bb[2]) / 2, bb[3])
    sa = REF_H[ca] / max(ba[3] - ba[1], 1.0)
    sb = REF_H[cb] / max(bb[3] - bb[1], 1.0)
    return math.hypot(ga[0] - gb[0], ga[1] - gb[1]) * (sa + sb) / 2


def speed(tr):
    """Median ground speed of a track in m/s (ground point, scaled by typical object height)."""
    cls, v = tr["cls"], []
    for (t0, b0), (t1, b1) in zip(tr["pts"], tr["pts"][1:]):
        dt = t1 - t0
        if dt > 0:
            s = REF_H[cls] / max(b1[3] - b1[1], 1.0)
            v.append(math.hypot((b1[0] + b1[2]) / 2 - (b0[0] + b0[2]) / 2, b1[3] - b0[3]) * s / dt)
    v.sort()
    return v[len(v) // 2] if v else 0.0


def box_at(tr, t):
    return min(tr["pts"], key=lambda p: abs(p[0] - t))[1]


def pair_event(a, b):
    """A vehicle and a pedestrian/cyclist that came close while the vehicle was moving, then moved apart.
    Requires a sustained approach and a sustained separation, a moving vehicle, a plausible closing speed
    and similar apparent depth. Returns None otherwise."""
    veh, vru = (a, b) if a["cls"] in VEH else (b, a)
    if not (veh["cls"] in VEH and vru["cls"] in VRU):
        return None
    bt = {round(t, 3): bx for t, bx in b["pts"]}
    pr = [(t, bx, bt[round(t, 3)]) for t, bx in a["pts"] if round(t, 3) in bt]
    if len(pr) < 6:
        return None
    ts = [p[0] for p in pr]
    raw = [dist_m(a["cls"], p[1], b["cls"], p[2]) for p in pr]
    d = [sum(raw[max(0, i - 1): i + 2]) / len(raw[max(0, i - 1): i + 2]) for i in range(len(raw))]
    cl = [0.0] + [(d[i - 1] - d[i]) / max(ts[i] - ts[i - 1], 1e-6) for i in range(1, len(d))]
    k = min(range(len(d)), key=lambda i: d[i])
    peak = max(cl[: k + 1])
    if d[k] > NEAR_M or peak < CLOSE_MPS or peak > MAX_CLOSE_MPS:
        return None
    if sum(1 for i in range(max(1, k - 3), k + 1) if cl[i] >= CLOSE_MPS) < 2:
        return None  # a single fast sample is noise, not an approach
    j = min(k + 2, len(d) - 1)
    if max(d[k:]) - d[k] < SEP_M or d[j] - d[k] < SEP_M / 2:
        return None  # they did not clearly move apart again
    vs = speed(veh)
    if vs < MIN_VEH_MPS:
        return None  # parked or crawling vehicle
    bv, bp = box_at(veh, ts[k]), box_at(vru, ts[k])
    ratio = (REF_H[veh["cls"]] / max(bv[3] - bv[1], 1.0)) / (REF_H[vru["cls"]] / max(bp[3] - bp[1], 1.0))
    if not DEPTH_LO <= ratio <= DEPTH_HI:
        return None  # probably at different depths, one behind the other
    kc = max(range(k + 1), key=lambda i: cl[i])
    ttc = d[kc] / cl[kc] if cl[kc] > 1e-6 else None
    sev = 0.5 * max(0, 1 - d[k] / NEAR_M) + 0.3 * min(1, peak / 6) + 0.2 * (max(0, 1 - ttc / 2) if ttc else 0)
    return {"classes": [a["cls"], b["cls"]], "t_closest": round(ts[k], 2), "t_start": round(ts[0], 2), "t_end": round(ts[-1], 2),
            "severity": round(sev, 3), "min_dist_m": round(d[k], 2), "peak_closing_mps": round(peak, 2),
            "ttc_s": None if ttc is None else round(ttc, 2), "vehicle_speed_mps": round(vs, 2)}


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


def template(e):
    ttc = "" if e["ttc_s"] is None else ", time to collision %s s" % e["ttc_s"]
    return "A %s and a %s came within about %s m at %s s into the clip (closing at %s m/s%s) and then moved apart." % (
        e["classes"][0], e["classes"][1], e["min_dist_m"], e["t_closest"], e["peak_closing_mps"], ttc)


def grounded(text, e):
    """True when every number in text is one of the measured values of event e."""
    ok = {str(v) for v in [e["min_dist_m"], e["t_closest"], e["peak_closing_mps"], e["ttc_s"], e["severity"], e.get("vehicle_speed_mps")] if v is not None}
    ok |= {x.rstrip("0").rstrip(".") for x in ok}
    return bool(text) and all(n in ok or n.rstrip("0").rstrip(".") in ok for n in re.findall(r"\d+(?:\.\d+)?", text))


def explain(e, scene):
    """W&B serverless inference; only accepted if every number in the sentence was measured."""
    base = template(e)
    key = os.environ.get("WANDB_API_KEY")
    if not key:
        return {"text": base, "source": "measured"}
    try:
        body = {"model": os.environ.get("PHAROS_MODEL", "meta-llama/Llama-3.1-8B-Instruct"), "temperature": 0, "messages": [
            {"role": "system", "content": "You write careful, factual safety notes."},
            {"role": "user", "content": "Write one short plain sentence for a safety reviewer. Use ONLY these facts and add no new numbers.\nFacts: %s\nScene: %s" % (base, scene[:300])}]}
        h = {"Content-Type": "application/json", "Authorization": "Bearer " + key}
        if os.environ.get("WANDB_TEAM") and os.environ.get("WANDB_PROJECT"):
            h["OpenAI-Project"] = os.environ["WANDB_TEAM"] + "/" + os.environ["WANDB_PROJECT"]
        r = u.Request("https://api.inference.wandb.ai/v1/chat/completions", data=json.dumps(body).encode(), headers=h)
        txt = json.loads(u.urlopen(r, timeout=40).read())["choices"][0]["message"]["content"].strip()
        if grounded(txt, e):
            return {"text": txt, "source": "W&B model, numbers checked"}
    except Exception:
        pass
    return {"text": base, "source": "measured"}


class API:
    def __init__(self):
        self.b = os.environ["INGRESS_URL"].rstrip("/")
        self.t = None
        self.t = self.call("POST", "/api/v1/auth/login", {"username": os.environ["USERNAME"], "password": os.environ["PASSWORD"]})["access_token"]

    def call(self, m, p, body=None, raw=False):
        h = {"Content-Type": "application/json"}
        if self.t:
            h["Authorization"] = "Bearer " + self.t
        r = u.Request(self.b + p, data=json.dumps(body).encode() if body else None, method=m, headers=h)
        try:
            data = u.urlopen(r, timeout=90).read()
            return data if raw else json.loads(data)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            raise


def stratified(events, n):
    """n events spread evenly across the severity ranking (so reviewers see strong and weak candidates)."""
    ev = sorted(events, key=lambda e: e["severity"], reverse=True)
    if len(ev) <= n:
        return ev
    step = len(ev) / n
    return [ev[int(i * step)] for i in range(n)]


def seg_src(prev, k):
    return re.sub(r"_segment_\d+_of_", "_segment_%03d_of_" % k, prev)


def scan(loc="new_york", flt="VID_", maxc=40):
    api = API()
    chunks, off = [], 0
    while len(chunks) < maxc and off < 2000:
        page = (api.call("GET", "/api/v1/videos/explore?scope=all&limit=48&offset=%d&location=%s" % (off, loc)) or {}).get("chunks", [])
        if not page:
            break
        chunks += [c for c in page if flt in c["filename"]]
        off += 48
    chunks = chunks[:maxc]
    print(len(chunks), "chunks", loc, flt)
    allev = []
    for c in chunks:
        prev, total = c["preview_source"], c.get("total_segments", 6)
        rows = []
        for k in range(1, total + 1):
            d = api.call("GET", "/api/v1/videos/detections?source=" + q.quote(seg_src(prev, k), safe=":/"))
            if d:
                rows += sidecar_rows(d, (k - 1) * 5.0)
        for e in find_events(build_tracks(rows))[:3]:
            k = min(total, int(e["t_closest"] // 5) + 1)
            e.update(video=c["filename"], segment=k, source=seg_src(prev, k), t_in_segment=round(e["t_closest"] - (k - 1) * 5.0, 2))
            allev.append(e)
        print(c["filename"][:34], "samples", len(rows), "events", len([x for x in allev if x["video"] == c["filename"]]))
    allev = stratified(allev, int(os.environ.get("PHAROS_SAMPLE", "40")))
    for e in allev:
        e["id"] = "%s|%d|%.1f|%s" % (e["video"], e["segment"], e["t_in_segment"], "+".join(e["classes"]))
    for e in allev:
        md = api.call("GET", "/api/v1/videos/metadata?source=" + q.quote(e["source"], safe=":/")) or {}
        e["scene"] = (md.get("reasoning") or md.get("reasoning_content") or "")[:400]
        e["explanation"] = explain(e, e["scene"])
    json.dump(allev, open("events.json", "w"), indent=1)
    print("TOP near misses (approximate metres):")
    for e in allev[:8]:
        print(e["severity"], "+".join(e["classes"]), e["video"][:26], "seg", e["segment"], "t=%.1fs" % e["t_in_segment"], "dist", e["min_dist_m"], "m closing", e["peak_closing_mps"], "m/s ttc", e["ttc_s"])


PAGE = """<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1"><title>PharOs</title>
<style>body{margin:0;background:#0e1420;color:#e8edf7;font:16px system-ui}h1{padding:16px;margin:0}.c{display:grid;gap:10px;background:#172033;margin:12px;padding:12px;border-radius:12px}@media(min-width:760px){.c{grid-template-columns:420px 1fr}}video{width:100%;border-radius:8px}.s{background:#ff7a45;border-radius:99px;padding:2px 8px;font-weight:700}small{color:#9aa7bd}</style>
<h1>PharOs: near misses in Manhattan camera footage</h1><div id=l></div><script>
fetch('/events').then(r=>r.json()).then(es=>{l.innerHTML=es.map(e=>`<div class=c><video controls preload=metadata src="/clip?src=${encodeURIComponent(e.source)}#t=${Math.max(0,e.t_in_segment-1)}"></video><div><span class=s>severity ${e.severity}</span> <b>${e.classes.join(' + ')}</b> <small>${e.video} segment ${e.segment}, ${e.t_in_segment}s</small><p>${e.explanation.text} <small>(${e.explanation.source})</small></p><small>Measured: closest ${e.min_dist_m} m, closing ${e.peak_closing_mps} m/s, time to collision ${e.ttc_s===null?'n/a':e.ttc_s+' s'}</small><p><small>Cosmos caption: ${e.scene||'n/a'}</small></p></div></div>`).join('')})
</script>"""


def serve(port=8000):
    api = API()

    class H(BaseHTTPRequestHandler):
        def do_GET(self):
            p = q.urlparse(self.path)
            if p.path == "/":
                body, ct = PAGE.encode(), "text/html"
            elif p.path == "/events":
                body, ct = open("events.json", "rb").read(), "application/json"
            elif p.path == "/clip":
                src = q.parse_qs(p.query)["src"][0]
                body = api.call("GET", "/api/v1/videos/stream?source=" + q.quote(src, safe=":/") + "&token=" + api.t, raw=True)
                ct = "video/mp4"
            else:
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header("Content-Type", ct)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *a):
            pass
    print("serving on port", port)
    ThreadingHTTPServer(("0.0.0.0", port), H).serve_forever()


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "scan"
    if cmd == "scan":
        scan(*(sys.argv[2:3] or ["new_york"]), *(sys.argv[3:4] or ["VID_"]), *(int(x) for x in sys.argv[4:5]))
    else:
        serve(*(int(x) for x in sys.argv[2:3]))
