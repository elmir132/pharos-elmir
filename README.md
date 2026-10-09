# PharOS

A lighthouse for city intersections. PharOS shows where people get hurt in Manhattan, lets you open the live camera at each intersection, and finds candidate near misses in street footage, with the measurements behind each one.

Built at the Real-Time Video Agents Hack (VAST Data, NVIDIA, CoreWeave, Weights & Biases, Cursor), NYC, Oct 9 2026. Design and the meaning of the name: [`design/README.md`](design/README.md). Research and data sources: [`design/RESEARCH.md`](design/RESEARCH.md).

## Where we are

| Part | Status |
|------|--------|
| 3D Manhattan map, crash heatmap, 377 camera nodes, per-intersection panel, causes, suggested fixes, walkthrough (`web/pharos/`) | Working, public data only |
| Near-miss detector: one implementation in `nm.py` (vehicle with a pedestrian, cyclist or motorcyclist, moving vehicle, sustained approach and separation, similar depth, plausible speed), 12 tests | Working; runs on VAST footage on the workshop VM and on any local video (`local_video.py`) |
| Review tab: mark each candidate real, false or unsure, add a reason, export CSV | Built (Mac); the VM copy is older and does not have it yet |
| Source health and honest failure states: each data source can fail alone, unknown is never shown as zero, stills are labelled as stills | Built and tested by blocking the collision source |
| `eval_labels.py`: precision with a 95% interval, agreement and kappa between two reviewers | Built, tested on synthetic labels; no real labels yet |
| W&B sentences with a check that every number was measured; Cosmos scene captions | Working on the VM |
| Cosmos YES/NO check of each candidate (`nm3.py verify`) | Blocked: the GPU endpoint URL is not in the team config |
| Trajectory projection to future crosswalk conflicts | Designed, not built (needs a calibrated camera and crosswalk polygons) |
| Live detection on NYC DOT cameras | Not possible: they serve still images, not video |
| Merge with the other team members' version | Not done |

## Run the map (any laptop with a GPU)

    cd web/pharos
    python3 -m http.server 8099
    open http://127.0.0.1:8099

Open it in a normal, visible browser tab (a background tab never finishes drawing the WebGL map). It reads NYC Open Data collisions live; the camera list is `web/pharos/data/cameras.json` because the camera API does not allow browser requests. The collision file currently ends on 2026-06-11. The Review tab reads `/events` (served by `nm5.py`) or `web/pharos/data/events.json` if you export one.

## Run the near-miss scan (workshop VM only)

The VAST, Cosmos, YOLO and W&B services are reachable only from the VM. In the VM terminal:

    set -a; . /config/team-*.config; set +a
    PHAROS_SAMPLE=40 python3 nm3.py scan new_york VID_ 60   # writes events.json, 40 candidates spread across severity
    python3 nm5.py 8000                                      # serves the map app, clips, search and the review queue

`nm.py` is standard library only, so it can be pasted onto the VM. The VM browser has no WebGL, so the 3D map does not draw there; the panels, clips and the review queue do.

## Measure precision

1. Each reviewer opens the Review tab, enters their initials, marks the clips, and presses Export CSV.
2. `python eval_labels.py A.csv B.csv` prints precision among the clips marked real or false, a 95% interval, and agreement between reviewers.
3. Do not tune thresholds on the clips you then use to report precision. The result describes only the reviewed sample, not events the detector missed.

## Code map

- `web/pharos/index.html` the whole map app and review queue (MapLibre, OpenFreeMap buildings)
- `nm.py` the detector (ground-point distance, tracking, scoring, filters), VSS client, W&B sentence check, scan
- `nm3.py` Cosmos check; `nm5.py` server for the VM; `local_video.py` run the detector on a local video
- `eval_labels.py` precision and agreement from exported labels
- `tests/test_nm.py` (`python -m pytest -q`)
- `design/` brand, logo, research; `IDEA.md` one-page brief

## Limits

- Distances are approximate metres from the ground point of each box scaled by typical object height. No camera calibration.
- Thresholds were tuned on synthetic tracks and checked by eye on a handful of clips. Some candidates are false (for example a person in the foreground while a car passes behind).
- Cause is the first factor on the police report; about half are unspecified.
- Never commit keys. Credentials are read from the VM environment only.
