# Generates the CRACKLINE GDevelop project (game.json) — Phase 2.
# All gameplay logic is native GDevelop events (no JavaScript events).
import json, sys, uuid, os
sys.path.insert(0, os.path.dirname(__file__))
from gen_params import P, HIT, IMG, LANE_COUNT

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
TUNING = [
    ("BaseSpeed", P["BaseSpeed"]), ("MaxSpeed", P["MaxSpeed"]), ("SpeedGrowth", P["SpeedGrowth"]), ("SpeedGrowthInterval", P["SpeedGrowthInterval"]),
    ("DifficultyRampTime", P["DifficultyRampTime"]),
    ("BranchDuration", 0.15), ("BranchDistance", 130), ("BranchCooldown", 0.08),
    ("TipScreenRatio", 0.7), ("EdgeMargin", 30), ("PixelsPerMeter", 20),
    ("TrailStep", 14), ("TrailJitter", 8), ("TrailMaxSegments", 160),
    ("LaneCount", LANE_COUNT), ("SpawnMargin", 100), ("FirstRowOffset", P["FirstRowOffset"]),
    ("RowGapStart", P["RowGapStart"]), ("RowGapEnd", P["RowGapEnd"]),
    ("DensityStart", P["DensityStart"]), ("DensityEnd", P["DensityEnd"]),
    ("EmptyChanceStart", P["EmptyChanceStart"]), ("EmptyChanceEnd", P["EmptyChanceEnd"]),
    ("WallChanceStart", P["WallChanceStart"]), ("WallChanceEnd", P["WallChanceEnd"]),
    ("CrystalChanceStart", P["CrystalChanceStart"]), ("CrystalChanceEnd", P["CrystalChanceEnd"]),
    ("SolidChanceStart", P["SolidChanceStart"]), ("SolidChanceEnd", P["SolidChanceEnd"]),
    ("BreakChanceStart", P["BreakChanceStart"]), ("BreakChanceEnd", P["BreakChanceEnd"]),
    ("WallBreakableShare", P["WallBreakableShare"]),
    ("BlockerChanceStart", P["BlockerChanceStart"]), ("BlockerChanceEnd", P["BlockerChanceEnd"]), ("CorridorStayChance", P["CorridorStayChance"]), ("LaneJitterX", P["LaneJitterX"]), ("RowJitterY", P["RowJitterY"]),
    ("PowerupChance", P["PowerupChance"]), ("PowerupCooldownTime", P["PowerupCooldownTime"]),
    ("SlowTimeDuration", P["SlowTimeDuration"]), ("SlowTimeFactor", P["SlowTimeFactor"]), ("StrengthMaxCharges", P["StrengthMaxCharges"]),
    ("RestartDelay", 0.3),
]
STATE = ["ScrollSpeed", "EffectiveSpeed", "Distance", "RunTime", "DifficultyLevel", "CrackWorldX", "CrackWorldY", "TipScreenY",
         "BranchDirection", "BranchTimer", "BranchStartX", "CooldownTimer", "TrailLastX", "TrailLastWorldY", "TrailNewX",
         "NextRowWorldY", "RowWorldY", "RowGap", "SafeLane", "PrevSafeLane", "CorridorMin", "CorridorMax", "RowType", "RowRoll",
         "Density", "EmptyChance", "WallChance", "CrystalChance", "SolidChance", "BreakChance",
         "LaneIter", "LaneWidth", "BlockerChance", "CrackLane", "CorridorShift", "TypeRoll", "ObjType", "LaneX", "ObjWorldY",
         "PowerupCooldown", "SlowTimeRemaining", "StrengthCharges", "InvulnerabilityRemaining", "GameOverTime"]
scene_vars = [num(n, v) for n, v in TUNING] + [st("GameState", "Playing")] + [num(n, 0) for n in STATE] + [boo("NewBest", False)]
global_vars = [st("GameMode", "Endless"), num("BestEndlessDistance", 0)]

# ---------------------------------------------------------------- resources & objects
IMAGES = ["bg_soil", "rock_small", "rock_medium", "crack_tip", "crack_hitbox", "trail_segment", "spark", "impact_flash", "ui_overlay",
          "ui_button", "barrier_solid", "barrier_breakable", "crystal_purple", "crystal_pink", "crystal_cyan", "powerup_slow", "powerup_strength"]
resources = [{"alwaysLoaded": False, "file": f"assets/{n}.png", "kind": "image", "metadata": "", "name": n, "smoothed": True, "userAdded": True} for n in IMAGES]

