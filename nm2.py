"""Stricter filters on top of nm.py: the vehicle must really be moving, objects must be at a similar depth,
and absurd closing speeds (tracker glitches) are dropped."""
import math, sys
import nm

orig = nm.pair_event


def speed(tr, cls):
    v = []
    for (t0, b0), (t1, b1) in zip(tr["pts"], tr["pts"][1:]):
        dt = t1 - t0
        if dt > 0:
            s = nm.REF_H[cls] / max(b1[3] - b1[1], 1.0)
            v.append(math.hypot((b1[0] + b1[2]) / 2 - (b0[0] + b0[2]) / 2, b1[3] - b0[3]) * s / dt)
    v.sort()
    return v[len(v) // 2] if v else 0.0


def box_at(tr, t):
    return min(tr["pts"], key=lambda p: abs(p[0] - t))[1]


def pair_event(a, b):
    e = orig(a, b)
    if not e:
        return None
    veh, vru = (a, b) if a["cls"] in nm.VEH else (b, a)
    if speed(veh, veh["cls"]) < 1.5 or e["peak_closing_mps"] > 12:
        return None
    ba, bb = box_at(veh, e["t_closest"]), box_at(vru, e["t_closest"])
    sa, sb = nm.REF_H[veh["cls"]] / max(ba[3] - ba[1], 1.0), nm.REF_H[vru["cls"]] / max(bb[3] - bb[1], 1.0)
    if not 0.6 <= sa / sb <= 1.6:
        return None
    e["vehicle_speed_mps"] = round(speed(veh, veh["cls"]), 2)
    return e


nm.pair_event = pair_event

if __name__ == "__main__":
    sys.argv[0] = "nm2.py"
    cmd = sys.argv[1] if len(sys.argv) > 1 else "scan"
    if cmd == "scan":
        nm.scan(*(sys.argv[2:3] or ["new_york"]), *(sys.argv[3:4] or ["VID_"]), *(int(x) for x in sys.argv[4:5]))
    else:
        nm.serve(*(int(x) for x in sys.argv[2:3]))
