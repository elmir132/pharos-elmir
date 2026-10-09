# PharOs: near-miss agent for camera footage

Finds moments in camera footage where two moving objects (person, car, bicycle and so on) almost collide,
and shows the measurements behind every flag.

Pipeline: video -> YOLO tracking -> pairwise gap, closing speed and time to collision -> ranked events ->
short clip + sentence (Weights & Biases inference model, checked so it can only repeat measured numbers) ->
searchable web page.

## What is built
- `pharos/events.py` near-miss logic (6 tests)
- `pharos/detect.py` YOLO11 tracking, `pharos/clips.py` ffmpeg clips
- `pharos/llm.py` W&B serverless inference + number check, falls back to a measured sentence
- `pharos/search.py` BM25 search over events, `pharos/app.py` FastAPI + `web/index.html`

## What is NOT built yet
- NVIDIA Cosmos / VSS scene descriptions (`pharos/describe.py` is a stub until the workshop endpoint is known)
- VAST AI OS storage and vector search (BM25 is a placeholder)
- Distances are 2D image distances in body units, not real metres (no camera calibration)
- Thresholds are tuned on synthetic tracks only

## Run
    python3.12 -m venv .venv && .venv/bin/pip install ultralytics opencv-python-headless fastapi uvicorn openai pytest weave
    export WANDB_API_KEY=...        # never commit it
    .venv/bin/python -m pharos.pipeline data/video.mp4
    .venv/bin/python -m uvicorn pharos.app:app
    .venv/bin/python -m pytest -q
