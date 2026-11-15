# Generates the CRACKLINE GDevelop project (game.json) — Phase 3.
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
def posx(obj, op, val): return C("PosX", obj, op, val)
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
    ("BaseSpeed", P["BaseSpeed"]), ("MaxSpeed", P["MaxSpeed"]), ("SpeedStepDistance", 250), ("SpeedStepFactor", 1.25), ("SpeedRampRate", 120), ("SpeedTarget", 180),
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
    ("WormChanceStart", P["WormChanceStart"]), ("WormChanceEnd", P["WormChanceEnd"]), ("WormSpeedStart", P["WormSpeedStart"]), ("WormSpeedEnd", P["WormSpeedEnd"]),
    ("WormMinX", P["WormMinX"]), ("WormMaxX", P["WormMaxX"]), ("FissureChanceStart", P["FissureChanceStart"]), ("FissureChanceEnd", P["FissureChanceEnd"]), ("FissureClearance", P["FissureClearance"]),
    ("BlockerChanceStart", P["BlockerChanceStart"]), ("BlockerChanceEnd", P["BlockerChanceEnd"]), ("CorridorStayChance", P["CorridorStayChance"]), ("LaneJitterX", P["LaneJitterX"]), ("RowJitterY", P["RowJitterY"]),
    ("PowerupChance", P["PowerupChance"]), ("PowerupCooldownTime", P["PowerupCooldownTime"]),
    ("SlowTimeDuration", P["SlowTimeDuration"]), ("SlowTimeFactor", P["SlowTimeFactor"]), ("StrengthMaxCharges", P["StrengthMaxCharges"]),
    ("RestartDelay", 0.3),
    ("PlanetDistanceStep", 1000), ("ThemeCount", 3),
    ("PlanetDifficultyStart", 0.15), ("PlanetDifficultyStep", 0.2), ("PlanetProgressDifficulty", 0.2),
    ("PlanetMaxSpeed", 520), ("BreakDuration", 2.0),
    ("GemChance", 0.5), ("RiskyGemChance", 0.15), ("RestartFromShop", 0),
    ("ReviveInvulnerability", 2), ("ReviveClearBehind", 250), ("ReviveClearAhead", 750),
]
STATE = ["ScrollSpeed", "EffectiveSpeed", "Distance", "RunTime", "DifficultyLevel", "CrackWorldX", "CrackWorldY", "TipScreenY",
         "BranchDirection", "BranchTimer", "BranchStartX", "CooldownTimer", "TrailLastX", "TrailLastWorldY", "TrailNewX",
         "NextRowWorldY", "RowWorldY", "RowGap", "SafeLane", "PrevSafeLane", "CorridorMin", "CorridorMax", "RowType", "RowRoll",
         "Density", "EmptyChance", "WallChance", "CrystalChance", "SolidChance", "BreakChance",
         "LaneIter", "LaneWidth", "BlockerChance", "CrackLane", "CorridorShift", "TypeRoll", "ObjType", "LaneX", "ObjWorldY",
         "PowerupCooldown", "SlowTimeRemaining", "StrengthCharges", "InvulnerabilityRemaining", "GameOverTime",
         "TotalDistance", "PlanetIndex", "PlanetTheme", "PlanetsBroken", "PlanetTargetDistance", "PlanetDistance", "PlanetStartWorldY",
         "ThemeCrystalBonus", "ThemeWallBonus", "ThemeSolidBonus", "WormChance", "FissureChance", "WormSpeed", "RunCrystals", "GemSize", "GemRoll", "BreakTime", "SplitOffset", "PlanetCX", "PlanetCY"]
scene_vars = [num(n, v) for n, v in TUNING] + [st("GameState", "Playing"), st("RockTint", "255;255;255"), st("PlanetName", "EMBER")] + [num(n, 0) for n in STATE] + \
    [boo("ReviveUsed", False), boo("RequestRevive", False), boo("PlanetSetupPending", True), boo("BreakBurstDone", False)]
STYLES = ["Classic", "Frostbite", "Venom", "Amethyst", "Inferno", "Shadow"]
STYLE_PRICES = [0, 150, 300, 500, 800, 1200]
STYLE_SPARKS = ["255;210;110", "150;230;255", "180;255;120", "220;160;255", "255;130;90", "170;120;255"]
def arr(n, typ, vals): return {"name": n, "type": "array", "children": [{"type": typ, "value": v} for v in vals]}
global_vars = [st("GameMode", "Endless"), num("BestEndlessDistance", 0), num("BestPlanetsBroken", 0),
               num("CrystalWallet", 0), num("EquippedStyle", 0), num("Muted", 0), st("OwnedStyles", "100000"),
               arr("StyleNames", "string", [s.upper() for s in STYLES]), arr("StylePrices", "number", STYLE_PRICES), arr("StyleSparkColors", "string", STYLE_SPARKS)]

# ---------------------------------------------------------------- resources & objects
IMAGES = ["bg_soil", "rock_small", "rock_medium", "crack_hitbox", "ui_card", "spark", "impact_flash", "ui_overlay",
          "ui_button", "barrier_solid", "barrier_breakable", "crystal_purple", "crystal_pink", "crystal_cyan", "powerup_slow", "powerup_strength",
          "bg_verdant", "bg_frost", "shield_glow", "ui_white", "ui_button_blue", "worm", "worm_b", "fissure", "icon_audio_on", "icon_audio_off"] + [f"planet_{t}_{s}" for t in ("ember", "verdant", "frost") for s in ("left", "right")] + \
    [f"{k}_{s.lower()}" for s in ["Classic", "Frostbite", "Venom", "Amethyst", "Inferno", "Shadow"] for k in ("trail", "tip")]
