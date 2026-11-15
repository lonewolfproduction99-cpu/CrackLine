# Generates the CRACKLINE GDevelop project (game.json) — Phase 1.
# All gameplay logic is native GDevelop events (no JavaScript events).
import json, sys, uuid, os
sys.path.insert(0, os.path.dirname(__file__))
from patterns import CHUNKS, CHUNK_HEIGHT, HIT_RADIUS, IMAGE_SIZE

OUT = sys.argv[1]
NS = uuid.UUID('6f1c6c1e-3c8a-4c51-9a77-0c1a2c3b4d5e')
def uid(s): return str(uuid.uuid5(NS, s))

# ---------------------------------------------------------------- event helpers
def ins(t, *p, inv=False): return {"type": {"inverted": inv, "value": t}, "parameters": [str(x) for x in p], "subInstructions": []}
C = ins; A = ins
def ev(conds=(), acts=(), subs=()): return {"type": "BuiltinCommonInstructions::Standard", "conditions": list(conds), "actions": list(acts), "events": list(subs)}
def comment(text): return {"type": "BuiltinCommonInstructions::Comment", "color": {"b": 109, "g": 230, "r": 255, "textB": 0, "textG": 0, "textR": 0}, "comment": text, "comment2": ""}
def group(name, events, rgb=(74, 176, 228)): return {"type": "BuiltinCommonInstructions::Group", "colorR": rgb[0], "colorG": rgb[1], "colorB": rgb[2], "creationTime": 0, "name": name, "source": "", "events": events, "parameters": []}
def link(target): return {"type": "BuiltinCommonInstructions::Link", "include": {"includeConfig": 0}, "target": target}
def repeat(expr, acts=(), subs=()): return {"type": "BuiltinCommonInstructions::Repeat", "repeatExpression": expr, "conditions": [], "actions": list(acts), "events": list(subs)}

# instruction shorthands (names verified against GDevelop source metadata by tools/gdexport)
def setv(var, op, val): return A("SetNumberVariable", var, op, val)
def sets(var, val): return A("SetStringVariable", var, "=", val)
def isv(var, op, val): return C("NumberVariable", var, op, val)
def iss(var, val): return C("StringVariable", var, "=", val)
def cmp(a, op, b): return C("BuiltinCommonInstructions::CompareNumbers", a, op, b)
def setov(obj, var, op, val): return A("SetNumberObjectVariable", obj, var, op, val)
def setx(obj, val, op="="): return A("SetX", obj, op, val)
def sety(obj, val, op="="): return A("SetY", obj, op, val)
def posy(obj, op, val): return C("PosY", obj, op, val)
def create(obj, x, y, layer='""'): return A("Create", "", obj, x, y, layer)
def delete(obj): return A("Delete", obj, "")
def opacity(obj, op, val): return A("OpacityCapability::OpacityBehavior::SetValue", obj, "Opacity", op, val)
def scale(obj, op, val): return A("ScalableCapability::ScalableBehavior::SetValue", obj, "Scale", op, val)
def scalex(obj, op, val): return A("ScalableCapability::ScalableBehavior::SetX", obj, "Scale", op, val)
def scaley(obj, op, val): return A("ScalableCapability::ScalableBehavior::SetY", obj, "Scale", op, val)
def text(obj, val): return A("TextContainerCapability::TextContainerBehavior::SetValue", obj, "Text", "=", val)
PLAYING = iss("GameState", '"Playing"')
GAMEOVER = iss("GameState", '"GameOver"')

