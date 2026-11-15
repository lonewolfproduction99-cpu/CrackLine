Development scaffolding used to generate and verify this project. You don't need it in GDevelop.
build_project.py  - generates game.json (events, objects, chunks) from patterns.py
make_art.py       - generates the placeholder PNGs
reachability.py   - proves every chunk sequence has a reachable safe route (180/300/420 px/s)
gdexport.cpp      - loads game.json with GDevelop's own engine (built from source), checks every
                    instruction against GDevelop's metadata, and runs the official HTML5 exporter
run_tests.py      - plays the exported build in headless Chrome (taps, touch, collisions, restart)
