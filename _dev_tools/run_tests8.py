# Playgama requirements: Bridge storage, platform pause/audio, ads (rewarded revive, interstitials), Planet Breaker
# leaderboard + tabs, Credits screen, analytics ping off. The Bridge runs from its bundled copy (platform "mock");
# ads and leaderboards are stubbed where the mock platform has none.
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, 'run_tests7.py')).read().rsplit('async def main():', 1)[0].replace(
    "HERE = os.path.dirname(os.path.abspath(__file__))", f"HERE = {HERE!r}"))
GV = "(n) => window.__game.getVariables().get(n).getAsNumber()"
async def gv(page, n): return await page.evaluate(GV, n)
async def scene(page): return (await Gs(page))['scene']
async def volume(page): return await page.evaluate("() => window.__game.getSoundManager().getGlobalVolume()")
async def tscale(page): return await page.evaluate("() => window.__game.getSceneStack().getCurrentScene().getTimeManager().getTimeScale()")
async def platform_state(page, kind, value):   # what the Bridge reports when the platform pauses / mutes the game
    await page.evaluate("([k, v]) => gdjs._playgamaBridgeExtension[k === 'pause' ? 'platformPauseStateStack' : 'platformAudioStateStack'].push(v)", [kind, value])
    await asyncio.sleep(0.3)
async def die(page):
    await page.evaluate(setnum('NextRowWorldY', '1e9')); await page.evaluate(put('BarrierSolid', 0, 50))
    return await waitg(page, lambda s: s.get('state') == 'GameOver', 4)
def lvis(name): return "() => { %s const o = sc.getObjects('%s')[0]; return o.isVisible() && sc.getLayer(o.getLayer()).isVisible(); }" % (PRE, name)
def ltext(name): return "() => { %s return sc.getObjects('%s')[0].getText(); }" % (PRE, name)

