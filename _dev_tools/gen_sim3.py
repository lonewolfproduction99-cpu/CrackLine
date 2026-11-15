# Generator v3 safety check: mirrors the in-game row generator incl. burrowing worms (moving) and
# fissures (forced random branch). Exhaustive tap-timing search per frame, speeds up to 520 px/s.
import sys, random, math, os
sys.path.insert(0, os.path.dirname(__file__))
from gen_params import *
T, D, CD = 0.15, 130, 0.08
MINX, MAXX = 30, 690
TIPY = 896; SPAWN_MARGIN = 100; dt = 1 / 60
MAXSPEED = float(os.environ.get("SIM_MAXSPEED", 520))
def lerp(a, b, x): return a + (b - a) * x
def ease(p): return 1 - (1 - p) ** 2
def clampx(x): return max(MINX, min(MAXX, x))
def speed_at(t): return min(MAXSPEED, P["BaseSpeed"] * P["SpeedGrowth"] ** (t / P["SpeedGrowthInterval"]))

def worm_x(w, t):
    x0, d, v, t0 = w["x0"], w["dir"], w["v"], w["t0"]
    lo, hi = P["WormMinX"], P["WormMaxX"]; span = hi - lo
    s = (x0 - lo) + d * v * max(0, t - t0)
    m = s % (2 * span)
    return lo + (m if m <= span else 2 * span - m)

class Gen:
    def __init__(self, rng):
        self.r = rng; self.safe = rng.choice([0, 1, 4, 5]); self.next = TIPY + P["FirstRowOffset"]
        self.objs = []; self.worms = []; self.fissures = []
    def row(self, t):
        r = self.r; d = min(1, t / P["DifficultyRampTime"])
        prev = self.safe
        shift = 0 if r.random() < P["CorridorStayChance"] else (1 if r.random() < 0.5 else -1)
        self.safe = max(0, min(LANE_COUNT - 2, self.safe + shift))
        cmin, cmax = min(prev, self.safe), max(prev, self.safe) + 1
        empty = lerp(P["EmptyChanceStart"], P["EmptyChanceEnd"], d); wall = lerp(P["WallChanceStart"], P["WallChanceEnd"], d)
        worm = lerp(P["WormChanceStart"], P["WormChanceEnd"], d); fis = lerp(P["FissureChanceStart"], P["FissureChanceEnd"], d)
        dens = lerp(P["DensityStart"], P["DensityEnd"], d)
        cc = lerp(P["CrystalChanceStart"], P["CrystalChanceEnd"], d); sc = lerp(P["SolidChanceStart"], P["SolidChanceEnd"], d)
        bc = lerp(P["BreakChanceStart"], P["BreakChanceEnd"], d); blk = lerp(P["BlockerChanceStart"], P["BlockerChanceEnd"], d)
        rr = r.random()
        rowtype = 0 if rr < empty else 1 if rr < empty + wall else 3 if rr < empty + wall + worm else 4 if rr < empty + wall + worm + fis else 2
        gap = lerp(P["RowGapStart"], P["RowGapEnd"], d)
        if rowtype == 3:
            self.worms.append({"x0": r.uniform(P["WormMinX"], P["WormMaxX"]), "dir": r.choice([-1, 1]),
                               "v": lerp(P["WormSpeedStart"], P["WormSpeedEnd"], d), "t0": t, "wy": self.next})
        elif rowtype == 4:
            self.fissures.append(self.next); self.next += P["FissureClearance"]; return
        crack_lane = r.randint(0, LANE_COUNT - 1)
        for lane in range(LANE_COUNT):
            if rowtype in (0, 3) or (lane - cmin) * (lane - cmax) <= 0: continue
            tr = r.random(); x = (lane + 0.5) * LANE_W + r.uniform(-P["LaneJitterX"], P["LaneJitterX"])
            wy = self.next + r.uniform(-P["RowJitterY"], P["RowJitterY"]); typ = None
            if rowtype == 1: typ = "BarrierBreakable" if tr < P["WallBreakableShare"] else "BarrierSolid"
            elif r.random() < dens:
                typ = "Crystal"
                if tr >= cc: typ = "BarrierSolid"
                if tr >= cc + sc: typ = "BarrierBreakable"
                if tr >= cc + sc + bc: typ = "RockSmall" if r.random() < 0.5 else "RockMedium"
            if typ is None and lane == crack_lane and r.random() < blk:
                typ = "Crystal" if tr < cc else ("RockSmall" if r.random() < 0.5 else "RockMedium")
            if typ:
                if typ.startswith("Barrier"): wy = self.next
                self.objs.append((typ, x, wy))
        self.next += gap

