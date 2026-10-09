# PharOS

A lighthouse for city intersections. PharOS shows where people get hurt in Manhattan, lets you open the live camera at each intersection, and finds candidate near misses in street footage, with the measurements behind each one.

Built at the Real-Time Video Agents Hack (VAST Data, NVIDIA, CoreWeave, Weights & Biases, Cursor), NYC, Oct 9 2026. Design and the meaning of the name: [`design/README.md`](design/README.md). Research and data sources: [`design/RESEARCH.md`](design/RESEARCH.md).

## Where we are

| Part | Status |
|------|--------|
| 3D Manhattan map, crash heatmap, 377 camera nodes, per-intersection panel, causes, suggested fixes, walkthrough (`web/pharos/`) | Working, public data only |
| Candidate near misses from VAST street footage: tracking, distance, closing speed, time to collision (`nm*.py`, `pharos/`) | Working on the workshop VM, accuracy not measured |
| W&B inference sentences with a check that every number was measured | Working on the VM |
| Cosmos scene captions on each candidate | Working (comes from the VAST index) |
| Cosmos YES/NO check of each candidate (`nm3.py verify`) | Blocked: the GPU endpoint URL is not in the team config |
| Trajectory projection to future crosswalk conflicts | Designed, not built |
| Live detection on NYC DOT cameras | Not possible: they serve still images, not video |
| Merge with the other team members' version | Not done |

## Run the map (any laptop with a GPU)

    cd web/pharos
    python3 -m http.server 8099
    open http://127.0.0.1:8099

Open it in a normal, visible browser tab (a background tab never finishes drawing the WebGL map). It reads NYC Open Data collisions live; the camera list is `web/pharos/data/cameras.json` because the camera API does not allow browser requests. The collision file currently ends on 2026-06-11.

## Run the near-miss scan (workshop VM only)

The VAST, Cosmos, YOLO and W&B services are reachable only from the VM. See [`VM_RUNBOOK.md`](VM_RUNBOOK.md). In short, in the VM terminal:

    set -a; . /config/team-*.config; set +a
    python3 nm3.py scan new_york VID_ 40     # writes events.json (stationary street cameras)
    python3 nm5.py 8000                      # serves the map app plus clips and search

The VM browser has no WebGL, so the 3D map does not draw there; the panels and clips do.

## Code map

- `web/pharos/index.html` the whole map app (MapLibre, OpenFreeMap buildings)
- `nm.py` ground-point distance, tracking, event scoring, VSS client, W&B sentence check
- `nm2.py` filters: vehicle must be moving, objects at similar depth, plausible speed
- `nm3.py` scan and the Cosmos check; `nm5.py` server for the VM
- `pharos/` the same logic split into modules with 13 tests (`python -m pytest -q`)
- `design/` brand, logo, research

## Limits

- Distances are approximate metres from the ground point of each box scaled by typical object height. No camera calibration.
- Thresholds were tuned on synthetic tracks and checked by eye on a handful of clips. Some candidates are false (for example a person in the foreground while a car passes behind).
- Cause is the first factor on the police report; about half are unspecified.
- Never commit keys. Credentials are read from the VM environment only.
