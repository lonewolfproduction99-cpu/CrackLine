# Brute-force check that the chunk sequence always has a survivable route,
# using the same branch math as the GDevelop events (easeOut, clamp, cooldown, 1/60 s frames).
import sys, math
sys.path.insert(0, '/home/claude/tools')
from patterns import *
SPEED = float(sys.argv[1]) if len(sys.argv) > 1 else 180
T, D, CD = 0.18, 65, 0.08
MINX, MAXX = 30, 690
TIP_HALF_DIAG = 8.5      # 12x12 tip hitbox, conservative
TIPY = 896               # screen y of tip at 1280 height (70%)
dt = 1/60
def ease(p): return 1 - (1 - p) ** 2
def clamp(x): return max(MINX, min(MAXX, x))

def rocks_world(seq):
    out = []
    for k, c in enumerate(seq):
        bottom = TIPY + CHUNK_HEIGHT * k
        for (o, x, y) in c:
            out.append((x, bottom + (CHUNK_HEIGHT - y), HIT_RADIUS[o] + TIP_HALF_DIAG))
    return out

def hits(x, wy, rocks):
    for rx, ry, r in rocks:
        if abs(ry - wy) < r and (rx - x) ** 2 + (ry - wy) ** 2 < r * r: return True
    return False

def simulate(seq, start_xs):
    rocks = rocks_world(seq)
    end = TIPY + CHUNK_HEIGHT * len(seq)
    # state: (x, mode, elapsed, dir, startx)  mode 0 free, 1 branching, 2 cooldown
    states = {(round(x, 1), 0, 0, 0, 0) for x in start_xs}
    wy = 0.0; frames = 0
    while wy < end:
        wy += SPEED * dt; frames += 1
        new = set()
        for (x, m, e, d, sx) in states:
            cands = []
            if m == 0:
                cands.append((x, 0, 0, 0, 0))
                for dd in (-1, 1):  # tap this frame
                    e2 = dt; nx = clamp(x + dd * D * ease(min(1, e2 / T)))
                    cands.append((nx, 1, e2, dd, x))
            elif m == 1:
                e2 = e + dt
                if e2 >= T - 1e-9: cands.append((clamp(sx + d * D), 2, 0, 0, 0))
                else: cands.append((clamp(sx + d * D * ease(e2 / T)), 1, e2, d, sx))
            else:
                e2 = e + dt
                cands.append((x, 0 if e2 >= CD - 1e-9 else 2, 0 if e2 >= CD - 1e-9 else e2, 0, 0))
            for c in cands:
                c = (round(c[0], 1),) + c[1:]
                if not hits(c[0], wy, rocks): new.add(c)
        states = new
        if not states: return False, wy
    return True, wy

seq = list(range(len(CHUNKS))) + list(range(1, len(CHUNKS)))   # two full cycles, as spawned in game
ok, wy = simulate([CHUNKS[i] for i in seq], [360])
print(f"speed {SPEED}: full sequence from start x=360 survivable: {ok}  (checked up to world y {wy:.0f})")
# Fairness: each chunk + the next one must be survivable from ANY lane centre at chunk entry
bad = []
for i in range(1, len(CHUNKS)):
    j = i + 1 if i + 1 < len(CHUNKS) else 1
    for ln in range(7):
        ok2, _ = simulate([[], CHUNKS[i], CHUNKS[j]], [lane(ln)])
        if not ok2: bad.append((i, j, ln))
print("pairs not survivable from some lane:", bad if bad else "none")
