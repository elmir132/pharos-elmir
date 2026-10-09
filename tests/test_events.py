from pharos.events import Box, Track, find_events, pair_event


def track(tid, cls, pts, w=40, h=100, dt=0.1):
    """pts: list of (cx, cy) centres, one per sample."""
    return Track(tid, cls, [Box(i * dt, x - w / 2, y - h / 2, x + w / 2, y + h / 2) for i, (x, y) in enumerate(pts)])


def line(x0, y0, x1, y1, n=30):
    return [(x0 + (x1 - x0) * i / (n - 1), y0 + (y1 - y0) * i / (n - 1)) for i in range(n)]


def test_person_and_car_passing_close_is_flagged():
    person = track(1, "person", line(500, 100, 500, 500), w=40, h=100)      # walks down
    car = track(2, "car", line(100, 330, 900, 330), w=200, h=100)           # drives across
    ev = pair_event(person, car)
    assert ev is not None
    assert ev.evidence["min_gap_body_units"] <= 1.0
    assert 0 < ev.severity <= 1
    assert ev.t_start <= ev.t_closest <= ev.t_end


def test_far_apart_is_not_flagged():
    person = track(1, "person", line(100, 100, 100, 500))
    car = track(2, "car", line(900, 900, 1500, 900), w=200, h=100)
    assert pair_event(person, car) is None


def test_walking_together_is_not_flagged():
    a = track(1, "person", line(100, 300, 700, 300))
    b = track(2, "person", line(150, 300, 750, 300))   # constant small gap, never closing
    assert pair_event(a, b) is None


def test_contact_without_separating_is_not_flagged():
    a = track(1, "person", line(100, 300, 500, 300))
    b = track(2, "person", line(900, 300, 500, 300))   # they meet and stay together
    assert pair_event(a, b) is None


def test_non_movers_ignored():
    a = track(1, "person", line(100, 300, 700, 300))
    b = track(2, "chair", line(400, 100, 400, 500))
    assert pair_event(a, b) is None


def test_events_sorted_by_severity():
    person = track(1, "person", line(500, 100, 500, 500))
    car = track(2, "car", line(100, 330, 900, 330), w=200)
    far = track(3, "person", line(100, 100, 100, 500))
    events = find_events([person, car, far])
    assert events and events == sorted(events, key=lambda e: e.severity, reverse=True)
