# Generates placeholder painted-cartoon art for CRACKLINE Phase 1.
import math, random, sys, os
from PIL import Image, ImageDraw, ImageFilter, ImageChops
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
random.seed(7)

def save(img, name): img.save(os.path.join(out, name)); print(name, img.size)

# ---------- Tileable soil background 256x256 ----------
W = 256
bg = Image.new('RGBA', (W, W), (196, 98, 52, 255))
d = ImageDraw.Draw(bg)
# horizontal soft strata (tile vertically: use sin with period W)
for y in range(W):
    t = math.sin(y / W * 2 * math.pi * 2) * 0.5 + 0.5
    t2 = math.sin(y / W * 2 * math.pi * 5 + 1.3) * 0.5 + 0.5
    r = int(178 + 30 * t + 10 * t2); g = int(86 + 18 * t + 6 * t2); b = int(46 + 10 * t)
    d.line([(0, y), (W, y)], fill=(r, g, b, 255))
def wrapped_ellipse(draw_img, cx, cy, rx, ry, fill):
    layer = Image.new('RGBA', (W, W), (0, 0, 0, 0)); ld = ImageDraw.Draw(layer)
    for ox in (-W, 0, W):
        for oy in (-W, 0, W):
            ld.ellipse([cx - rx + ox, cy - ry + oy, cx + rx + ox, cy + ry + oy], fill=fill)
    return layer
# darker blotches
for _ in range(20):
    lay = wrapped_ellipse(bg, random.uniform(0, W), random.uniform(0, W), random.uniform(18, 40), random.uniform(8, 18), (120, 52, 28, 70))
    bg = Image.alpha_composite(bg, lay.filter(ImageFilter.GaussianBlur(6)))
# pebbles with highlight
for _ in range(12):
    cx, cy = random.uniform(0, W), random.uniform(0, W); r = random.uniform(2.5, 6)
    col = random.choice([(140, 70, 40), (226, 150, 90), (110, 84, 70), (240, 190, 110)])
    bg = Image.alpha_composite(bg, wrapped_ellipse(bg, cx, cy, r, r * 0.8, col + (200,)))
    bg = Image.alpha_composite(bg, wrapped_ellipse(bg, cx - r * 0.3, cy - r * 0.3, r * 0.35, r * 0.3, (255, 230, 190, 150)))
# a few tiny glowing mineral flecks
for _ in range(3):
    cx, cy = random.uniform(0, W), random.uniform(0, W)
    col = random.choice([(255, 210, 90), (120, 230, 255), (255, 120, 200)])
    glow = wrapped_ellipse(bg, cx, cy, 6, 6, col + (90,)).filter(ImageFilter.GaussianBlur(3))
    bg = Image.alpha_composite(bg, glow)
    bg = Image.alpha_composite(bg, wrapped_ellipse(bg, cx, cy, 1.8, 1.8, (255, 255, 240, 255)))
save(bg.convert('RGB'), 'bg_soil.png')

# ---------- Rocks ----------
def rock(size, base, seed):
    rnd = random.Random(seed)
    S = size * 4  # supersample
    img = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    cx = cy = S / 2; R = S * 0.44
    pts = []
    n = 11
    for i in range(n):
        a = i / n * 2 * math.pi
        rr = R * rnd.uniform(0.88, 1.0)
        pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
    mask = Image.new('L', (S, S), 0); ImageDraw.Draw(mask).polygon(pts, fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(S * 0.02)).point(lambda v: 255 if v > 128 else 0)
    # dark outline
    outline = mask.filter(ImageFilter.MaxFilter(9))
    img.paste((54, 34, 26, 255), (0, 0), outline)
    # base fill
    img.paste(base + (255,), (0, 0), mask)
    # shading: bottom-right shadow, top-left highlight
    shade = Image.new('L', (S, S), 0); sd = ImageDraw.Draw(shade)
    sd.ellipse([cx - R * 0.5, cy - R * 0.4, cx + R * 1.3, cy + R * 1.4], fill=150)
    shade = ImageChops.multiply(shade.filter(ImageFilter.GaussianBlur(S * 0.08)), mask)
    img.paste((max(base[0] - 70, 0), max(base[1] - 60, 0), max(base[2] - 50, 0), 255), (0, 0), shade)
    hl = Image.new('L', (S, S), 0); hd = ImageDraw.Draw(hl)
    hd.ellipse([cx - R * 0.75, cy - R * 0.8, cx + R * 0.05, cy - R * 0.15], fill=170)
    hl = ImageChops.multiply(hl.filter(ImageFilter.GaussianBlur(S * 0.06)), mask)
    img.paste((min(base[0] + 70, 255), min(base[1] + 65, 255), min(base[2] + 55, 255), 255), (0, 0), hl)
    # little cracks / specks
    dd = ImageDraw.Draw(img)
    for _ in range(3):
        x0, y0 = cx + rnd.uniform(-R * 0.5, R * 0.4), cy + rnd.uniform(-R * 0.3, R * 0.5)
        dd.line([(x0, y0), (x0 + rnd.uniform(-R * 0.25, R * 0.25), y0 + rnd.uniform(R * 0.05, R * 0.25))], fill=(60, 40, 30, 200), width=int(S * 0.025))
    return img.resize((size, size), Image.LANCZOS)
