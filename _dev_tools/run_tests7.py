# Playgama leaderboard checks (Bridge SDK extension). The sandbox cannot reach Playgama, so the Bridge runs
# from the extension's bundled copy (platform "mock", no leaderboard), then its leaderboard module is stubbed
# to behave like Playgama's in-game (SaaS) leaderboard.
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, 'run_tests5.py')).read().rsplit('async def main():', 1)[0].replace(
    "HERE = os.path.dirname(os.path.abspath(__file__))", f"HERE = {HERE!r}"))

STUB = '''(mode) => { window.__lbMode = mode; if (window.__lb) return true;   // Bridge wraps methods once, so stub once and read the mode live
  const lb = window.bridge.leaderboards; window.__lb = {scores: [], popups: 0, gets: 0}; const M = () => window.__lbMode;
  Object.defineProperty(lb, 'type', {get: () => M().type, configurable: true});
  lb.setScore = (id, score) => { window.__lb.scores.push([id, score]); return Promise.resolve(); };
  lb.showNativePopup = (id) => { window.__lb.popups++; return Promise.resolve(); };
  lb.getEntries = (id) => { window.__lb.gets++; window.__lb.lastId = id;
    if (M().fail) return Promise.reject(new Error('offline'));
    return new Promise(r => setTimeout(() => r(M().entries), M().delay || 300)); };
  Object.defineProperty(window.bridge.player, 'id', {get: () => 'me', configurable: true}); return true; }'''
ENTRIES = [{'id': f'p{i}', 'name': n, 'score': s, 'rank': i + 1, 'photo': ''} for i, (n, s) in enumerate(
    [('Ace', 5120), ('DeepDigger', 4380), ('', 3990), ('magma_queen', 3500), ('Bob', 3020), ('Zed', 2800),
     ('Nova', 2400), ('Kit', 2100), ('Rook', 1900), ('Pip', 1500), ('Overflow', 900), ('Extra', 500)])]
ENTRIES[2]['id'] = 'me'
LBSTATE = '''() => { %s const t = n => sc.getObjects(n).map(o => [o.getVariables().get('Row').getAsNumber(), o.getText(), o.getColor()]).sort((a, b) => a[0] - b[0]);
  return { scene: sc.getName(), status: sc.getObjects('LbStatus')[0].getText(), names: t('LbName'), scores: t('LbScore'), best: sc.getObjects('LbYourBest')[0].getText() }; }''' % PRE
MENU = '''() => { %s const o = n => { const x = sc.getObjects(n)[0]; const a = x.getAABB(); return {v: x.isVisible(), x0: a.min[0], x1: a.max[0], y0: a.min[1], y1: a.max[1]}; };
  return { ready: !!(window.bridge && window.bridge.isInitialized), platform: window.bridge && window.bridge.isInitialized ? window.bridge.platform.id : null, type: window.bridge && window.bridge.isInitialized ? window.bridge.leaderboards.type : null,
    sent: G('GameReadySent').getAsNumber(), synced: G('LeaderboardSynced').getAsNumber(), avail: V('LeaderboardAvailable').getAsNumber(),
    shop: o('ShopButton'), rank: o('RankButton'), mute: o('MuteButton'), W: sc.getGame().getGameResolutionWidth() }; }''' % PRE
def overlap(a, b): return not (a['x1'] <= b['x0'] or b['x1'] <= a['x0'] or a['y1'] <= b['y0'] or b['y1'] <= a['y0'])