# ---------------------------------------------------------------- variables
def num(n, v): return {"name": n, "type": "number", "value": v}
def st(n, v): return {"name": n, "type": "string", "value": v}
def boo(n, v): return {"name": n, "type": "boolean", "value": v}
scene_vars = [
    # --- tuning (edit these to change the feel) ---
    num("BaseSpeed", 180),        # starting scroll speed, px/s
    num("BranchDuration", 0.18),  # seconds a branch lasts
    num("BranchDistance", 65),    # lateral px per branch
    num("BranchCooldown", 0.08),  # seconds after a branch before the next tap is accepted
    num("TipScreenRatio", 0.7),   # crack tip height on screen (0 top .. 1 bottom)
    num("EdgeMargin", 30),        # crack can't go closer than this to the screen edges
    num("PixelsPerMeter", 20),    # distance unit: 20 world px = 1 m
    num("TrailStep", 14),         # new trail segment every N px travelled
    num("TrailJitter", 6),        # random sideways offset per trail point (jaggedness)
    num("TrailMaxSegments", 160), # hard cap on live trail segments
    num("ChunkHeight", CHUNK_HEIGHT),
    num("ChunkCount", len(CHUNKS)),  # number of external layouts named Chunk0..ChunkN-1
    num("ChunkLoopStart", 1),     # after the last chunk, loop back to this one (Chunk0 = warm-up)
    num("SpawnMargin", 100),      # chunks are created this far above the top of the screen
    num("RestartDelay", 0.3),     # seconds before the restart button accepts taps
    # --- runtime state ---
    st("GameState", "Playing"),
    num("ScrollSpeed", 180),
    num("Distance", 0),
    num("CrackWorldX", 360),
    num("CrackWorldY", 0),
    num("TipScreenY", 896),
    num("BranchDirection", 0),
    num("BranchTimer", 0),
    num("BranchStartX", 0),
    num("CooldownTimer", 0),
    num("TrailLastX", 360),
    num("TrailLastWorldY", 0),
    num("TrailNewX", 0),
    num("NextChunkWorldY", 0),
    num("ChunkIndex", 0),
    num("GameOverTime", 0),
]

# ---------------------------------------------------------------- resources & objects
IMAGES = ["bg_soil", "rock_small", "rock_medium", "crack_tip", "crack_hitbox", "trail_segment", "spark", "impact_flash", "ui_overlay", "ui_button"]
resources = [{"alwaysLoaded": False, "file": f"assets/{n}.png", "kind": "image", "metadata": "", "name": n, "smoothed": True, "userAdded": True} for n in IMAGES]

def octagon(cx, cy, r):
    import math
    return [{"x": round(cx + r * math.cos(math.pi / 8 + i * math.pi / 4), 2), "y": round(cy + r * math.sin(math.pi / 8 + i * math.pi / 4), 2)} for i in range(8)]

def sprite(name, image, origin=(0, 0), center=None, mask=None, variables=()):
    return {"adaptCollisionMaskAutomatically": False, "assetStoreId": "", "name": name, "type": "Sprite", "updateIfNotVisible": False,
            "variables": list(variables), "effects": [], "behaviors": [],
            "animations": [{"name": "", "useMultipleDirections": False, "directions": [{"looping": False, "timeBetweenFrames": 0.08, "sprites": [{
                "hasCustomCollisionMask": mask is not None, "image": image, "points": [],
                "originPoint": {"name": "origine", "x": origin[0], "y": origin[1]},
                "centerPoint": {"automatic": center is None, "name": "centre", "x": (center or (0, 0))[0], "y": (center or (0, 0))[1]},
                "customCollisionMask": [mask] if mask else []}]}]}]}

def textobj(name, s, size, rgb="255;240;214", bold=True, align="center"):
    r, g, b = [int(x) for x in rgb.split(";")]
    return {"assetStoreId": "", "bold": bold, "italic": False, "name": name, "smoothed": True, "type": "TextObject::Text", "underlined": False,
            "variables": [], "effects": [], "behaviors": [], "string": s, "font": "", "textAlignment": align, "characterSize": size,
            "color": {"r": r, "g": g, "b": b},
            "content": {"bold": bold, "isOutlineEnabled": True, "isShadowEnabled": True, "italic": False, "outlineColor": "70;24;8", "outlineThickness": 4,
                        "shadowAngle": 90, "shadowBlurRadius": 2, "shadowColor": "0;0;0", "shadowDistance": 4, "shadowOpacity": 120, "smoothed": True,
                        "underlined": False, "text": s, "font": "", "textAlignment": align, "characterSize": size, "color": rgb}}