import math
def octagon(cx, cy, r):   # inscribed circle radius r
    R = r / math.cos(math.pi / 8)
    return [{"x": round(cx + R * math.cos(math.pi / 8 + i * math.pi / 4), 2), "y": round(cy + R * math.sin(math.pi / 8 + i * math.pi / 4), 2)} for i in range(8)]
def rect(cx, cy, hw, hh): return [{"x": cx - hw, "y": cy - hh}, {"x": cx + hw, "y": cy - hh}, {"x": cx + hw, "y": cy + hh}, {"x": cx - hw, "y": cy + hh}]

def frame(image, origin, center=None, mask=None):
    return {"hasCustomCollisionMask": mask is not None, "image": image, "points": [],
            "originPoint": {"name": "origine", "x": origin[0], "y": origin[1]},
            "centerPoint": {"automatic": center is None, "name": "centre", "x": (center or (0, 0))[0], "y": (center or (0, 0))[1]},
            "customCollisionMask": [mask] if mask else []}
def sprite(name, image, origin=(0, 0), center=None, mask=None, variables=(), anims=None):
    anims = anims or [("", image)]
    return {"adaptCollisionMaskAutomatically": False, "assetStoreId": "", "name": name, "type": "Sprite", "updateIfNotVisible": False,
            "variables": list(variables), "effects": [], "behaviors": [],
            "animations": [{"name": an, "useMultipleDirections": False, "directions": [{"looping": False, "timeBetweenFrames": 0.08,
                            "sprites": [frame(img, origin, center, mask)]}]} for an, img in anims]}

def textobj(name, s, size, rgb="255;240;214", bold=True, align="center"):
    r, g, b = [int(x) for x in rgb.split(";")]
    return {"assetStoreId": "", "bold": bold, "italic": False, "name": name, "smoothed": True, "type": "TextObject::Text", "underlined": False,
            "variables": [], "effects": [], "behaviors": [], "string": s, "font": "", "textAlignment": align, "characterSize": size,
            "color": {"r": r, "g": g, "b": b},
            "content": {"bold": bold, "isOutlineEnabled": True, "isShadowEnabled": True, "italic": False, "outlineColor": "70;24;8", "outlineThickness": 4,
                        "shadowAngle": 90, "shadowBlurRadius": 2, "shadowColor": "0;0;0", "shadowDistance": 4, "shadowOpacity": 120, "smoothed": True,
                        "underlined": False, "text": s, "font": "", "textAlignment": align, "characterSize": size, "color": rgb}}

