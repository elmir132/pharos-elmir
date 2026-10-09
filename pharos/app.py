"""FastAPI app: python -m uvicorn pharos.app:app --reload"""
from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .search import Index

OUT = Path("out")
app = FastAPI(title="PharOs near-miss agent")


def _load() -> list[dict]:
    p = OUT / "events.json"
    return json.loads(p.read_text())["events"] if p.exists() else []


@app.get("/api/events")
def events():
    return _load()


@app.get("/api/search")
def search(q: str = Query(..., min_length=1), top: int = 5):
    return Index(_load()).search(q, top)


@app.get("/")
def home():
    return FileResponse("web/index.html")


if OUT.exists():
    app.mount("/out", StaticFiles(directory=OUT), name="out")
