# Phase 2 placeholder art: barriers, crystals (3 colours), power-ups, white UI pixel, calmer background.
import math, random, sys, os
from PIL import Image, ImageDraw, ImageFilter, ImageChops
out = sys.argv[1]; random.seed(11)
def save(img, n): img.save(os.path.join(out, n)); print(n, img.size)
SS = 4

# ---- calmer painted background (tileable 256) ----
W = 256
bg = Image.new('RGBA', (W, W))
d = ImageDraw.Draw(bg)
for y in range(W):
    t = math.sin(y / W * 2 * math.pi * 2) * 0.5 + 0.5; t2 = math.sin(y / W * 2 * math.pi * 6 + 1.3) * 0.5 + 0.5
    d.line([(0, y), (W, y)], fill=(int(176 + 28 * t + 8 * t2), int(84 + 18 * t + 5 * t2), int(44 + 10 * t), 255))
def wrapped(cx, cy, rx, ry, fill, blur=0):
    lay = Image.new('RGBA', (W, W), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
    for ox in (-W, 0, W):
        for oy in (-W, 0, W): ld.ellipse([cx - rx + ox, cy - ry + oy, cx + rx + ox, cy + ry + oy], fill=fill)
    return lay.filter(ImageFilter.GaussianBlur(blur)) if blur else lay
for _ in range(18): bg = Image.alpha_composite(bg, wrapped(random.uniform(0, W), random.uniform(0, W), random.uniform(20, 46), random.uniform(8, 16), (118, 50, 26, 60), 7))
for _ in range(10): bg = Image.alpha_composite(bg, wrapped(random.uniform(0, W), random.uniform(0, W), random.uniform(16, 34), random.uniform(6, 12), (232, 140, 80, 45), 6))
for _ in range(7):
    cx, cy, r = random.uniform(0, W), random.uniform(0, W), random.uniform(3, 5.5)
    bg = Image.alpha_composite(bg, wrapped(cx, cy, r, r * .8, (128, 66, 40, 220)))
    bg = Image.alpha_composite(bg, wrapped(cx - r * .3, cy - r * .3, r * .35, r * .3, (250, 210, 160, 150)))
for col in [(255, 200, 90), (120, 220, 255)]:
    cx, cy = random.uniform(0, W), random.uniform(0, W)
    bg = Image.alpha_composite(bg, wrapped(cx, cy, 7, 7, col + (80,), 3)); bg = Image.alpha_composite(bg, wrapped(cx, cy, 1.6, 1.6, (255, 255, 240, 255)))
save(bg.convert('RGB'), 'bg_soil.png')

# ---- barriers 112x64 ----
def barrier(solid):
    w, h = 112 * SS, 64 * SS
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); dd = ImageDraw.Draw(im)
    dd.rounded_rectangle([0, 4 * SS, w - 1, h - 1], radius=16 * SS, fill=(20, 16, 22, 255))           # outline/shadow
    base = (78, 84, 100) if solid else (92, 70, 60)
    dd.rounded_rectangle([3 * SS, 2 * SS, w - 3 * SS, h - 6 * SS], radius=14 * SS, fill=base + (255,))
    dd.rounded_rectangle([7 * SS, 5 * SS, w - 7 * SS, 22 * SS], radius=10 * SS, fill=tuple(min(255, c + 45) for c in base) + (255,))
    if solid:
        for x in (20, 56, 92):   # metal bands + rivets
            dd.rectangle([(x - 5) * SS, 2 * SS, (x + 5) * SS, (64 - 6) * SS], fill=(150, 160, 178, 255))
            dd.rectangle([(x - 5) * SS, 2 * SS, (x - 2) * SS, (64 - 6) * SS], fill=(200, 210, 225, 255))
            for y in (12, 44): dd.ellipse([(x - 3) * SS, (y - 3) * SS, (x + 3) * SS, (y + 3) * SS], fill=(60, 64, 76, 255))
    else:
        glow = Image.new('RGBA', (w, h), (0, 0, 0, 0)); gd = ImageDraw.Draw(glow)
        pts = [(14, 30), (34, 22), (50, 36), (66, 20), (82, 34), (98, 26)]
        gd.line([(x * SS, y * SS) for x, y in pts], fill=(255, 150, 40, 255), width=7 * SS)
        gd.line([(50 * SS, 36 * SS), (46 * SS, 52 * SS)], fill=(255, 150, 40, 255), width=5 * SS)
        im = Image.alpha_composite(im, glow.filter(ImageFilter.GaussianBlur(3 * SS)))
        dd = ImageDraw.Draw(im)
        dd.line([(x * SS, y * SS) for x, y in pts], fill=(40, 18, 10, 255), width=3 * SS)
        dd.line([(50 * SS, 36 * SS), (46 * SS, 52 * SS)], fill=(40, 18, 10, 255), width=2 * SS)
    return im.resize((112, 64), Image.LANCZOS)
