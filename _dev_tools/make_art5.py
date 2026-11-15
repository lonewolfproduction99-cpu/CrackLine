# Crack styles (trail segment + tip glow per palette) and shop card panel.
import sys, os
from PIL import Image, ImageDraw, ImageFilter
out = sys.argv[1]
STYLES = {  # name: (hot core, mid, outer, dark edge)
    'classic':  ((255, 250, 215), (255, 200, 70), (232, 120, 28), (40, 20, 12)),
    'frostbite': ((240, 255, 255), (140, 230, 255), (40, 140, 255), (10, 20, 50)),
    'venom':    ((240, 255, 220), (170, 255, 90), (40, 190, 60), (10, 40, 10)),
    'amethyst': ((250, 230, 255), (210, 140, 255), (130, 50, 220), (30, 10, 50)),
    'inferno':  ((255, 240, 200), (255, 110, 60), (200, 20, 20), (40, 5, 5)),
    'shadow':   ((230, 210, 255), (130, 70, 210), (50, 15, 80), (5, 0, 10)),
}
for name, (core, mid, outer, edge) in STYLES.items():
    TW, TH, S = 32, 48, 4
    seg = Image.new('RGBA', (TW * S, TH * S), (0, 0, 0, 0)); d = ImageDraw.Draw(seg); cy = TH * S / 2
    d.rectangle([0, cy - 20 * S, TW * S, cy + 20 * S], fill=edge + (230,))
    d.rectangle([0, cy - 12 * S, TW * S, cy + 12 * S], fill=outer + (255,))
    d.rectangle([0, cy - 6 * S, TW * S, cy + 6 * S], fill=mid + (255,))
    d.rectangle([0, cy - 2.4 * S, TW * S, cy + 2.4 * S], fill=core + (255,))
    seg.resize((TW, TH), Image.LANCZOS).save(os.path.join(out, f'trail_{name}.png'))
    S2 = 128 * 4; tip = Image.new('RGBA', (S2, S2), (0, 0, 0, 0))
    for r, col in [(0.48, outer + (90,)), (0.34, mid + (170,)), (0.2, core + (255,)), (0.11, (255, 255, 255, 255))]:
        lay = Image.new('RGBA', (S2, S2), (0, 0, 0, 0)); ImageDraw.Draw(lay).ellipse([S2/2 - r*S2, S2/2 - r*S2, S2/2 + r*S2, S2/2 + r*S2], fill=col)
        tip = Image.alpha_composite(tip, lay.filter(ImageFilter.GaussianBlur(S2 * 0.04)))
    tip.resize((128, 128), Image.LANCZOS).save(os.path.join(out, f'tip_{name}.png'))
    print(name)
S = 4; W, H = 300, 200
card = Image.new('RGBA', (W * S, H * S), (0, 0, 0, 0)); d = ImageDraw.Draw(card)
d.rounded_rectangle([0, 0, W * S - 1, H * S - 1], radius=26 * S, fill=(255, 230, 190, 255))
d.rounded_rectangle([5 * S, 5 * S, (W - 5) * S, (H - 5) * S], radius=22 * S, fill=(60, 30, 18, 235))
card.resize((W, H), Image.LANCZOS).save(os.path.join(out, 'ui_card.png'))