wvar = [num("WorldY", 0)]
objects = [
    {"assetStoreId": "", "name": "Background", "type": "TiledSpriteObject::TiledSprite", "texture": "bg_soil", "width": 720, "height": 3000,
     "variables": [], "effects": [], "behaviors": []},
    sprite("RockSmall", "rock_small", origin=(38, 38), mask=octagon(38, 38, HIT["RockSmall"][1]), variables=wvar),
    sprite("RockMedium", "rock_medium", origin=(58, 58), mask=octagon(58, 58, HIT["RockMedium"][1]), variables=wvar),
    sprite("BarrierBreakable", "barrier_breakable", origin=(56, 32), mask=rect(56, 32, HIT["BarrierBreakable"][1], HIT["BarrierBreakable"][2]), variables=wvar),
    sprite("BarrierSolid", "barrier_solid", origin=(56, 32), mask=rect(56, 32, HIT["BarrierSolid"][1], HIT["BarrierSolid"][2]), variables=wvar),
    sprite("Crystal", "crystal_purple", origin=(48, 54), mask=octagon(48, 54, HIT["Crystal"][1]), variables=wvar,
           anims=[("Purple", "crystal_purple"), ("Pink", "crystal_pink"), ("Cyan", "crystal_cyan")]),
    sprite("PowerSlow", "powerup_slow", origin=(40, 40), mask=octagon(40, 40, 36), variables=wvar),
    sprite("PowerStrength", "powerup_strength", origin=(40, 40), mask=octagon(40, 40, 36), variables=wvar),
    sprite("TrailSegment", "trail_segment", origin=(0, 24), center=(0, 24), variables=wvar),
    sprite("CrackTip", "crack_tip", origin=(64, 64)),
    sprite("CrackHitbox", "crack_hitbox", origin=(6, 6)),
    sprite("Spark", "spark", origin=(6, 6), variables=[num("VX", 0), num("VY", 0), num("Life", 0.35)]),
    sprite("ImpactFlash", "impact_flash", origin=(64, 64)),
    textobj("DistanceText", "DISTANCE: 0000 m", 38),
    textobj("BestText", "BEST: 0000 m", 26, rgb="255;220;160"),
    textobj("SlowText", "SLOW 4.0", 30, rgb="150;205;255"),
    textobj("StrengthText", "STRENGTH x3", 30, rgb="255;170;110"),
    textobj("HintText", "TAP LEFT OR RIGHT TO BRANCH", 30, rgb="255;230;170"),
    sprite("Overlay", "ui_overlay"),
    textobj("GameOverTitle", "GAME OVER", 84, rgb="255;214;120"),
    textobj("FinalDistanceText", "DISTANCE: 0000 m", 44),
    textobj("GameOverBestText", "BEST: 0000 m", 34, rgb="255;220;160"),
    textobj("NewBestText", "NEW BEST!", 40, rgb="120;255;160"),
    sprite("RestartButton", "ui_button", origin=(180, 55)),
    textobj("RestartLabel", "RESTART", 48, rgb="80;26;6"),
]
folders = {"folderName": "__ROOT", "children": [
    {"folderName": "World", "children": [{"objectName": "Background"}]},
    {"folderName": "Crack", "children": [{"objectName": n} for n in ["CrackTip", "CrackHitbox", "TrailSegment", "Spark", "ImpactFlash"]]},
    {"folderName": "Obstacles", "children": [{"objectName": n} for n in ["RockSmall", "RockMedium", "BarrierBreakable", "BarrierSolid", "Crystal"]]},
    {"folderName": "Powerups", "children": [{"objectName": "PowerSlow"}, {"objectName": "PowerStrength"}]},
    {"folderName": "UI", "children": [{"objectName": n} for n in ["DistanceText", "BestText", "SlowText", "StrengthText", "HintText", "Overlay",
                                                                   "GameOverTitle", "FinalDistanceText", "GameOverBestText", "NewBestText", "RestartButton", "RestartLabel"]]},
]}
def grp(name, objs): return {"name": name, "objects": [{"name": o} for o in objs]}
groups = [grp("Obstacles", ["RockSmall", "RockMedium", "BarrierBreakable", "BarrierSolid", "Crystal"]),
          grp("Breakable", ["RockSmall", "RockMedium", "BarrierBreakable"]),
          grp("Powerups", ["PowerSlow", "PowerStrength"])]

def inst(name, x, y, z=0, layer="", w=0, h=0):
    return {"angle": 0, "customSize": bool(w), "height": h, "layer": layer, "locked": False, "name": name,
            "persistentUuid": uid(f"{name}-{layer}"), "width": w, "x": x, "y": y, "zOrder": z,
            "numberProperties": [], "stringProperties": [], "initialVariables": []}
