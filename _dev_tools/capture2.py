import asyncio, sys
from playwright.async_api import async_playwright
HIDE = """() => { const sc = window.__game.getSceneStack().getCurrentScene(); sc.getLayer('HUD').show(false);
  sc.getObjects('ShieldGlow').forEach(o => o.hide(true)); sc.getVariables().get('InvulnerabilityRemaining').setNumber(999);
  document.querySelectorAll('div').forEach(d => { if ((d.textContent || '').includes('Made with')) d.style.display = 'none'; }); }"""
async def main():
    async with async_playwright() as pw:
        b = await pw.chromium.launch(args=['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'])
        ctx = await b.new_context(viewport={'width': 540, 'height': 960}, device_scale_factor=2); p = await ctx.new_page()
        await p.goto('http://127.0.0.1:8792/index.html')
        for _ in range(300):
            if await p.evaluate("() => !!(window.__game && window.__game.getVariables().get('ProfileLoaded').getAsNumber() === 1)"): break
            await asyncio.sleep(0.05)
        await asyncio.sleep(1)
        for run, style in enumerate([4, 7, 1]):
            await p.evaluate(f"""() => {{ const g = window.__game; g.getVariables().get('GameMode').setString('Endless'); g.getVariables().get('EquippedStyle').setNumber({style});
                g.getVariables().get('OwnedStyles').setString('11111111'); g.getSceneStack().replace('Gameplay', true); }}""")
            await asyncio.sleep(0.5); await p.evaluate(HIDE)
            k = 0
            for i in range(14):
                side = 0.25 if i % 2 == 0 else 0.75
                await p.mouse.move(540 * side, 700); await p.mouse.down(); await asyncio.sleep(0.35); await p.mouse.up(); await asyncio.sleep(0.45)
                await p.evaluate(HIDE)
                if i >= 6:
                    await p.evaluate("() => window.__game.getSceneStack().getCurrentScene().getVariables().get('InvulnerabilityRemaining').setNumber(0)")
                    await asyncio.sleep(0.07)
                    await p.screenshot(path=f'/tmp/covers/g_{run}_{i}.png')
                    await p.evaluate(HIDE)
        await b.close()
asyncio.run(main())