obstacle_vars = [num("WorldY", 0), boo("Ready", False)]
objects = [
    {"assetStoreId": "", "name": "Background", "type": "TiledSpriteObject::TiledSprite", "texture": "bg_soil", "width": 720, "height": 3000,
     "variables": [], "effects": [], "behaviors": []},
    sprite("RockSmall", "rock_small", origin=(38, 38), mask=octagon(38, 38, HIT_RADIUS["RockSmall"] / 0.9239), variables=obstacle_vars),
    sprite("RockMedium", "rock_medium", origin=(58, 58), mask=octagon(58, 58, HIT_RADIUS["RockMedium"] / 0.9239), variables=obstacle_vars),
    sprite("TrailSegment", "trail_segment", origin=(0, 12), center=(0, 12), variables=[num("WorldY", 0)]),
    sprite("CrackTip", "crack_tip", origin=(32, 32)),
    sprite("CrackHitbox", "crack_hitbox", origin=(6, 6)),
    sprite("Spark", "spark", origin=(6, 6), variables=[num("VX", 0), num("VY", 0), num("Life", 0.35)]),
    sprite("ImpactFlash", "impact_flash", origin=(64, 64)),
    textobj("DistanceText", "DISTANCE: 0000 m", 38),
    textobj("HintText", "TAP LEFT OR RIGHT TO BRANCH", 30, rgb="255;230;170"),
    sprite("Overlay", "ui_overlay"),
    textobj("GameOverTitle", "GAME OVER", 84, rgb="255;214;120"),
    textobj("FinalDistanceText", "DISTANCE: 0000 m", 44),
    sprite("RestartButton", "ui_button", origin=(180, 55)),
    textobj("RestartLabel", "RESTART", 48, rgb="80;26;6"),
]
# Note: the octagon radius above is set so the octagon's *inscribed* circle equals HIT_RADIUS.
# The hit polygon is deliberately smaller than the painted rock (forgiving).

folders = {"folderName": "__ROOT", "children": [
    {"folderName": "World", "children": [{"objectName": "Background"}]},
    {"folderName": "Crack", "children": [{"objectName": n} for n in ["CrackTip", "CrackHitbox", "TrailSegment", "Spark", "ImpactFlash"]]},
    {"folderName": "Obstacles", "children": [{"objectName": "RockSmall"}, {"objectName": "RockMedium"}]},
    {"folderName": "UI", "children": [{"objectName": n} for n in ["DistanceText", "HintText", "Overlay", "GameOverTitle", "FinalDistanceText", "RestartButton", "RestartLabel"]]},
]}
groups = [{"name": "Obstacles", "objects": [{"name": "RockSmall"}, {"name": "RockMedium"}]}]

def inst(name, x, y, z=0, layer="", w=0, h=0, key=None):
    return {"angle": 0, "customSize": bool(w), "height": h, "layer": layer, "locked": False, "name": name,
            "persistentUuid": uid(key or f"{name}-{x}-{y}-{layer}"), "width": w, "x": x, "y": y, "zOrder": z,
            "numberProperties": [], "stringProperties": [], "initialVariables": []}

instances = [
    inst("Background", 0, -800, z=-10, w=720, h=3200),
    inst("CrackTip", 360, 896, z=10),
    inst("CrackHitbox", 360, 896, z=11),
    inst("DistanceText", 140, 50, layer="HUD", z=1),
    inst("HintText", 90, 1040, layer="HUD", z=1),
    inst("Overlay", 0, -400, layer="GameOver", z=0, w=720, h=3000),
    inst("GameOverTitle", 130, 330, layer="GameOver", z=1),
    inst("FinalDistanceText", 150, 470, layer="GameOver", z=1),
    inst("RestartButton", 360, 650, layer="GameOver", z=1),
    inst("RestartLabel", 270, 618, layer="GameOver", z=2),
]

def layer(name, visible=True):
    return {"ambientLightColorB": 200, "ambientLightColorG": 200, "ambientLightColorR": 200, "camera3DFarPlaneDistance": 10000,
            "camera3DFieldOfView": 45, "camera3DNearPlaneDistance": 3, "cameraType": "", "followBaseLayerCamera": False,
            "isLightingLayer": False, "isLocked": False, "name": name, "renderingType": "", "visibility": visible,
            "cameras": [{"defaultSize": True, "defaultViewport": True, "height": 0, "viewportBottom": 1, "viewportLeft": 0, "viewportRight": 1, "viewportTop": 0, "width": 0}],
            "effects": []}

