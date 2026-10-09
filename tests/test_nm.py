import nm


def tracks(person_pts, car_pts, car_w=250, dt=0.1):
    rows = []
    for i, ((px, py), (cx, cy)) in enumerate(zip(person_pts, car_pts)):
        rows.append((i * dt, "person", (px - 20, py - 100, px + 20, py)))
        rows.append((i * dt, "car", (cx - car_w / 2, cy - 100, cx + car_w / 2, cy)))
    return nm.build_tracks(rows)


def crossing(n=40):
    person = [(300 + i * 4, 400) for i in range(n)]       # walks right at about 0.7 m/s
    car = [(900 - i * 15, 400) for i in range(n)]         # drives left at about 2.3 m/s, passes the person
    return person, car


def test_vehicle_passing_close_to_pedestrian_is_flagged():
    ev = nm.find_events(tracks(*crossing()))
    assert len(ev) == 1
    e = ev[0]
    assert e["classes"] and set(e["classes"]) == {"person", "car"}
    assert e["min_dist_m"] <= nm.NEAR_M and e["vehicle_speed_mps"] >= nm.MIN_VEH_MPS
    assert e["t_start"] <= e["t_closest"] <= e["t_end"]


def test_parked_car_is_not_flagged():
    person = [(300 + i * 14, 400) for i in range(40)]
    car = [(600, 400)] * 40
    assert nm.find_events(tracks(person, car)) == []


def test_far_apart_is_not_flagged():
    person = [(100 + i * 3, 400) for i in range(40)]
    car = [(2000 + i * 3, 400) for i in range(40)]
    assert nm.find_events(tracks(person, car)) == []


def test_contact_without_moving_apart_is_not_flagged():
    person = [(500, 400)] * 40
    car = [(900 - i * 15, 400) if 900 - i * 15 > 520 else (520, 400) for i in range(40)]
    assert nm.find_events(tracks(person, car)) == []


def test_single_noisy_sample_is_not_an_approach():
    person, car = crossing()
    car = [(c[0], c[1]) for c in car]
    # replace the approach by a jump for one sample only
    car = [(900, 400)] * 18 + [(560, 400)] + [(900, 400)] * 21
    assert nm.find_events(tracks(person, car)) == []


def test_two_pedestrians_never_pair():
    rows = []
    for i in range(40):
        rows.append((i * 0.1, "person", (100 + i * 4, 300, 140 + i * 4, 400)))
        rows.append((i * 0.1, "person", (400 - i * 4, 300, 440 - i * 4, 400)))
    assert nm.find_events(nm.build_tracks(rows)) == []


def test_person_in_foreground_with_car_behind_is_not_flagged():
    rows = []
    for i in range(40):
        rows.append((i * 0.1, "person", (480 + i * 2, 100, 560 + i * 2, 600)))      # tall box: close to the camera
        rows.append((i * 0.1, "car", (900 - i * 15 - 60, 300, 900 - i * 15 + 60, 360)))  # small box: far away
    assert nm.find_events(nm.build_tracks(rows)) == []


def test_numbers_in_a_sentence_must_be_measured():
    e = {"classes": ["person", "car"], "t_closest": 4.5, "severity": 0.71, "min_dist_m": 0.4,
         "peak_closing_mps": 2.1, "ttc_s": 0.9, "vehicle_speed_mps": 3.0}
    assert nm.grounded(nm.template(e), e)
    assert not nm.grounded("They came within 0.1 m.", e)


def test_stratified_sample_spans_the_ranking():
    ev = [{"severity": s / 100} for s in range(100)]
    pick = nm.stratified(ev, 10)
    assert len(pick) == 10 and pick[0]["severity"] == 0.99 and pick[-1]["severity"] < 0.15


def test_sidecar_rows_keep_confident_detections_only():
    d = {"frames": [{"frame_index": 0, "time_sec": 0.0, "detections": [{"label": "car", "confidence": 0.9, "bbox": [0, 0, 5, 5]}, {"label": "person", "confidence": 0.2, "bbox": [1, 1, 2, 2]}]},
                    {"frame_index": 1, "time_sec": 0.03, "detections": [{"label": "car", "confidence": 0.9, "bbox": [0, 0, 5, 5]}]}]}
    rows = nm.sidecar_rows(d, 10.0, stride=3)
    assert rows == [(10.0, "car", (0, 0, 5, 5))]


def test_wilson_interval_and_precision():
    import eval_labels as ev
    lo, hi = ev.wilson(0, 0)
    assert (lo, hi) == (0.0, 0.0)
    lo, hi = ev.wilson(30, 40)
    assert 0.59 < lo < 0.62 and 0.85 < hi < 0.90
    c, decided, p, _, _ = ev.precision(["real"] * 6 + ["false"] * 2 + ["uncertain"])
    assert decided == 8 and abs(p - 0.75) < 1e-9


def test_kappa_perfect_and_chance():
    import eval_labels as ev
    a = {str(i): ("real" if i % 2 else "false") for i in range(10)}
    assert ev.kappa(a, dict(a)) == (1.0, 1.0)
    b = {str(i): ("false" if i % 2 else "real") for i in range(10)}
    agree, k = ev.kappa(a, b)
    assert agree == 0.0 and k < 0