instances = [
    inst("Background", 0, -800, z=-10, w=720, h=3200),
    inst("CrackTip", 360, 896, z=10), inst("CrackHitbox", 360, 896, z=11),
    inst("DistanceText", 140, 40, layer="HUD", z=1), inst("BestText", 250, 92, layer="HUD", z=1),
    inst("SlowText", 30, 140, layer="HUD", z=1), inst("StrengthText", 470, 140, layer="HUD", z=1),
    inst("HintText", 90, 1040, layer="HUD", z=1),
    inst("Overlay", 0, -400, layer="GameOver", z=0, w=720, h=3000),
    inst("GameOverTitle", 130, 300, layer="GameOver", z=1), inst("FinalDistanceText", 150, 430, layer="GameOver", z=1),
    inst("GameOverBestText", 220, 500, layer="GameOver", z=1), inst("NewBestText", 250, 560, layer="GameOver", z=1),
    inst("RestartButton", 360, 700, layer="GameOver", z=1), inst("RestartLabel", 270, 668, layer="GameOver", z=2),
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
def pad4(v): return f'StrRepeat("0", max(0, 4 - StrLength(ToString({v})))) + ToString({v})'
SAVE, KEY = '"CracklineSave"', '"BestEndlessDistance"'
ENDLESS = iss("GameMode", '"Endless"')
def color(obj, rgb): return A("ChangeColor", obj, f'"{rgb}"')

spark_burst = lambda count, vx, vy, x="CrackWorldX", y="TipScreenY": repeat(count, [
    create("Spark", x, y), setov("Spark", "VX", "=", vx), setov("Spark", "VY", "=", vy),
    setov("Spark", "Life", "=", "RandomFloatInRange(0.2, 0.4)")])

ev_gamestate = [
    comment("GAME STATE — scene setup, best score loading, invulnerability timer, game over overlay and restart. GameState is \"Playing\" or \"GameOver\". GameMode (global) is \"Endless\" for now; Planet mode arrives in Phase 3 and will reuse this same scene."),
    group("Scene start", [
        ev([C("SceneJustBegins", "")], [
            setv("TipScreenY", "=", "SceneWindowHeight() * TipScreenRatio"),
            setv("LaneWidth", "=", "SceneWindowWidth() / LaneCount"),
            setv("CrackWorldX", "=", "SceneWindowWidth() / 2"), setv("CrackWorldY", "=", "0"),
            setv("ScrollSpeed", "=", "BaseSpeed"), setv("EffectiveSpeed", "=", "BaseSpeed"),
            setv("TrailLastX", "=", "CrackWorldX"), setv("TrailLastWorldY", "=", "CrackWorldY"),
            setv("NextRowWorldY", "=", "TipScreenY + FirstRowOffset"),
            setv("SafeLane", "=", "RandomInRange(0, 1) * 4 + RandomInRange(0, 1)"),   # corridor starts off-centre (lanes 0-1 or 4-5): the first rows teach branching
            setv("PowerupCooldown", "=", "6"),
            sets("GameState", '"Playing"'),
            A("HideLayer", "", '"GameOver"'),
            A("Hide", "CrackHitbox"), A("Hide", "SlowText"), A("Hide", "StrengthText"), A("Hide", "NewBestText"),
            opacity("Overlay", "=", "170"),
            sety("HintText", "SceneWindowHeight() * 0.82"),
            sety("GameOverTitle", "SceneWindowHeight() * 0.22"),
            sety("FinalDistanceText", "SceneWindowHeight() * 0.33"),
            sety("GameOverBestText", "SceneWindowHeight() * 0.39"),
            sety("NewBestText", "SceneWindowHeight() * 0.44"),
            sety("RestartButton", "SceneWindowHeight() * 0.56"),
            sety("RestartLabel", "RestartButton.Y() - 32"),
        ], [
            ev([iss("GameMode", '""')], [sets("GameMode", '"Endless"')]),
            comment("Load the personal best saved on this device (GDevelop storage). NOTE: Playgama requires its Bridge storage instead; this gets swapped when the SDK is integrated."),
            ev([C("GroupExists", SAVE, KEY)], [A("ReadNumberFromStorage", SAVE, KEY, "", "BestEndlessDistance")]),
        ]),
    ]),
    group("Timers", [
        ev([isv("InvulnerabilityRemaining", ">", "0")], [setv("InvulnerabilityRemaining", "-", "TimeDelta()")]),
    ]),
    group("Game over", [
        ev([GAMEOVER], [setv("GameOverTime", "+", "TimeDelta()")]),
        comment("Restart: tap/click the RESTART button. Restarting the scene resets every scene variable; global variables (best score, mode) persist."),
        ev([GAMEOVER, isv("GameOverTime", ">=", "RestartDelay"), C("HasAnyTouchOrMouseStarted", ""),
            C("CollisionPoint", "RestartButton", 'TouchX(StartedTouchOrMouseId(0), "GameOver")', 'TouchY(StartedTouchOrMouseId(0), "GameOver")')],
           [A("Scene", "", '"Gameplay"', "")]),
        comment("Impact flash fades out and grows."),
        ev([], [opacity("ImpactFlash", "-", "900 * TimeDelta()"), scale("ImpactFlash", "+", "4 * TimeDelta()")]),
        ev([C("OpacityCapability::OpacityBehavior::Value", "ImpactFlash", "Opacity", "<=", "0")], [delete("ImpactFlash")]),
    ]),
]

ev_movement = [
    comment("CRACK MOVEMENT — the crack tip stays at TipScreenY; the world scrolls instead. CrackWorldY = distance travelled upward in px."),
    group("Speed and difficulty", [
        comment("Speed grows SpeedGrowth (8%) every SpeedGrowthInterval (20 s), smoothly, capped at MaxSpeed. DifficultyLevel goes 0 -> 1 over DifficultyRampTime and drives the obstacle generator. Slow Time multiplies the effective speed by SlowTimeFactor."),
        ev([PLAYING], [
            setv("RunTime", "+", "TimeDelta()"),
            setv("DifficultyLevel", "=", "clamp(RunTime / DifficultyRampTime, 0, 1)"),
            setv("ScrollSpeed", "=", "min(MaxSpeed, BaseSpeed * pow(SpeedGrowth, RunTime / SpeedGrowthInterval))"),
            setv("EffectiveSpeed", "=", "ScrollSpeed"),
        ], [ev([isv("SlowTimeRemaining", ">", "0")], [setv("EffectiveSpeed", "=", "ScrollSpeed * SlowTimeFactor")])]),
    ]),
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
        comment("Lateral offset follows an ease-out curve over BranchDuration (computed from elapsed time, so frame-rate independent). Clamped so the crack can never leave the screen or get stuck."),
        ev([isv("CooldownTimer", ">", "0")], [setv("CooldownTimer", "-", "TimeDelta()")]),
        ev([PLAYING, isv("BranchDirection", "!=", "0")], [setv("BranchTimer", "+", "TimeDelta()")], [
            ev([isv("BranchTimer", "<", "BranchDuration")],
               [setv("CrackWorldX", "=", CLAMPX.format("BranchStartX + BranchDirection * BranchDistance * (1 - pow(1 - BranchTimer / BranchDuration, 2))"))]),
            ev([isv("BranchTimer", ">=", "BranchDuration")],
               [setv("CrackWorldX", "=", CLAMPX.format("BranchStartX + BranchDirection * BranchDistance")),
                setv("BranchDirection", "=", "0"), setv("CooldownTimer", "=", "BranchCooldown")]),
        ]),
    ]),
    group("Forward motion and scrolling", [
        ev([PLAYING], [
            setv("CrackWorldY", "+", "EffectiveSpeed * TimeDelta()"),
            setv("Distance", "=", "floor(CrackWorldY / PixelsPerMeter)"),
            A("TiledSpriteObject::YOffset", "Background", "=", "-CrackWorldY"),
        ]),
        ev([], [setx("CrackTip", "CrackWorldX"), sety("CrackTip", "TipScreenY"), setx("CrackHitbox", "CrackWorldX"), sety("CrackHitbox", "TipScreenY")]),
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
            setv("TrailLastX", "=", "TrailNewX"), setv("TrailLastWorldY", "=", "CrackWorldY"),
        ]),
    ]),
    group("Scroll and clean up", [
        ev([], [sety("TrailSegment", screen_y("TrailSegment.WorldY"))]),
        ev([posy("TrailSegment", ">", "SceneWindowHeight() + 40")], [delete("TrailSegment")]),
    ]),
    group("Sparks", [
        ev([], [setx("Spark", "Spark.VX * TimeDelta()", op="+"), sety("Spark", "(Spark.VY + EffectiveSpeed) * TimeDelta()", op="+"),
                setov("Spark", "Life", "-", "TimeDelta()"), opacity("Spark", "=", "clamp(Spark.Life / 0.3, 0, 1) * 255"), A("SetZOrder", "Spark", "=", "9")]),
        ev([C("NumberObjectVariable", "Spark", "Life", "<=", "0")], [delete("Spark")]),
    ]),
]

