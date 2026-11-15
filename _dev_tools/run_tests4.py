# Update tests: 1k-per-planet progression with per-planet speed/difficulty, fissures (forced random branch), burrowing worms.
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, 'run_tests3.py')).read().rsplit('async def main():', 1)[0].replace(
    "HERE = os.path.dirname(os.path.abspath(__file__))", f"HERE = {HERE!r}"))
JS_X = '''() => { %s const w = sc.getObjects('Worm'), f = sc.getObjects('Fissure');
  return { state: V('GameState').getAsString(), x: V('CrackWorldX').getAsNumber(), wy: V('CrackWorldY').getAsNumber(), dir: V('BranchDirection').getAsNumber(),
    speed: V('ScrollSpeed').getAsNumber(), diff: V('DifficultyLevel').getAsNumber(), idx: V('PlanetIndex').getAsNumber(), target: V('PlanetTargetDistance').getAsNumber(),
    charges: V('StrengthCharges').getAsNumber(), ptime: V('PlanetTime').getAsNumber(),
    worms: w.map(o => ({id: o.id, x: o.getX(), dir: o.getVariables().get('Dir').getAsNumber(), spd: o.getVariables().get('Speed').getAsNumber(), flip: o.isFlippedX()})),
    fis: f.map(o => ({id: o.id, used: o.getVariables().get('Used').getAsBoolean(), wy: o.getVariables().get('WorldY').getAsNumber()})) }; }''' % PRE
async def X(page): return await page.evaluate(JS_X)
def mk(obj, x, ahead, extra=''):
    return '''() => { %s const o = sc.createObject('%s'); o.setX(%s); o.getVariables().get('WorldY').setNumber(V('CrackWorldY').getAsNumber() + %f); %s return o.id; }''' % (PRE, obj, x, ahead, extra)