save(barrier(True), 'barrier_solid.png'); save(barrier(False), 'barrier_breakable.png')

# ---- crystals 96x96 (purple, pink, cyan) ----
def crystal(col, seed):
    rnd = random.Random(seed); S = 96 * SS
    im = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    glow = Image.new('RGBA', (S, S), (0, 0, 0, 0)); ImageDraw.Draw(glow).ellipse([S * .12, S * .18, S * .88, S * .92], fill=col + (110,))
    im = Image.alpha_composite(im, glow.filter(ImageFilter.GaussianBlur(S * .07)))
    dd = ImageDraw.Draw(im)
    shards = [(-0.3, 0.6, 0.2), (0.3, 0.58, 0.2), (0, 0.8, 0.24), (-0.14, 0.5, 0.16), (0.16, 0.48, 0.15)]
    for ang, ln, wd in sorted(shards, key=lambda s: -s[1]):
        bx, by = S / 2 + ang * S * .25, S * .86
        tx, ty = bx + math.sin(ang * 2.2) * ln * S * .55, by - ln * S * .9
        nx, ny = math.cos(ang * 2.2) * wd * S * .5, -math.sin(ang * 2.2) * wd * S * .5 * 0
        poly = [(bx - wd * S * .5, by), (bx - wd * S * .5 + (tx - bx) * .85, by + (ty - by) * .85), (tx, ty), (bx + wd * S * .5 + (tx - bx) * .85, by + (ty - by) * .85), (bx + wd * S * .5, by)]
        dd.polygon(poly, fill=(30, 14, 40, 255))
        inner = [((px - bx) * .86 + bx, (py - by) * .9 + by - 2 * SS) for px, py in poly]
        dd.polygon(inner, fill=col + (255,))
        hl = [inner[0], inner[1], inner[2], ((inner[0][0] + inner[4][0]) / 2, inner[0][1])]
        dd.polygon(hl, fill=tuple(min(255, c + 90) for c in col) + (255,))
    return im.resize((96, 96), Image.LANCZOS)
for name, col, sd in [('crystal_purple', (170, 80, 255), 1), ('crystal_pink', (255, 90, 190), 2), ('crystal_cyan', (60, 220, 255), 3)]:
    save(crystal(col, sd), name + '.png')

# ---- power-ups 80x80 ----
def orb(col):
    S = 80 * SS; im = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    g = Image.new('RGBA', (S, S), (0, 0, 0, 0)); ImageDraw.Draw(g).ellipse([S * .05, S * .05, S * .95, S * .95], fill=col + (140,))
    im = Image.alpha_composite(im, g.filter(ImageFilter.GaussianBlur(S * .05)))
    dd = ImageDraw.Draw(im)
    dd.ellipse([S * .16, S * .16, S * .84, S * .84], fill=(255, 255, 255, 255))
    dd.ellipse([S * .2, S * .2, S * .8, S * .8], fill=col + (255,))
    dd.ellipse([S * .26, S * .22, S * .56, S * .42], fill=(255, 255, 255, 110))
    return im, dd, S
im, dd, S = orb((40, 120, 255))     # slow time: clock
dd.ellipse([S * .3, S * .3, S * .7, S * .7], outline=(255, 255, 255, 255), width=4 * SS)
dd.line([(S * .5, S * .5), (S * .5, S * .36)], fill=(255, 255, 255, 255), width=4 * SS)
dd.line([(S * .5, S * .5), (S * .61, S * .56)], fill=(255, 255, 255, 255), width=4 * SS)
save(im.resize((80, 80), Image.LANCZOS), 'powerup_slow.png')
im, dd, S = orb((255, 90, 30))      # crack strength: lightning fracture
pts = [(.56, .26), (.4, .5), (.52, .5), (.42, .76), (.64, .46), (.52, .46), (.6, .26)]
dd.polygon([(x * S, y * S) for x, y in pts], fill=(255, 245, 200, 255))
save(im.resize((80, 80), Image.LANCZOS), 'powerup_strength.png')
save(Image.new('RGBA', (8, 8), (255, 255, 255, 255)), 'ui_white.png')