def spawn(obj, wy, extra=()):
    return [create(obj, "LaneX", screen_y(wy)), setov(obj, "WorldY", "=", wy), A("SetZOrder", obj, "=", "5")] + list(extra)
L = lambda a, b: f"lerp({a}, {b}, DifficultyLevel)"
ev_spawner = [
    comment("PROCEDURAL OBSTACLE ROWS with a guaranteed safe route. The screen is split into LaneCount (7) lanes. Every row keeps a 2-lane wide CORRIDOR free (SafeLane and SafeLane+1). The corridor drifts by at most one lane per row (on most rows), and on a drift row the lanes of both the old and new corridor stay free, so the corridor is continuous. A 2-lane gap is always wider than one branch (130 px), so a branch can always land inside it. This rule was validated offline by brute-force searching every tap timing over 60 random 5-minute runs at the real speeds (tools: gen_sim.py)."),
    comment("Row types: EMPTY (nothing), WALL (every lane outside the corridor gets a reinforced barrier, a share of them breakable), SCATTER (each lane outside the corridor gets an obstacle with probability Density). Density, row spacing and the share of crystals/solid barriers rise with DifficultyLevel; empty rows become rarer."),
    group("Spawn next row", [
        ev([PLAYING, cmp("CrackWorldY + TipScreenY + SpawnMargin", ">=", "NextRowWorldY")], [
            setv("RowWorldY", "=", "NextRowWorldY"),
            setv("RowGap", "=", L("RowGapStart", "RowGapEnd")),
            setv("Density", "=", L("DensityStart", "DensityEnd")),
            setv("EmptyChance", "=", L("EmptyChanceStart", "EmptyChanceEnd")),
            setv("WallChance", "=", L("WallChanceStart", "WallChanceEnd")),
            setv("CrystalChance", "=", L("CrystalChanceStart", "CrystalChanceEnd")),
            setv("SolidChance", "=", L("SolidChanceStart", "SolidChanceEnd")),
            setv("BreakChance", "=", L("BreakChanceStart", "BreakChanceEnd")),
            setv("PrevSafeLane", "=", "SafeLane"),
            setv("BlockerChance", "=", L("BlockerChanceStart", "BlockerChanceEnd")),
            setv("CrackLane", "=", "clamp(floor(CrackWorldX / LaneWidth), 0, LaneCount - 1)"),
            setv("CorridorShift", "=", "RandomInRange(0, 1) * 2 - 1"),
            setv("RowRoll", "=", "RandomFloat(1)"),
            setv("RowType", "=", "2"),
            setv("LaneIter", "=", "0"),
        ], [
            comment("The corridor drifts left or right on most rows (it stays put only CorridorStayChance of the time), so the player must keep moving."),
            ev([cmp("RandomFloat(1)", "<", "CorridorStayChance")], [setv("CorridorShift", "=", "0")]),
            ev([], [setv("SafeLane", "=", "clamp(SafeLane + CorridorShift, 0, LaneCount - 2)"),
                    setv("CorridorMin", "=", "min(PrevSafeLane, SafeLane)"), setv("CorridorMax", "=", "max(PrevSafeLane, SafeLane) + 1")]),
            ev([isv("RowRoll", "<", "EmptyChance")], [setv("RowType", "=", "0")]),
            ev([isv("RowRoll", ">=", "EmptyChance"), isv("RowRoll", "<", "EmptyChance + WallChance")], [setv("RowType", "=", "1")]),
            repeat("LaneCount", [], [
                comment("Lanes inside the corridor are skipped: (lane - min) * (lane - max) > 0 only outside it."),
                ev([cmp("(LaneIter - CorridorMin) * (LaneIter - CorridorMax)", ">", "0")], [
                    setv("ObjType", "=", "0"), setv("TypeRoll", "=", "RandomFloat(1)"),
                    setv("LaneX", "=", "(LaneIter + 0.5) * LaneWidth + RandomFloatInRange(-LaneJitterX, LaneJitterX)"),
                    setv("ObjWorldY", "=", "RowWorldY + RandomFloatInRange(-RowJitterY, RowJitterY)"),
                ], [
                    comment("ObjType: 1 small rock, 2 medium rock, 3 crystal, 4 breakable barrier, 5 solid barrier."),
                    ev([isv("RowType", "=", "1")], [setv("ObjType", "=", "4")], [ev([isv("TypeRoll", ">=", "WallBreakableShare")], [setv("ObjType", "=", "5")])]),
                    ev([isv("RowType", "=", "2"), cmp("RandomFloat(1)", "<", "Density")], [setv("ObjType", "=", "3")], [
                        ev([isv("TypeRoll", ">=", "CrystalChance")], [setv("ObjType", "=", "5")]),
                        ev([isv("TypeRoll", ">=", "CrystalChance + SolidChance")], [setv("ObjType", "=", "4")]),
                        ev([isv("TypeRoll", ">=", "CrystalChance + SolidChance + BreakChance")], [setv("ObjType", "=", "1")],
                           [ev([cmp("RandomFloat(1)", ">=", "0.5")], [setv("ObjType", "=", "2")])]),
                    ]),
                    comment("Anti-camping: if this lane is where the crack is right now (and outside the corridor), block it with BlockerChance, so going straight is rarely safe."),
                    ev([isv("ObjType", "=", "0"), isv("RowType", "!=", "0"), isv("LaneIter", "=", "CrackLane"), cmp("RandomFloat(1)", "<", "BlockerChance")],
                       [setv("ObjType", "=", "3")], [ev([isv("TypeRoll", ">=", "CrystalChance")], [setv("ObjType", "=", "1")],
                                                       [ev([cmp("RandomFloat(1)", ">=", "0.5")], [setv("ObjType", "=", "2")])])]),
                    ev([isv("ObjType", "=", "1")], spawn("RockSmall", "ObjWorldY")),
                    ev([isv("ObjType", "=", "2")], spawn("RockMedium", "ObjWorldY")),
                    ev([isv("ObjType", "=", "3")], spawn("Crystal", "ObjWorldY", [A("AnimatableCapability::AnimatableBehavior::SetIndex", "Crystal", "Animation", "=", "RandomInRange(0, 2)")])),
                    ev([isv("ObjType", "=", "4")], spawn("BarrierBreakable", "RowWorldY")),
                    ev([isv("ObjType", "=", "5")], spawn("BarrierSolid", "RowWorldY")),
                ]),
                ev([], [setv("LaneIter", "+", "1")]),
            ]),
            comment("Power-ups: uncommon (PowerupChance per row, then a PowerupCooldownTime cooldown). Placed in the middle of the safe corridor, halfway to the next row, so they are always reachable and never inside an obstacle."),
            ev([isv("PowerupCooldown", "<=", "0"), cmp("RandomFloat(1)", "<", "PowerupChance")], [
                setv("PowerupCooldown", "=", "PowerupCooldownTime"),
                setv("LaneX", "=", "(SafeLane + 1) * LaneWidth"),
                setv("ObjWorldY", "=", "RowWorldY + RowGap / 2"),
                setv("TypeRoll", "=", "RandomFloat(1)"),
            ], [
                ev([isv("TypeRoll", "<", "0.5")], spawn("PowerSlow", "ObjWorldY")),
                ev([isv("TypeRoll", ">=", "0.5")], spawn("PowerStrength", "ObjWorldY")),
            ]),
            ev([], [setv("NextRowWorldY", "+", "RowGap")]),
        ]),
    ]),
    group("Scroll and clean up", [
        ev([], [sety("Obstacles", screen_y("Obstacles.WorldY")), sety("Powerups", screen_y("Powerups.WorldY"))]),
        ev([posy("Obstacles", ">", "SceneWindowHeight() + 120")], [delete("Obstacles")]),
        ev([posy("Powerups", ">", "SceneWindowHeight() + 120")], [delete("Powerups")]),
    ]),
]

