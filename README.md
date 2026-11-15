# CRACKLINE: Phase 2 (Endless Depth), GDevelop

This is a portrait 720×1280 arcade game. All gameplay is built with native GDevelop events, with no JavaScript.

## Open it
On a tablet or in a browser, open
`https://editor.gdevelop.io/?project=https://raw.githubusercontent.com/lonewolfproduction99-cpu/CrackLine/main/game.json`
and press **Preview** (▶). To keep your own editable copy, use **File → Save as** and choose cloud.

## How to play
- Tap the left or right half of the screen to make the crack branch that way.
- The game keeps speeding up. Survive as long as you can and try to beat your best distance.
- **Blue clock (Slow Time):** the world moves 40% slower for 4 seconds.
- **Orange bolt (Crack Strength):** gives you 3 charges. Each charge smashes one rock or one cracked barrier.
- **Crystals** and **metal-banded barriers** always kill you, even when you have charges.

## Where things are
| What | Where |
|---|---|
| Scene setup, best-score loading, game over, restart | External events `EV_GameState` |
| Speed and difficulty, taps, branching, scrolling | `EV_CrackMovement` |
| Procedural obstacle rows and power-up spawning | `EV_ObstacleSpawner` |
| Power-up pickup, timers and HUD | `EV_Powerups` |
| Trail and sparks | `EV_Trail` |
| Breaking obstacles, death, saving the best score | `EV_Collisions` |
| Distance and best-score HUD | `EV_Scoring` |

There is one scene, `Gameplay`. The global variable `GameMode` is set to `"Endless"`. Planet mode is planned for Phase 3 and will reuse this same scene.

## How the obstacles are generated
- The screen is split into 7 lanes, and a new row of obstacles appears every `RowGap` px.
- Every row keeps a **2-lane corridor** free of obstacles.
- The corridor shifts by one lane on most rows. It stays put only `CorridorStayChance` (20%) of the time. On a shifting row, both the old and the new corridor lanes stay free, so the safe path never breaks.
- The corridor starts off-centre, so the first rows teach branching.
- **Anti-camping:** if the lane the crack is in is outside the corridor, it gets blocked with `BlockerChance` (75% rising to 90%). Holding straight is almost never safe.
- A 2-lane gap is wider than one branch (130 px), so a branch can always land inside it.
- Each row is one of three types:
  - **Empty:** no obstacles.
  - **Wall:** a barrier in every lane outside the corridor.
  - **Scatter:** each lane outside the corridor gets an obstacle with probability `Density`.
- As `DifficultyLevel` rises from 0 to 1 over 180 seconds, rows get denser and closer together, crystals and solid barriers appear more often, and empty rows get rarer.
- Power-ups appear in the middle of the corridor, so they can always be reached safely.

## Tuning (scene variables of `Gameplay`)
| Variable | Default | Meaning |
|---|---|---|
| BaseSpeed / MaxSpeed | 180 / 420 | scroll speed range in px/s |
| SpeedGrowth / SpeedGrowthInterval | 1.08 / 20 | speed rises 8% every 20 seconds |
| DifficultyRampTime | 180 | seconds until maximum difficulty |
| BranchDistance / BranchDuration / BranchCooldown | 130 / 0.15 / 0.08 | how one branch behaves |
| RowGapStart / RowGapEnd | 280 / 210 | spacing between rows, easy to hard |
| DensityStart / DensityEnd | 0.40 / 0.65 | chance that a lane gets an obstacle |
| EmptyChance*, WallChance*, CrystalChance*, SolidChance*, BreakChance* | see editor | how often each row and obstacle type appears |
| BlockerChanceStart / End | 0.75 / 0.9 | chance that the crack's current lane gets blocked |
| CorridorStayChance | 0.2 | chance that the safe corridor doesn't move on a row |
| FirstRowOffset | 600 | empty warm-up distance at the start |
| PowerupChance / PowerupCooldownTime | 0.12 / 10 | how often power-ups appear |
| SlowTimeDuration / SlowTimeFactor | 4 / 0.6 | how long Slow Time lasts and how much it slows the world |
| StrengthMaxCharges | 3 | charges per Crack Strength pickup |

## Replacing the art
Every sprite reads one PNG file in `assets/`. To replace it, overwrite the file using the same name. Keep these details in mind:
- Origins are at the centre of each image. Collision masks are polygons slightly smaller than the art, so hits feel fair.
- `Crystal` has three animations: Purple, Pink and Cyan. The game picks one at random.
- `TrailSegment` has its origin and centre point at the middle of its left edge, because the game stretches it to the right.
- `CrackHitbox` is the real collision point. It is hidden in game.

## Notes for publishing on Playgama later
- The best score is saved with GDevelop storage. Playgama requires its Bridge storage instead, so this will be swapped when the SDK is added.
- GDevelop's exported builds send an anonymous session ping to `api.gdevelop-app.com`. Playgama does not allow external analytics, so this needs to be switched off at export time.