# ---------------------------------------------------------------- EVENTS
CLAMPX = "clamp({}, EdgeMargin, SceneWindowWidth() - EdgeMargin)"
TOUCHX = 'TouchX(StartedTouchOrMouseId(0), "")'
def screen_y(world): return f"TipScreenY - ({world} - CrackWorldY)"

ev_gamestate = [
    comment("GAME STATE — scene setup, game over overlay and restart. GameState is \"Playing\" or \"GameOver\"."),
    group("Scene start", [
        ev([C("SceneJustBegins", "")], [
            setv("TipScreenY", "=", "SceneWindowHeight() * TipScreenRatio"),
            setv("CrackWorldX", "=", "SceneWindowWidth() / 2"),
            setv("CrackWorldY", "=", "0"),
            setv("ScrollSpeed", "=", "BaseSpeed"),
            setv("TrailLastX", "=", "CrackWorldX"),
            setv("TrailLastWorldY", "=", "CrackWorldY"),
            setv("NextChunkWorldY", "=", "TipScreenY"),
            setv("ChunkIndex", "=", "0"),
            sets("GameState", '"Playing"'),
            A("HideLayer", "", '"GameOver"'),
            A("Hide", "CrackHitbox"),
            opacity("Overlay", "=", "170"),
            sety("HintText", "SceneWindowHeight() * 0.82"),
            sety("GameOverTitle", "SceneWindowHeight() * 0.26"),
            sety("FinalDistanceText", "SceneWindowHeight() * 0.37"),
            sety("RestartButton", "SceneWindowHeight() * 0.52"),
            sety("RestartLabel", "RestartButton.Y() - 32"),
        ]),
    ]),
    group("Game over", [
        comment("Count time spent on the game over screen (prevents a frantic tap from restarting instantly)."),
        ev([GAMEOVER], [setv("GameOverTime", "+", "TimeDelta()")]),
        comment("Restart: tap/click the RESTART button. Restarting the scene resets every scene variable to its default."),
        ev([GAMEOVER, isv("GameOverTime", ">=", "RestartDelay"), C("HasAnyTouchOrMouseStarted", ""),
            C("CollisionPoint", "RestartButton", 'TouchX(StartedTouchOrMouseId(0), "GameOver")', 'TouchY(StartedTouchOrMouseId(0), "GameOver")')],
           [A("Scene", "", '"Gameplay"', "")]),
        comment("Impact flash fades out and grows."),
        ev([], [opacity("ImpactFlash", "-", "900 * TimeDelta()"), scale("ImpactFlash", "+", "4 * TimeDelta()")]),
        ev([C("OpacityCapability::OpacityBehavior::Value", "ImpactFlash", "Opacity", "<=", "0")], [delete("ImpactFlash")]),
    ]),
]

spark_burst = lambda count, vx, vy: repeat(count, [
    create("Spark", "CrackWorldX", "TipScreenY"),
    setov("Spark", "VX", "=", vx), setov("Spark", "VY", "=", vy),
    setov("Spark", "Life", "=", "RandomFloatInRange(0.2, 0.4)"),
])

