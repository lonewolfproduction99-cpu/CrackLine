# Phase 3 automated play-tests: main menu, Planet Breaker, planet split, revive, both-mode restart, resolutions.
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, 'run_tests2.py')).read().split('async def main():')[0])   # shared harness (server, S(), put(), boot(), enter()...)

JS_P = '''() => { %s if (!sc) return null; const vis = n => sc.getObjects(n).length ? sc.getObjects(n)[0].isVisible() : null;
  return { scene: sc.getName(), state: V('GameState') ? V('GameState').getAsString() : null, mode: G('GameMode').getAsString(),
    idx: V('PlanetIndex') ? V('PlanetIndex').getAsNumber() : null, theme: V('PlanetTheme') ? V('PlanetTheme').getAsNumber() : null,
    broken: V('PlanetsBroken') ? V('PlanetsBroken').getAsNumber() : null, target: V('PlanetTargetDistance') ? V('PlanetTargetDistance').getAsNumber() : null,
    pdist: V('PlanetDistance') ? V('PlanetDistance').getAsNumber() : null, diff: V('DifficultyLevel') ? V('DifficultyLevel').getAsNumber() : null,
    inv: V('InvulnerabilityRemaining') ? V('InvulnerabilityRemaining').getAsNumber() : null, reviveUsed: V('ReviveUsed') ? V('ReviveUsed').getAsBoolean() : null,
    dist: V('Distance') ? V('Distance').getAsNumber() : null, runtime: V('RunTime') ? V('RunTime').getAsNumber() : null, wy: V('CrackWorldY') ? V('CrackWorldY').getAsNumber() : null,
    bestP: G('BestPlanetsBroken').getAsNumber(), bestE: G('BestEndlessDistance').getAsNumber(),
    cinematic: sc.hasLayer('Cinematic') ? sc.getLayer('Cinematic').isVisible() : null, gameOver: sc.hasLayer('GameOver') ? sc.getLayer('GameOver').isVisible() : null,
    bg: ['BgEmber', 'BgVerdant', 'BgFrost'].map(vis), shield: vis('ShieldGlow'), reviveBtn: vis('ReviveButton'), hud: vis('PlanetHudText'),
    hudText: sc.getObjects('PlanetHudText').length ? sc.getObjects('PlanetHudText')[0].getText() : '', goPlanets: sc.getObjects('GameOverPlanetsText').length ? sc.getObjects('GameOverPlanetsText')[0].getText() : '',
    menuBest: sc.getObjects('MenuBestText').length ? sc.getObjects('MenuBestText')[0].getText() : '',
    nObs: ['RockSmall','RockMedium','BarrierBreakable','BarrierSolid','Crystal'].reduce((a, n) => a + sc.getObjects(n).length, 0) }; }''' % PRE
async def P(page): return await page.evaluate(JS_P)
async def waitp(page, cond, timeout):
    t0 = time.time()
    while time.time() - t0 < timeout:
        st = await P(page)
        if st and cond(st): return st
        await asyncio.sleep(0.03)
    return await P(page)
async def click_obj(page, name):
    js = "() => { %s const o = sc.getObjects('%s')[0]; const l = sc.getLayer(o.getLayer()); const c = l.convertInverseCoords(o.getCenterXInScene(), o.getCenterYInScene()); return [c[0], c[1], sc.getGame().getGameResolutionWidth()]; }" % (PRE, name)
    x, y, gw = await page.evaluate(js); k = page.viewport_size['width'] / gw
    await page.mouse.click(x * k, y * k)
def setnum(n, expr): return "() => { %s V('%s').setNumber(%s); }" % (PRE, n, expr)
async def finish_planet(page):
    await page.evaluate(setnum('NextRowWorldY', '1e9'))
    await page.evaluate(setnum('PlanetStartWorldY', "V('CrackWorldY').getAsNumber() - (V('PlanetTargetDistance').getAsNumber() * 20 - 30)"))