async def main():
    allerr, reqs = [], []
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(args=['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'])
        ctx = await browser.new_context(viewport={'width': 405, 'height': 720}); page = await ctx.new_page(); errors = []
        page.on('console', lambda m: errors.append(m.text) if m.type == 'error' else None); page.on('pageerror', lambda e: errors.append(str(e)))
        page.on('request', lambda r: reqs.append(r.url))
        # ---- saved progress comes from Bridge storage
        await page.goto('http://127.0.0.1:8765/index.html'); await waitg(page, lambda s: s['scene'] == 'MainMenu', 15)
        await page.evaluate("() => { localStorage.clear(); localStorage.setItem('BestEndlessDistance', '321'); localStorage.setItem('BestPlanetsBroken', '4'); localStorage.setItem('CrystalWallet', '987'); localStorage.setItem('OwnedStyles', '11000000'); localStorage.setItem('EquippedStyle', '1'); localStorage.setItem('Muted', '0'); }")
        await page.reload(); await waitg(page, lambda s: s['scene'] == 'MainMenu', 15); await prep(page); await asyncio.sleep(0.3)
        s = await Gs(page); best = await page.evaluate(ltext('MenuBestText'))
        check('progress loads from Playgama Bridge storage (best, planets, crystals, styles)', s['wallet'] == 987 and s['owned'] == '11000000' and s['equipped'] == 1 and best == 'BEST: 321 m   |   4 PLANETS', best)
        check('GAME_READY sent after progress loaded', await gv(page, 'GameReadySent') == 1)
        MUS = "() => { const sm = window.__game.getSoundManager(); const m = sm.getMusicOnChannel(0); return [window.__game.getVariables().get('CurrentMusic').getAsString(), !!m, m ? m.getLoop() : null]; }"
        await page.mouse.click(5, 5); await asyncio.sleep(0.5)
        mu = await page.evaluate(MUS); check('menu music loops on the menu', mu == ['music_menu', True, True], str(mu))
        # ---- saving goes through Bridge storage, never GDevelop storage
        await to_scene(page, 'Gameplay', 'EndlessButton'); await page.evaluate(gem(5, 0.55, 60)); await asyncio.sleep(0.8)
        mu = await page.evaluate(MUS); check('gameplay music takes over in a run', mu == ['music_game', True, True], str(mu))
        await die(page); await asyncio.sleep(0.8)
        ls = await page.evaluate("() => Object.fromEntries(Object.keys(localStorage).map(k => [k, localStorage.getItem(k)]))")
        check('crystals earned are saved to Bridge storage at game over', ls.get('CrystalWallet') == '992', str(ls.get('CrystalWallet')))
        check('nothing is written to GDevelop storage any more', not any('CracklineSave' in k for k in ls), ', '.join(ls))
        # ---- rewarded revive
        check('REVIVE - WATCH AD offered where rewarded ads exist', await page.evaluate(lvis('ReviveButton')) and await page.evaluate(ltext('ReviveLabel')) == 'REVIVE - WATCH AD')
        await page.evaluate("() => { window.__ads.mode = 'close'; }"); await click_obj(page, 'ReviveButton'); await asyncio.sleep(0.9)
        s = await Gs(page); n = await page.evaluate("() => window.__ads.rewarded")
        check('ad closed early: no revive, button offered again', n == 1 and s['state'] == 'GameOver' and await page.evaluate(ltext('ReviveLabel')) == 'REVIVE - WATCH AD')
        await page.evaluate("() => { window.__ads.mode = 'fail'; }"); await click_obj(page, 'ReviveButton'); await asyncio.sleep(0.6)
        check('no ad available: says so, no revive', (await Gs(page))['state'] == 'GameOver' and await page.evaluate(ltext('ReviveLabel')) == 'NO AD RIGHT NOW')
        await page.evaluate("() => { window.__ads.mode = 'watch'; }"); await click_obj(page, 'ReviveButton')
        await asyncio.sleep(0.2); mid = (await Gs(page))['state']
        s = await waitg(page, lambda s: s.get('state') == 'Playing', 3)
        check('revive only after the ad is watched to the end', mid == 'GameOver' and s['state'] == 'Playing')
        # ---- interstitials when leaving game over
        await asyncio.sleep(2.3); await die(page); await asyncio.sleep(0.5)
        i0 = await page.evaluate("() => window.__ads.interstitial")
        await click_obj(page, 'RestartButton'); await waitg(page, lambda s: s.get('state') == 'Playing', 3)
        i1 = await page.evaluate("() => window.__ads.interstitial")
        await die(page); await asyncio.sleep(0.5); await click_obj(page, 'MenuButton'); await waitg(page, lambda s: s['scene'] == 'MainMenu', 3)
        i2 = await page.evaluate("() => window.__ads.interstitial")
        check('interstitial requested on RESTART and on MAIN MENU (Playgama decides if it shows)', i0 == 0 and i1 == 1 and i2 == 2, f'{i0} {i1} {i2}')
        # ---- Endless has (practically) no speed cap, and a very fast frame can't skip an obstacle
        CLEAR = "() => { %s ['RockSmall','RockMedium','BarrierSolid','BarrierBreakable','Worm','Fissure','Crystal','PowerSlow','PowerStrength'].forEach(n => sc.getObjects(n).forEach(o => o.deleteFromScene(sc))); }" % PRE
        await to_scene(page, 'Gameplay', 'EndlessButton'); await page.evaluate(setnum('NextRowWorldY', '1e9')); await page.evaluate(CLEAR)
        await page.evaluate(setnum('CrackWorldY', 3000 * 20)); await page.evaluate(setnum('ScrollSpeed', 2600)); await asyncio.sleep(0.8)
        sp = (await S(page))['speed']
        check('Endless keeps speeding up past 520 (3000 m: 2620 px/s)', abs(sp - 2620.5) < 2, f'{sp:.0f} px/s')
        fps = await page.evaluate("() => window.__game.getSceneStack().getCurrentScene().getTimeManager().getElapsedTime()")
        await page.evaluate(CLEAR); await page.evaluate(put('RockSmall', 0, 500))
        s = await waitg(page, lambda s: s.get('state') == 'GameOver', 2)
        check(f'at 2620 px/s ({sp * fps / 1000:.0f} px per frame here) a small rock is still hit, not skipped', s['state'] == 'GameOver')
        await asyncio.sleep(0.8); await click_obj(page, 'MenuButton'); await waitg(page, lambda s: s['scene'] == 'MainMenu', 3)
        # ---- platform pause / audio
        await to_scene(page, 'Gameplay', 'EndlessButton'); await page.evaluate(setnum('NextRowWorldY', '1e9')); await asyncio.sleep(0.5)
        await platform_state(page, 'pause', True); a = (await S(page))['wy']; await asyncio.sleep(0.8); b = (await S(page))['wy']
        check('platform pause (tab hidden / ad open) stops the game and its sound', await tscale(page) == 0 and abs(b - a) < 0.01 and await volume(page) == 0, f'moved {b - a:.1f}px')
        await platform_state(page, 'pause', False); a = (await S(page))['wy']; await asyncio.sleep(0.5); b = (await S(page))['wy']
        check('resume: game moves and sound returns', await tscale(page) == 1 and b - a > 50 and await volume(page) == 100)
        await platform_state(page, 'audio', False); v0 = await volume(page); await platform_state(page, 'audio', True); v1 = await volume(page)
        check('platform audio off mutes, back on unmutes', v0 == 0 and v1 == 100)
        await click_obj(page, 'MuteButton'); await asyncio.sleep(0.3); await platform_state(page, 'audio', True)
        check("player's own mute still wins when the platform allows audio", await volume(page) == 0)
        await click_obj(page, 'MuteButton'); await asyncio.sleep(0.3)
        # ---- Planet Breaker leaderboard
        await page.evaluate(STUB, {'type': 'in_game', 'entries': ENTRIES})
        await die(page); await asyncio.sleep(0.4); await click_obj(page, 'MenuButton'); await waitg(page, lambda s: s['scene'] == 'MainMenu', 3)
        await to_scene(page, 'Gameplay', 'PlanetButton'); await page.evaluate(setnum('NextRowWorldY', '1e9'))
        await page.evaluate("() => { const sc = window.__game.getSceneStack().getCurrentScene(); sc.getVariables().get('PlanetsBroken').setNumber(6); }")
        await die(page); await asyncio.sleep(0.4)
        sent = await page.evaluate("() => window.__lb.scores")
        check('new Planet Breaker best goes to the "planets_broken" leaderboard', ['planets_broken', 6] in sent, str(sent))
        await click_obj(page, 'MenuButton'); await waitg(page, lambda s: s['scene'] == 'MainMenu', 3)
        await to_scene(page, 'Leaderboard', 'RankButton'); await asyncio.sleep(1.2)
        st = await page.evaluate(LBSTATE); lid = await page.evaluate("() => window.__lb.lastId")
        check('after playing Planet Breaker the board opens on PLANET BREAKER (no "m")', lid == 'planets_broken' and st['scores'][0][1] == '5120' and st['best'] == 'YOUR BEST: 6 PLANETS', f"{lid} {st['scores'][0][1]} {st['best']}")
        await page.screenshot(path=f'{SHOTS}/p8_lb_planets.png')
        await click_obj(page, 'LbTabDepth'); await asyncio.sleep(1.2); st = await page.evaluate(LBSTATE); lid = await page.evaluate("() => window.__lb.lastId")
        check('ENDLESS DEPTH tab switches to best_distance', lid == 'best_distance' and st['scores'][0][1] == '5120 m' and st['best'].startswith('YOUR BEST:') and st['best'].endswith(' m'), f"{lid} {st['scores'][0][1]}")
        L = await page.evaluate(LAYOUT % ('[""]', '^Lb(Title|TabDepth|TabPlanets|Name|Score|YourBest|BackButton)$'))
        bad = [(a['n'], b['n']) for i, a in enumerate(L['boxes']) for b in L['boxes'][i + 1:] if overlap(a, b)]
        check('leaderboard with tabs: nothing overlaps', not bad, str(bad[:3]))
        await page.screenshot(path=f'{SHOTS}/p8_lb_depth.png')
        await to_scene(page, 'MainMenu', 'LbBackButton')
        # ---- Credits
        await to_scene(page, 'Credits', 'CreditsButton'); body = await page.evaluate(ltext('CreditsBody'))
        check('CREDITS opens and names every creator and license', await scene(page) == 'Credits' and all(w in body for w in ['KENNEY', 'BEATSCRIBE', 'PLAYGAMA', 'GDEVELOP', 'CC0', 'MIT']))
        L = await page.evaluate(LAYOUT % ('[""]', '^Credits(Title|Body|BackButton)$'))
        bad = [(a['n'], b['n']) for i, a in enumerate(L['boxes']) for b in L['boxes'][i + 1:] if overlap(a, b)]
        off = [b['n'] for b in L['boxes'] if b['y0'] < 0 or b['y1'] > L['H'] or b['x0'] < 0 or b['x1'] > L['W']]
        check('credits fit on screen', not bad and not off, f'{bad} {off}')
        fs = await page.evaluate("() => { %s const o = sc.getObjects('CreditsBody')[0]; return o.getCharacterSize() * o.getScaleY(); }" % PRE)
        check('credits text is a readable size on a phone-shaped screen', fs >= 22, f'{fs:.1f}px of 720')
        await page.screenshot(path=f'{SHOTS}/p8_credits.png')
        await to_scene(page, 'MainMenu', 'CreditsBackButton'); check('BACK returns to the menu', await scene(page) == 'MainMenu')
        m = await page.evaluate(MENU); cb = await page.evaluate("() => { %s const a = sc.getObjects('CreditsButton')[0].getAABB(); return {x0: a.min[0], x1: a.max[0], y0: a.min[1], y1: a.max[1]}; }" % PRE)
        check('menu: CREDITS button overlaps nothing', not overlap(cb, m['shop']) and not overlap(cb, m['rank']) and not overlap(cb, m['mute']) and cb['y1'] <= 1280)
        await page.screenshot(path=f'{SHOTS}/p8_menu.png')
        await asyncio.sleep(3)
        check('no GDevelop analytics ping is sent', not [u for u in reqs if 'gdevelop-app.com' in u], str([u for u in reqs if 'gdevelop-app.com' in u][:2]))
        allerr += errors; await ctx.close()
        # ---- local platform without ads: revive hidden; square window menu + credits
        ctx = await browser.new_context(viewport={'width': 600, 'height': 600}); page = await ctx.new_page(); errors = []
        page.on('console', lambda m: errors.append(m.text) if m.type == 'error' else None); page.on('pageerror', lambda e: errors.append(str(e)))
        await page.goto('http://127.0.0.1:8765/index.html'); await waitg(page, lambda s: s['scene'] == 'MainMenu', 15)
        for _ in range(300):
            if await gv(page, 'ProfileLoaded') == 1: break
            await asyncio.sleep(0.05)
        await asyncio.sleep(0.3); await page.screenshot(path=f'{SHOTS}/p8_menu_square.png')
        m = await page.evaluate(MENU); cb = await page.evaluate("() => { %s const a = sc.getObjects('CreditsButton')[0].getAABB(); return {x0: a.min[0], x1: a.max[0], y0: a.min[1], y1: a.max[1]}; }" % PRE)
        H = await page.evaluate("() => window.__game.getGameResolutionHeight()")
        check('1:1 window: CREDITS button fits', cb['y1'] <= H and not overlap(cb, m['shop']) and not overlap(cb, m['mute']), f"{cb['y1']:.0f}/{H}")
        await click_obj(page, 'CreditsButton'); await waitg(page, lambda s: s['scene'] == 'Credits', 4); await asyncio.sleep(0.4)
        L = await page.evaluate(LAYOUT % ('[""]', '^Credits(Title|Body|BackButton)$'))
        off = [b['n'] for b in L['boxes'] if b['y0'] < 0 or b['y1'] > L['H'] or b['x0'] < 0 or b['x1'] > L['W']]
        bad = [(a['n'], b['n']) for i, a in enumerate(L['boxes']) for b in L['boxes'][i + 1:] if overlap(a, b)]
        check('1:1 window: credits fit', not off and not bad and len(L['boxes']) == 3, f'{off} {bad}')
        await page.screenshot(path=f'{SHOTS}/p8_credits_square.png')
        await click_obj(page, 'CreditsBackButton'); await waitg(page, lambda s: s['scene'] == 'MainMenu', 4); await asyncio.sleep(0.3)
        await click_obj(page, 'EndlessButton'); await waitg(page, lambda s: s['scene'] == 'Gameplay', 4); await asyncio.sleep(0.5)
        await die(page); await asyncio.sleep(0.5)
        check('no rewarded ads on this platform: revive button hidden', not await page.evaluate(lvis('ReviveButton')))
        allerr += errors; await ctx.close()
        allerr = [e for e in allerr if 'api.gdevelop-app.com' not in e and 'ERR_TUNNEL' not in e and 'playgama.com' not in e and 'ERR_CONNECTION' not in e]
        check('no runtime errors in console', not allerr, '; '.join(allerr[:3]))
        await browser.close()
    srv.shutdown()
    print(f"\n{sum(r[1] for r in results)}/{len(results)} checks passed")
asyncio.run(main())