resources = [{"alwaysLoaded": False, "file": f"assets/{n}.png", "kind": "image", "metadata": "", "name": n, "smoothed": True, "userAdded": True} for n in IMAGES]
SOUNDS = ["sfx_branch", "sfx_break", "sfx_crash", "sfx_fissure", "sfx_crystal", "sfx_powerup", "sfx_click", "sfx_error", "sfx_buy", "sfx_revive", "jingle_gameover", "jingle_planet"]
resources += [{"file": f"audio/{n}.ogg", "kind": "audio", "metadata": "", "name": n, "preloadAsMusic": False, "preloadAsSound": True, "preloadInCache": False, "userAdded": True} for n in SOUNDS]
def snd(name, vol="100", pitch="1"): return A("PlaySound", "", name, "", vol, pitch)

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
def sprite(name, image, origin=(0, 0), center=None, mask=None, variables=(), anims=None, frames=None, frame_time=0.08):
    anims = anims or [("", image)]
    if frames:   # one looping animation made of several images
        o = sprite(name, image, origin, center, mask, variables)
        o["animations"][0]["directions"][0].update({"looping": True, "timeBetweenFrames": frame_time, "sprites": [frame(f, origin, center, mask) for f in frames]})
        return o
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
] + [{"assetStoreId": "", "name": n, "type": "TiledSpriteObject::TiledSprite", "texture": t, "width": 720, "height": 3000,
     "variables": [], "effects": [], "behaviors": []} for n, t in (("BgEmber", "bg_soil"), ("BgVerdant", "bg_verdant"), ("BgFrost", "bg_frost"))] + [
    sprite("RockSmall", "rock_small", origin=(38, 38), mask=octagon(38, 38, HIT["RockSmall"][1]), variables=wvar),
    sprite("RockMedium", "rock_medium", origin=(58, 58), mask=octagon(58, 58, HIT["RockMedium"][1]), variables=wvar),
    sprite("BarrierBreakable", "barrier_breakable", origin=(56, 32), mask=rect(56, 32, HIT["BarrierBreakable"][1], HIT["BarrierBreakable"][2]), variables=wvar),
    sprite("BarrierSolid", "barrier_solid", origin=(56, 32), mask=rect(56, 32, HIT["BarrierSolid"][1], HIT["BarrierSolid"][2]), variables=wvar),
    sprite("Crystal", "crystal_purple", origin=(48, 48), mask=octagon(48, 48, 30), variables=wvar + [num("Value", 1)],
           anims=[("Purple", "crystal_purple"), ("Pink", "crystal_pink"), ("Cyan", "crystal_cyan")]),
    sprite("Worm", "worm", origin=(80, 32), mask=rect(80, 32, HIT["Worm"][1], HIT["Worm"][2]), variables=wvar + [num("Dir", 1), num("Speed", 150)], frames=["worm", "worm_b"], frame_time=0.18),
    sprite("Fissure", "fissure", origin=(0, 32), mask=rect(360, 32, 360, 12), variables=wvar + [boo("Used", False)]),
    sprite("PowerSlow", "powerup_slow", origin=(40, 40), mask=octagon(40, 40, 36), variables=wvar),
    sprite("PowerStrength", "powerup_strength", origin=(40, 40), mask=octagon(40, 40, 36), variables=wvar),
    sprite("TrailSegment", "trail_classic", origin=(0, 24), center=(0, 24), variables=wvar, anims=[(s, f"trail_{s.lower()}") for s in STYLES]),
    sprite("CrackTip", "tip_classic", origin=(64, 64), anims=[(s, f"tip_{s.lower()}") for s in STYLES]),
    sprite("GemIcon", "crystal_cyan", origin=(48, 48)),
    sprite("MuteButton", "icon_audio_on", origin=(50, 50), anims=[("On", "icon_audio_on"), ("Off", "icon_audio_off")]),
    textobj("GemText", "0", 34, rgb="160;240;255", align="left"),
    textobj("GameOverGemsText", "CRYSTALS +0", 28, rgb="160;240;255"),
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
    textobj("FinalDistanceText", "DISTANCE: 0000 m", 36),
    textobj("GameOverBestText", "BEST: 0000 m", 30, rgb="255;220;160"),
    textobj("NewBestText", "NEW BEST!", 34, rgb="120;255;160"),
    sprite("RestartButton", "ui_button", origin=(180, 55)),
    textobj("RestartLabel", "RESTART", 48, rgb="80;26;6"),
    sprite("ReviveButton", "ui_button_blue", origin=(180, 55)),
    textobj("ReviveLabel", "SIMULATE AD REVIVE (TEST)", 20, rgb="255;255;255"),
    sprite("MenuButton", "ui_button", origin=(180, 55)),
    textobj("MenuLabel", "MAIN MENU", 40, rgb="80;26;6"),
    textobj("GameOverPlanetsText", "PLANETS BROKEN: 0", 34, rgb="255;240;214"),
    sprite("ShieldGlow", "shield_glow", origin=(70, 70)),
    sprite("ProgressBack", "ui_white"), sprite("ProgressFill", "ui_white"),
    textobj("PlanetHudText", "EMBER  0 / 500 m", 26, rgb="255;240;214"),
    sprite("PlanetLeft", "planet_ember_left", origin=(160, 160), anims=[(t.capitalize(), f"planet_{t}_left") for t in ("ember", "verdant", "frost")]),
    sprite("PlanetRight", "planet_ember_right", origin=(160, 160), anims=[(t.capitalize(), f"planet_{t}_right") for t in ("ember", "verdant", "frost")]),
    textobj("PlanetBrokenText", "EMBER BROKEN!", 56, rgb="255;230;140"),
]
folders = {"folderName": "__ROOT", "children": [
    {"folderName": "World", "children": [{"objectName": "BgEmber"}, {"objectName": "BgVerdant"}, {"objectName": "BgFrost"}]},
    {"folderName": "Planet", "children": [{"objectName": n} for n in ["PlanetLeft", "PlanetRight", "PlanetBrokenText", "ShieldGlow"]]},
    {"folderName": "Crack", "children": [{"objectName": n} for n in ["CrackTip", "CrackHitbox", "TrailSegment", "Spark", "ImpactFlash"]]},
    {"folderName": "Obstacles", "children": [{"objectName": n} for n in ["RockSmall", "RockMedium", "BarrierBreakable", "BarrierSolid", "Worm", "Fissure"]]},
    {"folderName": "Collectibles", "children": [{"objectName": "Crystal"}, {"objectName": "GemIcon"}]},
    {"folderName": "Powerups", "children": [{"objectName": "PowerSlow"}, {"objectName": "PowerStrength"}]},
    {"folderName": "UI", "children": [{"objectName": n} for n in ["DistanceText", "BestText", "SlowText", "StrengthText", "HintText", "Overlay",
                                                                   "GameOverTitle", "FinalDistanceText", "GameOverBestText", "NewBestText", "RestartButton", "RestartLabel",
                                                                   "ReviveButton", "ReviveLabel", "MenuButton", "MenuLabel", "GemText", "GameOverGemsText", "GameOverPlanetsText", "ProgressBack", "ProgressFill", "PlanetHudText"]]},
]}
def grp(name, objs): return {"name": name, "objects": [{"name": o} for o in objs]}
groups = [grp("Obstacles", ["RockSmall", "RockMedium", "BarrierBreakable", "BarrierSolid", "Worm"]),
          grp("Breakable", ["RockSmall", "RockMedium", "BarrierBreakable", "Worm"]),
          grp("Powerups", ["PowerSlow", "PowerStrength"]),
          grp("Backgrounds", ["BgEmber", "BgVerdant", "BgFrost"]), grp("Rocks", ["RockSmall", "RockMedium"])]

def inst(name, x, y, z=0, layer="", w=0, h=0):
    return {"angle": 0, "customSize": bool(w), "height": h, "layer": layer, "locked": False, "name": name,
            "persistentUuid": uid(f"{name}-{layer}"), "width": w, "x": x, "y": y, "zOrder": z,
            "numberProperties": [], "stringProperties": [], "initialVariables": []}