ev_movement = [
    comment("CRACK MOVEMENT — the crack tip stays at TipScreenY; the world scrolls instead. CrackWorldY = distance travelled upward in px."),
    group("Input (tap / click)", [
        comment("One tap = one branch. Taps during a branch or the short cooldown are ignored (no queueing). Left half = left, right half = right."),
        ev([PLAYING, C("HasAnyTouchOrMouseStarted", ""), isv("BranchDirection", "=", "0"), isv("CooldownTimer", "<=", "0")], [], [
            ev([cmp(TOUCHX, "<", "SceneWindowWidth() / 2")], [setv("BranchDirection", "=", "-1")]),
            ev([cmp(TOUCHX, ">=", "SceneWindowWidth() / 2")], [setv("BranchDirection", "=", "1")]),
            ev([], [setv("BranchTimer", "=", "0"), setv("BranchStartX", "=", "CrackWorldX"), A("Hide", "HintText")]),
            spark_burst("5", "-BranchDirection * RandomFloatInRange(60, 200)", "RandomFloatInRange(-140, 40)"),
        ]),
    ]),
    group("Branch motion", [
        comment("Lateral offset follows an ease-out curve over BranchDuration, so the branch starts fast (responsive) and lands softly. Position is computed from elapsed time, so the total distance is frame-rate independent. Clamped to the screen so the crack can never get stuck."),
        ev([C("NumberVariable", "CooldownTimer", ">", "0")], [setv("CooldownTimer", "-", "TimeDelta()")]),
        ev([PLAYING, C("NumberVariable", "BranchDirection", "!=", "0")], [setv("BranchTimer", "+", "TimeDelta()")], [
            ev([isv("BranchTimer", "<", "BranchDuration")],
               [setv("CrackWorldX", "=", CLAMPX.format("BranchStartX + BranchDirection * BranchDistance * (1 - pow(1 - BranchTimer / BranchDuration, 2))"))]),
            ev([isv("BranchTimer", ">=", "BranchDuration")],
               [setv("CrackWorldX", "=", CLAMPX.format("BranchStartX + BranchDirection * BranchDistance")),
                setv("BranchDirection", "=", "0"), setv("CooldownTimer", "=", "BranchCooldown")]),
        ]),
    ]),
    group("Forward motion and scrolling", [
        ev([PLAYING], [
            setv("CrackWorldY", "+", "ScrollSpeed * TimeDelta()"),
            setv("Distance", "=", "floor(CrackWorldY / PixelsPerMeter)"),
            A("TiledSpriteObject::YOffset", "Background", "=", "-CrackWorldY"),
        ]),
        comment("Place the visual tip and the (hidden) hitbox on the crack's logical position."),
        ev([], [setx("CrackTip", "CrackWorldX"), sety("CrackTip", "TipScreenY"),
                setx("CrackHitbox", "CrackWorldX"), sety("CrackHitbox", "TipScreenY")]),
        ev([PLAYING], [scale("CrackTip", "=", "1 + 0.12 * sin(TimeFromStart() * 14)")]),
    ]),
]

ev_trail = [
    comment("FRACTURE TRAIL — visual only (never tested for collisions). A segment is laid every TrailStep px from the last trail point to the current (slightly jittered) tip position, then scrolls with the world."),
    group("Lay segments", [
        ev([PLAYING, cmp("DistanceBetweenPositions(TrailLastX, TrailLastWorldY, CrackWorldX, CrackWorldY)", ">=", "TrailStep"),
            C("SceneInstancesCount", "", "TrailSegment", "<", "TrailMaxSegments")], [
            setv("TrailNewX", "=", "CrackWorldX + RandomFloatInRange(-TrailJitter, TrailJitter)"),
            create("TrailSegment", "TrailLastX", screen_y("TrailLastWorldY")),
            setov("TrailSegment", "WorldY", "=", "TrailLastWorldY"),
            A("SetAngle", "TrailSegment", "=", "ToDeg(atan2(-(CrackWorldY - TrailLastWorldY), TrailNewX - TrailLastX))"),
            scalex("TrailSegment", "=", "(DistanceBetweenPositions(TrailLastX, TrailLastWorldY, TrailNewX, CrackWorldY) + 2) / 32"),
            scaley("TrailSegment", "=", "RandomFloatInRange(0.75, 1.15)"),
            A("SetZOrder", "TrailSegment", "=", "1"),
            setv("TrailLastX", "=", "TrailNewX"),
            setv("TrailLastWorldY", "=", "CrackWorldY"),
        ]),
    ]),
    group("Scroll and clean up", [
        ev([], [sety("TrailSegment", screen_y("TrailSegment.WorldY"))]),
        ev([posy("TrailSegment", ">", "SceneWindowHeight() + 40")], [delete("TrailSegment")]),
    ]),
    group("Sparks", [
        comment("Small sparks when the crack changes direction (or breaks). Cheap: a handful of sprites moved by events, deleted after ~0.3 s."),
        ev([], [setx("Spark", "Spark.VX * TimeDelta()", op="+"), sety("Spark", "(Spark.VY + ScrollSpeed) * TimeDelta()", op="+"),
                setov("Spark", "Life", "-", "TimeDelta()"), opacity("Spark", "=", "clamp(Spark.Life / 0.3, 0, 1) * 255"), A("SetZOrder", "Spark", "=", "9")]),
        ev([C("NumberObjectVariable", "Spark", "Life", "<=", "0")], [delete("Spark")]),
    ]),
]

