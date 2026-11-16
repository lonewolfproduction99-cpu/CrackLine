# Shop + crystal points tests.
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, 'run_tests3.py')).read().rsplit('async def main():', 1)[0].replace(
    "HERE = os.path.dirname(os.path.abspath(__file__))", f"HERE = {HERE!r}"))
JS_G = '''() => { %s if (!sc) return {scene: null}; const g = n => G(n);
  const txt = n => sc.getObjects(n).length ? sc.getObjects(n)[0].getText() : null;
  const out = { scene: sc.getName(), wallet: g('CrystalWallet').getAsNumber(), owned: g('OwnedStyles').getAsString(), equipped: g('EquippedStyle').getAsNumber(),
    walletText: txt('WalletText') || txt('MenuWalletText'), msg: txt('ShopMsg'), msgOpacity: sc.getObjects('ShopMsg').length ? sc.getObjects('ShopMsg')[0].getOpacity() : null,
    prices: sc.getObjects('ShopPrice').map(o => [o.getVariables().get('StyleIndex').getAsNumber(), o.getText()]).sort((a, b) => a[0] - b[0]).map(a => a[1]),
    names: sc.getObjects('ShopName').map(o => [o.getVariables().get('StyleIndex').getAsNumber(), o.getText()]).sort((a, b) => a[0] - b[0]).map(a => a[1]) };
  if (sc.getName() === 'Gameplay') { out.state = V('GameState').getAsString(); out.run = V('RunCrystals').getAsNumber(); out.gemText = txt('GemText');
    out.goGems = txt('GameOverGemsText'); out.tipAnim = sc.getObjects('CrackTip')[0].getAnimation();
    out.trailAnims = [...new Set(sc.getObjects('TrailSegment').map(o => o.getAnimation()))];
    out.gems = sc.getObjects('Crystal').map(o => ({id: o.id, v: o.getVariables().get('Value').getAsNumber(), s: o.getScale(), a: o.getAnimation(), x: o.getX(), wy: o.getVariables().get('WorldY').getAsNumber()})); }
  return out; }''' % PRE
async def Gs(page): return await page.evaluate(JS_G)
async def waitg(page, cond, timeout):
    t0 = time.time()
    while time.time() - t0 < timeout:
        s = await Gs(page)
        if cond(s): return s
        await asyncio.sleep(0.05)
    return await Gs(page)
async def click_card(page, k):
    js = "() => { %s const o = sc.getObjects('ShopCard').find(o => o.getVariables().get('StyleIndex').getAsNumber() === %d); return [o.getCenterXInScene(), o.getCenterYInScene(), sc.getGame().getGameResolutionWidth()]; }" % (PRE, k)
    x, y, gw = await page.evaluate(js); kk = page.viewport_size['width'] / gw
    await page.mouse.click(x * kk, y * kk); await asyncio.sleep(0.3)
async def to_scene(page, name, btn):
    await click_obj(page, btn); await waitg(page, lambda s: s['scene'] == name, 5); await asyncio.sleep(0.4)
def gem(value, scale, ahead, dx=0):
    return '''() => { %s const o = sc.createObject('Crystal'); o.setX(V('CrackWorldX').getAsNumber() + %f); o.setScale(%f);
      o.getVariables().get('Value').setNumber(%d); o.setAnimation({5: 1, 3: 0, 1: 2}[%d]); o.getVariables().get('WorldY').setNumber(V('CrackWorldY').getAsNumber() + %f); return o.id; }''' % (PRE, dx, scale, value, value, ahead)