async def main():
    allerr = []
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(args=['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'])
        ctx = await browser.new_context(viewport={'width': 405, 'height': 720}); page = await ctx.new_page(); errors = []
        page.on('console', lambda m: errors.append(m.text) if m.type == 'error' else None); page.on('pageerror', lambda e: errors.append(str(e)))
        await page.goto('http://127.0.0.1:8765/index.html'); await enter(page, 'Planet')
        await page.evaluate(setnum('InvulnerabilityRemaining', '1e9'))
        s = await X(page)
        rows = [(s['idx'], s['target'], s['speed'], s['diff'])]
        for k in range(3):
            await finish_planet(page)
            await waitp(page, lambda p: p['state'] == 'Playing' and p['idx'] == k + 1 and p['hudText'].startswith(f'PLANET {k + 2} '), 10)
            s = await X(page); rows.append((s['idx'], s['target'], s['speed'], s['diff']))
        print('    planet start values (index, target m, speed, difficulty):', [(i, t, round(v, 1), round(d, 2)) for i, t, v, d in rows])
        check('planet goals are 1000, 2000, 3000, 4000 m', [r[1] for r in rows] == [1000, 2000, 3000, 4000])
        check('each planet starts harder (+0.2 difficulty)', all(abs(r[3] - (0.15 + 0.2 * i)) < 0.02 for i, r in enumerate(rows)), ', '.join(f'{r[3]:.2f}' for r in rows))
        await page.evaluate("() => { %s V('CrackWorldY').setNumber(26000); V('PlanetStartWorldY').setNumber(26000); V('TrailLastWorldY').setNumber(26000); }" % PRE)
        await asyncio.sleep(3.5)
        s = await X(page)
        check('Planet Breaker: same 250 m steps, capped at PlanetMaxSpeed 520 (not 420)', abs(s['speed'] - 520) < 0.01, f"{s['speed']:.0f} px/s at {s['wy'] / 20:.0f} m")
        allerr += errors; await ctx.close()

        # ---------- fissures & worms (Endless, random rows suppressed) ----------
        ctx, page, errors = await boot(browser); allerr += errors
        await page.evaluate(setnum('NextRowWorldY', '1e9'))
        dirs = []
        for i in range(8):
            await page.evaluate(setnum('CrackWorldX', 360)); await asyncio.sleep(0.1)
            x0 = (await X(page))['x']
            fid = await page.evaluate(mk('Fissure', 0, 60))
            t0 = time.time(); s = await X(page)
            while time.time() - t0 < 2 and not any(f['used'] and f['id'] == fid for f in s['fis']): await asyncio.sleep(0.02); s = await X(page)
            d = s['dir']; await asyncio.sleep(0.35); s2 = await X(page)
            dirs.append(d)
            if i == 0:
                check('crossing a fissure forces a branch (not lethal)', d != 0 and abs(abs(s2['x'] - x0) - 130) < 0.5 and s2['state'] == 'Playing', f'{x0:.0f} -> {s2["x"]:.0f}')
            await asyncio.sleep(0.6)
        check('fissure branch direction is random (both seen in 8 crossings)', -1 in dirs and 1 in dirs, str(dirs))
        s = await X(page); check('each fissure triggers only once', all(f['used'] for f in s['fis']))
        await hold_start(page, 'L'); await asyncio.sleep(0.1)
        fid = await page.evaluate(mk('Fissure', 0, 40)); t0 = time.time(); s = await X(page)
        while time.time() - t0 < 2 and not any(f['used'] and f['id'] == fid for f in s['fis']): await asyncio.sleep(0.01); s = await X(page)
        x_hit = s['x']; await asyncio.sleep(0.1); during = await X(page); await asyncio.sleep(0.15); after = await X(page); await hold_end(page)
        check('fissure jolt overrides steering, then steering resumes', s['dir'] != 0 and abs(abs(after['x'] - x_hit) - 130) < 90 and after['dir'] == 0, f"{x_hit:.0f} -> {after['x']:.0f}")
        # worms
        await page.evaluate(setnum('CrackWorldX', 650))
        wid = await page.evaluate(mk('Worm', 200, 900, "o.getVariables().get('Dir').setNumber(1); o.getVariables().get('Speed').setNumber(150);"))
        a = await X(page); await asyncio.sleep(1.0); b = await X(page)
        wa = [w for w in a['worms'] if w['id'] == wid][0]; wb = [w for w in b['worms'] if w['id'] == wid][0]
        check('worm burrows sideways at its speed', 120 < wb['x'] - wa['x'] < 180 and not wb['flip'], f"{wb['x'] - wa['x']:.0f} px in ~1 s")
        await page.evaluate("() => { %s for (const o of sc.getObjects('Worm')) o.setX(635); }" % PRE); await asyncio.sleep(0.4); c = await X(page)
        wc = [w for w in c['worms'] if w['id'] == wid][0]
        check('worm turns around at the edge and faces the other way', wc['dir'] == -1 and wc['flip'], f"x={wc['x']:.0f}")
        await page.screenshot(path=f'{SHOTS}/p4_worm.png')
        await page.evaluate("() => { %s for (const o of sc.getObjects('Worm')) o.deleteFromScene(); }" % PRE)
        await page.evaluate(put('PowerStrength', 0, 45)); await wait_state(page, lambda s: s['charges'] > 0, 1.5)
        await page.evaluate(mk('Worm', "V('CrackWorldX').getAsNumber()", 70, "o.getVariables().get('Speed').setNumber(0);"))
        await asyncio.sleep(0.8); s = await X(page)
        check('Crack Strength smashes a worm', s['state'] == 'Playing' and s['charges'] == 2 and not s['worms'])
        await page.evaluate(setnum('StrengthCharges', 0))
        await page.evaluate(mk('Worm', "V('CrackWorldX').getAsNumber()", 70, "o.getVariables().get('Speed').setNumber(0);"))
        s = await wait_state(page, lambda s: s['state'] != 'Playing', 2)
        check('worm kills without Strength', s['state'] == 'GameOver')
        await restart(page)
        # ---------- natural generation at high difficulty ----------
        await page.evaluate(setnum('InvulnerabilityRemaining', 1e9)); await page.evaluate(setnum('RunTime', 400))
        seen_w, seen_f, objs, t0 = {}, {}, {}, time.time()
        while time.time() - t0 < 50:
            s = await X(page); st = await S(page)
            for w in s['worms']: seen_w[w['id']] = w
            for f in s['fis']: seen_f[f['id']] = f['wy']
            for o in st['objs']: objs[o['id']] = o
            if len(seen_f) and not os.path.exists(f'{SHOTS}/p4_fissure.png'): await page.screenshot(path=f'{SHOTS}/p4_fissure.png')
            await asyncio.sleep(0.05)
        check('generator spawns worms and fissures at high difficulty', len(seen_w) > 0 and len(seen_f) > 0, f'{len(seen_w)} worms, {len(seen_f)} fissures in 50 s')
        viol = [o for o in objs.values() for fy in seen_f.values() if fy + 40 < o['wy'] < fy + 1000 - 80 and not o['t'].startswith('Power')]
        check('nothing spawns in the clearance after a fissure', not viol, f'{len(viol)} violations')
        allerr += errors; await ctx.close()
        allerr = [e for e in allerr if 'api.gdevelop-app.com' not in e and 'ERR_TUNNEL' not in e]
        check('no runtime errors in console', not allerr, '; '.join(allerr[:3]))
        await browser.close()
    srv.shutdown()
    print(f"\n{sum(r[1] for r in results)}/{len(results)} checks passed")
asyncio.run(main())
