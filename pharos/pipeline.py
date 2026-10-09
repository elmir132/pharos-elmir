"""python -m pharos.pipeline data/video.mp4  ->  out/events.json and out/clips/*.mp4"""
from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path

from .clips import cut_clip
from .describe import describe_chunks, scene_for
from .detect import track_video
from .events import find_events
from .llm import explain


def run(video: str, out_dir: str = "out", top: int = 15) -> list[dict]:
    out = Path(out_dir)
    (out / "clips").mkdir(parents=True, exist_ok=True)
    tracks, fps = track_video(video)
    chunks = describe_chunks(video)
    events = find_events(tracks)[:top]
    rows = []
    for i, ev in enumerate(events, 1):
        d = asdict(ev)
        d["id"] = i
        d["scene"] = scene_for(chunks, ev.t_closest)
        d["explanation"] = explain(d, d["scene"])
        d["clip"] = f"clips/event_{i}.mp4"
        cut_clip(video, ev.t_start, ev.t_end, str(out / d["clip"]))
        d["text"] = f'{" ".join(d["classes"])} near miss {d["explanation"]["text"]} {d["scene"]}'
        rows.append(d)
    (out / "events.json").write_text(json.dumps({"video": video, "fps": fps, "events": rows}, indent=2))
    return rows


if __name__ == "__main__":
    rows = run(sys.argv[1])
    print(f"{len(rows)} events written to out/events.json")