ev_spawner = [
    comment("OBSTACLE SPAWNER (Phase 1: hand-made chunks). Each chunk is an external layout named Chunk0, Chunk1, ... that is ChunkHeight px tall. Edit them visually in the editor (Project manager > External layouts). Chunk0 is a warm-up; after the last one the sequence loops back to ChunkLoopStart."),
    group("Spawn next chunk", [
        ev([PLAYING, cmp("CrackWorldY + TipScreenY + SpawnMargin", ">=", "NextChunkWorldY")], [
            A("BuiltinExternalLayouts::CreateObjectsFromExternalLayout", "", '"Chunk" + ToString(ChunkIndex)', "0",
              "TipScreenY - (NextChunkWorldY - CrackWorldY) - ChunkHeight", "0"),
            setv("NextChunkWorldY", "+", "ChunkHeight"),
            setv("ChunkIndex", "+", "1"),
        ], [
            ev([isv("ChunkIndex", ">=", "ChunkCount")], [setv("ChunkIndex", "=", "ChunkLoopStart")]),
        ]),
        comment("Freshly created obstacles: record their logical world position once."),
        ev([C("BooleanObjectVariable", "Obstacles", "Ready", "False", "")], [
            setov("Obstacles", "WorldY", "=", "CrackWorldY + TipScreenY - Obstacles.Y()"),
            A("SetBooleanObjectVariable", "Obstacles", "Ready", "True", ""),
        ]),
    ]),
    group("Scroll and clean up", [
        ev([], [sety("Obstacles", screen_y("Obstacles.WorldY"))]),
        ev([posy("Obstacles", ">", "SceneWindowHeight() + 120")], [delete("Obstacles")]),
    ]),
]

ev_collisions = [
    comment("COLLISIONS — only the small hidden CrackHitbox at the tip is tested, against the Obstacles group (simple octagon masks). The trail never collides."),
    ev([PLAYING, C("CollisionNP", "CrackHitbox", "Obstacles", "", "", "")], [
        sets("GameState", '"GameOver"'),
        setv("BranchDirection", "=", "0"),
        create("ImpactFlash", "CrackWorldX", "TipScreenY"),
        A("SetZOrder", "ImpactFlash", "=", "12"),
        A("ChangeColor", "CrackTip", '"255;120;90"'),
        text("FinalDistanceText", '"DISTANCE: " + ToString(Distance) + " m"'),
        A("ShowLayer", "", '"GameOver"'),
        A("Hide", "HintText"),
    ], [
        spark_burst("12", "RandomFloatInRange(-260, 260)", "RandomFloatInRange(-320, 120)"),
        ev([], [A("SetCenterX", "FinalDistanceText", "=", "SceneWindowWidth() / 2")]),
    ]),
]

ev_scoring = [
    comment("SCORING / HUD — distance is derived from the logical world position (CrackWorldY), not from frame counts."),
    ev([], [text("DistanceText", '"DISTANCE: " + StrRepeat("0", max(0, 4 - StrLength(ToString(Distance)))) + ToString(Distance) + " m"')]),
]

external_events = [
    ("EV_GameState", ev_gamestate), ("EV_CrackMovement", ev_movement), ("EV_ObstacleSpawner", ev_spawner),
    ("EV_Trail", ev_trail), ("EV_Collisions", ev_collisions), ("EV_Scoring", ev_scoring),
]
scene_events = [comment("CRACKLINE — Phase 1 prototype. Each system lives in its own external events sheet (Project manager > External events). Order matters: state, movement, spawning, trail, collisions, HUD.")] + \
    [link(n) for n, _ in external_events]

