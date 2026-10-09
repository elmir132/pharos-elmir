"""YOLO detection and tracking: video file in, tracks out."""
from __future__ import annotations

from .events import MOVERS, Box, Track


def track_video(path: str, model_name: str = "yolo11n.pt", stride: int = 3, conf: float = 0.3):
    """Return (tracks, fps). Samples every `stride`-th frame to keep it fast."""
    import cv2
    from ultralytics import YOLO

    cap = cv2.VideoCapture(path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    cap.release()

    model = YOLO(model_name)
    tracks: dict[int, Track] = {}
    results = model.track(source=path, stream=True, persist=True, conf=conf,
                          vid_stride=stride, tracker="bytetrack.yaml", verbose=False)
    for i, r in enumerate(results):
        if r.boxes is None or r.boxes.id is None:
            continue
        t = i * stride / fps
        for xyxy, tid, c in zip(r.boxes.xyxy.tolist(), r.boxes.id.int().tolist(), r.boxes.cls.int().tolist()):
            name = r.names[c]
            if name not in MOVERS:
                continue
            tr = tracks.setdefault(tid, Track(tid, name))
            tr.boxes.append(Box(t, *xyxy))
    return list(tracks.values()), fps
