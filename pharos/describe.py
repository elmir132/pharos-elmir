"""Scene descriptions per video chunk (NVIDIA Cosmos / Video Search and Summarization).

Not wired yet: the VSS endpoint and request format come from the workshop lab, which needs the browser.
Set PHAROS_DESCRIBER=file to read descriptions from a JSON file ({"chunks": [{"start": 0, "end": 10, "text": "..."}]})
until the real client is added.
"""
from __future__ import annotations

import json
import os


def describe_chunks(video: str) -> list[dict]:
    mode = os.environ.get("PHAROS_DESCRIBER", "none")
    if mode == "file":
        with open(os.environ["PHAROS_DESCRIPTIONS"], encoding="utf-8") as fh:
            return json.load(fh)["chunks"]
    return []


def scene_for(chunks: list[dict], t: float) -> str:
    for c in chunks:
        if c["start"] <= t <= c["end"]:
            return c["text"]
    return ""
