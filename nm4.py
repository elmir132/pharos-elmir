"""PharOs web UI v2 on top of nm.py: summary tiles, filters, severity bars, 'ask the footage' search.
  python3 nm4.py serve 8000     (events.json comes from: python3 nm3.py scan new_york VID_ 40)
"""
import json, os, sys, urllib.parse as q
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import nm, nm2

PAGE = r"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>PharOs</title><style>
:root{--bg:#0d1320;--card:#161f33;--line:#26324d;--ink:#eaf0fb;--mute:#93a1ba;--acc:#ff7a45;--ok:#3ecf8e;--warn:#f5b84a}
@media (prefers-color-scheme:light){:root{--bg:#f3f5fa;--card:#fff;--line:#dde3ef;--ink:#142034;--mute:#5a6780}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 system-ui,-apple-system,sans-serif}
.wrap{max-width:1080px;margin:0 auto;padding:0 16px 48px}
header{padding:26px 0 8px}h1{margin:0;font-size:28px;letter-spacing:.3px}h1 b{color:var(--acc)}
.sub{color:var(--mute);margin:4px 0 14px}
.steps{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 16px}.steps span{background:var(--card);border:1px solid var(--line);border-radius:999px;padding:4px 12px;font-size:13px;color:var(--mute)}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin-bottom:16px}
.tile{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px 14px}.tile b{display:block;font-size:24px}.tile small{color:var(--mute)}
form{display:flex;gap:8px;margin-bottom:10px}input{flex:1;padding:11px 13px;border-radius:10px;border:1px solid var(--line);background:var(--card);color:var(--ink);font-size:15px}
button{padding:10px 16px;border:0;border-radius:10px;background:var(--acc);color:#fff;font-weight:700;cursor:pointer}
.chips{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 14px}.chip{background:var(--card);border:1px solid var(--line);color:var(--ink);font-weight:600;padding:6px 12px;border-radius:999px}
.chip.on{background:var(--acc);border-color:var(--acc);color:#fff}
.card{display:grid;gap:14px;background:var(--card);border:1px solid var(--line);border-radius:14px;padding:14px;margin-bottom:14px}
@media(min-width:800px){.card{grid-template-columns:400px 1fr}}
video{width:100%;border-radius:10px;background:#000;aspect-ratio:16/9}
.top{display:flex;flex-wrap:wrap;align-items:center;gap:8px}.pill{border-radius:999px;padding:2px 10px;font-size:12px;font-weight:700;background:var(--line)}
.pill.yes{background:var(--ok);color:#06231a}.pill.no{background:#5a6780;color:#fff}
.bar{height:8px;border-radius:99px;background:var(--line);overflow:hidden;margin:8px 0}.bar i{display:block;height:100%;background:linear-gradient(90deg,var(--warn),var(--acc))}
.m{display:grid;grid-template-columns:repeat(auto-fit,minmax(110px,1fr));gap:8px;margin:10px 0}.m div{background:var(--bg);border-radius:8px;padding:6px 10px}.m b{display:block;font-size:17px}.m small{color:var(--mute)}
details{color:var(--mute);font-size:13px}p.e{margin:6px 0}.note{color:var(--mute);font-size:13px;margin-top:20px}
.hit{border-top:1px solid var(--line);padding:8px 0;font-size:14px}
</style></head><body><div class="wrap">
<header><h1>Phar<b>Os</b></h1><p class="sub">Near misses in Manhattan street-camera footage, each one with the numbers behind it.</p>
<div class="steps"><span>VAST stores video</span><span>YOLO11 finds people and cars</span><span>We measure distance and speed</span><span>Cosmos describes the scene</span><span>W&amp;B writes the note</span></div></header>
<div class="tiles" id="tiles"></div>
<form id="f"><input id="q" placeholder="Ask the footage, for example: pedestrian crossing in front of a taxi"><button>Search</button></form>
<div class="chips" id="chips"></div><div id="hits"></div><div id="list"></div>
<p class="note">Distances are approximate metres from the ground point of each box, scaled by typical object height, with no camera calibration. Treat results as candidates for human review.</p>
</div><script>
const $=id=>document.getElementById(id);let ALL=[],F='all';
const fmt=v=>v===null||v===undefined?'n/a':v;
function card(e){const c=e.cosmos?`<span class="pill ${e.cosmos.verdict==='YES'?'yes':'no'}">Cosmos check: ${e.cosmos.verdict}</span>`:'';
return `<div class="card"><video controls preload="metadata" src="/clip?src=${encodeURIComponent(e.source)}#t=${Math.max(0,e.t_in_segment-1)}"></video><div>
<div class="top"><span class="pill" style="background:var(--acc);color:#fff">severity ${e.severity}</span><b>${e.classes.join(' + ')}</b>${c}<small style="color:var(--mute)">segment ${e.segment}, ${e.t_in_segment}s</small></div>
<div class="bar"><i style="width:${Math.round(e.severity*100)}%"></i></div>
<div class="m"><div><b>${Number(e.min_dist_m).toFixed(2)} m</b><small>closest</small></div><div><b>${Number(e.peak_closing_mps).toFixed(1)} m/s</b><small>closing speed</small></div><div><b>${fmt(e.ttc_s)}${e.ttc_s!==null?' s':''}</b><small>time to collision</small></div><div><b>${fmt(e.vehicle_speed_mps)}${e.vehicle_speed_mps!==undefined?' m/s':''}</b><small>vehicle speed</small></div></div>
<p class="e">${e.explanation.text} <small style="color:var(--mute)">(${e.explanation.source})</small></p>
<details><summary>Cosmos scene caption</summary><p>${e.scene||'n/a'}</p>${e.cosmos?`<p>Cosmos check: ${e.cosmos.text}</p>`:''}</details>
<small style="color:var(--mute)">${e.video}</small></div></div>`}
function render(){const es=ALL.filter(e=>F==='all'||e.classes.includes(F));$('list').innerHTML=es.length?es.map(card).join(''):'<p>No events yet. Run the scan first.</p>'}
function tiles(){const mx=ALL.reduce((a,e)=>Math.max(a,e.severity),0),cs=ALL.filter(e=>e.cosmos&&e.cosmos.verdict==='YES').length;
$('tiles').innerHTML=`<div class="tile"><b>${ALL.length}</b><small>candidate events</small></div><div class="tile"><b>${mx.toFixed?mx.toFixed(2):mx}</b><small>highest severity</small></div><div class="tile"><b>${cs}</b><small>confirmed by Cosmos check</small></div><div class="tile"><b>5 s</b><small>clip around each event</small></div>`;
const cl=[...new Set(ALL.flatMap(e=>e.classes))];$('chips').innerHTML=['all',...cl].map(c=>`<button class="chip ${c===F?'on':''}" data-c="${c}">${c}</button>`).join('');
document.querySelectorAll('.chip').forEach(b=>b.onclick=()=>{F=b.dataset.c;tiles();render()})}
fetch('/events').then(r=>r.json()).then(d=>{ALL=d;tiles();render()});
$('f').onsubmit=async ev=>{ev.preventDefault();const t=$('q').value.trim();if(!t){$('hits').innerHTML='';return}
$('hits').innerHTML='<p>Searching the Manhattan index...</p>';const r=await (await fetch('/search?q='+encodeURIComponent(t))).json();
$('hits').innerHTML=r.length?'<h3>Matches in the footage</h3>'+r.map(h=>`<div class="hit"><video controls preload="metadata" style="max-width:380px" src="/clip?src=${encodeURIComponent(h.source)}"></video><br><b>${h.camera||''}</b> score ${h.score} <small style="color:var(--mute)">${h.caption||''}</small></div>`).join(''):'<p>No matches.</p>'};
</script></body></html>"""


def serve(port=8000):
    api = nm.API()

    class H(BaseHTTPRequestHandler):
        def do_GET(self):
            p = q.urlparse(self.path)
            try:
                if p.path == "/":
                    body, ct = PAGE.encode(), "text/html; charset=utf-8"
                elif p.path == "/events":
                    body, ct = open("events.json", "rb").read(), "application/json"
                elif p.path == "/clip":
                    src = q.parse_qs(p.query)["src"][0]
                    body = api.call("GET", "/api/v1/videos/stream?source=" + q.quote(src, safe=":/") + "&token=" + api.t, raw=True)
                    ct = "video/mp4"
                elif p.path == "/search":
                    text = q.parse_qs(p.query)["q"][0]
                    r = api.call("POST", "/api/v1/search", {"query": text, "top_k": 6, "min_similarity": 0.25, "llm_top_n": 1, "metadata_filters": {"location": "new_york"}})
                    hits = [{"source": x["source"], "score": round(x.get("similarity_score", 0), 2), "camera": x.get("camera_id"), "caption": (x.get("reasoning_content") or "")[:160]} for x in r.get("results", [])]
                    body, ct = json.dumps(hits).encode(), "application/json"
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
    serve(*(int(x) for x in sys.argv[2:3]))
