# Phase 2 automated play-tests of the real GDevelop HTML5 export in headless Chrome.
import asyncio, json, math, os, shutil, sys, time, http.server, threading, functools
from playwright.async_api import async_playwright
BUILD, SHOTS, HARVEST = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(SHOTS, exist_ok=True)
TEST = '/tmp/crack_test_build'
shutil.rmtree(TEST, ignore_errors=True); shutil.copytree(BUILD, TEST)
p = os.path.join(TEST, 'index.html'); s = open(p).read()
s = s.replace('var game = new gdjs.RuntimeGame(gdjs.projectData, gdjs.runtimeGameOptions);',
              'var game = new gdjs.RuntimeGame(gdjs.projectData, gdjs.runtimeGameOptions); window.__game = game;')
assert 'window.__game' in s; open(p, 'w').write(s)
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
srv = http.server.ThreadingHTTPServer(('127.0.0.1', 8765), functools.partial(Q, directory=TEST))
threading.Thread(target=srv.serve_forever, daemon=True).start()
results = []
def check(name, ok, detail=''):
    results.append((name, bool(ok))); print(('PASS ' if ok else 'FAIL ') + name + ('  -- ' + detail if detail else ''), flush=True)

PRE = "const sc = window.__game && window.__game.getSceneStack().getCurrentScene(); const V = n => sc.getVariables().get(n); const G = n => window.__game.getVariables().get(n);"
TYPES = ['RockSmall', 'RockMedium', 'BarrierBreakable', 'BarrierSolid', 'Crystal', 'PowerSlow', 'PowerStrength']
JS_STATE = '''() => { %s if (!sc) return null;
  const objs = []; for (const t of %s) for (const o of sc.getObjects(t)) objs.push({id: o.id, t, x: o.getX(), wy: o.getVariables().get('WorldY').getAsNumber()});
  return { scene: sc.getName(), state: V('GameState').getAsString(), x: V('CrackWorldX').getAsNumber(), wy: V('CrackWorldY').getAsNumber(),
    dist: V('Distance').getAsNumber(), dir: V('BranchDirection').getAsNumber(), tipY: V('TipScreenY').getAsNumber(), speed: V('ScrollSpeed').getAsNumber(),
    eff: V('EffectiveSpeed').getAsNumber(), slow: V('SlowTimeRemaining').getAsNumber(), charges: V('StrengthCharges').getAsNumber(),
    best: G('BestEndlessDistance').getAsNumber(), mode: G('GameMode').getAsString(), diff: V('DifficultyLevel').getAsNumber(), runtime: V('RunTime').getAsNumber(),
    w: sc.getGame().getGameResolutionWidth(), h: sc.getGame().getGameResolutionHeight(), objs,
    trail: sc.getObjects('TrailSegment').length, sparks: sc.getObjects('Spark').length,
    gameOver: sc.getLayer('GameOver').isVisible(), newBest: sc.getObjects('NewBestText')[0].isVisible(),
    slowHud: sc.getObjects('SlowText')[0].isVisible(), strHud: sc.getObjects('StrengthText')[0].isVisible(),
    bestText: sc.getObjects('BestText')[0].getText(), t: performance.now() }; }''' % (PRE, json.dumps(TYPES))
def put(obj, dx, ahead):  # create an object 'ahead' px in front of the tip, offset dx from the crack
    return '''() => { %s const o = sc.createObject('%s'); o.setX(V('CrackWorldX').getAsNumber() + %f);
      o.getVariables().get('WorldY').setNumber(V('CrackWorldY').getAsNumber() + %f); return o.id; }''' % (PRE, obj, dx, ahead)
def setvar(n, v): return "() => { %s V('%s').setNumber(%s); }" % (PRE, n, v)

async def boot(browser, w=405, h=720, touch=False, ctx=None):
    ctx = ctx or await browser.new_context(viewport={'width': w, 'height': h}, has_touch=touch, is_mobile=touch)
    page = await ctx.new_page(); errors = []
    page.on('console', lambda m: errors.append(m.text) if m.type == 'error' else None)
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.on('requestfailed', lambda r: errors.append('REQFAIL ' + r.url))
    await page.goto('http://127.0.0.1:8765/index.html')
    await enter(page, 'Endless')
    return ctx, page, errors
