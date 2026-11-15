# Mirrors the in-game row generator and proves (by exhaustive frame-by-frame search over every
# possible tap timing) that each generated run has a survivable route, at the real progressive speed.
import sys, random, math, os
sys.path.insert(0, os.path.dirname(__file__))
from gen_params import *
T, D, CD = 0.15, 130, 0.08
MINX, MAXX = 30, 690
TIPY = 896; SPAWN_MARGIN = 100
dt = 1 / 60
def lerp(a, b, x): return a + (b - a) * x
def ease(p): return 1 - (1 - p) ** 2
def clampx(x): return max(MINX, min(MAXX, x))

def speed_at(t): return min(P["MaxSpeed"], P["BaseSpeed"] * P["SpeedGrowth"] ** (t / P["SpeedGrowthInterval"]))

class Gen:
    def __init__(self, rng):
        self.r = rng; self.safe = 3; self.next = TIPY + P["FirstRowOffset"]; self.objs = []
    def row(self, t):
        r = self.r; d = min(1, t / P["DifficultyRampTime"])
        prev = self.safe
        self.safe = max(0, min(LANE_COUNT - 2, self.safe + r.randint(-1, 1)))
        cmin, cmax = min(prev, self.safe), max(prev, self.safe) + 1
        empty = lerp(P["EmptyChanceStart"], P["EmptyChanceEnd"], d); wall = lerp(P["WallChanceStart"], P["WallChanceEnd"], d)
        dens = lerp(P["DensityStart"], P["DensityEnd"], d)
        cc = lerp(P["CrystalChanceStart"], P["CrystalChanceEnd"], d); sc = lerp(P["SolidChanceStart"], P["SolidChanceEnd"], d)
        bc = lerp(P["BreakChanceStart"], P["BreakChanceEnd"], d)
        rr = r.random(); rowtype = 0 if rr < empty else (1 if rr < empty + wall else 2)
        for lane in range(LANE_COUNT):
            if (lane - cmin) * (lane - cmax) <= 0: continue
            tr = r.random(); x = (lane + 0.5) * LANE_W + r.uniform(-P["LaneJitterX"], P["LaneJitterX"])
            wy = self.next + r.uniform(-P["RowJitterY"], P["RowJitterY"])
            typ = None
            if rowtype == 1: typ = "BarrierBreakable" if tr < P["WallBreakableShare"] else "BarrierSolid"
            elif rowtype == 2 and r.random() < dens:
                typ = "Crystal"
                if tr >= cc: typ = "BarrierSolid"
                if tr >= cc + sc: typ = "BarrierBreakable"
                if tr >= cc + sc + bc: typ = "RockSmall" if r.random() < 0.5 else "RockMedium"
            if typ:
                if typ.startswith("Barrier"): wy = self.next
                self.objs.append((typ, x, wy))
        self.next += lerp(P["RowGapStart"], P["RowGapEnd"], d)

def hit(x, wy, objs):
    for typ, ox, oy in objs:
        h = HIT[typ]
        if h[0] == "circle":
            rr = h[1] + 8.5
            if abs(oy - wy) < rr and (ox - x) ** 2 + (oy - wy) ** 2 < rr * rr: return True
        else:
            if abs(ox - x) < h[1] + 6 and abs(oy - wy) < h[2] + 6: return True
    return False

def run(seed, duration):
    g = Gen(random.Random(seed)); t = 0.0; wy = 0.0
    states = {(360.0, 0, 0, 0, 0)}
    while t < duration:
        while wy + TIPY + SPAWN_MARGIN >= g.next: g.row(t)
        t += dt; wy += speed_at(t) * dt
        near = [o for o in g.objs if abs(o[2] - wy) < 80]
        new = set()
        for (x, m, e, d, sx) in states:
            if m == 0:
                cands = [(x, 0, 0, 0, 0)] + [(clampx(x + dd * D * ease(min(1, dt / T))), 1, dt, dd, x) for dd in (-1, 1)]
            elif m == 1:
                e2 = e + dt
                cands = [(clampx(sx + d * D), 2, 0, 0, 0)] if e2 >= T - 1e-9 else [(clampx(sx + d * D * ease(e2 / T)), 1, e2, d, sx)]
            else:
                e2 = e + dt; cands = [(x, 0, 0, 0, 0)] if e2 >= CD - 1e-9 else [(x, 2, e2, 0, 0)]
            for c in cands:
                c = (round(c[0], 1),) + c[1:]
                if not hit(c[0], wy, near): new.add(c)
        states = new
        if not states: return False, t, len(g.objs)
        if len(g.objs) > 400: g.objs = [o for o in g.objs if o[2] > wy - 200]
    return True, t, len(g.objs)

if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 20; dur = float(sys.argv[2]) if len(sys.argv) > 2 else 260
    fails = 0
    for s in range(n):
        ok, t, _ = run(s, dur)
        if not ok: fails += 1; print(f"seed {s}: NO ROUTE at t={t:.1f}s speed={speed_at(t):.0f}")
    print(f"{n - fails}/{n} runs survivable for {dur:.0f}s (speed reaches {speed_at(dur):.0f} px/s)")
