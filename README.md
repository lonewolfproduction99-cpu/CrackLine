# CRACKLINE — Phase 1 prototype (GDevelop)

Portrait 720×1280 arcade prototype. All gameplay is native GDevelop events, with no JavaScript.

## Open it

**On the tablet (web editor):** open
`https://editor.gdevelop.io/?project=https://raw.githubusercontent.com/lonewolfproduction99-cpu/CrackLine/main/game.json`
then press **Preview** (▶). Use **File → Save as** (cloud) to keep your own editable copy.

**On a desktop:** unzip, then use GDevelop → Open project → `crackline/game.json`.

## How to play
Tap the left half of the screen to branch left and the right half to branch right. A mouse click works the same way. Avoid the rocks. When you crash, tap **RESTART**.

## Where things are
| What | Where in GDevelop |
|---|---|
| Scene | `Gameplay` (layers: base, `HUD`, `GameOver`) |
| Game state, restart, game-over overlay | External events `EV_GameState` |
| Taps, branching, forward motion, scrolling | `EV_CrackMovement` |
| Obstacle chunks (spawning, scrolling, cleanup) | `EV_ObstacleSpawner` |
| Fracture trail and sparks | `EV_Trail` |
| Death on collision | `EV_Collisions` |
| Distance HUD | `EV_Scoring` |
| Obstacle patterns | External layouts `Chunk0` … `Chunk8` (edit them visually) |

The scene's own event sheet only links these sheets, in this order.

## Tuning (scene variables of `Gameplay`)
| Variable | Default | Meaning |
|---|---|---|
| BaseSpeed | 180 | scroll speed (px/s) |
| BranchDistance | 65 | sideways px per tap |
| BranchDuration | 0.18 | seconds per branch |
| BranchCooldown | 0.08 | lockout after a branch |
| TipScreenRatio | 0.7 | tip height on screen |
| EdgeMargin | 30 | closest the crack gets to the screen edge |
| PixelsPerMeter | 20 | distance unit |
| TrailStep / TrailJitter / TrailMaxSegments | 14 / 6 / 160 | trail density, jaggedness and cap |
| ChunkHeight / ChunkCount / ChunkLoopStart | 640 / 9 / 1 | obstacle chunk system |

## Editing obstacle chunks
Each `ChunkN` external layout is a 640 px tall strip. Here, y = 0 is the top of the chunk and y = 640 is the bottom, and x runs from 0 to 720. The grid shows the 7 lanes. Place `RockSmall` and `RockMedium` instances anywhere in it. If you add `Chunk9`, set `ChunkCount` to 10. `Chunk0` is the empty warm-up and only plays once.

## Replacing the art
Every sprite reads one PNG in `assets/`. Overwrite the file with the same name, or change the image in the object editor. Keep these points in mind:
- **RockSmall / RockMedium**: the origin is at the image centre, and the hitbox is an octagon smaller than the rock so it feels forgiving. If you change the image size, redo the hitbox.
- **TrailSegment**: the origin and centre point are on the middle of the left edge. The segment stretches to the right.
- **CrackHitbox** is the real collision box at the tip. It is hidden while playing. **CrackTip** is only the glow.
- `bg_soil.png` is a seamless tile that the `Background` tiled sprite scrolls.
