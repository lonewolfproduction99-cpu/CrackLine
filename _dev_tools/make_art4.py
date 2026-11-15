# Worm (burrowing, faces right; flipped in game when moving left) and full-width fissure.
import math, random, sys, os
from PIL import Image, ImageDraw, ImageFilter
out = sys.argv[1]
def save(img, n): img.save(os.path.join(out, n)); print(n, img.size)
SS = 4
W, H = 160 * SS, 64 * SS
im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
segs = 6
for i in range(segs):   # tail -> head
    t = i / (segs - 1); cx = (14 + t * 106) * SS; r = (13 + 9 * t) * SS; cy = (34 + 4 * math.sin(i * 1.3)) * SS
    d.ellipse([cx - r - 3 * SS, cy - r - 3 * SS, cx + r + 3 * SS, cy + r + 3 * SS], fill=(40, 22, 20, 255))
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(214, 150, 120, 255))
    d.ellipse([cx - r * .7, cy - r * .85, cx + r * .3, cy - r * .2], fill=(245, 205, 175, 255))
    d.arc([cx - r * .9, cy - r * .9, cx + r * .9, cy + r * .9], 60, 120, fill=(150, 90, 70, 255), width=2 * SS)
hx, hy, hr = 128 * SS, 32 * SS, 22 * SS   # head with digging mouth
d.ellipse([hx - hr - 3 * SS, hy - hr - 3 * SS, hx + hr + 3 * SS, hy + hr + 3 * SS], fill=(40, 22, 20, 255))
d.ellipse([hx - hr, hy - hr, hx + hr, hy + hr], fill=(226, 160, 128, 255))
d.ellipse([hx - hr * .6, hy - hr * .9, hx + hr * .2, hy - hr * .3], fill=(250, 215, 185, 255))
d.pieslice([hx + hr * .1, hy - hr * .55, hx + hr * 1.05, hy + hr * .55], -40, 40, fill=(60, 20, 30, 255))
for a in (-25, 0, 25):   # little teeth
    tx = hx + hr * .55 + math.cos(math.radians(a)) * hr * .38; ty = hy + math.sin(math.radians(a)) * hr * .38
    d.polygon([(tx, ty - 3 * SS), (tx + 6 * SS, ty), (tx, ty + 3 * SS)], fill=(255, 250, 230, 255))
d.ellipse([hx - 4 * SS, hy - 14 * SS, hx + 6 * SS, hy - 4 * SS], fill=(255, 255, 255, 255))
d.ellipse([hx, hy - 11 * SS, hx + 5 * SS, hy - 6 * SS], fill=(20, 10, 10, 255))
save(im.resize((160, 64), Image.LANCZOS), 'worm.png')

FW, FH = 720 * 2, 64 * 2   # fissure: dark gap with molten edges, tileable-looking across the width
rnd = random.Random(9)
top = [(x, 22 * 2 + rnd.uniform(-8, 8) * 2) for x in range(0, FW + 1, 36)]
bot = [(x, 42 * 2 + rnd.uniform(-8, 8) * 2) for x in range(0, FW + 1, 36)]
im = Image.new('RGBA', (FW, FH), (0, 0, 0, 0))
glow = Image.new('RGBA', (FW, FH), (0, 0, 0, 0)); gd = ImageDraw.Draw(glow)
gd.polygon(top + bot[::-1], fill=(255, 120, 30, 230))
im = Image.alpha_composite(im, glow.filter(ImageFilter.GaussianBlur(10)))
d = ImageDraw.Draw(im)
d.polygon(top + bot[::-1], fill=(255, 190, 80, 255))
inner_t = [(x, y + 5 * 2) for x, y in top]; inner_b = [(x, y - 5 * 2) for x, y in bot]
d.polygon(inner_t + inner_b[::-1], fill=(24, 10, 14, 255))
for i in range(0, len(top) - 1, 3):   # cracks spreading from the edges
    x, y = top[i]; d.line([(x, y), (x + rnd.uniform(-20, 20), y - rnd.uniform(10, 26))], fill=(40, 18, 10, 255), width=4)
    x, y = bot[i]; d.line([(x, y), (x + rnd.uniform(-20, 20), y + rnd.uniform(10, 26))], fill=(40, 18, 10, 255), width=4)
save(im.resize((720, 64), Image.LANCZOS), 'fissure.png')