LAYOUT = '''() => { %s const out = []; const W = sc.getGame().getGameResolutionWidth(), H = sc.getGame().getGameResolutionHeight();
  for (const ln of %%s) { if (!sc.getLayer(ln).isVisible()) continue;
    for (const o of sc.getAdhocListOfAllInstances()) { if (o.getLayer() !== ln || !o.isVisible() || !o.getName().match(/%%s/)) continue;
      const a = o.getAABB(); out.push({n: o.getName(), x0: a.min[0], y0: a.min[1], x1: a.max[0], y1: a.max[1]}); } }
  return {W, H, boxes: out}; }''' % PRE
def layout_ok(L, pairs_ok):
    issues = []
    for b in L['boxes']:
        if b['x0'] < -1 or b['y0'] < -1 or b['x1'] > L['W'] + 1 or b['y1'] > L['H'] + 1: issues.append(f"{b['n']} off-screen")
    bs = L['boxes']
    for i in range(len(bs)):
        for j in range(i + 1, len(bs)):
            a, b = bs[i], bs[j]
            if frozenset((a['n'], b['n'])) in pairs_ok: continue
            if a['x0'] < b['x1'] - 2 and b['x0'] < a['x1'] - 2 and a['y0'] < b['y1'] - 2 and b['y0'] < a['y1'] - 2: issues.append(f"{a['n']}/{b['n']} overlap")
    return issues