save(rock(76, (150, 112, 86), 1), 'rock_small.png')
save(rock(116, (128, 120, 116), 2), 'rock_medium.png')

# ---------- Crack tip (glow) 48x48 ----------
S = 64 * 4; tip = Image.new('RGBA', (S, S), (0, 0, 0, 0))
for r, col in [(0.48, (255, 140, 30, 90)), (0.34, (255, 190, 60, 170)), (0.2, (255, 240, 170, 255)), (0.11, (255, 255, 255, 255))]:
    lay = Image.new('RGBA', (S, S), (0, 0, 0, 0)); ImageDraw.Draw(lay).ellipse([S/2 - r*S, S/2 - r*S, S/2 + r*S, S/2 + r*S], fill=col)
    tip = Image.alpha_composite(tip, lay.filter(ImageFilter.GaussianBlur(S * 0.04)))
save(tip.resize((64, 64), Image.LANCZOS), 'crack_tip.png')

# ---------- Crack hitbox (debug only, hidden in game) 12x12 ----------
hb = Image.new('RGBA', (12, 12), (255, 0, 255, 160)); save(hb, 'crack_hitbox.png')

# ---------- Trail segment 32x18: dark jagged edges + golden core ----------
TW, TH = 32, 24; S = 4
seg = Image.new('RGBA', (TW * S, TH * S), (0, 0, 0, 0)); sd = ImageDraw.Draw(seg)
cy = TH * S / 2
sd.rectangle([0, cy - 10 * S, TW * S, cy + 10 * S], fill=(40, 20, 12, 230))       # dark fractured edge
sd.rectangle([0, cy - 6 * S, TW * S, cy + 6 * S], fill=(232, 120, 28, 255))     # orange
sd.rectangle([0, cy - 3 * S, TW * S, cy + 3 * S], fill=(255, 200, 70, 255))     # gold
sd.rectangle([0, cy - 1.2 * S, TW * S, cy + 1.2 * S], fill=(255, 250, 215, 255)) # hot centre
seg = seg.resize((TW, TH), Image.LANCZOS)
save(seg, 'trail_segment.png')

# ---------- Spark 12x12 ----------
S = 48; sp = Image.new('RGBA', (S, S), (0, 0, 0, 0))
ImageDraw.Draw(sp).ellipse([8, 8, 40, 40], fill=(255, 200, 80, 255))
sp = sp.filter(ImageFilter.GaussianBlur(4)); ImageDraw.Draw(sp).ellipse([18, 18, 30, 30], fill=(255, 255, 230, 255))
save(sp.resize((12, 12), Image.LANCZOS), 'spark.png')

# ---------- Impact flash 128x128 ----------
S = 128; fl = Image.new('RGBA', (S, S), (0, 0, 0, 0))
for r, col in [(60, (255, 160, 40, 120)), (40, (255, 230, 150, 200)), (20, (255, 255, 255, 255))]:
    lay = Image.new('RGBA', (S, S), (0, 0, 0, 0)); ImageDraw.Draw(lay).ellipse([64 - r, 64 - r, 64 + r, 64 + r], fill=col)
    fl = Image.alpha_composite(fl, lay.filter(ImageFilter.GaussianBlur(6)))
save(fl, 'impact_flash.png')

# ---------- UI ----------
save(Image.new('RGBA', (8, 8), (20, 8, 4, 255)), 'ui_overlay.png')
S = 4; bw, bh = 360, 110
btn = Image.new('RGBA', (bw * S, bh * S), (0, 0, 0, 0)); bd = ImageDraw.Draw(btn)
bd.rounded_rectangle([0, 8 * S, bw * S - 1, bh * S - 1], radius=40 * S, fill=(120, 44, 10, 255))
bd.rounded_rectangle([0, 0, bw * S - 1, (bh - 10) * S], radius=40 * S, fill=(255, 150, 40, 255))
bd.rounded_rectangle([10 * S, 8 * S, (bw - 10) * S, 46 * S], radius=26 * S, fill=(255, 200, 110, 255))
save(btn.resize((bw, bh), Image.LANCZOS), 'ui_button.png')