ev_powerups = [
    comment("POWER-UPS — Slow Time: EffectiveSpeed x SlowTimeFactor (0.6 = 40% slower) for SlowTimeDuration real seconds; distance still follows real progress. Crack Strength: StrengthMaxCharges charges, each breaks one rock or breakable barrier (see EV_Collisions); crystals and solid barriers can't be broken. Picking it up again refills to max."),
    group("Pick up", [
        ev([PLAYING, C("CollisionNP", "CrackHitbox", "PowerSlow", "", "", "")], [
            setv("SlowTimeRemaining", "=", "SlowTimeDuration"), create("ImpactFlash", "PowerSlow.X()", "PowerSlow.Y()"),
            color("ImpactFlash", "120;180;255"), A("SetZOrder", "ImpactFlash", "=", "12"), delete("PowerSlow")]),
        ev([PLAYING, C("CollisionNP", "CrackHitbox", "PowerStrength", "", "", "")], [
            setv("StrengthCharges", "=", "StrengthMaxCharges"), create("ImpactFlash", "PowerStrength.X()", "PowerStrength.Y()"),
            color("ImpactFlash", "255;140;60"), A("SetZOrder", "ImpactFlash", "=", "12"), delete("PowerStrength")]),
    ]),
    group("Timers and HUD", [
        ev([PLAYING, isv("PowerupCooldown", ">", "0")], [setv("PowerupCooldown", "-", "TimeDelta()")]),
        ev([PLAYING, isv("SlowTimeRemaining", ">", "0")], [
            setv("SlowTimeRemaining", "-", "TimeDelta()"), A("TiledSpriteObject::SetColor", "Background", '"150;185;255"'), A("Show", "SlowText", ""),
            text("SlowText", '"SLOW " + ToString(round(max(0, SlowTimeRemaining) * 10) / 10)')]),
        ev([isv("SlowTimeRemaining", "<=", "0")], [A("TiledSpriteObject::SetColor", "Background", '"255;255;255"'), A("Hide", "SlowText")]),
        ev([isv("StrengthCharges", ">", "0")], [A("Show", "StrengthText", ""), text("StrengthText", '"STRENGTH x" + ToString(StrengthCharges)')]),
        ev([isv("StrengthCharges", "<=", "0")], [A("Hide", "StrengthText")]),
        comment("Crack colour shows Strength: orange-red while charged."),
        ev([PLAYING, isv("StrengthCharges", ">", "0")], [color("CrackTip", "255;120;60")]),
        ev([PLAYING, isv("StrengthCharges", "<=", "0")], [color("CrackTip", "255;255;255")]),
        ev([], [scale("Powerups", "=", "1 + 0.1 * sin(TimeFromStart() * 6)")]),
    ]),
]