instances = [
    inst("BgEmber", 0, -800, z=-12, w=720, h=3200), inst("BgVerdant", 0, -800, z=-11, w=720, h=3200), inst("BgFrost", 0, -800, z=-10, w=720, h=3200),
    inst("ShieldGlow", 360, 896, z=12),
    inst("CrackTip", 360, 896, z=10), inst("CrackHitbox", 360, 896, z=11),
    inst("DistanceText", 140, 40, layer="HUD", z=1), inst("BestText", 250, 104, layer="HUD", z=1),
    inst("SlowText", 30, 150, layer="HUD", z=1), inst("StrengthText", 470, 150, layer="HUD", z=1),
    inst("HintText", 90, 1040, layer="HUD", z=1),
    inst("GemIcon", 610, 66, layer="HUD", z=1), inst("MuteButton", 46, 46, layer="HUD", z=3), inst("GemText", 636, 44, layer="HUD", z=1), inst("GameOverGemsText", 200, 600, layer="GameOver", z=1),
    inst("Overlay", 0, -400, layer="GameOver", z=0, w=720, h=3000),
    inst("GameOverTitle", 130, 300, layer="GameOver", z=1), inst("FinalDistanceText", 150, 430, layer="GameOver", z=1),
    inst("GameOverBestText", 220, 500, layer="GameOver", z=1), inst("NewBestText", 250, 560, layer="GameOver", z=1),
    inst("RestartButton", 360, 700, layer="GameOver", z=1), inst("RestartLabel", 270, 668, layer="GameOver", z=2),
    inst("ReviveButton", 360, 840, layer="GameOver", z=1), inst("ReviveLabel", 200, 826, layer="GameOver", z=2),
    inst("MenuButton", 360, 980, layer="GameOver", z=1), inst("MenuLabel", 255, 958, layer="GameOver", z=2),
    inst("GameOverPlanetsText", 160, 430, layer="GameOver", z=1),
    inst("ProgressBack", 160, 200, layer="HUD", z=1, w=400, h=18), inst("ProgressFill", 162, 202, layer="HUD", z=2, w=396, h=14),
    inst("PlanetHudText", 200, 224, layer="HUD", z=1),
    inst("PlanetLeft", 360, 540, layer="Cinematic", z=1), inst("PlanetRight", 360, 540, layer="Cinematic", z=1),
    inst("PlanetBrokenText", 160, 800, layer="Cinematic", z=3),
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
SAVE, KEY, KEYP = '"CracklineSave"', '"BestEndlessDistance"', '"BestPlanetsBroken"'
KW, KO, KE, KM = '"CrystalWallet"', '"OwnedStyles"', '"EquippedStyle"', '"Muted"'
def load_profile():
    """Loads everything saved on the device (shared by MainMenu, Shop and Gameplay)."""
    return [
        ev([C("GroupExists", SAVE, KEY)], [A("ReadNumberFromStorage", SAVE, KEY, "", "BestEndlessDistance")]),
        ev([C("GroupExists", SAVE, KEYP)], [A("ReadNumberFromStorage", SAVE, KEYP, "", "BestPlanetsBroken")]),
        ev([C("GroupExists", SAVE, KW)], [A("ReadNumberFromStorage", SAVE, KW, "", "CrystalWallet")]),
        ev([C("GroupExists", SAVE, KE)], [A("ReadNumberFromStorage", SAVE, KE, "", "EquippedStyle")]),
        ev([C("GroupExists", SAVE, KO)], [A("ReadStringFromStorage", SAVE, KO, "", "OwnedStyles")]),
        ev([C("GroupExists", SAVE, KM)], [A("ReadNumberFromStorage", SAVE, KM, "", "Muted")]),
        ev([], [A("SetGlobalVolume", "", "=", "100 * (1 - Muted)")]),
    ]
def mute_events(layer='""'):
    """Speaker button: toggles all sound on/off, saved on the device (Playgama requires a mute button)."""
    return [ev([isv("Muted", "=", "0")], [A("AnimatableCapability::AnimatableBehavior::SetIndex", "MuteButton", "Animation", "=", "0")]),
            ev([isv("Muted", "=", "1")], [A("AnimatableCapability::AnimatableBehavior::SetIndex", "MuteButton", "Animation", "=", "1")]),
            ev([C("HasAnyTouchOrMouseStarted", ""), C("CollisionPoint", "MuteButton", f'TouchX(StartedTouchOrMouseId(0), {layer})', f'TouchY(StartedTouchOrMouseId(0), {layer})')],
               [setv("Muted", "=", "1 - Muted"), A("EcrireFichierExp", SAVE, KM, "Muted"), A("SetGlobalVolume", "", "=", "100 * (1 - Muted)"), snd("sfx_click", "80")])]
def save_wallet(): return A("EcrireFichierExp", SAVE, KW, "CrystalWallet")
ENDLESS = iss("GameMode", '"Endless"')
def color(obj, rgb): return A("ChangeColor", obj, f'"{rgb}"')

spark_burst = lambda count, vx, vy, x="CrackWorldX", y="TipScreenY": repeat(count, [
    create("Spark", x, y), A("ChangeColor", "Spark", "StyleSparkColors[EquippedStyle]"), setov("Spark", "VX", "=", vx), setov("Spark", "VY", "=", vy),
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
            A("HideLayer", "", '"GameOver"'), A("HideLayer", "", '"Cinematic"'), A("Hide", "ShieldGlow"),
            A("Hide", "CrackHitbox"), A("Hide", "SlowText"), A("Hide", "StrengthText"), A("Hide", "NewBestText"),
            opacity("Overlay", "=", "170"),
            sety("HintText", "SceneWindowHeight() * 0.82"),
            sety("GameOverTitle", "SceneWindowHeight() / 2 - 338"),
            sety("FinalDistanceText", "SceneWindowHeight() / 2 - 170"),
            sety("GameOverBestText", "SceneWindowHeight() / 2 - 118"),
            sety("NewBestText", "SceneWindowHeight() / 2 - 73"),
            sety("RestartButton", "SceneWindowHeight() / 2 + 86"), scale("RestartButton", "=", "0.9"), scale("ReviveButton", "=", "0.9"), scale("MenuButton", "=", "0.9"),
            sety("RestartLabel", "RestartButton.Y() - 32"), A("SetCenterX", "RestartLabel", "=", "SceneWindowWidth() / 2"), A("SetCenterX", "MenuLabel", "=", "SceneWindowWidth() / 2"),
            sety("ReviveButton", "SceneWindowHeight() / 2 + 193"), sety("ReviveLabel", "ReviveButton.Y() - 12"),
            sety("MenuButton", "SceneWindowHeight() / 2 + 300"), sety("MenuLabel", "MenuButton.Y() - 24"),
            sety("GameOverPlanetsText", "SceneWindowHeight() / 2 - 222"), sety("GameOverGemsText", "SceneWindowHeight() / 2 - 23"),
            color("ProgressBack", "40;20;12"), opacity("ProgressBack", "=", "170"),
        ], [
            ev([iss("GameMode", '""')], [sets("GameMode", '"Endless"')]),
            comment("Load the personal best saved on this device (GDevelop storage). NOTE: Playgama requires its Bridge storage instead; this gets swapped when the SDK is integrated."),
            *load_profile(),
            comment("Equipped crack style (bought in the Shop) recolours the tip, trail and sparks."),
            ev([], [A("AnimatableCapability::AnimatableBehavior::SetIndex", "CrackTip", "Animation", "=", "EquippedStyle"), scale("GemIcon", "=", "0.36")]),
            comment("Planet-mode HUD (surface progress bar) only in Planet Breaker; Endless shows only the Ember background."),
            ev([iss("GameMode", '"Endless"')], [A("Hide", "ProgressBack"), A("Hide", "ProgressFill"), A("Hide", "PlanetHudText"), A("Hide", "BgVerdant"), A("Hide", "BgFrost")]),
        ]),
    ]),
    group("Sound toggle", [comment("Speaker button (top-left of the HUD). Taps on it never count as a branch tap.")] + mute_events('"HUD"')),
    group("Timers", [
        ev([isv("InvulnerabilityRemaining", ">", "0")], [setv("InvulnerabilityRemaining", "-", "TimeDelta()")]),
    ]),
    group("Game over", [
        ev([GAMEOVER], [setv("GameOverTime", "+", "TimeDelta()")]),
        comment("Restart: tap/click the RESTART button. Restarting the scene resets every scene variable; global variables (best score, mode) persist."),
        ev([GAMEOVER, isv("GameOverTime", ">=", "RestartDelay"), C("HasAnyTouchOrMouseStarted", ""),
            C("CollisionPoint", "RestartButton", 'TouchX(StartedTouchOrMouseId(0), "GameOver")', 'TouchY(StartedTouchOrMouseId(0), "GameOver")')],
           [snd("sfx_click", "80"), A("Scene", "", '"Gameplay"', "")]),
        ev([GAMEOVER, isv("GameOverTime", ">=", "RestartDelay"), C("HasAnyTouchOrMouseStarted", ""),
            C("CollisionPoint", "MenuButton", 'TouchX(StartedTouchOrMouseId(0), "GameOver")', 'TouchY(StartedTouchOrMouseId(0), "GameOver")')],
           [snd("sfx_click", "80"), A("Scene", "", '"MainMenu"', "")]),
        comment("SIMULATE AD REVIVE (TEST) button: it only REQUESTS a revive (RequestRevive = true); EV_Revive does the work. A future Playgama rewarded-ad 'rewarded' callback should set RequestRevive the same way. No ad is shown or faked here."),
        ev([GAMEOVER, isv("GameOverTime", ">=", "RestartDelay"), C("BooleanVariable", "ReviveUsed", "False", ""), C("HasAnyTouchOrMouseStarted", ""),
            C("CollisionPoint", "ReviveButton", 'TouchX(StartedTouchOrMouseId(0), "GameOver")', 'TouchY(StartedTouchOrMouseId(0), "GameOver")')],
           [snd("sfx_click", "80"), A("SetBooleanVariable", "RequestRevive", "True", "")]),
        comment("Impact flash fades out and grows."),
        ev([], [opacity("ImpactFlash", "-", "900 * TimeDelta()"), scale("ImpactFlash", "+", "4 * TimeDelta()")]),
        ev([C("OpacityCapability::OpacityBehavior::Value", "ImpactFlash", "Opacity", "<=", "0")], [delete("ImpactFlash")]),
    ]),
]