def hit_static(x, wy, objs):
    for typ, ox, oy in objs:
        h = HIT[typ]
        if h[0] == "circle":
            rr = h[1] + 8.5
            if abs(oy - wy) < rr and (ox - x) ** 2 + (oy - wy) ** 2 < rr * rr: return True
        elif abs(ox - x) < h[1] + 6 and abs(oy - wy) < h[2] + 6: return True
    return False
def hit(x, wy, t, objs, worms):
    if hit_static(x, wy, objs): return True
    hw, hh = HIT["Worm"][1] + 6, HIT["Worm"][2] + 6
    return any(abs(w["wy"] - wy) < hh and abs(worm_x(w, t) - x) < hw for w in worms)

def step(states, wy, t, objs, worms):
    new = set()
    for (x, m, e, d, sx) in states:
        if m == 0: cands = [(x, 0, 0, 0, 0)] + [(clampx(x + dd * D * ease(min(1, dt / T))), 1, dt, dd, x) for dd in (-1, 1)]
        elif m == 1:
            e2 = e + dt; cands = [(clampx(sx + d * D), 2, 0, 0, 0)] if e2 >= T - 1e-9 else [(clampx(sx + d * D * ease(e2 / T)), 1, e2, d, sx)]
        else:
            e2 = e + dt; cands = [(x, 0, 0, 0, 0)] if e2 >= CD - 1e-9 else [(x, 2, e2, 0, 0)]
        for c in cands:
            c = (round(c[0]),) + c[1:]
            if not hit(c[0], wy, t, objs, worms): new.add(c)
    return new
def forced(states, dirs):   # fissure: a new branch starts from wherever the crack is
    return {(x, 1, 0.0, dd, x) for (x, m, e, d, sx) in states for dd in dirs}

def run(seed, duration, recovery_checks=True):
    g = Gen(random.Random(seed)); t = 0.0; wy = 0.0
    states = {(360.0, 0, 0, 0, 0)}; done_f = set(); worst = None
    while t < duration:
        while wy + TIPY + SPAWN_MARGIN >= g.next: g.row(t)
        t += dt; wy += speed_at(t) * dt
        near = [o for o in g.objs if abs(o[2] - wy) < 80]; nw = [w for w in g.worms if abs(w["wy"] - wy) < 60]
        states = step(states, wy, t, near, nw)
        for f in g.fissures:
            if f not in done_f and wy >= f - 20:
                done_f.add(f)
                if recovery_checks:   # fair for ANY position and EITHER random direction
                    for x0 in range(30, 691, 30):
                        for dd in (-1, 1):
                            if not recover(g, {(float(x0), 1, 0.0, dd, float(x0))}, wy, t, f):
                                return False, t, f"no recovery after fissure from x={x0} dir={dd}"
                states = forced(states, (-1, 1))
        if not states: return False, t, "no route"
        if len(g.objs) > 400: g.objs = [o for o in g.objs if o[2] > wy - 200]
    return True, t, f"{len(g.fissures)} fissures, {len(g.worms)} worms"

def recover(g, states, wy, t, f):
    end = f + P["FissureClearance"] + 3 * P["RowGapStart"]
    while wy < end:
        while wy + TIPY + SPAWN_MARGIN >= g.next: g.row(t)
        t += dt; wy += speed_at(t) * dt
        near = [o for o in g.objs if abs(o[2] - wy) < 80]; nw = [w for w in g.worms if abs(w["wy"] - wy) < 60]
        states = step(states, wy, t, near, nw)
        if not states: return False
    return True

if __name__ == "__main__":
    n = int(sys.argv[1]); dur = float(sys.argv[2]); start = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    fails = 0; F = W = 0
    for s in range(start, start + n):
        ok, t, info = run(s, dur)
        if not ok: fails += 1; print(f"seed {s}: FAIL at t={t:.1f}s speed={speed_at(t):.0f}: {info}", flush=True)
        else: print(f"seed {s}: ok ({info})", flush=True)
    print(f"{n - fails}/{n} runs survivable for {dur:.0f}s (speed up to {speed_at(dur):.0f} px/s)")
