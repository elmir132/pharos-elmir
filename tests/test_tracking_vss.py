from pharos.tracking import build_tracks, iou
from pharos.vss import boxes_from_sidecar


def test_iou_basic():
    assert iou((0, 0, 10, 10), (0, 0, 10, 10)) == 1.0
    assert iou((0, 0, 10, 10), (20, 20, 30, 30)) == 0.0


def test_ids_used_when_present():
    rows = [(0.0, 7, "person", (0, 0, 10, 20)), (0.1, 7, "person", (1, 0, 11, 20)), (0.0, 9, "car", (50, 0, 90, 30))]
    tracks = build_tracks(rows)
    assert sorted(t.id for t in tracks) == [7, 9]
    assert len([t for t in tracks if t.id == 7][0].boxes) == 2


def test_iou_matching_without_ids_and_non_movers_dropped():
    rows = [(0.0, None, "person", (0, 0, 10, 20)), (0.1, None, "person", (2, 0, 12, 20)),
            (0.2, None, "person", (4, 0, 14, 20)), (0.0, None, "chair", (100, 100, 120, 120))]
    tracks = build_tracks(rows)
    assert len(tracks) == 1 and len(tracks[0].boxes) == 3


def test_sidecar_shapes():
    side = {"frames": [{"t": 1.0, "detections": [{"class": "car", "bbox": [0, 0, 5, 5], "track_id": 3}]},
                       {"time": 2.0, "objects": [{"label": "person", "box": [1, 1, 2, 2]}]}]}
    rows = boxes_from_sidecar(side, segment_start=10.0)
    assert rows[0] == (11.0, 3, "car", (0.0, 0.0, 5.0, 5.0))
    assert rows[1][2] == "person" and rows[1][1] is None
