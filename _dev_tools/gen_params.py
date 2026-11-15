# Shared constants for the Phase 2 procedural generator (used by build_project.py and gen_sim.py).
LANE_COUNT = 7
LANE_W = 720 / LANE_COUNT

# hit shapes (collision polygons in game.json are built from these)
HIT = {
    "RockSmall": ("circle", 28), "RockMedium": ("circle", 44), "Crystal": ("circle", 28),
    "BarrierBreakable": ("rect", 50, 26), "BarrierSolid": ("rect", 50, 26),   # half-width, half-height
}
IMG = {"RockSmall": 76, "RockMedium": 116, "Crystal": 96, "BarrierBreakable": (112, 64), "BarrierSolid": (112, 64)}
BREAKABLE = {"RockSmall", "RockMedium", "BarrierBreakable"}

P = dict(
    BaseSpeed=180, MaxSpeed=420, SpeedGrowth=1.08, SpeedGrowthInterval=20,
    DifficultyRampTime=180,
    RowGapStart=320, RowGapEnd=210,
    DensityStart=0.30, DensityEnd=0.65,
    EmptyChanceStart=0.25, EmptyChanceEnd=0.05,
    WallChanceStart=0.05, WallChanceEnd=0.22,
    CrystalChanceStart=0.05, CrystalChanceEnd=0.30,
    SolidChanceStart=0.00, SolidChanceEnd=0.12,
    BreakChanceStart=0.05, BreakChanceEnd=0.15,
    WallBreakableShare=0.6,
    LaneJitterX=8, RowJitterY=18,
    FirstRowOffset=600,          # first row this far above the top of the screen (warm-up)
    PowerupChance=0.12, PowerupCooldownTime=10,
    SlowTimeDuration=4, SlowTimeFactor=0.6, StrengthMaxCharges=3,
)
