from PIL import Image, ImageDraw, ImageFont, ImageFilter
A = '/home/claude/repo_crackline/assets/'
FONT = '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf'
shot = Image.open('/tmp/covers/g_1_7.png').convert('RGBA')        # 1080x1920 live gameplay frame (Aurora crack)

def title(img, cx, y, size, sub=True):
    d = ImageDraw.Draw(img)
    f = ImageFont.truetype(FONT, size); fs = ImageFont.truetype(FONT, int(size * 0.3))
    # soft shadow
    sh = Image.new('RGBA', img.size, (0, 0, 0, 0)); ds = ImageDraw.Draw(sh)
    ds.text((cx, y + size * 0.07), "CRACKLINE", font=f, anchor='mt', fill=(0, 0, 0, 150), stroke_width=int(size * 0.07), stroke_fill=(0, 0, 0, 150))
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(size * 0.04)))
    d.text((cx, y), "CRACKLINE", font=f, anchor='mt', fill=(255, 214, 120), stroke_width=int(size * 0.06), stroke_fill=(70, 24, 8))
    if sub:
        d.text((cx, y + size * 1.08), "SPLIT THE WORLD", font=fs, anchor='mt', fill=(255, 240, 214), stroke_width=max(2, int(size * 0.025)), stroke_fill=(70, 24, 8))

def top_shade(img, h, a=150):
    g = Image.new('L', (1, h)); [g.putpixel((0, y), int(a * (1 - y / h) ** 1.5)) for y in range(h)]
    sh = Image.new('RGBA', img.size, (40, 12, 4, 0)); sh.putalpha(g.resize((img.width, h)).crop((0, 0, img.width, h)).resize((img.width, h)) if False else Image.new('L', img.size, 0))
    mask = Image.new('L', img.size, 0); mask.paste(g.resize((img.width, h)), (0, 0))
    sh.putalpha(mask); img.alpha_composite(sh)

# ---- portrait 1080x1920
p = shot.copy(); top_shade(p, 600, 170); title(p, 540, 130, 158)
p.convert('RGB').save('/tmp/covers/cover_portrait.png')

# ---- square 800x800: the crack and obstacles, title on top
sq = shot.crop((0, 560, 1080, 1640)).resize((800, 800), Image.LANCZOS)
top_shade(sq, 300, 170); title(sq, 400, 56, 112)
sq.convert('RGB').save('/tmp/covers/cover_square.png')

# ---- landscape 1920x1080: game ground tiled, planet splitting on the left, title, gameplay on the right
tile = Image.open(A + 'bg_soil.png').convert('RGBA').resize((384, 384), Image.NEAREST)
ls = Image.new('RGBA', (1920, 1080))
for x in range(0, 1920, 384):
    for y in range(0, 1080, 384): ls.alpha_composite(tile, (x, y))
dark = Image.new('RGBA', ls.size, (40, 12, 4, 70)); ls.alpha_composite(dark)
pl, pr = [Image.open(A + f).convert("RGBA") for f in ("planet_magma_left.png", "planet_magma_right.png")]; pl, pr = pl.crop(pl.getbbox()), pr.crop(pr.getbbox())
s = 420 / pl.height; pl = pl.resize((int(pl.width * s), 420)); pr = pr.resize((int(pr.width * s), 420))
cx, cy = 640, 650
ls.alpha_composite(pl.rotate(8, expand=True, resample=Image.BICUBIC), (cx - pl.width - 28, cy - 240))
ls.alpha_composite(pr.rotate(-8, expand=True, resample=Image.BICUBIC), (cx + 6, cy - 220))
title(ls, 640, 110, 170)
# gameplay "phone" panel on the right
g = shot.crop((0, 200, 1080, 1920)).resize((540, 860), Image.LANCZOS)
frame = Image.new('RGBA', (540 + 24, 860 + 24), (70, 24, 8, 255))
mask = Image.new('L', frame.size, 0); ImageDraw.Draw(mask).rounded_rectangle((0, 0, frame.width - 1, frame.height - 1), 36, fill=255)
fr = Image.new('RGBA', frame.size, (0, 0, 0, 0)); fr.paste(frame, (0, 0), mask)
gm = Image.new('L', g.size, 0); ImageDraw.Draw(gm).rounded_rectangle((0, 0, g.width - 1, g.height - 1), 26, fill=255)
fr.paste(g, (12, 12), gm)
shadow = Image.new('RGBA', ls.size, (0, 0, 0, 0)); ImageDraw.Draw(shadow).rounded_rectangle((1290, 120, 1290 + fr.width, 120 + fr.height), 36, fill=(0, 0, 0, 140))
ls.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(18))); ls.alpha_composite(fr, (1270, 98))
ls.convert('RGB').save('/tmp/covers/cover_landscape.png')
for n in ('square', 'portrait', 'landscape'):
    im = Image.open(f'/tmp/covers/cover_{n}.png'); print(n, im.size)
