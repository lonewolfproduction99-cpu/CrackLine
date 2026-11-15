# Automated play-test of the real GDevelop HTML5 export in headless Chrome.
import asyncio, json, math, os, shutil, sys, time, http.server, threading, functools
from playwright.async_api import async_playwright
BUILD = sys.argv[1]; SHOTS = sys.argv[2]; os.makedirs(SHOTS, exist_ok=True)
TEST = '/tmp/crack_test_build'
shutil.rmtree(TEST, ignore_errors=True); shutil.copytree(BUILD, TEST)
p = os.path.join(TEST, 'index.html'); s = open(p).read()
s = s.replace('var game = new gdjs.RuntimeGame(gdjs.projectData, gdjs.runtimeGameOptions);',
              'var game = new gdjs.RuntimeGame(gdjs.projectData, gdjs.runtimeGameOptions); window.__game = game;')
assert 'window.__game' in s; open(p, 'w').write(s)
H = functools.partial(http.server.SimpleHTTPRequestHandler, directory=TEST)
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
H = functools.partial(Q, directory=TEST)
srv = http.server.ThreadingHTTPServer(('127.0.0.1', 8765), H); threading.Thread(target=srv.serve_forever, daemon=True).start()

results = []
def check(name, ok, detail=''):
    results.append((name, bool(ok), detail)); print(('PASS ' if ok else 'FAIL ') + name + ('  -- ' + detail if detail else ''), flush=True)

JS_STATE = '''() => { const sc = window.__game && window.__game.getSceneStack().getCurrentScene(); if (!sc) return null;
  const v = n => sc.getVariables().get(n); const g = n => v(n).getAsNumber();
  const obs = sc.getObjects('RockSmall').concat(sc.getObjects('RockMedium')).map(o => ({x:o.getX(), y:o.getY(), wy:o.getVariables().get('WorldY').getAsNumber(), r: o.getName()==='RockSmall'?28:44}));
  return { scene: sc.getName(), state: v('GameState').getAsString(), x: g('CrackWorldX'), wy: g('CrackWorldY'), dist: g('Distance'),
    dir: g('BranchDirection'), tipY: g('TipScreenY'), w: sc.getGame().getGameResolutionWidth(), h: sc.getGame().getGameResolutionHeight(),
    trail: sc.getObjects('TrailSegment').length, sparks: sc.getObjects('Spark').length, obs, chunk: g('ChunkIndex'),
    gameOverVisible: sc.getLayer('GameOver').isVisible(), tipX: sc.getObjects('CrackTip')[0].getX(), t: performance.now() }; }'''

async def boot(browser, w, h, touch=False):
    ctx = await browser.new_context(viewport={'width': w, 'height': h}, has_touch=touch, is_mobile=touch, device_scale_factor=1)
    page = await ctx.new_page(); errors = []
    page.on('console', lambda m: errors.append(m.text) if m.type == 'error' else None)
    page.on('pageerror', lambda e: errors.append(str(e)))
    await page.goto('http://127.0.0.1:8765/index.html')
    for _ in range(200):
        st = await page.evaluate(JS_STATE)
        if st and st['scene'] == 'Gameplay' and st['wy'] > 0: break
        await asyncio.sleep(0.05)
    return ctx, page, errors

async def state(page): return await page.evaluate(JS_STATE)
async def tap(page, side, touch=False):
    vp = page.viewport_size; x = vp['width'] * (0.25 if side == 'L' else 0.75); y = vp['height'] * 0.5
    if touch: await page.touchscreen.tap(x, y)
    else: await page.mouse.click(x, y)

