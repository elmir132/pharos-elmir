"""Adds a Cosmos Reason check to each candidate event and a verdict line to the web page.
  python3 nm3.py scan | verify | serve
"""
import base64, json, os, sys, urllib.parse as q, urllib.request as u
import nm


def cosmos(api, src):
    url = os.environ["COSMOS3_REASON_URL"].rstrip("/")
    h = {"Content-Type": "application/json", "Authorization": "Bearer " + os.environ.get("GPU_BEARER_TOKEN", "")}
    model = json.loads(u.urlopen(u.Request(url + "/v1/models", headers=h), timeout=30).read())["data"][0]["id"]
    clip = api.call("GET", "/api/v1/videos/stream?source=" + q.quote(src, safe=":/") + "&token=" + api.t, raw=True)
    b64 = base64.b64encode(clip).decode()
    body = {"model": model, "max_tokens": 120, "temperature": 0, "messages": [{"role": "user", "content": [
        {"type": "text", "text": "Watch this short street clip. Does a moving vehicle come within about one metre of a pedestrian or cyclist, so that someone has to step back or brake? Start your answer with YES or NO, then give one short sentence naming what you see."},
        {"type": "video_url", "video_url": {"url": "data:video/mp4;base64," + b64}}]}]}
    r = u.Request(url + "/v1/chat/completions", data=json.dumps(body).encode(), headers=h)
    txt = json.loads(u.urlopen(r, timeout=180).read())["choices"][0]["message"]["content"].strip()
    up = txt.upper()
    return {"verdict": "YES" if up.startswith("YES") else "NO" if up.startswith("NO") else "UNSURE", "text": txt[:240]}


def verify():
    api = nm.API()
    ev = json.load(open("events.json"))
    for e in ev:
        try:
            e["cosmos"] = cosmos(api, e["source"])
        except Exception as ex:
            e["cosmos"] = {"verdict": "ERROR", "text": str(ex)[:120]}
        print(e["video"][:26], "seg", e["segment"], e["cosmos"]["verdict"], e["cosmos"]["text"][:80])
    ev.sort(key=lambda e: (e["cosmos"]["verdict"] != "YES", -e["severity"]))
    json.dump(ev, open("events.json", "w"), indent=1)


nm.PAGE = nm.PAGE.replace("<p><small>Cosmos caption", "<p><b>Cosmos Reason check: ${e.cosmos?e.cosmos.verdict:'n/a'}</b> <small>${e.cosmos?e.cosmos.text:''}</small></p><p><small>Cosmos caption")

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "scan"
    if cmd == "scan":
        nm.scan(*(sys.argv[2:3] or ["new_york"]), *(sys.argv[3:4] or ["VID_"]), *(int(x) for x in sys.argv[4:5]))
    elif cmd == "verify":
        verify()
    else:
        nm.serve(*(int(x) for x in sys.argv[2:3]))