async def main():
    allerr = []
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(args=['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'])
        ctx = await browser.new_context(viewport={'width': 405, 'height': 720}); page = await ctx.new_page(); errors = []
        page.on('console', lambda m: errors.append(m.text) if m.type == 'error' else None); page.on('pageerror', lambda e: errors.append(str(e)))
        await page.goto('http://127.0.0.1:8765/index.html'); await waitg(page, lambda s: s['scene'] == 'MainMenu', 15)
        t0 = time.time()
        while time.time() - t0 < 12 and not (await page.evaluate(MENU))['ready']: await asyncio.sleep(0.2)
        await asyncio.sleep(0.3); m = await page.evaluate(MENU)
        check('Playgama Bridge loads and initializes (bundled copy, CDN unreachable here)', m['ready'], f"platform={m['platform']}")
        check('GAME_READY sent once the Bridge is ready', m['sent'] == 1)
        check('no leaderboard here (mock platform): LEADERBOARD hidden, SHOP full width and centred',
              m['type'] == 'not_available' and not m['rank']['v'] and abs((m['shop']['x0'] + m['shop']['x1']) / 2 - m['W'] / 2) < 2 and m['shop']['x1'] - m['shop']['x0'] > 300, str(m['type']))
        # Behave like Playgama: in-game (SaaS) leaderboard
        await page.evaluate(STUB, {'type': 'in_game', 'entries': ENTRIES}); await asyncio.sleep(0.3); m = await page.evaluate(MENU)
        check('in-game leaderboard: LEADERBOARD button shown next to SHOP, nothing overlaps',
              m['rank']['v'] and not overlap(m['rank'], m['shop']) and not overlap(m['rank'], m['mute']) and m['rank']['x1'] <= m['W'] and m['shop']['x0'] >= 0)
        await page.screenshot(path=f'{SHOTS}/p7_menu.png')
        # New Endless best is submitted
        await to_scene(page, 'Gameplay', 'EndlessButton'); await page.evaluate(setnum('NextRowWorldY', '1e9')); await asyncio.sleep(2.5)
        await page.evaluate(put('BarrierSolid', 0, 60)); await waitg(page, lambda s: s.get('state') == 'GameOver', 4); await asyncio.sleep(0.4)
        best = await page.evaluate("() => window.__game.getVariables().get('BestEndlessDistance').getAsNumber()")
        sc_ = await page.evaluate("() => window.__lb.scores")
        check('new Endless best is sent to the leaderboard "best_distance"', best > 0 and sc_ and sc_[-1] == ['best_distance', best], f'best={best} sent={sc_}')
        n = len(sc_)
        await to_scene(page, 'Gameplay', 'RestartButton'); await page.evaluate(setnum('NextRowWorldY', '1e9')); await asyncio.sleep(0.4)
        await page.evaluate(put('BarrierSolid', 0, 40)); await waitg(page, lambda s: s.get('state') == 'GameOver', 4); await asyncio.sleep(0.4)
        check('a run that does not beat the best sends nothing', len(await page.evaluate("() => window.__lb.scores")) == n)
        await to_scene(page, 'MainMenu', 'MenuButton')
        # Leaderboard scene
        await page.evaluate(STUB, {'type': 'in_game', 'entries': ENTRIES, 'delay': 1500})
        await to_scene(page, 'Leaderboard', 'RankButton')
        st = await page.evaluate(LBSTATE); check('leaderboard opens with LOADING... while entries load', st['status'] == 'LOADING...', st['status'])
        await asyncio.sleep(1.8); st = await page.evaluate(LBSTATE)
        names, scores = [x[1] for x in st['names']], [x[1] for x in st['scores']]
        check('top 10 rows filled in rank order (rank. NAME / distance m)', names[0] == '1.  ACE' and scores[0] == '5120 m' and names[9] == '10.  PIP' and st['status'] == '',
              ' | '.join(f'{a} {b}' for a, b in zip(names[:4], scores[:4])))
        check('only 10 rows shown even when there are more entries', len([x for x in names if x]) == 10)
        check('blank player name shows as PLAYER; long names are cut', names[2] == '3.  PLAYER' and names[3] == '4.  MAGMA_QUEEN', f'{names[2]} / {names[3]}')
        check('your own row is highlighted green', st['names'][2][2] == '120;255;160' and st['scores'][2][2] == '120;255;160' and st['names'][0][2] != '120;255;160')
        check('your best shown under the table', st['best'] == f'YOUR BEST: {best} m', st['best'])
        lid = await page.evaluate("() => window.__lb.lastId"); check('entries requested for "best_distance"', lid == 'best_distance')
        L = await page.evaluate(LAYOUT % ('[""]', '^Lb(Title|Subtitle|Name|Score|YourBest|BackButton)$'))
        bad = [(a['n'], b['n']) for i, a in enumerate(L['boxes']) for b in L['boxes'][i + 1:] if overlap(a, b)]
        check('portrait: leaderboard texts do not overlap', not bad, str(bad[:3]))
        await page.screenshot(path=f'{SHOTS}/p7_leaderboard.png')
        await to_scene(page, 'MainMenu', 'LbBackButton'); check('BACK returns to the menu', (await Gs(page))['scene'] == 'MainMenu')
        await page.evaluate(STUB, {'type': 'in_game', 'entries': []}); await to_scene(page, 'Leaderboard', 'RankButton'); await asyncio.sleep(0.8)
        st = await page.evaluate(LBSTATE); check('empty leaderboard says NO SCORES YET', st['status'].startswith('NO SCORES YET'), st['status'])
        await to_scene(page, 'MainMenu', 'LbBackButton')
        await page.evaluate(STUB, {'type': 'in_game', 'fail': True}); await to_scene(page, 'Leaderboard', 'RankButton'); await asyncio.sleep(0.6)
        st = await page.evaluate(LBSTATE); check('network failure says COULDN\'T LOAD', st['status'].startswith("COULDN'T LOAD"), st['status'])
        await page.screenshot(path=f'{SHOTS}/p7_failed.png')
        await to_scene(page, 'MainMenu', 'LbBackButton')
        await page.evaluate(STUB, {'type': 'native_popup', 'entries': []}); await asyncio.sleep(0.2)
        await click_obj(page, 'RankButton'); await asyncio.sleep(0.5)
        r = await page.evaluate("() => { %s return [window.__lb.popups, sc.getName()]; }" % PRE)
        check('platforms with their own popup (Facebook): button opens it, no scene change', r[0] == 1 and r[1] == 'MainMenu')
        await page.evaluate(STUB, {'type': 'native', 'entries': []}); await asyncio.sleep(0.3); m = await page.evaluate(MENU)
        check('platforms that show the board themselves: button hidden', not m['rank']['v'])
        allerr += errors; await ctx.close()
        # square window, fresh page
        ctx = await browser.new_context(viewport={'width': 600, 'height': 600}); page = await ctx.new_page(); errors = []
        page.on('console', lambda m: errors.append(m.text) if m.type == 'error' else None); page.on('pageerror', lambda e: errors.append(str(e)))
        await page.goto('http://127.0.0.1:8765/index.html'); await waitg(page, lambda s: s['scene'] == 'MainMenu', 15)
        t0 = time.time()
        while time.time() - t0 < 12 and not (await page.evaluate(MENU))['ready']: await asyncio.sleep(0.2)
        await page.evaluate(STUB, {'type': 'in_game', 'entries': ENTRIES}); await asyncio.sleep(0.5)
        m = await page.evaluate(MENU); check('1:1 window: menu buttons still fit', m['rank']['v'] and not overlap(m['rank'], m['mute']) and not overlap(m['rank'], m['shop']))
        await page.screenshot(path=f'{SHOTS}/p7_menu_square.png')
        await to_scene(page, 'Leaderboard', 'RankButton'); await asyncio.sleep(1.2)
        L = await page.evaluate(LAYOUT % ('[""]', '^Lb(Title|Subtitle|Name|Score|YourBest|BackButton)$'))
        bad = [(a['n'], b['n']) for i, a in enumerate(L['boxes']) for b in L['boxes'][i + 1:] if overlap(a, b)]
        off = [b['n'] for b in L['boxes'] if b['y0'] < 0 or b['y1'] > L['H'] or b['x0'] < 0 or b['x1'] > L['W']]
        check('1:1 window: leaderboard fits with no overlaps', (await Gs(page))['scene'] == 'Leaderboard' and len(L['boxes']) >= 24 and not bad and not off, f'{len(L["boxes"])} boxes {bad[:3]} {off[:3]}')
        await page.screenshot(path=f'{SHOTS}/p7_leaderboard_square.png')
        allerr += errors; await ctx.close()
        allerr = [e for e in allerr if 'api.gdevelop-app.com' not in e and 'ERR_TUNNEL' not in e and 'playgama.com' not in e and 'ERR_CONNECTION' not in e]
        check('no runtime errors in console', not allerr, '; '.join(allerr[:3]))
        await browser.close()
    srv.shutdown()
    print(f"\n{sum(r[1] for r in results)}/{len(results)} checks passed")
asyncio.run(main())