# ---------------------------------------------------------------- external layouts (obstacle chunks)
ext_layouts = []
for i, chunk in enumerate(CHUNKS):
    ext_layouts.append({"associatedLayout": "Gameplay", "name": f"Chunk{i}",
        "instances": [inst(o, x, y, z=5, key=f"chunk{i}-{j}") for j, (o, x, y) in enumerate(chunk)],
        "editionSettings": {"grid": True, "gridType": "rectangular", "gridWidth": round(720 / 7, 3), "gridHeight": 80, "gridOffsetX": 0, "gridOffsetY": 0,
                            "gridColor": 10401023, "gridAlpha": 0.8, "snap": False, "zoomFactor": 0.5, "windowMask": True}})

ui_settings = {"grid": False, "gridType": "rectangular", "gridWidth": 32, "gridHeight": 32, "gridOffsetX": 0, "gridOffsetY": 0, "gridColor": 10401023,
               "gridAlpha": 0.8, "snap": False, "zoomFactor": 0.5, "windowMask": True}
layout = {"b": 40, "disableInputWhenNotFocused": True, "mangledName": "Gameplay", "name": "Gameplay", "r": 110, "standardSortMethod": True,
          "stopSoundsOnStartup": True, "title": "", "v": 60, "uiSettings": ui_settings, "objectsGroups": groups, "variables": scene_vars,
          "instances": instances, "objects": objects, "objectsFolderStructure": folders, "events": scene_events,
          "layers": [layer(""), layer("HUD"), layer("GameOver", visible=False)], "behaviorsSharedData": []}

project = {
    "firstLayout": "Gameplay",
    "gdVersion": {"build": 99, "major": 4, "minor": 0, "revision": 0},
    "properties": {
        "adaptGameResolutionAtRuntime": True, "antialiasingMode": "none", "antialisingEnabledOnMobile": False, "folderProject": False,
        "orientation": "portrait", "packageName": "com.lonewolfproduction.crackline", "pixelsRounding": False,
        "projectUuid": uid("project"), "scaleMode": "linear", "sizeOnStartupMode": "adaptHeight", "templateSlug": "",
        "useExternalSourceFiles": False, "version": "0.1.0", "name": "CRACKLINE", "description": "Phase 1 prototype", "author": "",
        "windowWidth": 720, "windowHeight": 1280, "latestCompilationDirectory": "", "maxFPS": 60, "minFPS": 20, "verticalSync": False,
        "platformSpecificAssets": {},
        "loadingScreen": {"backgroundColor": 2101764, "backgroundFadeInDuration": 0.2, "backgroundImageResourceName": "", "gdevelopLogoStyle": "light",
                          "logoAndProgressFadeInDuration": 0.2, "logoAndProgressLogoFadeInDelay": 0.2, "minDuration": 0, "progressBarColor": 16753190,
                          "progressBarHeight": 20, "progressBarMaxWidth": 200, "progressBarMinWidth": 40, "progressBarWidthPercent": 30,
                          "showGDevelopSplash": True, "showProgressBar": True},
        "watermark": {"placement": "bottom-left", "showWatermark": True},
        "authorIds": [], "authorUsernames": [], "categories": [], "playableDevices": ["mobile"], "extensionProperties": [],
        "platforms": [{"name": "GDevelop JS platform"}], "currentPlatform": "GDevelop JS platform"},
    "resources": {"resources": resources, "resourceFolders": []},
    "objects": [], "objectsGroups": [], "variables": [], "layouts": [layout],
    "externalEvents": [{"associatedLayout": "Gameplay", "lastChangeTimeStamp": 0, "name": n, "events": e} for n, e in external_events],
    "eventsFunctionsExtensions": [], "externalLayouts": ext_layouts, "externalSourceFiles": [],
}
os.makedirs(OUT, exist_ok=True)
with open(os.path.join(OUT, "game.json"), "w") as f: json.dump(project, f, indent=2)
print("wrote", os.path.join(OUT, "game.json"))
