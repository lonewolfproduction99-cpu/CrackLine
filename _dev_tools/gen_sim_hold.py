# Safety search for HOLD-TO-STEER controls: every frame the player may hold left, hold right or release.
# Lateral speed = max(HoldMinSpeed, ScrollSpeed * HoldSpeedFactor), reached with HoldAccel. Fissures still force a
# 130 px / 0.15 s jolt (input ignored meanwhile). Same generator, worms and 250 m speed steps as the game.
import os, sys, math, random
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault("SPEED_MODE", "steps")
import gen_sim3 as G
from gen_params import P
HOLD_MIN, HOLD_FACTOR, HOLD_ACCEL = float(os.environ.get("HOLD_MIN", 300)), float(os.environ.get("HOLD_FACTOR", 1.0)), float(os.environ.get("HOLD_ACCEL", 5000))
dt = G.dt; QX = 4; QV = HOLD_ACCEL * dt
def lat_speed(wy, t): return max(HOLD_MIN, G.speed_wy(wy, t) * HOLD_FACTOR)

def step(states, wy, t, objs, worms):
    vmax = lat_speed(wy, t); new = set()
    for st in states:
        if st[0] == 'J':   # fissure jolt: ('J', x, elapsed, dir, startx)
            _, x, e, d, sx = st; e2 = e + dt
            if e2 >= G.T - 1e-9: c = ('S', G.clampx(sx + d * G.D), 0.0)
            else: c = ('J', G.clampx(sx + d * G.D * G.ease(e2 / G.T)), e2, d, sx)
            cands = [c]
        else:              # steering: ('S', x, v). Velocity change modelled as instant but at 90% speed (covers the ~0.06 s ramp)
            _, x, v = st
            cands = [('S', G.clampx(x + hold * vmax * 0.9 * dt), 0.0) for hold in (-1, 0, 1)]
        for c in cands:
            cq = (c[0], round(c[1] / QX) * QX) + tuple(round(z, 3) if isinstance(z, float) else z for z in c[2:])
            if not G.hit(cq[1], wy, t, objs, worms): new.add(cq)
    return new
def jolt(states, dirs): return {('J', s[1], 0.0, d, s[1]) for s in states for d in dirs}

def run(seed, duration):
    g = G.Gen(random.Random(seed)); t = 0.0; wy = 0.0; states = {('S', 360, 0.0)}; done = set()
    while t < duration:
        while wy + G.TIPY + G.SPAWN_MARGIN >= g.next: g.row(t)
        t += dt; wy += G.speed_wy(wy, t) * dt
        near = [o for o in g.objs if abs(o[2] - wy) < 80]; nw = [w for w in g.worms if abs(w["wy"] - wy) < 60]
        states = step(states, wy, t, near, nw)
        for f in g.fissures:
            if f not in done and wy >= f - 20:
                done.add(f)
                for x0 in range(30, 691, 30):          # fair from ANY position, EITHER direction
                    for d in (-1, 1):
                        if not recover(g, {('J', x0, 0.0, d, x0)}, wy, t, f): return False, t, f"no recovery after fissure x={x0} dir={d}"
                states = jolt(states, (-1, 1))
        if not states: return False, t, "no route"
        if len(g.objs) > 400: g.objs = [o for o in g.objs if o[2] > wy - 200]
    return True, t, f"{len(g.fissures)} fissures, {len(g.worms)} worms, reached {G.speed_wy(wy, t):.0f} px/s"
def recover(g, states, wy, t, f):
    end = f + P["FissureClearance"] + 3 * P["RowGapStart"]
    while wy < end:
        while wy + G.TIPY + G.SPAWN_MARGIN >= g.next: g.row(t)
        t += dt; wy += G.speed_wy(wy, t) * dt
        near = [o for o in g.objs if abs(o[2] - wy) < 80]; nw = [w for w in g.worms if abs(w["wy"] - wy) < 60]
        states = step(states, wy, t, near, nw)
        if not states: return False
    return True
if __name__ == "__main__":
    n, dur, start = int(sys.argv[1]), float(sys.argv[2]), int(sys.argv[3]) if len(sys.argv) > 3 else 0
    ok_n = 0
    for s in range(start, start + n):
        ok, t, info = run(s, dur); ok_n += ok
        print(f"seed {s}: {'ok' if ok else 'FAIL'} at {t:.0f}s ({info})", flush=True)
    print(f"{ok_n}/{n} runs survivable (hold-to-steer: min {HOLD_MIN}, factor {HOLD_FACTOR}, accel {HOLD_ACCEL})")