# Playgama Bridge: wait until it has started and the saved progress has loaded (menu buttons work from then on, like for a real player).
# The local test platform has no ads, so rewarded/interstitial ads are stubbed: a rewarded ad "is watched" ~0.3 s after it is requested.
AD_STUB = '''() => { if (window.__ads) return; const ad = window.bridge.advertisement; const ext = gdjs._playgamaBridgeExtension;
  window.__ads = {rewarded: 0, interstitial: 0, mode: 'watch'};
  Object.defineProperty(ad, 'isRewardedSupported', {get: () => true, configurable: true});
  Object.defineProperty(ad, 'isInterstitialSupported', {get: () => true, configurable: true});
  Object.defineProperty(ad, 'rewardedState', {get: () => window.__ads.state || 'closed', configurable: true});
  const push = st => { window.__ads.state = st; ext.rewardedStateStack.push(st); };
  ad.showRewarded = () => { window.__ads.rewarded++; push('loading');
    setTimeout(() => { if (window.__ads.mode === 'fail') { push('failed'); return; } push('opened');
      setTimeout(() => { if (window.__ads.mode === 'watch') push('rewarded'); push('closed'); }, 300); }, 50); };
  ad.showInterstitial = () => { window.__ads.interstitial++; }; }'''
async def prep(page):
    for _ in range(300):
        if await page.evaluate("() => !!(window.bridge && window.bridge.isInitialized && window.__game && window.__game.getVariables().get('ProfileLoaded').getAsNumber() === 1)"): break
        await asyncio.sleep(0.05)
    await page.evaluate(AD_STUB)
async def enter(page, mode):
    js = "() => { const sc = window.__game && window.__game.getSceneStack().getCurrentScene(); return sc ? sc.getName() : null }"
    for _ in range(300):
        if await page.evaluate(js) == 'MainMenu': break
        await asyncio.sleep(0.05)
    await prep(page)
    await asyncio.sleep(0.3)
    btn = "() => { const sc = window.__game.getSceneStack().getCurrentScene(); const b = sc.getObjects('%sButton')[0]; return [b.getCenterXInScene(), b.getCenterYInScene(), sc.getGame().getGameResolutionWidth()] }" % mode
    bx, by, gw = await page.evaluate(btn); k = page.viewport_size['width'] / gw
    await page.mouse.click(bx * k, by * k)
    for _ in range(300):
        st = await page.evaluate(JS_STATE)
        if st and st['scene'] == 'Gameplay' and st['wy'] > 0: return
        await asyncio.sleep(0.05)
async def S(page): return await page.evaluate(JS_STATE)
async def tap(page, side, touch=False):
    vp = page.viewport_size; x = vp['width'] * (0.25 if side == 'L' else 0.75)
    if touch: await page.touchscreen.tap(x, vp['height'] * 0.5)
    else: await page.mouse.click(x, vp['height'] * 0.5)
async def hold_start(page, side, touch=False):
    vp = page.viewport_size; x = vp['width'] * (0.25 if side == 'L' else 0.75); y = vp['height'] * 0.5
    if touch:
        cdp = await page.context.new_cdp_session(page); page._cdp = cdp
        await cdp.send('Input.dispatchTouchEvent', {'type': 'touchStart', 'touchPoints': [{'x': x, 'y': y, 'id': 1}]})
    else: await page.mouse.move(x, y); await page.mouse.down()
async def hold_end(page, touch=False):
    if touch: await page._cdp.send('Input.dispatchTouchEvent', {'type': 'touchEnd', 'touchPoints': []})
    else: await page.mouse.up()
async def hold(page, side, secs, touch=False):
    await hold_start(page, side, touch); await asyncio.sleep(secs); await hold_end(page, touch)
async def wait_state(page, cond, timeout):
    t0 = time.time()
    while time.time() - t0 < timeout:
        st = await S(page)
        if cond(st): return st
        await asyncio.sleep(0.03)
    return await S(page)
