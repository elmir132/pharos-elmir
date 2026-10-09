"""PharOS server for the VAST workshop VM: the map app plus clips, search and candidate events.
  python3 nm5.py 8000      (needs index.html next to it, events.json from nm3.py scan)
"""
import json, sys, urllib.parse as q, urllib.request as u
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import nm, nm2


def serve(port=8000):
    api = nm.API()
    cams = json.dumps([x for x in json.loads(u.urlopen("https://webcams.nyctmc.org/api/cameras", timeout=30).read()) if x.get("area") == "Manhattan"]).encode()

    class H(BaseHTTPRequestHandler):
        def do_GET(self):
            p = q.urlparse(self.path)
            try:
                if p.path in ("/", "/index.html"):
                    body, ct = open("index.html", "rb").read(), "text/html; charset=utf-8"
                elif p.path == "/data/cameras.json":
                    body, ct = cams, "application/json"
                elif p.path == "/events":
                    body, ct = open("events.json", "rb").read(), "application/json"
                elif p.path == "/clip":
                    src = q.parse_qs(p.query)["src"][0]
                    body = api.call("GET", "/api/v1/videos/stream?source=" + q.quote(src, safe=":/") + "&token=" + api.t, raw=True)
                    ct = "video/mp4"
                elif p.path == "/search":
                    text = q.parse_qs(p.query)["q"][0]
                    r = api.call("POST", "/api/v1/search", {"query": text, "top_k": 6, "min_similarity": 0.25, "llm_top_n": 1, "metadata_filters": {"location": "new_york"}})
                    body = json.dumps([{"source": x["source"], "score": round(x.get("similarity_score", 0), 2), "camera": x.get("camera_id"), "caption": (x.get("reasoning_content") or "")[:160]} for x in r.get("results", [])]).encode()
                    ct = "application/json"
                else:
                    self.send_error(404)
                    return
            except Exception as ex:
                self.send_error(500, str(ex)[:80])
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
    serve(*(int(x) for x in sys.argv[1:2]))