ev_movement = [
    comment("CRACK MOVEMENT — the crack tip stays at TipScreenY; the world scrolls instead. CrackWorldY = distance travelled upward in px."),
    group("Speed and difficulty", [
        comment("Speed jumps x SpeedStepFactor (1.25 = +25%) every SpeedStepDistance (250 m) travelled, capped at MaxSpeed (Endless) or PlanetMaxSpeed (Planet Breaker). Each jump eases in at SpeedRampRate px/s per second so it never lurches. DifficultyLevel goes 0 -> 1 over DifficultyRampTime and drives the obstacle generator. Slow Time multiplies the effective speed by SlowTimeFactor."),
        ev([PLAYING], [
            setv("RunTime", "+", "TimeDelta()"),
            setv("DifficultyLevel", "=", "clamp(RunTime / DifficultyRampTime, 0, 1)"),
            setv("TotalDistance", "=", "Distance"),
            setv("SpeedTarget", "=", "min(MaxSpeed, BaseSpeed * pow(SpeedStepFactor, floor(Distance / SpeedStepDistance)))"),
        ], [
            comment("Planet Breaker: every planet starts harder (PlanetDifficultyStart + PlanetDifficultyStep per planet) and difficulty rises a little within each planet. Speed uses the same 250 m steps but may go up to PlanetMaxSpeed."),
            ev([iss("GameMode", '"Planet"')], [
                setv("DifficultyLevel", "=", "clamp(PlanetDifficultyStart + PlanetDifficultyStep * PlanetIndex + PlanetProgressDifficulty * PlanetDistance / PlanetTargetDistance, 0, 1)"),
                setv("SpeedTarget", "=", "min(PlanetMaxSpeed, BaseSpeed * pow(SpeedStepFactor, floor(Distance / SpeedStepDistance)))")]),
            ev([], [setv("ScrollSpeed", "=", "min(SpeedTarget, ScrollSpeed + SpeedRampRate * TimeDelta())"), setv("EffectiveSpeed", "=", "ScrollSpeed")]),
            ev([isv("SlowTimeRemaining", ">", "0")], [setv("EffectiveSpeed", "=", "ScrollSpeed * SlowTimeFactor")]),
        ]),
    ]),
    group("Input (tap / click)", [
        comment("One tap = one branch. Taps during a branch or the short cooldown are ignored (no queueing). Left half = left, right half = right."),
        ev([PLAYING, C("HasAnyTouchOrMouseStarted", ""), isv("BranchDirection", "=", "0"), isv("CooldownTimer", "<=", "0"),
            C("CollisionPoint", "MuteButton", 'TouchX(StartedTouchOrMouseId(0), "HUD")', 'TouchY(StartedTouchOrMouseId(0), "HUD")', inv=True)], [snd("sfx_branch", "55", "RandomFloatInRange(0.9, 1.2)")], [
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
            A("TiledSpriteObject::YOffset", "Backgrounds", "=", "-CrackWorldY"),
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
            A("AnimatableCapability::AnimatableBehavior::SetIndex", "TrailSegment", "Animation", "=", "EquippedStyle"),
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
def gem_spawn():
    """Create a collectible crystal at (LaneX, ObjWorldY) with size GemSize: 0 small = 5 pts, 1 medium = 3 pts, 2 large = 1 pt."""
    # size events are SUB-events of the Create event, so they only affect the crystal just created
    # colour always matches size/value: PINK small = 5, PURPLE medium = 3, BLUE large = 1  (animations: 0 Purple, 1 Pink, 2 Cyan)
    anim = lambda i: A("AnimatableCapability::AnimatableBehavior::SetIndex", "Crystal", "Animation", "=", str(i))
    return [ev([], spawn("Crystal", "ObjWorldY"), [
            ev([isv("GemSize", "=", "0")], [setov("Crystal", "Value", "=", "5"), scale("Crystal", "=", "0.55"), anim(1)]),
            ev([isv("GemSize", "=", "1")], [setov("Crystal", "Value", "=", "3"), scale("Crystal", "=", "0.75"), anim(0)]),
            ev([isv("GemSize", "=", "2")], [setov("Crystal", "Value", "=", "1"), scale("Crystal", "=", "1"), anim(2)])])]
ev_spawner = [
    comment("PROCEDURAL OBSTACLE ROWS with a guaranteed safe route. The screen is split into LaneCount (7) lanes. Every row keeps a 2-lane wide CORRIDOR free (SafeLane and SafeLane+1). The corridor drifts by at most one lane per row (on most rows), and on a drift row the lanes of both the old and new corridor stay free, so the corridor is continuous. A 2-lane gap is always wider than one branch (130 px), so a branch can always land inside it. This rule was validated offline by brute-force searching every tap timing over 60 random 5-minute runs at the real speeds (tools: gen_sim.py)."),
    comment("Row types: EMPTY (nothing), WALL (every lane outside the corridor gets a reinforced barrier, a share of them breakable), SCATTER (each lane outside the corridor gets an obstacle with probability Density). Density, row spacing and the share of crystals/solid barriers rise with DifficultyLevel; empty rows become rarer."),
    group("Spawn next row", [
        ev([PLAYING, cmp("CrackWorldY + TipScreenY + SpawnMargin", ">=", "NextRowWorldY")], [
            setv("RowWorldY", "=", "NextRowWorldY"),
            setv("RowGap", "=", L("RowGapStart", "RowGapEnd")),
            setv("Density", "=", L("DensityStart", "DensityEnd")),
            setv("EmptyChance", "=", L("EmptyChanceStart", "EmptyChanceEnd")),
            setv("WallChance", "=", L("WallChanceStart", "WallChanceEnd") + " + ThemeWallBonus"),
            setv("CrystalChance", "=", L("CrystalChanceStart", "CrystalChanceEnd") + " + ThemeCrystalBonus"),
            setv("SolidChance", "=", L("SolidChanceStart", "SolidChanceEnd") + " + ThemeSolidBonus"),
            setv("BreakChance", "=", L("BreakChanceStart", "BreakChanceEnd")),
            setv("WormChance", "=", L("WormChanceStart", "WormChanceEnd")),
            setv("FissureChance", "=", L("FissureChanceStart", "FissureChanceEnd")),
            setv("WormSpeed", "=", L("WormSpeedStart", "WormSpeedEnd")),
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
            ev([isv("RowRoll", ">=", "EmptyChance + WallChance"), isv("RowRoll", "<", "EmptyChance + WallChance + WormChance")], [setv("RowType", "=", "3")]),
            ev([isv("RowRoll", ">=", "EmptyChance + WallChance + WormChance"), isv("RowRoll", "<", "EmptyChance + WallChance + WormChance + FissureChance")], [setv("RowType", "=", "4")]),
            comment("WORM row (RowType 3): only a burrowing worm, sweeping side to side between WormMinX and WormMaxX. Nothing else in the row, so there is always room to slip past it."),
            ev([isv("RowType", "=", "3")], [
                create("Worm", "RandomFloatInRange(WormMinX, WormMaxX)", screen_y("RowWorldY")), setov("Worm", "WorldY", "=", "RowWorldY"),
                setov("Worm", "Dir", "=", "RandomInRange(0, 1) * 2 - 1"), setov("Worm", "Speed", "=", "WormSpeed"),
                A("ChangeColor", "Worm", "RockTint"), A("SetZOrder", "Worm", "=", "5")]),
            comment("FISSURE row (RowType 4): a full-width ground gap. Touching it forces a branch in a random direction (EV_Collisions). The next FissureClearance px stay empty so the player can always recover from either direction."),
            ev([isv("RowType", "=", "4")], [
                create("Fissure", "0", screen_y("RowWorldY")), setov("Fissure", "WorldY", "=", "RowWorldY"), A("SetZOrder", "Fissure", "=", "2")]),
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
                    ev([isv("ObjType", "=", "0"), isv("RowType", ">=", "1"), isv("RowType", "<=", "2"), isv("LaneIter", "=", "CrackLane"), cmp("RandomFloat(1)", "<", "BlockerChance")],
                       [setv("ObjType", "=", "3")], [ev([isv("TypeRoll", ">=", "CrystalChance")], [setv("ObjType", "=", "1")],
                                                       [ev([cmp("RandomFloat(1)", ">=", "0.5")], [setv("ObjType", "=", "2")])])]),
                    ev([isv("ObjType", "=", "1")], spawn("RockSmall", "ObjWorldY", [A("ChangeColor", "RockSmall", "RockTint")])),
                    ev([isv("ObjType", "=", "2")], spawn("RockMedium", "ObjWorldY", [A("ChangeColor", "RockMedium", "RockTint")])),
                    comment("ObjType 3 used to be a hazard crystal; crystals are now collectibles, so this slot is a medium rock."),
                    ev([isv("ObjType", "=", "3")], spawn("RockMedium", "ObjWorldY", [A("ChangeColor", "RockMedium", "RockTint")])),
                    comment("Risky crystal: sometimes a free lane outside the safe corridor gets a crystal (usually a small, valuable one) right between the obstacles."),
                    ev([isv("ObjType", "=", "0"), isv("RowType", "=", "2"), cmp("RandomFloat(1)", "<", "RiskyGemChance")],
                       [setv("GemSize", "=", "0"), setv("ObjWorldY", "=", "RowWorldY")], [ev([cmp("RandomFloat(1)", "<", "0.3")], [setv("GemSize", "=", "1")]), *gem_spawn()]),
                    ev([isv("ObjType", "=", "4")], spawn("BarrierBreakable", "RowWorldY")),
                    ev([isv("ObjType", "=", "5")], spawn("BarrierSolid", "RowWorldY")),
                ]),
                ev([], [setv("LaneIter", "+", "1")]),
            ]),
            comment("Corridor crystal: GemChance per row (Verdant planets get more), placed in the safe corridor between this row and the next, so it is always reachable. Pink small = 5 points (small pickup area), purple medium = 3, blue large = 1."),
            ev([isv("RowType", "<=", "2"), cmp("RandomFloat(1)", "<", "GemChance + ThemeCrystalBonus")], [
                setv("LaneX", "=", "(SafeLane + RandomInRange(0, 1) + 0.5) * LaneWidth"), setv("ObjWorldY", "=", "RowWorldY + RowGap * 0.28"),
                setv("GemRoll", "=", "RandomFloat(1)"), setv("GemSize", "=", "2")], [
                ev([isv("GemRoll", "<", "0.55")], [setv("GemSize", "=", "1")]),
                ev([isv("GemRoll", "<", "0.2")], [setv("GemSize", "=", "0")]),
                *gem_spawn()]),
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
            ev([isv("RowType", "!=", "4")], [setv("NextRowWorldY", "+", "RowGap")]),
            ev([isv("RowType", "=", "4")], [setv("NextRowWorldY", "+", "FissureClearance")]),
        ]),
    ]),
    group("Scroll and clean up", [
        ev([], [sety("Obstacles", screen_y("Obstacles.WorldY")), sety("Powerups", screen_y("Powerups.WorldY"))]),
        ev([posy("Obstacles", ">", "SceneWindowHeight() + 120")], [delete("Obstacles")]),
        ev([posy("Powerups", ">", "SceneWindowHeight() + 120")], [delete("Powerups")]),
        ev([], [sety("Fissure", screen_y("Fissure.WorldY")), sety("Crystal", screen_y("Crystal.WorldY"))]),
        ev([posy("Crystal", ">", "SceneWindowHeight() + 80")], [delete("Crystal")]),
        ev([posy("Fissure", ">", "SceneWindowHeight() + 80")], [delete("Fissure")]),
    ]),
    group("Burrowing worms", [
        comment("Worms move sideways in world space (slowed by Slow Time like everything else) and turn around at WormMinX / WormMaxX."),
        ev([PLAYING], [setx("Worm", "Worm.Dir * Worm.Speed * TimeDelta() * EffectiveSpeed / ScrollSpeed", op="+"),
                       scaley("Worm", "=", "1 + 0.07 * sin(TimeFromStart() * 12 + Worm.X() * 0.05)")]),
        ev([posx("Worm", "<", "WormMinX"), C("NumberObjectVariable", "Worm", "Dir", "<", "0")], [setov("Worm", "Dir", "=", "1")]),
        ev([posx("Worm", ">", "WormMaxX"), C("NumberObjectVariable", "Worm", "Dir", ">", "0")], [setov("Worm", "Dir", "=", "-1")]),
        ev([C("NumberObjectVariable", "Worm", "Dir", "<", "0")], [A("FlippableCapability::FlippableBehavior::FlipX", "Worm", "Flippable", "yes")]),
        ev([C("NumberObjectVariable", "Worm", "Dir", ">", "0")], [A("FlippableCapability::FlippableBehavior::FlipX", "Worm", "Flippable", "no")]),
    ]),
]

ev_powerups = [
    comment("POWER-UPS — Slow Time: EffectiveSpeed x SlowTimeFactor (0.6 = 40% slower) for SlowTimeDuration real seconds; distance still follows real progress. Crack Strength: StrengthMaxCharges charges, each breaks one rock or breakable barrier (see EV_Collisions); crystals and solid barriers can't be broken. Picking it up again refills to max."),
    group("Pick up", [
        ev([PLAYING, C("CollisionNP", "CrackHitbox", "PowerSlow", "", "", "")], [
            setv("SlowTimeRemaining", "=", "SlowTimeDuration"), snd("sfx_powerup", "80"), create("ImpactFlash", "PowerSlow.X()", "PowerSlow.Y()"),
            color("ImpactFlash", "120;180;255"), A("SetZOrder", "ImpactFlash", "=", "12"), delete("PowerSlow")]),
        ev([PLAYING, C("CollisionNP", "CrackHitbox", "PowerStrength", "", "", "")], [
            setv("StrengthCharges", "=", "StrengthMaxCharges"), snd("sfx_powerup", "80", "1.2"), create("ImpactFlash", "PowerStrength.X()", "PowerStrength.Y()"),
            color("ImpactFlash", "255;140;60"), A("SetZOrder", "ImpactFlash", "=", "12"), delete("PowerStrength")]),
    ]),
    group("Crystals (points)", [
        comment("Collecting a crystal adds its Value to RunCrystals (this run) and CrystalWallet (saved; spent in the Shop)."),
        ev([PLAYING, C("CollisionNP", "CrackHitbox", "Crystal", "", "", "")], [
            setv("RunCrystals", "+", "Crystal.Value"), setv("CrystalWallet", "+", "Crystal.Value"),
            snd("sfx_crystal", "70", "1 + (Crystal.Value - 1) * 0.1"),
            create("ImpactFlash", "Crystal.X()", "Crystal.Y()"), color("ImpactFlash", "150;235;255"), scale("ImpactFlash", "=", "0.5"), A("SetZOrder", "ImpactFlash", "=", "12"),
            delete("Crystal")]),
        ev([], [text("GemText", "ToString(RunCrystals)"), A("AnimatableCapability::AnimatableBehavior::SetIndex", "GemIcon", "Animation", "=", "0"),
                scale("Crystal", "+", "0")]),
    ]),
    group("Timers and HUD", [
        ev([PLAYING, isv("PowerupCooldown", ">", "0")], [setv("PowerupCooldown", "-", "TimeDelta()")]),
        ev([PLAYING, isv("SlowTimeRemaining", ">", "0")], [
            setv("SlowTimeRemaining", "-", "TimeDelta()"), A("TiledSpriteObject::SetColor", "Backgrounds", '"150;185;255"'), A("Show", "SlowText", ""),
            text("SlowText", '"SLOW " + ToString(round(max(0, SlowTimeRemaining) * 10) / 10)')]),
        ev([isv("SlowTimeRemaining", "<=", "0")], [A("TiledSpriteObject::SetColor", "Backgrounds", '"255;255;255"'), A("Hide", "SlowText")]),
        ev([isv("StrengthCharges", ">", "0")], [A("Show", "StrengthText", ""), text("StrengthText", '"STRENGTH x" + ToString(StrengthCharges)')]),
        ev([isv("StrengthCharges", "<=", "0")], [A("Hide", "StrengthText")]),
        comment("Crack colour shows Strength: orange-red while charged."),
        ev([PLAYING, isv("StrengthCharges", ">", "0")], [color("CrackTip", "255;120;60")]),
        ev([PLAYING, isv("StrengthCharges", "<=", "0")], [color("CrackTip", "255;255;255")]),
        ev([], [scale("Powerups", "=", "1 + 0.1 * sin(TimeFromStart() * 6)")]),
    ]),
]

ev_collisions = [
    comment("FISSURE: touching a ground gap forces an immediate branch in a random direction (even mid-branch). Each fissure triggers once."),
    ev([PLAYING, C("CollisionNP", "CrackHitbox", "Fissure", "", "", ""), C("BooleanObjectVariable", "Fissure", "Used", "False", "")], [
        A("SetBooleanObjectVariable", "Fissure", "Used", "True", ""),
        setv("BranchDirection", "=", "RandomInRange(0, 1) * 2 - 1"), setv("BranchTimer", "=", "0"), setv("BranchStartX", "=", "CrackWorldX"),
        setv("CooldownTimer", "=", "0"), A("Hide", "HintText"), snd("sfx_fissure", "90"),
        create("ImpactFlash", "CrackWorldX", "TipScreenY"), color("ImpactFlash", "255;160;60"), A("SetZOrder", "ImpactFlash", "=", "12"),
    ], [spark_burst("8", "BranchDirection * RandomFloatInRange(100, 320)", "RandomFloatInRange(-200, 60)")]),
    comment("COLLISIONS — only the small hidden CrackHitbox at the tip is tested. Order matters: first Crack Strength breaks Breakable obstacles (rocks, breakable barriers), then anything still touched kills, unless InvulnerabilityRemaining > 0 (used by the revive in Phase 3)."),
    ev([PLAYING, isv("StrengthCharges", ">", "0"), C("CollisionNP", "CrackHitbox", "Breakable", "", "", "")], [
        create("ImpactFlash", "Breakable.X()", "Breakable.Y()"), A("SetZOrder", "ImpactFlash", "=", "12"),
        delete("Breakable"), setv("StrengthCharges", "-", "1"), snd("sfx_break", "80"),
    ], [spark_burst("10", "RandomFloatInRange(-300, 300)", "RandomFloatInRange(-300, 100)")]),
    ev([PLAYING, isv("InvulnerabilityRemaining", "<=", "0"), C("CollisionNP", "CrackHitbox", "Obstacles", "", "", "")], [
        sets("GameState", '"GameOver"'), setv("BranchDirection", "=", "0"), snd("sfx_crash", "90"), snd("jingle_gameover", "65"),
        create("ImpactFlash", "CrackWorldX", "TipScreenY"), A("SetZOrder", "ImpactFlash", "=", "12"),
        color("CrackTip", "255;90;70"),
        text("FinalDistanceText", '"DISTANCE: " + ToString(Distance) + " m"'),
        A("Hide", "HintText"), save_wallet(),
        text("GameOverGemsText", '"CRYSTALS +" + ToString(RunCrystals) + "   (TOTAL " + ToString(CrystalWallet) + ")"'),
    ], [
        spark_burst("12", "RandomFloatInRange(-260, 260)", "RandomFloatInRange(-320, 120)"),
        ev([C("BooleanVariable", "ReviveUsed", "True", "")], [A("Hide", "ReviveButton"), A("Hide", "ReviveLabel")]),
        comment("Endless: best distance. Planet Breaker: best planets broken. Both saved locally."),
        ev([ENDLESS], [A("Hide", "GameOverPlanetsText"), text("GameOverBestText", '"BEST: " + ToString(BestEndlessDistance) + " m"')],
           [ev([cmp("Distance", ">", "BestEndlessDistance")], [
                setv("BestEndlessDistance", "=", "Distance"), A("EcrireFichierExp", SAVE, KEY, "BestEndlessDistance"),
                A("Show", "NewBestText", ""), text("GameOverBestText", '"BEST: " + ToString(BestEndlessDistance) + " m"')])]),
        ev([iss("GameMode", '"Planet"')], [A("Show", "GameOverPlanetsText", ""), text("GameOverPlanetsText", '"PLANETS BROKEN: " + ToString(PlanetsBroken)'),
                 text("FinalDistanceText", '"TOTAL DISTANCE: " + ToString(Distance) + " m"'),
                 text("GameOverBestText", '"BEST: " + ToString(BestPlanetsBroken) + " PLANETS"')],
           [ev([cmp("PlanetsBroken", ">", "BestPlanetsBroken")], [
                setv("BestPlanetsBroken", "=", "PlanetsBroken"), A("EcrireFichierExp", SAVE, KEYP, "BestPlanetsBroken"),
                A("Show", "NewBestText", ""), text("GameOverBestText", '"BEST: " + ToString(BestPlanetsBroken) + " PLANETS"')])]),
        ev([], [A("SetCenterX", "GameOverPlanetsText", "=", "SceneWindowWidth() / 2"), A("SetCenterX", "GameOverGemsText", "=", "SceneWindowWidth() / 2"), A("SetCenterX", "ReviveLabel", "=", "SceneWindowWidth() / 2"),
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
    ev([iss("GameMode", '"Planet"')], [text("BestText", '"PLANETS BROKEN: " + ToString(PlanetsBroken) + "   BEST: " + ToString(BestPlanetsBroken)'),
                 A("SetCenterX", "BestText", "=", "SceneWindowWidth() / 2")]),
]


PLANET = iss("GameMode", '"Planet"')
def theme(i, name, rocktint, cb, wb, sb, bg):
    hide = [A("Hide", o) for o in ("BgEmber", "BgVerdant", "BgFrost") if o != bg]
    return ev([isv("PlanetTheme", "=", str(i))], [sets("PlanetName", f'"{name}"'), sets("RockTint", f'"{rocktint}"'),
        setv("ThemeCrystalBonus", "=", cb), setv("ThemeWallBonus", "=", wb), setv("ThemeSolidBonus", "=", sb),
        setv("PlanetTargetDistance", "=", "PlanetDistanceStep * (PlanetIndex + 1)"),
        A("Show", bg, "")] + hide)
EASE = "(1 - pow(1 - clamp({}, 0, 1), 3))"
ev_planet = [
    comment("PLANET BREAKER — same engine as Endless; this sheet only adds planet themes, the surface progress bar and the planet-splitting sequence. Planet N needs N x PlanetDistanceStep metres (1000, 2000, 3000...). Themes cycle Ember -> Verdant -> Frost (ThemeCount); every planet is faster and harder (see EV_CrackMovement)."),
    group("Planet setup", [
        comment("Runs once at scene start and after every broken planet: picks the theme, target distance and theme modifiers (Verdant = more crystals, Frost = more barriers/solid barriers)."),
        ev([PLANET, C("BooleanVariable", "PlanetSetupPending", "True", "")], [
            A("SetBooleanVariable", "PlanetSetupPending", "False", ""),
            setv("PlanetTheme", "=", "mod(PlanetIndex, ThemeCount)"),
            setv("PlanetStartWorldY", "=", "CrackWorldY"),
        ], [
            theme(0, "EMBER", "255;255;255", "-0.04", "0", "0", "BgEmber"),
            theme(1, "VERDANT", "200;240;205", "0.15", "0", "0", "BgVerdant"),
            theme(2, "FROST", "190;215;255", "0", "0.15", "0.08", "BgFrost"),
        ]),
    ]),
    group("Progress toward the surface", [
        ev([PLANET], [
            setv("PlanetDistance", "=", "max(0, floor((CrackWorldY - PlanetStartWorldY) / PixelsPerMeter))"),
            A("ResizableCapability::ResizableBehavior::SetWidth", "ProgressFill", "Resizable", "=", "max(1, 396 * min(1, PlanetDistance / PlanetTargetDistance))"),
            text("PlanetHudText", '"PLANET " + ToString(PlanetIndex + 1) + "  " + PlanetName + "   " + ToString(min(PlanetDistance, PlanetTargetDistance)) + " / " + ToString(PlanetTargetDistance) + " m"'),
            A("SetCenterX", "PlanetHudText", "=", "SceneWindowWidth() / 2"),
        ], [ev([isv("PlanetTheme", "=", "0")], [color("ProgressFill", "255;150;50")]),
            ev([isv("PlanetTheme", "=", "1")], [color("ProgressFill", "90;240;180")]),
            ev([isv("PlanetTheme", "=", "2")], [color("ProgressFill", "160;190;255")])]),
    ]),
    group("Reach the surface -> break the planet", [
        ev([PLANET, PLAYING, cmp("PlanetDistance", ">=", "PlanetTargetDistance")], [
            sets("GameState", '"PlanetBreak"'), setv("BreakTime", "=", "0"), A("SetBooleanVariable", "BreakBurstDone", "False", ""),
            setv("BranchDirection", "=", "0"), setv("SlowTimeRemaining", "=", "0"),
            delete("Obstacles"), delete("Powerups"), delete("Crystal"), save_wallet(),
            setv("PlanetCX", "=", "SceneWindowWidth() / 2"), setv("PlanetCY", "=", "SceneWindowHeight() * 0.42"),
            A("AnimatableCapability::AnimatableBehavior::SetIndex", "PlanetLeft", "Animation", "=", "PlanetTheme"),
            A("AnimatableCapability::AnimatableBehavior::SetIndex", "PlanetRight", "Animation", "=", "PlanetTheme"),
            text("PlanetBrokenText", 'PlanetName + " BROKEN!"'), A("Hide", "PlanetBrokenText"),
            A("ShowLayer", "", '"Cinematic"'),
        ]),
        comment("Event-driven animation (BreakTime seconds): 0-0.35 planet pops in, 0.35-0.75 a glowing crack runs down its centre, 0.75-1.45 the two halves fly apart with an ease-out, then a message; at BreakDuration the next planet starts."),
        ev([iss("GameState", '"PlanetBreak"')], [
            setv("BreakTime", "+", "TimeDelta()"),
            setv("SplitOffset", "=", "170 * " + EASE.format("(BreakTime - 0.75) / 0.7")),
            scale("PlanetLeft", "=", EASE.format("BreakTime / 0.35")), scale("PlanetRight", "=", EASE.format("BreakTime / 0.35")),
            setx("PlanetLeft", "PlanetCX - SplitOffset"), sety("PlanetLeft", "PlanetCY + SplitOffset * 0.15"),
            setx("PlanetRight", "PlanetCX + SplitOffset"), sety("PlanetRight", "PlanetCY - SplitOffset * 0.15"),
            A("SetAngle", "PlanetLeft", "=", "-SplitOffset * 0.08"), A("SetAngle", "PlanetRight", "=", "SplitOffset * 0.08"),
            A("SetCenterX", "PlanetBrokenText", "=", "PlanetCX"), sety("PlanetBrokenText", "PlanetCY + 200"),
        ], [
            ev([isv("BreakTime", ">=", "0.75"), C("BooleanVariable", "BreakBurstDone", "False", "")], [
                A("SetBooleanVariable", "BreakBurstDone", "True", ""), A("Show", "PlanetBrokenText", ""), snd("sfx_break", "85", "0.8"), snd("jingle_planet", "70"),
                create("ImpactFlash", "PlanetCX", "PlanetCY", '"Cinematic"'), scale("ImpactFlash", "=", "2.5"), A("SetZOrder", "ImpactFlash", "=", "5"),
            ], [spark_burst("16", "RandomFloatInRange(-420, 420)", "RandomFloatInRange(-420, 420) - EffectiveSpeed", "PlanetCX", "PlanetCY")]),
            ev([isv("BreakTime", ">=", "BreakDuration")], [
                setv("PlanetsBroken", "+", "1"), setv("PlanetIndex", "+", "1"),
                A("SetBooleanVariable", "PlanetSetupPending", "True", ""),
                setv("NextRowWorldY", "=", "CrackWorldY + TipScreenY + FirstRowOffset"),
                A("HideLayer", "", '"Cinematic"'), sets("GameState", '"Playing"'),
            ]),
        ]),
    ]),
]

ev_revive = [
    comment("REVIVE (modular). Anything that sets RequestRevive = true while GameState is GameOver triggers it: today the SIMULATE AD REVIVE (TEST) button, later the Playgama rewarded-ad callback. One revive per run (ReviveUsed). Score, distance, speed, difficulty and planet progress are all kept."),
    ev([C("BooleanVariable", "RequestRevive", "True", "")], [A("SetBooleanVariable", "RequestRevive", "False", "")], [
        ev([GAMEOVER, C("BooleanVariable", "ReviveUsed", "False", "")], [
            A("SetBooleanVariable", "ReviveUsed", "True", ""), snd("sfx_revive", "80"),
        ] + [
            setv("InvulnerabilityRemaining", "=", "ReviveInvulnerability"),
            setv("GameOverTime", "=", "0"), setv("BranchDirection", "=", "0"), setv("CooldownTimer", "=", "0"),
            A("HideLayer", "", '"GameOver"'), A("Hide", "NewBestText"), color("CrackTip", "255;255;255"),
            sets("GameState", '"Playing"'),
        ], [
            comment("Clear lethal obstacles around the crack so it can't die again immediately (the 2 s protection covers the rest)."),
            ev([C("NumberObjectVariable", "Obstacles", "WorldY", "<", "CrackWorldY + ReviveClearAhead"),
                C("NumberObjectVariable", "Obstacles", "WorldY", ">", "CrackWorldY - ReviveClearBehind")], [delete("Obstacles")]),
        ]),
    ]),
    comment("Protective glow while invulnerable."),
    ev([isv("InvulnerabilityRemaining", ">", "0")], [A("Show", "ShieldGlow", ""), setx("ShieldGlow", "CrackWorldX"), sety("ShieldGlow", "TipScreenY"),
        scale("ShieldGlow", "=", "1 + 0.08 * sin(TimeFromStart() * 18)"), opacity("ShieldGlow", "=", "160 + 95 * sin(TimeFromStart() * 18)")]),
    ev([isv("InvulnerabilityRemaining", "<=", "0")], [A("Hide", "ShieldGlow")]),
]

external_events = [("EV_GameState", ev_gamestate), ("EV_PlanetMode", ev_planet), ("EV_CrackMovement", ev_movement), ("EV_ObstacleSpawner", ev_spawner),
                   ("EV_Powerups", ev_powerups), ("EV_Trail", ev_trail), ("EV_Collisions", ev_collisions), ("EV_Revive", ev_revive), ("EV_Scoring", ev_scoring)]
scene_events = [comment("CRACKLINE — Phase 3. Endless Depth and Planet Breaker share this one scene (GameMode global). Each system lives in its own external events sheet (Project manager > External events). Order matters.")] + \
    [link(n) for n, _ in external_events]

ui_settings = {"grid": False, "gridType": "rectangular", "gridWidth": 32, "gridHeight": 32, "gridOffsetX": 0, "gridOffsetY": 0, "gridColor": 10401023,
               "gridAlpha": 0.8, "snap": False, "zoomFactor": 0.5, "windowMask": True}
layout = {"b": 40, "disableInputWhenNotFocused": True, "mangledName": "Gameplay", "name": "Gameplay", "r": 110, "standardSortMethod": True,
          "stopSoundsOnStartup": False, "title": "", "v": 60, "uiSettings": ui_settings, "objectsGroups": groups, "variables": scene_vars,
          "instances": instances, "objects": objects, "objectsFolderStructure": folders, "events": scene_events,
          "layers": [layer(""), layer("Cinematic", visible=False), layer("HUD"), layer("GameOver", visible=False)], "behaviorsSharedData": []}


# ---------------------------------------------------------------- MAIN MENU scene
CY = "SceneWindowHeight() / 2"
menu_objects = [
    {"assetStoreId": "", "name": "MenuBg", "type": "TiledSpriteObject::TiledSprite", "texture": "bg_soil", "width": 720, "height": 3000, "variables": [], "effects": [], "behaviors": []},
    textobj("TitleText", "CRACKLINE", 110, rgb="255;214;120"),
    textobj("SubtitleText", "SPLIT THE WORLD", 34, rgb="255;240;214"),
    textobj("MenuBestText", "BEST: 0 m   |   0 PLANETS", 28, rgb="255;220;160"),
    textobj("MenuWalletText", "CRYSTALS: 0", 30, rgb="160;240;255"),
    sprite("EndlessButton", "ui_button", origin=(180, 55)), textobj("EndlessLabel", "ENDLESS DEPTH", 40, rgb="80;26;6"),
    sprite("PlanetButton", "ui_button", origin=(180, 55)), textobj("PlanetLabel", "PLANET BREAKER", 38, rgb="80;26;6"),
    sprite("ShopButton", "ui_button_blue", origin=(180, 55)), textobj("ShopLabel", "SHOP", 44, rgb="255;255;255"),
    sprite("MuteButton", "icon_audio_on", origin=(50, 50), anims=[("On", "icon_audio_on"), ("Off", "icon_audio_off")]),
]
menu_instances = [inst("MenuBg", 0, -800, z=-10, w=720, h=3200), inst("TitleText", 60, 220, z=2), inst("SubtitleText", 210, 350, z=2),
                  inst("MenuBestText", 150, 420, z=2), inst("MenuWalletText", 240, 460, z=2),
                  inst("EndlessButton", 360, 620, z=2), inst("EndlessLabel", 210, 594, z=3),
                  inst("PlanetButton", 360, 750, z=2), inst("PlanetLabel", 200, 725, z=3),
                  inst("ShopButton", 360, 880, z=2), inst("ShopLabel", 300, 852, z=3), inst("MuteButton", 670, 50, z=4)]
def tapped(obj, layer='""'): return [C("HasAnyTouchOrMouseStarted", ""), C("CollisionPoint", obj, f'TouchX(StartedTouchOrMouseId(0), {layer})', f'TouchY(StartedTouchOrMouseId(0), {layer})')]
def center_all(*objs): return [A("SetCenterX", o, "=", "SceneWindowWidth() / 2") for o in objs]
menu_events = [
    comment("MAIN MENU — pick a mode or open the Shop. Both modes open the same Gameplay scene; only the global GameMode differs."),
    comment("Positions are offsets from the screen centre so the menu fits any portrait height (and a square window)."),
    ev([C("SceneJustBegins", "")], [
        sety("TitleText", f"{CY} - 340"), sety("SubtitleText", f"{CY} - 205"),
        sety("MenuBestText", f"{CY} - 145"), sety("MenuWalletText", f"{CY} - 100"),
        sety("EndlessButton", f"{CY} + 25"), sety("EndlessLabel", "EndlessButton.Y() - 24"),
        sety("PlanetButton", f"{CY} + 150"), sety("PlanetLabel", "PlanetButton.Y() - 24"),
        sety("ShopButton", f"{CY} + 275"), sety("ShopLabel", "ShopButton.Y() - 27"),
        sety("MuteButton", f"{CY} + 275"), scale("MuteButton", "=", "0.75"),
    ], load_profile() + [
        ev([], [text("MenuBestText", '"BEST: " + ToString(BestEndlessDistance) + " m   |   " + ToString(BestPlanetsBroken) + " PLANETS"'),
                text("MenuWalletText", '"CRYSTALS: " + ToString(CrystalWallet)')]),
    ]),
    ev([], [A("TiledSpriteObject::YOffset", "MenuBg", "=", "-TimeFromStart() * 60")] +
            center_all("TitleText", "SubtitleText", "EndlessLabel", "PlanetLabel", "ShopLabel", "MenuBestText", "MenuWalletText")),
    ev(tapped("EndlessButton"), [snd("sfx_click", "80"), sets("GameMode", '"Endless"'), A("Scene", "", '"Gameplay"', "")]),
    ev(tapped("PlanetButton"), [snd("sfx_click", "80"), sets("GameMode", '"Planet"'), A("Scene", "", '"Gameplay"', "")]),
    ev(tapped("ShopButton"), [snd("sfx_click", "80"), A("Scene", "", '"Shop"', "")]),
] + mute_events() + [
]
def simple_layout(name, objs, insts, events, groups=(), variables=()):
    return {"b": 40, "disableInputWhenNotFocused": True, "mangledName": name, "name": name, "r": 110, "standardSortMethod": True,
            "stopSoundsOnStartup": False, "title": "", "v": 60, "uiSettings": ui_settings, "objectsGroups": list(groups), "variables": list(variables),
            "instances": insts, "objects": objs,
            "objectsFolderStructure": {"folderName": "__ROOT", "children": [{"objectName": o["name"]} for o in objs]},
            "events": events, "layers": [layer("")], "behaviorsSharedData": []}
menu_layout = simple_layout("MainMenu", menu_objects, menu_instances, menu_events)

# ---------------------------------------------------------------- SHOP scene
def sidx(): return [num("StyleIndex", 0)]
shop_objects = [
    {"assetStoreId": "", "name": "ShopBg", "type": "TiledSpriteObject::TiledSprite", "texture": "bg_soil", "width": 720, "height": 3000, "variables": [], "effects": [], "behaviors": []},
    textobj("ShopTitle", "CRACK STYLES", 46, rgb="255;214;120", align="left"),
    textobj("WalletText", "CRYSTALS: 0", 30, rgb="160;240;255", align="left"),
    sprite("ShopCard", "ui_card", origin=(150, 100), variables=sidx()),
    sprite("ShopTrail", "trail_classic", origin=(0, 24), variables=sidx(), anims=[(s, f"trail_{s.lower()}") for s in STYLES]),
    sprite("ShopTip", "tip_classic", origin=(64, 64), variables=sidx(), anims=[(s, f"tip_{s.lower()}") for s in STYLES]),
    textobj("ShopName", "CLASSIC", 28, rgb="255;240;214"),
    textobj("ShopPrice", "EQUIPPED", 22, rgb="255;220;120"),
    sprite("BackButton", "ui_button", origin=(180, 55)), textobj("BackLabel", "BACK", 44, rgb="80;26;6"),
    textobj("ShopMsg", "", 30, rgb="255;255;255"),
]
for o in shop_objects:
    if o["name"] in ("ShopName", "ShopPrice"): o["variables"] = sidx()
def sinst(name, k, z):
    d = inst(name, 0, 0, z=z); d["persistentUuid"] = uid(f"shop-{name}-{k}")
    d["initialVariables"] = [{"name": "StyleIndex", "type": "number", "value": k}]; return d
shop_instances = [inst("ShopBg", 0, -800, z=-10, w=720, h=3200), inst("ShopTitle", 30, 20, z=2), inst("WalletText", 420, 30, z=2),
                  inst("BackButton", 360, 1180, z=2), inst("BackLabel", 300, 1150, z=3), inst("ShopMsg", 200, 1080, z=4)] + \
                 [sinst(n, k, z) for k in range(len(STYLES)) for n, z in (("ShopCard", 1), ("ShopTrail", 2), ("ShopTip", 3), ("ShopName", 4), ("ShopPrice", 4))]
COLX = "(190 + mod({o}.StyleIndex, 2) * 340)"
ROWY = f"({CY} - 205 + floor({{o}}.StyleIndex / 2) * 170)"
def place(o, dx, dy, center=False):
    acts = [sety(o, ROWY.format(o=o) + f" + {dy}")]
    acts.append(A("SetCenterX", o, "=", COLX.format(o=o) + f" + {dx}") if center else setx(o, COLX.format(o=o) + f" + {dx}"))
    return acts
shop_events = [
    comment("SHOP — crack styles. Prices and names live in the global arrays StylePrices / StyleNames (index = StyleIndex 0-5). Owned styles are a string of 0/1 flags (OwnedStyles, e.g. \"110000\"); EquippedStyle is the index in use. Everything is saved on the device. NOTE: Playgama will require its Bridge storage instead."),
    ev([C("SceneJustBegins", "")], [scale("ShopCard", "=", "0.8"), scale("ShopTip", "=", "0.55"), scalex("ShopTrail", "=", "6.5"), scaley("ShopTrail", "=", "0.55"),
        scale("BackButton", "=", "0.7"), sety("ShopTitle", f"{CY} - 352"), sety("WalletText", f"{CY} - 342"),
        sety("BackButton", f"{CY} + 312"), sety("BackLabel", "BackButton.Y() - 27"), sety("ShopMsg", f"{CY} + 222")]
       + place("ShopCard", 0, 0) + place("ShopTrail", -104, -6) + place("ShopTip", 0, -6)
       + [A("AnimatableCapability::AnimatableBehavior::SetIndex", "ShopTrail", "Animation", "=", "ShopTrail.StyleIndex"),
          A("AnimatableCapability::AnimatableBehavior::SetIndex", "ShopTip", "Animation", "=", "ShopTip.StyleIndex")],
       load_profile()),
    comment("Card texts, refreshed every frame: name, and EQUIPPED / OWNED / price."),
    {"type": "BuiltinCommonInstructions::ForEach", "object": "ShopName", "conditions": [], "actions": [text("ShopName", "StyleNames[ShopName.StyleIndex]")] + place("ShopName", 0, -66, center=True), "events": []},
    {"type": "BuiltinCommonInstructions::ForEach", "object": "ShopPrice", "conditions": [], "actions": [
        text("ShopPrice", '"PRICE: " + ToString(StylePrices[ShopPrice.StyleIndex])'), A("TextObject::ChangeColor", "ShopPrice", '"160;240;255"')], "events": [
        ev([C("BuiltinCommonInstructions::CompareStrings", "SubStr(OwnedStyles, ShopPrice.StyleIndex, 1)", "=", '"1"')], [text("ShopPrice", '"OWNED: TAP TO USE"'), A("TextObject::ChangeColor", "ShopPrice", '"255;240;214"')]),
        ev([C("NumberObjectVariable", "ShopPrice", "StyleIndex", "=", "EquippedStyle")], [text("ShopPrice", '"EQUIPPED"'), A("TextObject::ChangeColor", "ShopPrice", '"120;255;160"')]),
        ev([], place("ShopPrice", 0, 34, center=True))]},
    ev([], [color("ShopCard", "255;255;255"), text("WalletText", '"CRYSTALS: " + ToString(CrystalWallet)'), A("SetCenterX", "BackLabel", "=", "SceneWindowWidth() / 2"),
            A("SetCenterX", "ShopMsg", "=", "SceneWindowWidth() / 2"), A("SetX", "WalletText", "=", "SceneWindowWidth() - 30 - WalletText.Width()")]),
    ev([C("NumberObjectVariable", "ShopCard", "StyleIndex", "=", "EquippedStyle")], [color("ShopCard", "140;255;170")]),
    comment("Tap a card: equip it if owned; otherwise buy it if you have enough crystals (then equip and save); otherwise say how many more you need."),
    ev(tapped("ShopCard"), [setv("ShopSel", "=", "ShopCard.StyleIndex"), setv("ShopOwned", "=", "0"), setv("MsgTime", "=", "1.8")], [
        ev([C("BuiltinCommonInstructions::CompareStrings", "SubStr(OwnedStyles, ShopSel, 1)", "=", '"1"')], [setv("ShopOwned", "=", "1")]),
        ev([isv("ShopOwned", "=", "1")], [setv("EquippedStyle", "=", "ShopSel"), A("EcrireFichierExp", SAVE, KE, "EquippedStyle"),
                                          text("ShopMsg", 'StyleNames[ShopSel] + " EQUIPPED"'), snd("sfx_click", "80")]),
        ev([isv("ShopOwned", "=", "0"), cmp("CrystalWallet", ">=", "StylePrices[ShopSel]")], [
            setv("CrystalWallet", "-", "StylePrices[ShopSel]"),
            sets("OwnedStyles", 'SubStr(OwnedStyles, 0, ShopSel) + "1" + SubStr(OwnedStyles, ShopSel + 1, 99)'),
            setv("EquippedStyle", "=", "ShopSel"),
            A("EcrireFichierExp", SAVE, KW, "CrystalWallet"), A("EcrireFichierTxt", SAVE, KO, "OwnedStyles"), A("EcrireFichierExp", SAVE, KE, "EquippedStyle"),
            text("ShopMsg", '"UNLOCKED " + StyleNames[ShopSel] + "!"'), snd("sfx_buy", "75")]),
        ev([isv("ShopOwned", "=", "0"), cmp("CrystalWallet", "<", "StylePrices[ShopSel]")], [
            text("ShopMsg", '"NEED " + ToString(StylePrices[ShopSel] - CrystalWallet) + " MORE CRYSTALS"'), snd("sfx_error", "80")]),
    ]),
    ev([isv("MsgTime", ">", "0")], [setv("MsgTime", "-", "TimeDelta()"), opacity("ShopMsg", "=", "255 * clamp(MsgTime / 0.4, 0, 1)")]),
    ev([isv("MsgTime", "<=", "0")], [opacity("ShopMsg", "=", "0")]),
    ev([], [A("TiledSpriteObject::YOffset", "ShopBg", "=", "-TimeFromStart() * 30")]),
    ev(tapped("BackButton"), [snd("sfx_click", "80"), A("Scene", "", '"MainMenu"', "")]),
]
shop_layout = simple_layout("Shop", shop_objects, shop_instances, shop_events,
                            variables=[num("ShopSel", 0), num("ShopOwned", 0), num("MsgTime", 0)])

project = {
    "firstLayout": "MainMenu",
    "gdVersion": {"build": 99, "major": 4, "minor": 0, "revision": 0},
    "properties": {
        "adaptGameResolutionAtRuntime": True, "antialiasingMode": "none", "antialisingEnabledOnMobile": False, "folderProject": False,
        "orientation": "portrait", "packageName": "com.lonewolfproduction.crackline", "pixelsRounding": False,
        "projectUuid": uid("project"), "scaleMode": "linear", "sizeOnStartupMode": "adaptHeight", "templateSlug": "",
        "useExternalSourceFiles": False, "version": "0.3.0", "name": "CRACKLINE", "description": "Phase 3 - Endless Depth + Planet Breaker", "author": "",
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
    "objects": [], "objectsGroups": [], "variables": global_vars, "layouts": [menu_layout, shop_layout, layout],
    "externalEvents": [{"associatedLayout": "Gameplay", "lastChangeTimeStamp": 0, "name": n, "events": e} for n, e in external_events],
    "eventsFunctionsExtensions": [], "externalLayouts": [], "externalSourceFiles": [],
}
os.makedirs(OUT, exist_ok=True)
with open(os.path.join(OUT, "game.json"), "w") as f: json.dump(project, f, indent=2)
print("wrote", os.path.join(OUT, "game.json"))
