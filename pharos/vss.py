"""Client for the VAST Builders Challenge backend (runs on the workshop VM).

All settings come from environment variables that are already set on the VM
(INGRESS_URL, USERNAME, PASSWORD, YOLO_URL). Nothing is read from or written to files here,
and credentials are never printed.

Endpoints follow the organizers' guide (github.com/vast-data/vast-builders-challenge, .cursor/skills).
They have NOT been exercised from this laptop: the backend is only reachable from the VM.
"""
from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request


class VSS:
    def __init__(self, backend: str | None = None, username: str | None = None, password: str | None = None):
        self.backend = (backend or os.environ["INGRESS_URL"]).rstrip("/")
        self._user = username or os.environ["USERNAME"]
        self._pw = password or os.environ["PASSWORD"]
        self._token: str | None = None

    # -- plumbing -----------------------------------------------------------------
    def _req(self, method: str, path: str, body: dict | None = None, auth: bool = True, timeout: int = 120):
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(self.backend + path, data=data, method=method)
        req.add_header("Content-Type", "application/json")
        if auth:
            req.add_header("Authorization", f"Bearer {self.token}")
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())

    @property
    def token(self) -> str:
        if not self._token:
            r = self._req("POST", "/api/v1/auth/login", {"username": self._user, "password": self._pw}, auth=False)
            self._token = r["access_token"]
        return self._token

    # -- retrieval ----------------------------------------------------------------
    def explore(self, limit: int = 48, offset: int = 0) -> dict:
        return self._req("GET", f"/api/v1/videos/explore?scope=all&limit={limit}&offset={offset}")

    def search(self, query: str, top_k: int = 15, min_similarity: float = 0.3, **filters) -> dict:
        body = {"query": query, "top_k": top_k, "min_similarity": min_similarity, "llm_top_n": 3, **filters}
        return self._req("POST", "/api/v1/search", body)

    def detections(self, source: str) -> dict | None:
        """YOLO bbox sidecar for one segment; None when the segment has no sidecar (HTTP 404)."""
        try:
            return self._req("GET", "/api/v1/videos/detections?source=" + urllib.parse.quote(source, safe=":/"))
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            raise

    def synthesize(self, original_video: str, question: str, max_segments: int = 40) -> dict:
        return self._req("POST", "/api/v1/videos/synthesize",
                         {"original_video": original_video, "question": question, "max_segments": max_segments})

    def playback_url(self, source: str) -> str:
        q = urllib.parse.urlencode({"source": source, "token": self.token})
        return f"{self.backend}/api/v1/videos/stream?{q}"


def boxes_from_sidecar(sidecar: dict, segment_start: float = 0.0) -> list[tuple[float, int | None, str, tuple]]:
    """Best-effort reader for the YOLO sidecar: list of (t, track_id, class, (x1, y1, x2, y2)).

    The exact sidecar layout is not documented in the guide, so this accepts the common shapes:
    {"frames": [{"t" or "time" or "timestamp": s, "detections" or "objects": [{"class"/"label"/"name",
    "bbox"/"box"/"xyxy": [x1,y1,x2,y2], "track_id"/"id": n}]}]}.
    Check it against a real sidecar on the VM before trusting it.
    """
    out = []
    for fr in sidecar.get("frames", []):
        t = fr.get("t", fr.get("time", fr.get("timestamp")))
        if t is None:
            continue
        for d in fr.get("detections", fr.get("objects", [])):
            cls = d.get("class", d.get("label", d.get("name")))
            box = d.get("bbox", d.get("box", d.get("xyxy")))
            if cls is None or not box or len(box) != 4:
                continue
            out.append((float(t) + segment_start, d.get("track_id", d.get("id")), str(cls), tuple(float(v) for v in box)))
    return out