ev_collisions = [
    comment("COLLISIONS — only the small hidden CrackHitbox at the tip is tested. Order matters: first Crack Strength breaks Breakable obstacles (rocks, breakable barriers), then anything still touched kills, unless InvulnerabilityRemaining > 0 (used by the revive in Phase 3)."),
    ev([PLAYING, isv("StrengthCharges", ">", "0"), C("CollisionNP", "CrackHitbox", "Breakable", "", "", "")], [
        create("ImpactFlash", "Breakable.X()", "Breakable.Y()"), A("SetZOrder", "ImpactFlash", "=", "12"),
        delete("Breakable"), setv("StrengthCharges", "-", "1"),
    ], [spark_burst("10", "RandomFloatInRange(-300, 300)", "RandomFloatInRange(-300, 100)")]),
    ev([PLAYING, isv("InvulnerabilityRemaining", "<=", "0"), C("CollisionNP", "CrackHitbox", "Obstacles", "", "", "")], [
        sets("GameState", '"GameOver"'), setv("BranchDirection", "=", "0"),
        create("ImpactFlash", "CrackWorldX", "TipScreenY"), A("SetZOrder", "ImpactFlash", "=", "12"),
        color("CrackTip", "255;90;70"),
        text("FinalDistanceText", '"DISTANCE: " + ToString(Distance) + " m"'),
        A("Hide", "HintText"),
    ], [
        spark_burst("12", "RandomFloatInRange(-260, 260)", "RandomFloatInRange(-320, 120)"),
        comment("Endless mode: personal best is saved locally."),
        ev([ENDLESS, cmp("Distance", ">", "BestEndlessDistance")], [
            setv("BestEndlessDistance", "=", "Distance"), A("EcrireFichierExp", SAVE, KEY, "BestEndlessDistance"),
            A("Show", "NewBestText", "")]),
        ev([], [text("GameOverBestText", '"BEST: " + ToString(BestEndlessDistance) + " m"'),
                A("SetCenterX", "FinalDistanceText", "=", "SceneWindowWidth() / 2"),
                A("SetCenterX", "GameOverBestText", "=", "SceneWindowWidth() / 2"),
                A("SetCenterX", "NewBestText", "=", "SceneWindowWidth() / 2"),
                A("ShowLayer", "", '"GameOver"')]),
    ]),
]

