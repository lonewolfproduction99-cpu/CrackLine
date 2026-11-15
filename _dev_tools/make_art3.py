# Phase 3 placeholder art: Verdant/Frost backgrounds, split planets (3 themes), planet crack, shield ring.
import math, random, sys, os
from PIL import Image, ImageDraw, ImageFilter, ImageChops
out = sys.argv[1]
def save(img, n): img.save(os.path.join(out, n)); print(n, img.size)
W = 256
def background(base_fn, blob_dark, blob_light, flecks, seed):
    rnd = random.Random(seed)
    bg = Image.new('RGBA', (W, W)); d = ImageDraw.Draw(bg)
    for y in range(W):
        t = math.sin(y / W * 2 * math.pi * 2) * .5 + .5; t2 = math.sin(y / W * 2 * math.pi * 6 + 1.3) * .5 + .5
        d.line([(0, y), (W, y)], fill=base_fn(t, t2) + (255,))
    def wrapped(cx, cy, rx, ry, fill, blur=0):
        lay = Image.new('RGBA', (W, W), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
        for ox in (-W, 0, W):
            for oy in (-W, 0, W): ld.ellipse([cx - rx + ox, cy - ry + oy, cx + rx + ox, cy + ry + oy], fill=fill)
        return lay.filter(ImageFilter.GaussianBlur(blur)) if blur else lay
    for _ in range(18): bg = Image.alpha_composite(bg, wrapped(rnd.uniform(0, W), rnd.uniform(0, W), rnd.uniform(20, 46), rnd.uniform(8, 16), blob_dark + (60,), 7))
    for _ in range(10): bg = Image.alpha_composite(bg, wrapped(rnd.uniform(0, W), rnd.uniform(0, W), rnd.uniform(16, 34), rnd.uniform(6, 12), blob_light + (45,), 6))
    for col in flecks:
        cx, cy = rnd.uniform(0, W), rnd.uniform(0, W)
        bg = Image.alpha_composite(bg, wrapped(cx, cy, 7, 7, col + (90,), 3)); bg = Image.alpha_composite(bg, wrapped(cx, cy, 1.6, 1.6, (255, 255, 240, 255)))
    return bg.convert('RGB')
save(background(lambda t, t2: (int(40 + 20 * t), int(120 + 30 * t + 8 * t2), int(100 + 20 * t)), (14, 60, 50), (120, 220, 170), [(80, 255, 220), (255, 120, 220), (200, 255, 120)], 21), 'bg_verdant.png')
save(background(lambda t, t2: (int(70 + 20 * t + 6 * t2), int(84 + 22 * t), int(160 + 28 * t)), (34, 30, 90), (190, 210, 255), [(200, 240, 255), (180, 120, 255)], 22), 'bg_frost.png')

# ---- planets 320x320, split into left/right along a jagged vertical seam ----
S = 320 * 3
def planet(c1, c2, c3, seed):
    rnd = random.Random(seed)
    im = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    glow = Image.new('RGBA', (S, S), (0, 0, 0, 0)); ImageDraw.Draw(glow).ellipse([S * .04, S * .04, S * .96, S * .96], fill=c3 + (120,))
    im = Image.alpha_composite(im, glow.filter(ImageFilter.GaussianBlur(S * .03)))
    body = Image.new('RGBA', (S, S), (0, 0, 0, 0)); bd = ImageDraw.Draw(body)
    bd.ellipse([S * .08, S * .08, S * .92, S * .92], fill=(30, 18, 24, 255))
    bd.ellipse([S * .1, S * .1, S * .9, S * .9], fill=c1 + (255,))
    mask = Image.new('L', (S, S), 0); ImageDraw.Draw(mask).ellipse([S * .1, S * .1, S * .9, S * .9], fill=255)
    det = Image.new('RGBA', (S, S), (0, 0, 0, 0)); dd = ImageDraw.Draw(det)
    for i in range(6):   # bands
        y = S * (.2 + i * .12) + rnd.uniform(-10, 10)
        dd.ellipse([S * .05, y, S * .95, y + S * rnd.uniform(.04, .08)], fill=c2 + (150,))
    for _ in range(9):   # craters / patches
        cx, cy, r = rnd.uniform(S * .2, S * .8), rnd.uniform(S * .2, S * .8), rnd.uniform(S * .03, S * .07)
        dd.ellipse([cx - r, cy - r, cx + r, cy + r], fill=c2 + (200,))
        dd.ellipse([cx - r * .6, cy - r * .7, cx + r * .2, cy - r * .1], fill=(255, 255, 255, 60))
    det = det.filter(ImageFilter.GaussianBlur(S * .006))
    body.paste(det, (0, 0), ImageChops.multiply(det.split()[3], mask))
    shade = Image.new('L', (S, S), 0); ImageDraw.Draw(shade).ellipse([S * .3, S * .3, S * 1.2, S * 1.2], fill=140)
    shade = ImageChops.multiply(shade.filter(ImageFilter.GaussianBlur(S * .08)), mask)
    body.paste((20, 10, 30, 255), (0, 0), shade.point(lambda v: v // 2))
    hl = Image.new('L', (S, S), 0); ImageDraw.Draw(hl).ellipse([S * .2, S * .16, S * .5, S * .38], fill=120)
    body.paste((255, 255, 255, 255), (0, 0), ImageChops.multiply(hl.filter(ImageFilter.GaussianBlur(S * .05)), mask))
    im = Image.alpha_composite(im, body)
    # jagged seam
    pts = []; y = 0
    while y <= S:
        pts.append((S / 2 + rnd.uniform(-S * .035, S * .035), y)); y += S * .06
    pts[-1] = (pts[-1][0], S)
    left = Image.new('L', (S, S), 0); ImageDraw.Draw(left).polygon([(0, 0)] + pts + [(0, S)], fill=255)
    right = ImageChops.invert(left)
    halves = []
    for m in (left, right):
        h = Image.new('RGBA', (S, S), (0, 0, 0, 0)); h.paste(im, (0, 0), ImageChops.multiply(m, im.split()[3]))
        # glowing molten edge along the seam
        edge = Image.new('L', (S, S), 0); ImageDraw.Draw(edge).line(pts, fill=255, width=int(S * .02))
        edge = ImageChops.multiply(edge, ImageChops.multiply(m, mask))
        h.paste((255, 220, 120, 255), (0, 0), edge)
        halves.append(h.resize((320, 320), Image.LANCZOS))
    return halves
for name, c1, c2, c3, sd in [('ember', (226, 110, 50), (160, 60, 30), (255, 140, 60), 1), ('verdant', (60, 170, 130), (30, 110, 90), (90, 255, 200), 2),
                             ('frost', (120, 150, 230), (80, 90, 190), (170, 200, 255), 3)]:
    l, r = planet(c1, c2, c3, sd); save(l, f'planet_{name}_left.png'); save(r, f'planet_{name}_right.png')

# ---- planet crack: vertical glowing line 40x320 (origin top-centre) ----
cr = Image.new('RGBA', (40 * 4, 320 * 4), (0, 0, 0, 0)); cd = ImageDraw.Draw(cr)
pts = [(80 + random.Random(5).uniform(-14, 14) * (0 < i < 20), i * 64) for i in range(21)]
g = Image.new('RGBA', cr.size, (0, 0, 0, 0)); ImageDraw.Draw(g).line(pts, fill=(255, 170, 40, 255), width=40); cr = Image.alpha_composite(cr, g.filter(ImageFilter.GaussianBlur(14)))
ImageDraw.Draw(cr).line(pts, fill=(255, 250, 220, 255), width=12)
save(cr.resize((40, 320), Image.LANCZOS), 'planet_crack.png')

# ---- shield ring 140x140 ----
S2 = 140 * 4; sh = Image.new('RGBA', (S2, S2), (0, 0, 0, 0))
g = Image.new('RGBA', (S2, S2), (0, 0, 0, 0)); ImageDraw.Draw(g).ellipse([40, 40, S2 - 40, S2 - 40], outline=(110, 230, 255, 255), width=40)
sh = Image.alpha_composite(sh, g.filter(ImageFilter.GaussianBlur(16)))
ImageDraw.Draw(sh).ellipse([60, 60, S2 - 60, S2 - 60], outline=(220, 250, 255, 255), width=12)
save(sh.resize((140, 140), Image.LANCZOS), 'shield_glow.png')
save(Image.new('RGBA', (8, 8), (255, 255, 255, 255)), 'ui_white.png')
