Development scaffolding used to generate and verify this project. You don't need it in GDevelop.
build_project.py   - generates game.json (all events, objects, variables)
gen_params.py      - generator tuning shared by the builder and the simulator
gen_sim.py         - mirrors the in-game row generator and brute-force searches every tap timing to prove a route exists (60 runs x 5 min passed)
harvest_check.py   - same search, run on obstacle layouts recorded from the real running game
make_art.py / make_art2.py - placeholder art
gdexport.cpp       - loads game.json with GDevelop's own engine (built from source), checks every instruction, runs the official HTML5 exporter
run_tests2.py      - automated play-tests of the exported build in headless Chrome
make_art3.py       - Phase 3 art (planets, themes, shield)
run_tests3.py      - Phase 3 play-tests: menu, planets, split, revive, resolutions
gen_sim3.py        - generator safety search incl. worms and fissures (any-position recovery), up to 520 px/s
make_art4.py       - worm and fissure art
run_tests4.py      - tests: 1k planet progression, fissures, worms
make_art5.py       - crack style art (trails, tips) and shop card
run_tests5.py      - tests: crystals as points, shop buy/equip/persist, layouts