async def main():
    allerr = []
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(args=['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'])
        ctx = await browser.new_context(viewport={'width': 405, 'height': 720}); page = await ctx.new_page(); errors = []
        page.on('console', lambda m: errors.append(m.text) if m.type == 'error' else None); page.on('pageerror', lambda e: errors.append(str(e)))
        await page.goto('http://127.0.0.1:8765/index.html')
        st = await waitp(page, lambda s: s['scene'] == 'MainMenu', 15); await asyncio.sleep(0.5)
        check('game opens on the MainMenu scene', st['scene'] == 'MainMenu', st['menuBest'])
        await page.screenshot(path=f'{SHOTS}/p3_01_menu.png')
        await enter(page, 'Planet'); st = await P(page)
        check('Planet Breaker button -> Gameplay in Planet mode', st['scene'] == 'Gameplay' and st['mode'] == 'Planet' and st['state'] == 'Playing')
        check('planet 1 = Ember, 1000 m, progress HUD shown', st['theme'] == 0 and st['target'] == 1000 and st['hud'] and st['bg'] == [True, False, False], st['hudText'])
        await asyncio.sleep(1.0); st2 = await P(page)
        check('surface progress follows distance', st2['pdist'] > st['pdist'] and abs(st2['pdist'] - math.floor(st2['wy'] / 20)) <= 1, f"{st['pdist']} -> {st2['pdist']} m")
        await page.evaluate(setnum('InvulnerabilityRemaining', '1e9'))   # progression tests: don't let random rocks end the run
        diffs = [st2['diff']]
        expect = [(1, 2000, [False, True, False]), (2, 3000, [False, False, True]), (0, 4000, [True, False, False])]
        for k, (theme, target, bg) in enumerate(expect):
            await finish_planet(page)
            s = await waitp(page, lambda s: s['state'] == 'PlanetBreak', 3)
            if k == 0:
                check('reaching the surface stops play and clears obstacles', s['state'] == 'PlanetBreak' and s['nObs'] == 0 and s['cinematic'])
                await asyncio.sleep(0.55); await page.screenshot(path=f'{SHOTS}/p3_02_crack.png')
                await asyncio.sleep(0.6); await page.screenshot(path=f'{SHOTS}/p3_03_split.png')
            t0 = time.time()
            s = await waitp(page, lambda s: s['state'] == 'Playing' and s['idx'] == k + 1 and s['hudText'].startswith(f'PLANET {k + 2} '), 10); dur = time.time() - t0 + (1.15 if k == 0 else 0)
            check(f'planet {k + 1} broken -> planet {k + 2} ({["Ember", "Verdant", "Frost"][theme]}, {target} m)',
                  s['broken'] == k + 1 and s['idx'] == k + 1 and s['theme'] == theme and s['target'] == target and s['bg'] == bg and not s['cinematic'],
                  f"split sequence ~{dur:.1f}s, HUD: {s['hudText']}")
            diffs.append(s['diff'])
            if k == 0:
                await page.screenshot(path=f'{SHOTS}/p3_04_verdant.png')
                s = await waitp(page, lambda s: s['nObs'] > 0, 8)
                check('obstacles resume on the next planet', s['nObs'] > 0)
            if k == 1:
                await asyncio.sleep(4); await page.screenshot(path=f'{SHOTS}/p3_05_frost.png')
        check('difficulty rises from planet to planet', all(diffs[i + 1] > diffs[i] for i in range(len(diffs) - 1)), ', '.join(f'{d:.2f}' for d in diffs))
        # death in planet mode
        await page.evaluate(setnum('InvulnerabilityRemaining', '0'))
        await page.evaluate(setnum('NextRowWorldY', '1e9'))
        await page.evaluate(put('Crystal', 0, 70)); s = await waitp(page, lambda s: s['state'] == 'GameOver', 3)
        check('planet-mode game over shows planets broken + saves best', s['state'] == 'GameOver' and s['goPlanets'] == 'PLANETS BROKEN: 3' and s['bestP'] == 3, s['goPlanets'])
        await asyncio.sleep(0.5); await page.screenshot(path=f'{SHOTS}/p3_06_gameover.png')
        check('revive button offered on first death', s['reviveBtn'])
        before = await P(page)
        await page.evaluate(put('RockMedium', 0, 300)); await page.evaluate(put('Crystal', 130, 120))   # nearby lethal stuff to be cleared
        await click_obj(page, 'ReviveButton')
        s = await waitp(page, lambda s: s['state'] == 'Playing', 2)
        check('revive resumes play with 2 s protection + glow', s['state'] == 'Playing' and s['reviveUsed'] and 1.5 < s['inv'] <= 2 and s['shield'], f"inv {s['inv']:.2f}")
        check('revive keeps score, planets and difficulty', s['broken'] == 3 and s['dist'] >= before['dist'] and s['runtime'] >= before['runtime'] and s['idx'] == 3)
        check('revive clears nearby lethal obstacles', s['nObs'] == 0, f"{s['nObs']} left")
        await page.screenshot(path=f'{SHOTS}/p3_07_revived.png')
        await page.evaluate(put('Crystal', 0, 60)); await asyncio.sleep(0.6); s = await P(page)
        check('protected for the 2 s after revive', s['state'] == 'Playing')
        await waitp(page, lambda s: s['inv'] <= 0, 3)
        s = await waitp(page, lambda s: not s['shield'], 1); check('glow disappears when protection ends', not s['shield'])
        await page.evaluate(put('Crystal', 0, 60)); s = await waitp(page, lambda s: s['state'] == 'GameOver', 3)
        check('second death: no revive offered (one per run)', s['state'] == 'GameOver' and not s['reviveBtn'])
        await asyncio.sleep(0.5); await click_obj(page, 'ReviveButton'); await asyncio.sleep(0.4); s = await P(page)
        check('hidden revive button does nothing', s['state'] == 'GameOver')
        await click_obj(page, 'RestartButton'); s = await waitp(page, lambda s: s['state'] == 'Playing', 3)
        check('restart in Planet mode starts again at planet 1', s['mode'] == 'Planet' and s['idx'] == 0 and s['broken'] == 0 and s['theme'] == 0 and not s['reviveUsed'] and s['wy'] < 200)
        await page.evaluate(setnum('NextRowWorldY', '1e9')); await page.evaluate(put('Crystal', 0, 60)); await waitp(page, lambda s: s['state'] == 'GameOver', 3)
        await asyncio.sleep(0.5); await click_obj(page, 'MenuButton'); s = await waitp(page, lambda s: s['scene'] == 'MainMenu', 3); await asyncio.sleep(0.3); s = await P(page)
        check('MAIN MENU button returns to menu, showing bests', s['scene'] == 'MainMenu' and '3 PLANETS' in s['menuBest'], s['menuBest'])
        # endless mode from menu, revive there too
        await enter(page, 'Endless'); s = await P(page)
        check('Endless from menu: no planet HUD, Ember only', s['mode'] == 'Endless' and not s['hud'] and s['bg'] == [True, False, False])
        await page.evaluate(setnum('NextRowWorldY', '1e9')); await page.evaluate(put('Crystal', 0, 60)); await waitp(page, lambda s: s['state'] == 'GameOver', 3)
        await asyncio.sleep(0.5); await click_obj(page, 'ReviveButton'); s = await waitp(page, lambda s: s['state'] == 'Playing', 2)
        check('revive works in Endless too', s['state'] == 'Playing' and s['reviveUsed'])
        await asyncio.sleep(2.5); await page.evaluate(put('Crystal', 0, 60)); await waitp(page, lambda s: s['state'] == 'GameOver', 3)
        await asyncio.sleep(0.5); await click_obj(page, 'RestartButton'); s = await waitp(page, lambda s: s['state'] == 'Playing', 3)
        check('restart in Endless resets revive', s['mode'] == 'Endless' and not s['reviveUsed'] and s['wy'] < 200)
        allerr += errors; await ctx.close()

        # ---------- resolutions ----------
        for (w, h, label) in [(405, 720, '9x16'), (360, 800, '9x20'), (768, 1024, '3x4'), (600, 600, '1x1')]:
            ctx = await browser.new_context(viewport={'width': w, 'height': h}); page = await ctx.new_page(); errs = []
            page.on('pageerror', lambda e: errs.append(str(e)))
            await page.goto('http://127.0.0.1:8765/index.html'); await waitp(page, lambda s: s['scene'] == 'MainMenu', 15); await asyncio.sleep(0.6)
            Lm = await page.evaluate(LAYOUT % ('[""]', 'Text|Button|MenuTip'))
            await page.screenshot(path=f'{SHOTS}/p3_res_{label}_menu.png')
            await enter(page, 'Planet'); await asyncio.sleep(0.5)
            Lh = await page.evaluate(LAYOUT % ('["HUD"]', 'Text|Progress'))
            await page.evaluate("() => { %s G('BestPlanetsBroken').setNumber(-1); }" % PRE)   # force NEW BEST! to show
            await page.evaluate(setnum('NextRowWorldY', '1e9')); await page.evaluate(put('Crystal', 0, 60)); await waitp(page, lambda s: s['state'] == 'GameOver', 3)
            await asyncio.sleep(0.6)
            Lg = await page.evaluate(LAYOUT % ('["GameOver"]', 'Text|Button|Label'))
            await page.screenshot(path=f'{SHOTS}/p3_res_{label}_gameover.png')
            ok_pairs = {frozenset(p) for p in [('EndlessButton', 'EndlessLabel'), ('PlanetButton', 'PlanetLabel'), ('RestartButton', 'RestartLabel'),
                                                ('ReviveButton', 'ReviveLabel'), ('MenuButton', 'MenuLabel'), ('ProgressBack', 'ProgressFill')]}
            issues = layout_ok(Lm, ok_pairs) + layout_ok(Lh, ok_pairs) + layout_ok(Lg, ok_pairs)
            check(f'{label} ({w}x{h}): menu, HUD and game-over UI on screen, no overlaps', not issues and not errs, '; '.join(issues[:4]) or f"game res {Lg['W']}x{Lg['H']:.0f}")
            await ctx.close()
        allerr = [e for e in allerr if 'api.gdevelop-app.com' not in e and 'ERR_TUNNEL' not in e]
        check('no runtime errors in console', not allerr, '; '.join(allerr[:3]))
        await browser.close()
    srv.shutdown()
    print(f"\n{sum(r[1] for r in results)}/{len(results)} checks passed")
asyncio.run(main())
