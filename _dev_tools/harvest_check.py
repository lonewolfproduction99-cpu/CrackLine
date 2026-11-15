# Runs the exhaustive tap-timing search on obstacle layouts harvested from the real running game.
import json, sys, bisect, os
sys.path.insert(0, os.path.dirname(__file__))
from gen_sim import hit, ease, clampx, T, D, CD, dt
from gen_params import HIT
H = json.load(open(sys.argv[1]))
for label, h in H.items():
    obs = [tuple(o) for o in h['objs'] if o[0] in HIT]
    pows = [o for o in h['objs'] if o[0].startswith('Power')]
    sp = sorted(h['speeds']); ws = [s[0] for s in sp]
    def speed(wy): i = min(len(sp) - 1, bisect.bisect(ws, wy)); return sp[i][1]
    # power-ups must not overlap any obstacle
    bad_pow = [p for p in pows if hit(p[1], p[2], obs) or any(abs(p[1]-o[1]) < 40 + 50 and abs(p[2]-o[2]) < 40 + 30 for o in obs)]
    wy = h['start_wy'] + 900   # begin above the crack's harvest start (objects below were not fully observed)
    end = h['end_wy']
    # start from every lane-ish x to be strict (player could be anywhere when harvest began)
    states = {(float(x), 0, 0, 0, 0) for x in range(30, 691, 10) if not hit(x, wy, obs)}
    start_n = len(states); frames = 0
    while wy < end and states:
        wy += speed(wy) * dt; frames += 1
        near = [o for o in obs if abs(o[2] - wy) < 80]; new = set()
        for (x, m, e, d, sx) in states:
            if m == 0: cands = [(x, 0, 0, 0, 0)] + [(clampx(x + dd * D * ease(min(1, dt / T))), 1, dt, dd, x) for dd in (-1, 1)]
            elif m == 1:
                e2 = e + dt; cands = [(clampx(sx + d * D), 2, 0, 0, 0)] if e2 >= T - 1e-9 else [(clampx(sx + d * D * ease(e2 / T)), 1, e2, d, sx)]
            else:
                e2 = e + dt; cands = [(x, 0, 0, 0, 0)] if e2 >= CD - 1e-9 else [(x, 2, e2, 0, 0)]
            for c in cands:
                c = (round(c[0], 1),) + c[1:]
                if not hit(c[0], wy, near): new.add(c)
        states = new
    print(f"[{label}] {len(obs)} obstacles over {end - h['start_wy']:.0f} px at speeds {min(s[1] for s in sp):.0f}-{max(s[1] for s in sp):.0f}: "
          f"{'SURVIVABLE route exists' if states else 'NO ROUTE at wy=%.0f' % wy}; power-ups overlapping obstacles: {len(bad_pow)}/{len(pows)}")
