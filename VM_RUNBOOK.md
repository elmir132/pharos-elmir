# Running PharOs on the workshop VM

The VAST, Cosmos, YOLO and W&B services are only reachable from the workshop VM (browser desktop),
so this repo is written to move there. Credentials are already in the VM environment; never copy them into the repo.

## 1. Get the code onto the VM
After the repo is pushed to GitHub (Elmir decides when): in the VM terminal
    git clone <repo-url> ~/pharos && cd ~/pharos
    python3 -m venv .venv && .venv/bin/pip install fastapi uvicorn openai weave pytest
(`ultralytics` is NOT needed on the VM: YOLO runs on the shared endpoint and detections are already stored per segment.)

## 2. Check the stack (organizers' skills)
    cd ~/vast-builders-challenge && agent        # Cursor agent, then: /build-day-quickstart

## 3. Prompt to give the Cursor agent in ~/pharos
"Read pharos/vss.py, pharos/tracking.py and pharos/events.py. Using the retrieval/videos skill, list our indexed videos
with VSS.explore(), fetch each segment's YOLO sidecar with VSS.detections(source), convert it with
boxes_from_sidecar(sidecar, segment_start), build tracks with build_tracks(), run find_events(), write out/events.json
in the same shape pharos/pipeline.py writes, and cut clip URLs with VSS.playback_url(). Verify boxes_from_sidecar
against a real sidecar and fix it if the layout differs. Then run the app with uvicorn."

## 4. Sponsor tools used (be honest in the submission)
- VAST AI OS: ingestion, S3 segments, VastDB index and search (through the VSS backend)
- NVIDIA Cosmos: Cosmos Reason captions and Cosmos Embed vectors power /api/v1/search and agent-qa
- CoreWeave GPUs: serve YOLO11 and Cosmos for the pipeline
- Weights & Biases: Inference model for explanations, Weave traces (pharos/llm.py)
- Cursor: the build tool

## 5. Not verified yet
`pharos/vss.py` has never run against the real backend; the sidecar format is a guess (see boxes_from_sidecar).