async def main():
    allerr = []
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(args=['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'])
        ctx = await browser.new_context(viewport={'width': 405, 'height': 720}); page = await ctx.new_page(); errors = []
        page.on('console', lambda m: errors.append(m.text) if m.type == 'error' else None); page.on('pageerror', lambda e: errors.append(str(e)))
        await page.goto('http://127.0.0.1:8765/index.html'); s = await waitg(page, lambda s: s['scene'] == 'MainMenu', 15); await asyncio.sleep(0.5); s = await Gs(page)
        check('fresh device: 0 crystals, only Classic owned and equipped', s['wallet'] == 0 and s['owned'] == '10000000' and s['equipped'] == 0 and s['walletText'] == 'CRYSTALS: 0')
        await to_scene(page, 'Shop', 'ShopButton'); s = await Gs(page)
        check('SHOP button opens the Shop with 8 styles', s['scene'] == 'Shop' and s['names'] == ['CLASSIC', 'FROSTBITE', 'VENOM', 'AMETHYST', 'INFERNO', 'SHADOW', 'SUNBURST', 'AURORA'], ', '.join(s['names']))
        check('cards show EQUIPPED / prices', s['prices'] == ['EQUIPPED', 'PRICE: 150', 'PRICE: 300', 'PRICE: 500', 'PRICE: 800', 'PRICE: 1200', 'PRICE: 1600', 'PRICE: 2000'], ' | '.join(s['prices']))
        await page.screenshot(path=f'{SHOTS}/p5_shop_empty.png')
        await click_card(page, 1); s = await Gs(page)
        check('cannot buy without enough crystals (message, nothing changes)', s['msg'] == 'NEED 150 MORE CRYSTALS' and s['owned'] == '10000000' and s['wallet'] == 0, s['msg'])
        await to_scene(page, 'MainMenu', 'BackButton')
        await to_scene(page, 'Gameplay', 'EndlessButton'); await asyncio.sleep(0.3)
        await page.evaluate(setnum('NextRowWorldY', '1e9'))
        for v, sc_, dx in [(5, 0.55, 0), (3, 0.75, 0), (1, 1.0, 0)]:
            await page.evaluate(gem(v, sc_, 70, dx)); await asyncio.sleep(0.8)
        s = await Gs(page)
        check('crystals are points, not hazards: small 5 + medium 3 + large 1 = 9', s['state'] == 'Playing' and s['run'] == 9 and s['wallet'] == 9 and s['gemText'] == '9', f"run {s['run']}, wallet {s['wallet']}")
        await page.evaluate(gem(5, 0.55, 70, 34)); await asyncio.sleep(0.8); s = await Gs(page)
        check('small crystal has a small pickup area (34 px to the side = missed)', s['run'] == 9)
        await page.evaluate(gem(1, 1.0, 70, 34)); await asyncio.sleep(0.8); s = await Gs(page)
        check('large crystal has a big pickup area (34 px to the side = collected)', s['run'] == 10)
        # natural generation
        await page.evaluate(setnum('NextRowWorldY', "V('CrackWorldY').getAsNumber() + 1500")); await page.evaluate(setnum('InvulnerabilityRemaining', '1e9'))
        gems, objs, t0 = {}, {}, time.time()
        while time.time() - t0 < 30:
            s = await Gs(page); st = await S(page)
            for g in s['gems']: gems[g['id']] = g
            for o in st['objs']: objs[o['id']] = o
            await asyncio.sleep(0.1)
        vals = {}
        COL = {0: 'purple', 1: 'pink', 2: 'blue'}
        for g in gems.values():
            k = (g['v'], round(g['s'], 2), COL[g['a']]); vals[k] = vals.get(k, 0) + 1
        ok_map = all(k in [(5, 0.55, 'pink'), (3, 0.75, 'purple'), (1, 1.0, 'blue')] for k in vals)
        check('crystal colour always matches size and value (pink 5 small, purple 3 medium, blue 1 large)', ok_map and len(vals) == 3, str(vals))
        haz = [o for o in objs.values() if o['t'] in ('RockSmall', 'RockMedium', 'BarrierBreakable', 'BarrierSolid')]
        R = {'RockSmall': 28, 'RockMedium': 44, 'BarrierBreakable': 50, 'BarrierSolid': 50}
        overl = [g for g in gems.values() for o in haz if abs(g['x'] - o['x']) < R[o['t']] + 30 * g['s'] - 4 and abs(g['wy'] - o['wy']) < 26 + 30 * g['s'] - 4 and (o['t'].startswith('Barrier') or math.hypot(g['x'] - o['x'], g['wy'] - o['wy']) < R[o['t']] + 30 * g['s'] - 4)]
        check('no crystal spawns inside an obstacle', not overl, f'{len(gems)} crystals seen, {len(overl)} overlapping')
        await page.screenshot(path=f'{SHOTS}/p5_crystals.png')
        await page.evaluate(setnum('NextRowWorldY', '1e9'))
        await page.evaluate("() => { %s for (const n of ['RockSmall','RockMedium','BarrierBreakable','BarrierSolid','Worm','Fissure']) for (const o of sc.getObjects(n)) o.deleteFromScene(); }" % PRE)
        await asyncio.sleep(0.2); await page.evaluate(setnum('InvulnerabilityRemaining', 0))
        await page.evaluate("() => { %s G('CrystalWallet').setNumber(1000); V('RunCrystals').setNumber(25); }" % PRE)
        await page.evaluate(put('BarrierSolid', 0, 60)); s = await waitg(page, lambda s: s.get('state') == 'GameOver', 3)
        check('game over shows crystals earned and total', s['goGems'] == 'CRYSTALS +25   (TOTAL 1000)', s['goGems'])
        await asyncio.sleep(0.5); await to_scene(page, 'MainMenu', 'MenuButton'); s = await Gs(page)
        check('wallet saved and shown on menu', s['walletText'] == 'CRYSTALS: 1000')
        await to_scene(page, 'Shop', 'ShopButton')
        await click_card(page, 1); s = await Gs(page)
        check('buy Frostbite: -150, owned, equipped, message', s['wallet'] == 850 and s['owned'] == '11000000' and s['equipped'] == 1 and s['msg'] == 'UNLOCKED FROSTBITE!' and s['prices'][1] == 'EQUIPPED', s['msg'])
        await click_card(page, 0); s = await Gs(page)
        check('tap owned Classic: equips it for free', s['equipped'] == 0 and s['wallet'] == 850 and s['prices'][0] == 'EQUIPPED' and s['prices'][1] == 'OWNED')
        await click_card(page, 5); s = await Gs(page)
        check('Shadow (1200) refused with 850', s['msg'] == 'NEED 350 MORE CRYSTALS' and s['owned'] == '11000000')
        await click_card(page, 4); s = await Gs(page)
        check('buy Inferno (800): wallet 50, owned flags 11001000', s['wallet'] == 50 and s['owned'] == '11001000' and s['equipped'] == 4)
        await click_card(page, 1); await asyncio.sleep(2.2); s = await Gs(page)
        check('message fades out', s['msgOpacity'] == 0 and s['equipped'] == 1)
        await page.screenshot(path=f'{SHOTS}/p5_shop_bought.png')
        await page.reload(); await waitg(page, lambda s: s['scene'] == 'MainMenu', 15); await asyncio.sleep(0.4)
        await to_scene(page, 'Shop', 'ShopButton'); s = await Gs(page)
        check('purchases + equipped style survive a reload', s['wallet'] == 50 and s['owned'] == '11001000' and s['equipped'] == 1 and s['prices'][1] == 'EQUIPPED')
        await page.evaluate("() => { const s = JSON.parse(localStorage.getItem('GDJS_CracklineSave') || '{}'); }")
        keys = await page.evaluate("() => Object.keys(localStorage)")
        k = [x for x in keys if 'CracklineSave' in x][0]
        await page.evaluate("(k) => { const s = JSON.parse(localStorage.getItem(k)); s.OwnedStyles = {value: '', str: '110010'}; s.CrystalWallet = {value: 2100}; localStorage.setItem(k, JSON.stringify(s)); }", k)
        await page.reload(); await waitg(page, lambda s: s['scene'] == 'MainMenu', 15); await asyncio.sleep(0.4)
        await to_scene(page, 'Shop', 'ShopButton'); s = await Gs(page)
        check('older 6-style save is upgraded to 8 flags', s['owned'] == '11001000', s['owned'])
        await click_card(page, 7); s = await Gs(page)
        check('buy Aurora (2000) after upgrade: flag lands in slot 8', s['owned'] == '11001001' and s['equipped'] == 7 and s['wallet'] == 100, s['owned'])
        await page.screenshot(path=f'{SHOTS}/p5_shop_8.png')
        await click_card(page, 1)
        await to_scene(page, 'MainMenu', 'BackButton'); await to_scene(page, 'Gameplay', 'PlanetButton'); await asyncio.sleep(1.5); s = await Gs(page)
        check('equipped style recolours the crack tip and trail in game', s['tipAnim'] == 1 and s['trailAnims'] == [1], f"tip {s['tipAnim']}, trail {s['trailAnims']}")
        await page.screenshot(path=f'{SHOTS}/p5_frostbite.png')
        allerr += errors; await ctx.close()
        # layouts
        ok_pairs = {frozenset(p) for p in [('EndlessButton', 'EndlessLabel'), ('PlanetButton', 'PlanetLabel'), ('ShopButton', 'ShopLabel'), ('BackButton', 'BackLabel')]}
        for (w, h, label) in [(405, 720, '9x16'), (360, 800, '9x20'), (768, 1024, '3x4'), (600, 600, '1x1')]:
            ctx = await browser.new_context(viewport={'width': w, 'height': h}); page = await ctx.new_page()
            await page.goto('http://127.0.0.1:8765/index.html'); await waitg(page, lambda s: s['scene'] == 'MainMenu', 15); await asyncio.sleep(0.6)
            Lm = await page.evaluate(LAYOUT % ('[""]', 'Text|Button|Label'))
            await to_scene(page, 'Shop', 'ShopButton'); await click_card(page, 3)
            Ls = await page.evaluate(LAYOUT % ('[""]', 'Card|Title|Wallet|Button|Label|Msg'))
            # inside each card: its texts/preview must stay within the card
            inside = await page.evaluate('''() => { %s const bad = [];
              for (const c of sc.getObjects('ShopCard')) { const k = c.getVariables().get('StyleIndex').getAsNumber(), a = c.getAABB();
                for (const n of ['ShopName', 'ShopPrice', 'ShopTip', 'ShopTrail']) { const o = sc.getObjects(n).find(o => o.getVariables().get('StyleIndex').getAsNumber() === k); const b = o.getAABB();
                  if (b.min[0] < a.min[0] - 1 || b.max[0] > a.max[0] + 1 || b.min[1] < a.min[1] - 1 || b.max[1] > a.max[1] + 1) bad.push(n + k); } } return bad; }''' % PRE)
            await page.screenshot(path=f'{SHOTS}/p5_shop_{label}.png')
            issues = layout_ok(Lm, ok_pairs) + layout_ok(Ls, ok_pairs) + [f'{x} outside card' for x in inside]
            check(f'{label} ({w}x{h}): menu + shop fit, no overlaps', not issues, '; '.join(issues[:4]))
            await ctx.close()
        allerr = [e for e in allerr if 'api.gdevelop-app.com' not in e and 'ERR_TUNNEL' not in e]
        check('no runtime errors in console', not allerr, '; '.join(allerr[:3]))
        await browser.close()
    srv.shutdown()
    print(f"\n{sum(r[1] for r in results)}/{len(results)} checks passed")
asyncio.run(main())