async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(args=['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'])
        # ---------- 1. phone 9:16, mouse ----------
        ctx, page, errors = await boot(browser, 405, 720)
        st = await state(page)
        check('game launches into Gameplay scene, Playing', st and st['state'] == 'Playing', json.dumps({k: st[k] for k in ('w', 'h', 'tipY')}))
        await page.screenshot(path=f'{SHOTS}/01_start.png')
        a = await state(page); await asyncio.sleep(1.0); b = await state(page)
        speed = (b['wy'] - a['wy']) / ((b['t'] - a['t']) / 1000)
        check('crack advances automatically at ~180 px/s (time-based)', 165 < speed < 195, f'{speed:.1f} px/s')
        check('distance counter increases with world distance', b['dist'] == math.floor(b['wy'] / 20) and b['dist'] > a['dist'], f"{a['dist']} -> {b['dist']} m")
        check('tip held at 70% of screen height', abs(st['tipY'] - st['h'] * 0.7) < 0.5, f"tipY={st['tipY']:.1f} h={st['h']}")
        x0 = (await state(page))['x']
        await tap(page, 'L'); await asyncio.sleep(0.05); mid = await state(page); await asyncio.sleep(0.35); s1 = await state(page)
        check('tap LEFT half branches left by BranchDistance', abs((x0 - s1['x']) - 130) < 0.01, f'{x0:.1f} -> {s1["x"]:.1f}')
        check('branch is a smooth diagonal (partial offset mid-branch)', 0 < x0 - mid['x'] < 130 and mid['dir'] == -1, f'mid offset {x0 - mid["x"]:.1f}px')
        check('crack returns to straight movement after branch', s1['dir'] == 0)
        await page.screenshot(path=f'{SHOTS}/02_after_left.png')
        await tap(page, 'R'); await asyncio.sleep(0.4); s2 = await state(page)
        check('tap RIGHT half branches right by BranchDistance', abs((s2['x'] - s1['x']) - 130) < 0.01, f'{s1["x"]:.1f} -> {s2["x"]:.1f}')
        x0 = s2['x']; await tap(page, 'L'); await asyncio.sleep(0.05); await tap(page, 'L'); await asyncio.sleep(0.5); s3 = await state(page)
        check('second tap during a branch is ignored (no queue)', abs((x0 - s3['x']) - 130) < 0.01, f'moved {x0 - s3["x"]:.1f}px for 2 rapid taps')
        await ctx.close()

        # ---------- 2. edge clamping ----------
        ctx, page, errors2 = await boot(browser, 405, 720); errors += errors2
        for _ in range(7): await tap(page, 'L'); await asyncio.sleep(0.3)
        se = await state(page)
        check('crack clamped at left edge (EdgeMargin=30)', abs(se['x'] - 30) < 0.01 or se['state'] == 'GameOver', f'x={se["x"]:.1f} state={se["state"]}')
        await tap(page, 'R'); await asyncio.sleep(0.35); se2 = await state(page)
        check('not stuck at edge: right tap moves away', se2['x'] - se['x'] > 120 or se['state'] == 'GameOver', f'{se["x"]:.1f} -> {se2["x"]:.1f}')
        await ctx.close()

        # ---------- 3. idle -> death by centre rock, overlay, restart ----------
        ctx, page, errors2 = await boot(browser, 405, 720); errors += errors2
        t0 = time.time(); st = await state(page)
        while st['state'] == 'Playing' and time.time() - t0 < 15:
            if time.time() - t0 > 5.5 and not os.path.exists(f'{SHOTS}/03_approach.png'): await page.screenshot(path=f'{SHOTS}/03_approach.png')
            await asyncio.sleep(0.05); st = await state(page)
        check('idle crack collides with centre rock and dies', st['state'] == 'GameOver', f'died at {st["dist"]} m after {time.time() - t0:.1f}s')
        wy_dead = st['wy']; await asyncio.sleep(0.5); st2 = await state(page)
        check('movement and scrolling stop on death', st2['wy'] == wy_dead)
        check('game-over overlay shown', st2['gameOverVisible'])
        await page.screenshot(path=f'{SHOTS}/04_game_over.png')
        # click restart button (button centre: x=360, y=0.52*H in game coords)
        vp = page.viewport_size; sx = vp['width'] / st2['w']
        await page.mouse.click(360 * sx, st2['h'] * 0.52 * sx); await asyncio.sleep(0.3)
        st3 = await state(page)
        check('RESTART button restarts instantly', st3['state'] == 'Playing' and st3['wy'] < 120 and abs(st3['x'] - 360) < 0.01 and not st3['gameOverVisible'], f'wy={st3["wy"]:.0f}')
        await ctx.close()

        # ---------- 4. touch input + autopilot survival (tall phone) ----------
        ctx, page, errors2 = await boot(browser, 360, 800, touch=True); errors += errors2
        x0 = (await state(page))['x']; await tap(page, 'R', touch=True); await asyncio.sleep(0.35)
        check('touchscreen tap (right) branches', abs((await state(page))['x'] - x0 - 130) < 0.01)
        await tap(page, 'L', touch=True); await asyncio.sleep(0.35)
        check('touchscreen tap (left) branches', abs((await state(page))['x'] - x0) < 0.01)
        t0 = time.time(); maxtrail = 0; maxobs = 0; shot = False; taps = 0
        while time.time() - t0 < 40:
            st = await state(page)
            if st['state'] != 'Playing': break
            maxtrail = max(maxtrail, st['trail']); maxobs = max(maxobs, len(st['obs']))
            if st['dir'] == 0:
                ahead = [o for o in st['obs'] if -40 < o['wy'] - st['wy'] < 420]
                def free(x): return all(abs(x - o['x']) > o['r'] + 34 for o in ahead)
                if not free(st['x']):
                    near = [o for o in st['obs'] if -60 < o['wy'] - st['wy'] < 220]
                    def path_clear(tx):
                        lo, hi = min(tx, st['x']), max(tx, st['x'])
                        return all(not (lo - o['r'] - 20 < o['x'] < hi + o['r'] + 20) for o in near if abs(o['x'] - st['x']) > o['r'] + 10)
                    cands = [x for x in range(30, 691, 5) if free(x) and path_clear(x)]
                    if cands:
                        tgt = min(cands, key=lambda x: abs(x - st['x']))
                        await tap(page, 'L' if tgt < st['x'] else 'R', touch=True); taps += 1
            if time.time() - t0 > 12 and not shot: await page.screenshot(path=f'{SHOTS}/05_playing.png'); shot = True
            await asyncio.sleep(0.02)
        el = time.time() - t0
        if st['state'] != 'Playing':
            near = [o for o in st['obs'] if abs(o['wy'] - st['wy']) < 120]
            print('   death debug: x=%.1f wy=%.0f chunk=%d near=%s' % (st['x'], st['wy'], st['chunk'], [(round(o['x']), round(o['wy'] - st['wy']), o['r']) for o in near]))
        check('autopilot (touch input) survives 30+ s through all chunks', el >= 30, f'{el:.1f}s, {st["dist"]} m, {taps} taps, state={st["state"]}')
        check('trail segments capped / cleaned (<=160)', maxtrail <= 160 and maxtrail > 20, f'max live segments {maxtrail}')
        check('obstacles deleted offscreen (no accumulation)', maxobs <= 20, f'max live obstacles {maxobs}')
        await ctx.close()

        # ---------- 5. tablet portrait resolution ----------
        ctx, page, errors2 = await boot(browser, 800, 1280); errors += errors2
        st = await state(page); await asyncio.sleep(1)
        check('tablet portrait: width stays 720, tip at 70%', st['w'] == 720 and abs(st['tipY'] - st['h'] * 0.7) < 0.5, f'res {st["w"]}x{st["h"]:.0f}')
        await page.screenshot(path=f'{SHOTS}/06_tablet.png'); await ctx.close()
        check('no runtime errors in console', not errors, '; '.join(errors[:5]))
        await browser.close()
    srv.shutdown()
    print(f"\n{sum(r[1] for r in results)}/{len(results)} checks passed")
asyncio.run(main())
