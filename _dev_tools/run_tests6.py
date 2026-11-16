# Sound + human-made art checks: audio files load, sounds fire on gameplay events, mute button works and persists.
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, 'run_tests5.py')).read().rsplit('async def main():', 1)[0].replace(
    "HERE = os.path.dirname(os.path.abspath(__file__))", f"HERE = {HERE!r}"))
SND = '''() => { const sm = window.__game.getSoundManager();
  if (!sm.__spy) { sm.__spy = []; const orig = sm.playSound.bind(sm); sm.playSound = (name, ...a) => { sm.__spy.push(name); return orig(name, ...a); }; }
  return { count: sm.__spy.length, played: sm.__spy.slice(), vol: sm.getGlobalVolume() }; }'''
def mk(obj, x, ahead, extra=''):
    return '''() => { %s const o = sc.createObject('%s'); o.setX(%s); o.getVariables().get('WorldY').setNumber(V('CrackWorldY').getAsNumber() + %f); %s return o.id; }''' % (PRE, obj, x, ahead, extra)
async def snd(page): return await page.evaluate(SND)
async def main():
    allerr, failed_req = [], []
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(args=['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--autoplay-policy=no-user-gesture-required'])
        ctx = await browser.new_context(viewport={'width': 405, 'height': 720}); page = await ctx.new_page(); errors = []
        page.on('console', lambda m: errors.append(m.text) if m.type == 'error' else None); page.on('pageerror', lambda e: errors.append(str(e)))
        page.on('requestfailed', lambda r: failed_req.append(r.url))
        oggs = []
        page.on('response', lambda r: oggs.append((r.url.split('/')[-1], r.status)) if r.url.endswith('.ogg') else None)
        await page.goto('http://127.0.0.1:8765/index.html'); await waitg(page, lambda s: s['scene'] == 'MainMenu', 15); await asyncio.sleep(1.5)
        ok_oggs = sorted({n for n, st in oggs if st in (200, 304)})
        check('all 12 sound files load', len(ok_oggs) == 12 and not [u for u in failed_req if u.endswith('.ogg')], ', '.join(ok_oggs))
        s = await snd(page); check('sound on by default (global volume 100)', s['vol'] == 100)
        await click_obj(page, 'MuteButton'); await asyncio.sleep(0.3); s = await snd(page)
        anim = await page.evaluate("() => window.__game.getSceneStack().getCurrentScene().getObjects('MuteButton')[0].getAnimation()")
        check('menu mute button silences everything and shows the muted icon', s['vol'] == 0 and anim == 1)
        await page.reload(); await waitg(page, lambda s: s['scene'] == 'MainMenu', 15); await asyncio.sleep(0.5); s = await snd(page)
        check('mute setting survives a reload', s['vol'] == 0)
        await click_obj(page, 'MuteButton'); await asyncio.sleep(0.3); s = await snd(page)
        check('tap again: sound back on', s['vol'] == 100)
        await to_scene(page, 'Gameplay', 'EndlessButton'); await page.evaluate(setnum('NextRowWorldY', '1e9'))
        before = (await snd(page))['count']; x0 = (await S(page))['x']
        await hold(page, 'L', 0.3); await asyncio.sleep(0.1); s = await snd(page)
        check('starting to steer plays a sound', s['count'] > before, f"{before} -> {s['count']} sounds")
        x1 = (await S(page))['x']; await click_obj(page, 'MuteButton'); await asyncio.sleep(0.4); x2 = (await S(page))['x']; s = await snd(page)
        check('HUD mute button works and is not treated as a branch tap', s['vol'] == 0 and abs(x2 - x1) < 0.01, f'x {x1:.0f} -> {x2:.0f}')
        await click_obj(page, 'MuteButton'); await asyncio.sleep(0.3)
        for obj, ahead, label in [('PowerSlow', 45, 'power-up pickup'), ('Crystal', 60, 'crystal pickup')]:
            b = (await snd(page))['count']; await page.evaluate(put(obj, 0, ahead)); await asyncio.sleep(0.8); a = (await snd(page))['count']
            check(f'{label} plays a sound', a > b, ', '.join((await snd(page))['played'][b:a]))
        b = (await snd(page))['count']; await page.evaluate(mk('Fissure', 0, 60)); await asyncio.sleep(0.8); a = (await snd(page))['count']
        check('fissure plays a sound', a > b)
        await page.screenshot(path=f'{SHOTS}/p6_play.png')
        b = (await snd(page))['count']; await page.evaluate(put('BarrierSolid', 0, 60)); await waitg(page, lambda s: s.get('state') == 'GameOver', 3); await asyncio.sleep(0.3)
        s = await snd(page); a = s['count']; check('crash + game-over jingle play', 'sfx_crash' in s['played'][b:] and 'jingle_gameover' in s['played'][b:], ', '.join(s['played'][b:]))
        await page.screenshot(path=f'{SHOTS}/p6_gameover.png')
        allerr += errors; await ctx.close()
        allerr = [e for e in allerr if 'api.gdevelop-app.com' not in e and 'bridge.playgama.com' not in e and 'ERR_TUNNEL' not in e]
        check('no runtime errors in console', not allerr, '; '.join(allerr[:3]))
        await browser.close()
    srv.shutdown()
    print(f"\n{sum(r[1] for r in results)}/{len(results)} checks passed")
asyncio.run(main())
