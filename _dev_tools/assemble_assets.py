# Builds CRACKLINE's art + audio from HUMAN-MADE CC0 packs (Kenney, Beatscribe).
# Only mechanical edits are applied: resize, crop/split, recolour (multiply / hue shift), 9-slice, tiling, layering two packs' images.
import os, sys, subprocess, colorsys, shutil
from PIL import Image, ImageChops, ImageOps, ImageDraw
OUT = sys.argv[1]; AUD = os.path.join(OUT, '..', 'audio'); os.makedirs(AUD, exist_ok=True)
K = '/tmp/kn/2d'; NP = f'{K}/New Platformer Pack/Sprites'; PP = '/tmp/kenney-particle-pack/addons/kenney_particle_pack'
CREDITS = []
def src(path, pack, author='Kenney (kenney.nl)', lic='CC0 1.0'): CREDITS.append((os.path.basename(path), pack, author, lic)); return Image.open(path).convert('RGBA')
def save(img, name, note): img.save(os.path.join(OUT, name)); CREDITS[-1] = CREDITS[-1] + (name, note); print(name, img.size)
def fit(img, w, h):
    c = Image.new('RGBA', (w, h), (0, 0, 0, 0)); im = img.crop(img.getbbox())
    k = min(w / im.width, h / im.height); im = im.resize((max(1, round(im.width * k)), max(1, round(im.height * k))), Image.LANCZOS)
    c.alpha_composite(im, ((w - im.width) // 2, (h - im.height) // 2)); return c
def multiply(img, rgb):
    r, g, b, a = img.split(); return Image.merge('RGBA', (r.point(lambda v: v * rgb[0] // 255), g.point(lambda v: v * rgb[1] // 255), b.point(lambda v: v * rgb[2] // 255), a))
def colorize_white(img, rgb):   # particle textures are white-on-alpha: tint them
    r, g, b, a = img.split(); return Image.merge('RGBA', (Image.new('L', img.size, rgb[0]), Image.new('L', img.size, rgb[1]), Image.new('L', img.size, rgb[2]), a))
def hue_shift(img, deg, sat=1.0):
    px = img.load(); out = img.copy(); po = out.load()
    for y in range(img.height):
        for x in range(img.width):
            r, g, b, a = px[x, y]
            if a == 0: continue
            h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
            r2, g2, b2 = colorsys.hsv_to_rgb((h + deg / 360) % 1, min(1, s * sat), v)
            po[x, y] = (int(r2 * 255), int(g2 * 255), int(b2 * 255), a)
    return out
def tile_up(img, factor): return img.resize((img.width * factor, img.height * factor), Image.LANCZOS)

# ---------- world ----------
save(tile_up(src(f'{NP}/Tiles/Double/terrain_grass_block_center.png', 'New Platformer Pack'), 2), 'bg_soil.png', 'tile, upscaled 2x (Ember)')
save(multiply(tile_up(src(f'{NP}/Tiles/Double/terrain_purple_block_center.png', 'New Platformer Pack'), 2), (150, 225, 185)), 'bg_verdant.png', 'tile, upscaled 2x, recoloured green (Verdant)')
save(multiply(tile_up(src(f'{NP}/Tiles/Double/terrain_snow_block_center.png', 'New Platformer Pack'), 2), (175, 195, 255)), 'bg_frost.png', 'tile, upscaled 2x, recoloured blue (Frost)')
save(multiply(tile_up(src(f'{NP}/Tiles/Double/terrain_stone_block_center.png', 'New Platformer Pack'), 2), (170, 80, 60)), 'bg_magma.png', 'tile, upscaled 2x, recoloured dark red (Magma)')
save(multiply(tile_up(src(f'{NP}/Tiles/Double/terrain_purple_block_center.png', 'New Platformer Pack'), 2), (175, 130, 235)), 'bg_umbra.png', 'tile, upscaled 2x, recoloured violet (Umbra)')
save(fit(src(f'{K}/Space Shooter Remastered/Meteors/meteorBrown_big2.png', 'Space Shooter Redux'), 76, 76), 'rock_small.png', 'resized')
save(fit(src(f'{K}/Space Shooter Remastered/Meteors/meteorBrown_big1.png', 'Space Shooter Redux'), 116, 116), 'rock_medium.png', 'resized')
save(fit(multiply(src(f'{K}/Physics Assets/Stone elements/elementStone012.png', 'Physics Assets'), (215, 165, 120)), 112, 64), 'barrier_breakable.png', 'resized, recoloured warm stone (breakable)')
save(fit(src(f'{K}/Physics Assets/Metal elements/elementMetal012.png', 'Physics Assets'), 112, 64), 'barrier_solid.png', 'resized (riveted metal = unbreakable)')
w1 = src(f'{NP}/Enemies/Double/worm_ring_move_a.png', 'New Platformer Pack'); save(fit(ImageOps.mirror(w1), 160, 64), 'worm.png', 'mirrored to face right, frame A')
w2 = src(f'{NP}/Enemies/Double/worm_ring_move_b.png', 'New Platformer Pack'); save(fit(ImageOps.mirror(w2), 160, 64), 'worm_b.png', 'mirrored to face right, frame B')
lava = src(f'{NP}/Tiles/Double/lava_top_low.png', 'New Platformer Pack')       # 128x128, liquid in lower half
band = lava.crop((0, 64, 128, 128)).resize((64, 32), Image.LANCZOS)
strip = Image.new('RGBA', (720, 64), (0, 0, 0, 0))
for x in range(0, 720, 64):
    strip.alpha_composite(band, (x, 32)); strip.alpha_composite(ImageOps.flip(band), (x, 0))
save(strip, 'fissure.png', 'lava tile tiled across the width and mirrored into a band')
# crystals: colour = value (pink 5, purple 3, blue 1)
save(fit(src(f'{NP}/Tiles/Double/gem_blue.png', 'New Platformer Pack'), 96, 96), 'crystal_cyan.png', 'resized (blue = 1 point)')
save(fit(hue_shift(src(f'{NP}/Tiles/Double/gem_blue.png', 'New Platformer Pack'), 55), 96, 96), 'crystal_purple.png', 'hue-shifted to purple (3 points)')
save(fit(hue_shift(src(f'{NP}/Tiles/Double/gem_red.png', 'New Platformer Pack'), -28, 0.75), 96, 96), 'crystal_pink.png', 'hue-shifted to pink (5 points)')
# power-ups
pu = fit(src(f'{K}/Space Shooter Remastered/Power-ups/powerupBlue.png', 'Space Shooter Redux'), 80, 80)
hg = src('/tmp/kn/icons/Board Game Icons/Default (64px)/hourglass.png', 'Board Game Icons'); hg = hg.resize((38, 38), Image.LANCZOS)
pu.alpha_composite(hg, ((80 - hg.width) // 2, (80 - hg.height) // 2)); save(pu, 'powerup_slow.png', 'blue power-up + hourglass icon (Board Game Icons) layered')
save(fit(src(f'{K}/Space Shooter Remastered/Power-ups/powerupRed_bolt.png', 'Space Shooter Redux'), 80, 80), 'powerup_strength.png', 'resized')
# planets (split into halves along a jagged vertical line)
import random
for name, f in (('ember', 'planet08'), ('verdant', 'planet03'), ('frost', 'planet07'), ('magma', 'planet02'), ('umbra', 'planet09')):
    p = src(f'{K}/Planets/Planets/{f}.png', 'Planets').resize((320, 320), Image.LANCZOS)
    rnd = random.Random(name); pts = [(160 + rnd.uniform(-10, 10), y) for y in range(0, 321, 20)]
    left = Image.new('L', (320, 320), 0); ImageDraw.Draw(left).polygon([(0, 0)] + pts + [(0, 320)], fill=255); right = ImageOps.invert(left)
    for side, m in (('left', left), ('right', right)):
        h = Image.new('RGBA', (320, 320), (0, 0, 0, 0)); h.paste(p, (0, 0), ImageChops.multiply(m, p.split()[3]))
        h.save(os.path.join(OUT, f'planet_{name}_{side}.png'))
    CREDITS[-1] = CREDITS[-1] + (f'planet_{name}_left/right.png', 'resized and cut into two halves'); print('planet', name)
# ---------- crack, effects ----------
STY = {'classic': ((255, 200, 70), (255, 245, 215)), 'frostbite': ((90, 200, 255), (225, 250, 255)), 'venom': ((120, 240, 70), (235, 255, 215)),
       'amethyst': ((190, 110, 255), (245, 225, 255)), 'inferno': ((255, 80, 40), (255, 230, 190)), 'shadow': ((120, 50, 200), (215, 190, 255)),
       'sunburst': ((255, 230, 60), (255, 255, 255)), 'aurora': ((40, 255, 190), (255, 170, 235))}
trace = src(f'{PP}/rotated/trace_07_rotated.png', 'Particle Pack')
tip = src(f'{PP}/magic_05.png', 'Particle Pack')
for s, (col, core) in STY.items():
    t0 = trace.crop(trace.split()[3].point(lambda v: 255 if v > 40 else 0).getbbox()); tw, th = t0.size   # visible part only
    t = t0.crop((int(tw * 0.45), 0, int(tw * 0.55), th)).resize((32, 48), Image.LANCZOS)   # uniform middle slice so segments join seamlessly
    seg = colorize_white(t, col); inner = colorize_white(t.resize((32, 22), Image.LANCZOS), core)
    seg.alpha_composite(inner, (0, 13)); seg.save(os.path.join(OUT, f'trail_{s}.png'))
    g = colorize_white(tip.resize((128, 128), Image.LANCZOS), col); c = colorize_white(tip.resize((64, 64), Image.LANCZOS), core)
    g.alpha_composite(c, (32, 32)); g.save(os.path.join(OUT, f'tip_{s}.png'))
CREDITS[-2] = CREDITS[-2] + ('trail_<style>.png', 'middle slice of the streak, resized, tinted per crack style (two tinted layers)')
CREDITS[-1] = CREDITS[-1] + ('tip_<style>.png', 'resized, tinted per crack style (two tinted layers)')
save(src(f'{PP}/star_04.png', 'Particle Pack').resize((16, 16), Image.LANCZOS), 'spark.png', 'resized (tinted in game)')
save(src(f'{PP}/star_09.png', 'Particle Pack').resize((128, 128), Image.LANCZOS), 'impact_flash.png', 'resized')
save(colorize_white(src(f'{PP}/circle_03.png', 'Particle Pack').resize((140, 140), Image.LANCZOS), (130, 230, 255)), 'shield_glow.png', 'resized, tinted cyan')
# ---------- UI ----------
save(fit(src('/tmp/kn/ui/UI Pack/Yellow/Double/button_rectangle_depth_gloss.png', 'UI Pack').resize((360, 110), Image.LANCZOS), 360, 110), 'ui_button.png', 'resized')
save(fit(src('/tmp/kn/ui/UI Pack/Blue/Double/button_rectangle_depth_gloss.png', 'UI Pack').resize((360, 110), Image.LANCZOS), 360, 110), 'ui_button_blue.png', 'resized')
sq = src('/tmp/kn/ui/UI Pack/Grey/Double/button_square_depth_gloss.png', 'UI Pack'); b = 28   # 9-slice to 300x200
W, H = 300, 200; card = Image.new('RGBA', (W, H)); sw, sh = sq.size
parts = {(0, 0): (0, 0, b, b), (1, 0): (b, 0, sw - b, b), (2, 0): (sw - b, 0, sw, b), (0, 1): (0, b, b, sh - b), (1, 1): (b, b, sw - b, sh - b),
         (2, 1): (sw - b, b, sw, sh - b), (0, 2): (0, sh - b, b, sh), (1, 2): (b, sh - b, sw - b, sh), (2, 2): (sw - b, sh - b, sw, sh)}
xs = [(0, b), (b, W - b), (W - b, W)]; ys = [(0, b), (b, H - b), (H - b, H)]
for (i, j), box in parts.items():
    piece = sq.crop(box).resize((xs[i][1] - xs[i][0], ys[j][1] - ys[j][0]), Image.LANCZOS); card.alpha_composite(piece, (xs[i][0], ys[j][0]))
save(multiply(card, (95, 70, 60)), 'ui_card.png', '9-sliced to 300x200, darkened')
save(src('/tmp/kn/icons/Game Icons/White/2x/audioOn.png', 'Game Icons'), 'icon_audio_on.png', 'as is')
save(src('/tmp/kn/icons/Game Icons/White/2x/audioOff.png', 'Game Icons'), 'icon_audio_off.png', 'as is')
# plain fills (not artwork): debug hitbox, overlay, white pixel
Image.new('RGBA', (12, 12), (255, 0, 255, 160)).save(os.path.join(OUT, 'crack_hitbox.png'))
Image.new('RGBA', (8, 8), (20, 8, 4, 255)).save(os.path.join(OUT, 'ui_overlay.png'))
Image.new('RGBA', (8, 8), (255, 255, 255, 255)).save(os.path.join(OUT, 'ui_white.png'))

# ---------- audio ----------
S_IMP = '/tmp/kenney-impact-sounds-for-godot'; S_SCI = '/tmp/kenney-sci-fi-sounds-for-godot'; S_UI = '/tmp/kenney-interface-sounds'; BS = '/tmp/homebrew_vgm/NES/ogg'
def find(root, name):
    for d, _, fs in os.walk(root):
        if name in fs: return os.path.join(d, name)
    raise FileNotFoundError(name)
SOUNDS = [('sfx_branch', S_IMP, 'impact_mining_000.ogg', 'Impact Sounds', 'Kenney (kenney.nl)'),
          ('sfx_break', S_SCI, 'explosion_crunch_000.ogg', 'Sci-Fi Sounds', 'Kenney (kenney.nl)'),
          ('sfx_crash', S_SCI, 'low_frequency_explosion_000.ogg', 'Sci-Fi Sounds', 'Kenney (kenney.nl)'),
          ('sfx_fissure', S_IMP, 'impact_plate_heavy_000.ogg', 'Impact Sounds', 'Kenney (kenney.nl)'),
          ('sfx_crystal', S_UI, 'glass_001.wav', 'Interface Sounds', 'Kenney (kenney.nl)'),
          ('sfx_powerup', S_SCI, 'force_field_000.ogg', 'Sci-Fi Sounds', 'Kenney (kenney.nl)'),
          ('sfx_click', S_UI, 'click_001.wav', 'Interface Sounds', 'Kenney (kenney.nl)'),
          ('sfx_error', S_UI, 'error_004.wav', 'Interface Sounds', 'Kenney (kenney.nl)'),
          ('sfx_buy', BS, 'treasure.ogg', 'Homebrew Free Jingle and Fanfare Music Assets (NES)', 'Beatscribe'),
          ('sfx_revive', BS, 'charger.ogg', 'Homebrew Free Jingle and Fanfare Music Assets (NES)', 'Beatscribe'),
          ('jingle_gameover', BS, 'failure.ogg', 'Homebrew Free Jingle and Fanfare Music Assets (NES)', 'Beatscribe'),
          ('jingle_planet', BS, 'victory.ogg', 'Homebrew Free Jingle and Fanfare Music Assets (NES)', 'Beatscribe')]
for out, root, name, pack, author in SOUNDS:
    p = find(root, name); dst = os.path.join(AUD, out + '.ogg')
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', p, '-ac', '1', '-c:a', 'libvorbis', '-q:a', '4', dst], check=True)
    d = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', dst], capture_output=True, text=True).stdout.strip()
    CREDITS.append((name, pack, author, 'CC0 1.0', f'audio/{out}.ogg', f'converted to mono OGG ({float(d):.1f}s)')); print(out, d)

with open(os.path.join(OUT, '..', 'CREDITS.md'), 'w') as f:
    f.write('# CRACKLINE asset credits\n\nEvery image and sound in this game is human-made, from free CC0 (public domain) packs. Credit is not required but is given here with thanks.\n\n')
    f.write('- **Kenney** (www.kenney.nl): New Platformer Pack, Space Shooter Redux, Physics Assets, Planets, Particle Pack, UI Pack, Game Icons, Board Game Icons, Impact Sounds, Sci-Fi Sounds, Interface Sounds. License: CC0 1.0.\n')
    f.write('- **Beatscribe**: Homebrew Free Jingle and Fanfare Music Assets (github.com/Beatscribe/homebrew_vgm). License: CC0 1.0.\n\n')
    f.write('Only mechanical edits were made (resize, crop/split, recolour, 9-slice, tiling, layering, audio format conversion).\n\n| Game file | Source file | Pack | Author | License | Edit |\n|---|---|---|---|---|---|\n')
    for c in CREDITS:
        if len(c) == 6: f.write(f'| {c[4]} | {c[0]} | {c[1]} | {c[2]} | {c[3]} | {c[5]} |\n')
    f.write('\nPlain colour fills (crack_hitbox, ui_overlay, ui_white) are not artwork.\n')
    f.write('\n## Code\n| What | Source | License |\n|---|---|---|\n'
            '| Playgama Bridge extension v2.4.0 (leaderboard, platform messages) | github.com/playgama/bridge-gdevelop | MIT, (c) Playgama |\n')
print('credits rows', sum(1 for c in CREDITS if len(c) == 6))