ev_scoring = [
    comment("SCORING / HUD — distance comes from the logical world position (CrackWorldY), so Slow Time slows the counter exactly as much as real progress."),
    ev([], [text("DistanceText", '"DISTANCE: " + ' + pad4("Distance") + ' + " m"'),
            text("BestText", '"BEST: " + ' + pad4("BestEndlessDistance") + ' + " m"'),
            A("SetCenterX", "DistanceText", "=", "SceneWindowWidth() / 2"), A("SetCenterX", "BestText", "=", "SceneWindowWidth() / 2")]),
]

external_events = [("EV_GameState", ev_gamestate), ("EV_CrackMovement", ev_movement), ("EV_ObstacleSpawner", ev_spawner),
                   ("EV_Powerups", ev_powerups), ("EV_Trail", ev_trail), ("EV_Collisions", ev_collisions), ("EV_Scoring", ev_scoring)]
scene_events = [comment("CRACKLINE — Phase 2 (Endless Depth). Each system lives in its own external events sheet (Project manager > External events). Order matters.")] + \
    [link(n) for n, _ in external_events]

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
        "useExternalSourceFiles": False, "version": "0.2.0", "name": "CRACKLINE", "description": "Phase 2 - Endless Depth", "author": "",
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
    "objects": [], "objectsGroups": [], "variables": global_vars, "layouts": [layout],
    "externalEvents": [{"associatedLayout": "Gameplay", "lastChangeTimeStamp": 0, "name": n, "events": e} for n, e in external_events],
    "eventsFunctionsExtensions": [], "externalLayouts": [], "externalSourceFiles": [],
}
os.makedirs(OUT, exist_ok=True)
with open(os.path.join(OUT, "game.json"), "w") as f: json.dump(project, f, indent=2)
print("wrote", os.path.join(OUT, "game.json"))