async def restart(page):
    for _ in range(5):
        await asyncio.sleep(0.5); st = await S(page)
        if st['state'] == 'Playing': return
        vp = page.viewport_size; k = vp['width'] / st['w']
        await page.mouse.click(360 * k, st['h'] * 0.56 * k)
    await asyncio.sleep(0.4); return
    st = await S(page); vp = page.viewport_size; k = vp['width'] / st['w']
    await page.mouse.click(360 * k, st['h'] * 0.56 * k); await asyncio.sleep(0.4)

async def main():
    allerr = []
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(args=['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'])
        ctx, page, errors = await boot(browser); allerr += errors
        await page.evaluate(setvar('NextRowWorldY', 1e9))   # feature tests: no random rows interfering
        st = await S(page)
        check('launches into Gameplay, Endless mode, Playing', st['state'] == 'Playing' and st['mode'] == 'Endless')
        check('fresh device: best starts at 0', st['best'] == 0 and 'BEST: 0000 m' in st['bestText'], st['bestText'])
        a = await S(page); await asyncio.sleep(1); b = await S(page)
        sp = (b['wy'] - a['wy']) / ((b['t'] - a['t']) / 1000)
        check('starts at ~180 px/s', 165 < sp < 195, f'{sp:.1f} px/s')
        x0 = b['x']; await hold_start(page, 'L'); await asyncio.sleep(0.15); h1 = await S(page); await asyncio.sleep(0.35); h2 = await S(page)
        lat = (h1['x'] - h2['x']) / ((h2['t'] - h1['t']) / 1000); fwd = (h2['wy'] - h1['wy']) / ((h2['t'] - h1['t']) / 1000)
        check('holding LEFT steers up-left diagonally at ~300 px/s', h2['x'] < x0 and 270 < lat < 330, f'lateral {lat:.0f} px/s, forward {fwd:.0f} px/s')
        await hold_end(page); await asyncio.sleep(0.15); r1 = await S(page); await asyncio.sleep(0.4); r2 = await S(page)
        check('releasing goes straight up again', abs(r2['x'] - r1['x']) < 0.5, f"x {r1['x']:.1f} -> {r2['x']:.1f}")
        await hold_start(page, 'R'); await asyncio.sleep(0.15); h1 = await S(page); await asyncio.sleep(0.35); h2 = await S(page); await hold_end(page)
        lat = (h2['x'] - h1['x']) / ((h2['t'] - h1['t']) / 1000)
        check('holding RIGHT steers up-right', 270 < lat < 330, f'{lat:.0f} px/s')
        await hold_start(page, 'L'); await asyncio.sleep(0.2); await page.mouse.move(page.viewport_size['width'] * 0.75, page.viewport_size['height'] * 0.5)
        await asyncio.sleep(0.15); h1 = await S(page); await asyncio.sleep(0.25); h2 = await S(page); await hold_end(page)
        check('sliding the held finger across the middle switches direction', h2['x'] > h1['x'], f"{h1['x']:.0f} -> {h2['x']:.0f}")
        await page.screenshot(path=f'{SHOTS}/p2_01_start.png')

        # --- speed scaling: +25% every 250 m, eased in, capped at 420 ---
        sp = []
        for m in (250, 500, 750, 2000):
            await page.evaluate(setvar('CrackWorldY', m * 20 + 5)); await asyncio.sleep(2.2); sp.append((await S(page))['speed'])
        exp = [225, 281.25, 351.6, 420]
        check('speed +25% every 250 m (225, 281, 352) and capped at 420', all(abs(a - b) < 1 for a, b in zip(sp, exp)), ', '.join(f'{v:.0f}' for v in sp))
        await page.evaluate(setvar('RunTime', 400)); await asyncio.sleep(0.1); st = await S(page)
        check('difficulty reaches max after DifficultyRampTime', st['diff'] == 1)
        await page.evaluate(setvar('RunTime', 0)); await asyncio.sleep(0.1)

        # --- Slow Time pickup ---
        await page.evaluate(put('PowerSlow', 0, 45))
        st = await wait_state(page, lambda s: s['slow'] > 0, 1.5)
        check('Slow Time collected by touching it', st['slow'] > 3.5 and st['slowHud'], f"remaining {st['slow']:.2f}s")
        a = await S(page); await asyncio.sleep(1.0); b = await S(page)
        real = (b['wy'] - a['wy']) / ((b['t'] - a['t']) / 1000)
        check('Slow Time = 40% slower forward motion (distance follows real progress)', abs(real / b['speed'] - 0.6) < 0.06, f"{real:.0f} px/s vs speed {b['speed']:.0f}")
        await hold_start(page, 'L'); await asyncio.sleep(0.15); h1 = await S(page); await asyncio.sleep(0.3); h2 = await S(page); await hold_end(page)
        lat = (h1['x'] - h2['x']) / ((h2['t'] - h1['t']) / 1000)
        exp = max(300, h2['speed']); check('steering speed unaffected by Slow Time (= full ScrollSpeed, not slowed)', abs(lat / exp - 1) < 0.1, f'{lat:.0f} px/s vs {exp:.0f}')
        await hold(page, 'R', 0.45)
        st = await wait_state(page, lambda s: s['slow'] <= 0, 5)
        a = await S(page); await asyncio.sleep(0.8); b = await S(page)
        real = (b['wy'] - a['wy']) / ((b['t'] - a['t']) / 1000)
        check('Slow Time ends after ~4 s and speed is restored', not b['slowHud'] and abs(real / b['speed'] - 1) < 0.08, f"{real:.0f} vs {b['speed']:.0f}")

        # --- Crack Strength ---
        await page.evaluate(put('PowerStrength', 0, 45))
        st = await wait_state(page, lambda s: s['charges'] > 0, 1.5)
        check('Crack Strength collected -> 3 charges + HUD', st['charges'] == 3 and st['strHud'])
        rid = await page.evaluate(put('RockMedium', 0, 70))
        st = await wait_state(page, lambda s: s['charges'] < 3 or s['state'] != 'Playing', 2)
        check('Strength breaks a rock (charge used, still alive)', st['charges'] == 2 and st['state'] == 'Playing' and all(o['id'] != rid for o in st['objs']))
        await page.evaluate(put('BarrierBreakable', 0, 70))
        st = await wait_state(page, lambda s: s['charges'] < 2 or s['state'] != 'Playing', 2)
        check('Strength breaks a breakable barrier', st['charges'] == 1 and st['state'] == 'Playing')
        await page.screenshot(path=f'{SHOTS}/p2_02_strength.png')
        await page.evaluate(put('BarrierSolid', 0, 70))
        st = await wait_state(page, lambda s: s['state'] != 'Playing', 2)
        check('solid barrier kills even with Strength charges', st['state'] == 'GameOver' and st['charges'] == 1)
        d1 = st['dist']
        check('game over: best saved + NEW BEST shown', st['best'] == d1 and st['newBest'] and st['gameOver'], f'best={st["best"]}')
        await page.screenshot(path=f'{SHOTS}/p2_03_gameover.png')
        await restart(page); st = await S(page)
        await page.evaluate(setvar('NextRowWorldY', 1e9))
        check('restart keeps best (global) and resets run', st['state'] == 'Playing' and st['best'] == d1 and st['wy'] < 150 and st['charges'] == 0,
              st['bestText'])
        await page.evaluate(put('PowerStrength', 0, 45)); await wait_state(page, lambda s: s['charges'] > 0, 1.5)
        await page.evaluate(put('BarrierSolid', 0, 70))
        st = await wait_state(page, lambda s: s['state'] != 'Playing', 2)
        check('solid barrier kills even with Strength charges', st['state'] == 'GameOver' and st['charges'] == 3)
        check('lower score does not overwrite best / no NEW BEST', st['best'] == d1 and not st['newBest'])
        await page.evaluate(setvar('BestEndlessDistance', 0) .replace("V('BestEndlessDistance')", "G('BestEndlessDistance')"))
        await page.reload(); await enter(page, 'Endless'); st = await S(page)
        check('best persists after full page reload (device storage)', st['best'] == d1, f'loaded {st["best"]}')
        await restart(page); await page.evaluate(setvar('NextRowWorldY', 1e9))

        # --- unprotected rock kills ---
        await page.evaluate(put('RockSmall', 0, 60))
        st = await wait_state(page, lambda s: s['state'] != 'Playing', 2)
        check('rock kills without Strength', st['state'] == 'GameOver')
        await restart(page)

        # --- generator harvest: early game (real time) and max difficulty ---
        harvest = {}
        for label, rt, secs in [('early', 0, 35), ('max', 400, 45)]:
            await page.evaluate(setvar('InvulnerabilityRemaining', 1e9)); await page.evaluate(setvar('RunTime', rt))
            objs = {}; speeds = []; maxobj = 0; maxtrail = 0; t0 = time.time()
            while time.time() - t0 < secs:
                st = await S(page)
                for o in st['objs']: objs[o['id']] = (o['t'], o['x'], o['wy'])
                speeds.append((st['wy'], st['speed'])); maxobj = max(maxobj, len(st['objs'])); maxtrail = max(maxtrail, st['trail'])
                await asyncio.sleep(0.05)
            if label == 'max': await page.screenshot(path=f'{SHOTS}/p2_04_maxdiff.png')
            harvest[label] = {'objs': list(objs.values()), 'speeds': speeds, 'start_wy': speeds[0][0], 'end_wy': speeds[-1][0]}
            check(f'[{label}] no object accumulation', maxobj < 60 and maxtrail <= 160, f'max live obstacles+powerups {maxobj}, trail {maxtrail}')
            types = {}
            for o in objs.values(): types[o[0]] = types.get(o[0], 0) + 1
            print('   ', label, 'spawned:', types)
            await page.evaluate(setvar('InvulnerabilityRemaining', 0))
            await page.evaluate("() => { %s V('GameState').setString('GameOver'); }" % PRE); await asyncio.sleep(0.5); await restart(page)
        json.dump(harvest, open(HARVEST, 'w'))
        # --- no-input survival (should be short: going straight is rarely safe) ---
        idle = []
        for _ in range(3):
            await restart(page); t0 = time.time()
            st = await wait_state(page, lambda s: s['state'] != 'Playing', 60)
            idle.append(round(time.time() - t0, 1))
        check('holding straight with no taps dies quickly (anti-camping)', max(idle) < 20, f'idle survival times {idle}s (first 8 s are a warm-up)')
        allerr += errors; await ctx.close()

        # --- touch + tall phone + tablet ---
        ctx, page, errors = await boot(browser, 360, 800, touch=True); allerr += errors
        x0 = (await S(page))['x']; await hold_start(page, 'R', touch=True); await asyncio.sleep(0.4); x1 = (await S(page))['x']
        await hold_end(page, touch=True); await asyncio.sleep(0.15); x2 = (await S(page))['x']; await asyncio.sleep(0.3); x3 = (await S(page))['x']
        check('touchscreen: hold steers, release straightens', x1 - x0 > 60 and abs(x3 - x2) < 0.5, f'{x0:.0f} -> {x1:.0f}, then {x2:.0f} -> {x3:.0f}')
        await ctx.close()
        ctx, page, errors = await boot(browser, 800, 1280); allerr += errors
        st = await S(page); check('tablet portrait: width 720, tip at 70%', st['w'] == 720 and abs(st['tipY'] - st['h'] * 0.7) < 0.5, f"{st['w']}x{st['h']:.0f}")
        await page.screenshot(path=f'{SHOTS}/p2_05_tablet.png'); await ctx.close()
        allerr = [e for e in allerr if 'api.gdevelop-app.com/analytics' not in e and 'bridge.playgama.com' not in e and 'ERR_TUNNEL_CONNECTION_FAILED' not in e]
        check('no runtime errors in console (ignoring GDevelop analytics ping blocked by sandbox)', not allerr, '; '.join(allerr[:3]))
        await browser.close()
    srv.shutdown()
    print(f"\n{sum(r[1] for r in results)}/{len(results)} checks passed")
asyncio.run(main())
