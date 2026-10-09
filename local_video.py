"""Run the near-miss detector on a local video file (any laptop; needs ultralytics and opencv).
  python local_video.py clip.mp4
Detections come from YOLO11; tracking and scoring are the same code the VM scan uses (nm.py)."""
import sys

import nm


def rows_from_video(path, model_name="yolo11n.pt", stride=3, conf=0.4):
    import cv2
    from ultralytics import YOLO

    cap = cv2.VideoCapture(path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    cap.release()
    rows = []
    for i, r in enumerate(YOLO(model_name).predict(source=path, stream=True, vid_stride=stride, conf=conf, verbose=False)):
        t = i * stride / fps
        for xyxy, c in zip(r.boxes.xyxy.tolist(), r.boxes.cls.int().tolist()):
            rows.append((t, r.names[c], tuple(xyxy)))
    return rows


if __name__ == "__main__":
    ev = nm.find_events(nm.build_tracks(rows_from_video(sys.argv[1])))
    print(len(ev), "candidate near misses")
    for e in ev[:10]:
        print(e["severity"], "+".join(e["classes"]), "t=%.1fs" % e["t_closest"], "dist", e["min_dist_m"], "m closing", e["peak_closing_mps"], "m/s ttc", e["ttc_s"])
