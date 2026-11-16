# CRACKLINE: Phase 3 (Endless Depth + Planet Breaker), GDevelop

This is a portrait 720×1280 arcade game. All gameplay is built with native GDevelop events, with no JavaScript. The only code is Playgama's official **Playgama Bridge** extension, used for the online leaderboard.

## Open it
On a tablet or in a browser, open
`https://editor.gdevelop.io/?project=https://raw.githubusercontent.com/lonewolfproduction99-cpu/CrackLine/main/game.json`
and press **Preview** (▶). To keep your own editable copy, use **File → Save as** and choose cloud.

## How to play
The game opens on the **main menu**. Pick **ENDLESS DEPTH** or **PLANET BREAKER**, or open the **SHOP**, **LEADERBOARD** or **CREDITS**. The buttons wake up a moment after start, once your saved progress has loaded.
- **Planet Breaker:** you start at the planet's core and travel up to its surface. The progress bar shows how far you have left. Planet 1 needs **1,000 m**, planet 2 needs 2,000 m, planet 3 needs 3,000 m, and so on. Each planet starts noticeably harder. When you reach the surface, the planet splits in two and the next one begins. The planets cycle Ember → Verdant (more crystals) → Frost (more barriers) → **Magma** (more lava gaps) → **Umbra** (more worms), then start again.
- **Game over:** you can RESTART, go back to the MAIN MENU, or tap **REVIVE - WATCH AD** once per run. You are revived only if the ad is watched to the end. The revive clears nearby obstacles and gives you 2 seconds of protection, shown as a cyan ring, and you keep your score. The revive button only appears where the platform has rewarded ads (not in the GDevelop preview).
- **Hold** the left or right half of the screen and the crack travels diagonally that way. Let go and it goes straight up. You can slide your finger across the middle to switch direction.
- The game gets **25% faster every 250 m** (180 → 225 → 281 → 352 px/s and so on). Endless tops out at 420 px/s, and Planet Breaker tops out at 520 px/s. Survive as long as you can and try to beat your best distance.
- **Blue clock (Slow Time):** the world moves 40% slower for 4 seconds.
- **Orange bolt (Crack Strength):** gives you 3 charges. Each charge smashes one rock or one cracked barrier.
- **Metal-banded barriers** always kill you, even when you have charges.
- **Crystals are points**, and the colour always tells you the value: **pink** (small, hardest to grab) = 5, **purple** (medium) = 3, **blue** (large) = 1. Most appear in the safe path; some riskier ones sit between obstacles. Verdant planets have more of them. Your crystal total is saved on the device.
- **Shop:** spend crystals on crack styles. Classic is free, then Frostbite 150, Venom 300, Amethyst 500, Inferno 800, Shadow 1200, **Sunburst 1600** and **Aurora 2000**. Tap a style to buy it, or tap one you own to use it. The style recolours the trail, tip and sparks.
- **Ground gaps (fissures)** stretch across the whole screen. Touching one jolts your crack into a branch in a random direction. Nothing spawns just after a gap, so you can always recover.
- **Leaderboards:** your best **Endless Depth** distance and your most **planets broken** go on Playgama's online leaderboards. Tap **LEADERBOARD** on the menu to see the top 10 for either mode (tabs at the top), with your own row in green. The button only appears where the platform has a leaderboard (on Playgama, and in Playgama's QA tool). It stays hidden in the GDevelop preview, so there SHOP keeps its usual full-width button.
- **Burrowing worms** tunnel sideways back and forth across a row. They kill on contact, but Crack Strength can smash them. They are tinted to match each planet.

## Where things are
| What | Where |
|---|---|
| Main menu | Scene `MainMenu` (its own events) |
| Shop (buy and equip crack styles) | Scene `Shop` (its own events) |
| Leaderboard screen (top 10, two tabs) | Scene `Leaderboard` (its own events) |
| Credits screen | Scene `Credits` (its own events) |
| Loading saved progress | `MainMenu`, group "Load progress" |
| Saving, platform pause and sound, every scene | External events `EV_Platform` |
| Ads (interstitial, rewarded revive) | `EV_GameState`, group "Game over" |
| Leaderboard button, game-ready message, sending your saved best | `MainMenu`, group "Playgama" |
| Sending a new best after a run | `EV_Collisions`, inside "new best" (Endless) |
| Crystal pickups and counter | `EV_Powerups` (group "Crystals (points)") |
| Scene setup, best-score loading, game-over buttons | External events `EV_GameState` |
| Planet themes, surface progress, planet-split animation | `EV_PlanetMode` |
| Revive (one per run) | `EV_Revive` |
| Speed and difficulty, hold-to-steer, scrolling | `EV_CrackMovement` |
| Procedural obstacle rows and power-up spawning | `EV_ObstacleSpawner` |
| Power-up pickup, timers and HUD | `EV_Powerups` |
| Trail and sparks | `EV_Trail` |
| Breaking obstacles, death, saving the best score | `EV_Collisions` |
| Distance and best-score HUD | `EV_Scoring` |

Both modes run in the same `Gameplay` scene. The global variable `GameMode` (`"Endless"` or `"Planet"`) tells the scene which mode is active.

**Revive hook for Playgama:** the test button only sets the scene variable `RequestRevive` to true, and `EV_Revive` does the rest. A future rewarded-ad success callback just needs to set that same variable.

## How the obstacles are generated
- The screen is split into 7 lanes, and a new row of obstacles appears every `RowGap` px.
- Every row keeps a **2-lane corridor** free of obstacles.
- The corridor shifts by one lane on most rows. It stays put only `CorridorStayChance` (20%) of the time. On a shifting row, both the old and the new corridor lanes stay free, so the safe path never breaks.
- The corridor starts off-centre, so the first rows teach branching.
- **Anti-camping:** if the lane the crack is in is outside the corridor, it gets blocked with `BlockerChance` (85% rising to 90%). Holding straight is almost never safe.
- A 2-lane gap is wider than one branch (130 px), so a branch can always land inside it.
- Each row is one of five types:
  - **Empty:** no obstacles.
  - **Wall:** a barrier in every lane outside the corridor.
  - **Scatter:** each lane outside the corridor gets an obstacle with probability `Density`.
  - **Worm:** one burrowing worm sweeps the row, and nothing else is in it.
  - **Fissure:** a full-width gap, followed by `FissureClearance` px with no obstacles.
- A simulation over 5 runs of 5 minutes each, reaching 520 px/s, checked every tap timing. It also confirmed that after each of about 100 fissures, the crack can recover from **any** position in **either** random direction.
- As `DifficultyLevel` rises from 0 to 1 over 180 seconds, rows get denser and closer together, crystals and solid barriers appear more often, and empty rows get rarer.
- Power-ups appear in the middle of the corridor, so they can always be reached safely.

## Tuning (scene variables of `Gameplay`)
| Variable | Default | Meaning |
|---|---|---|
| BaseSpeed / MaxSpeed | 180 / 420 | scroll speed range in px/s |
| SpeedStepFactor / SpeedStepDistance / SpeedRampRate | 1.25 / 250 / 120 | +25% speed every 250 m; each jump eases in at 120 px/s per second |
| DifficultyRampTime | 180 | seconds until maximum difficulty |
| HoldMinSpeed / HoldSpeedFactor / HoldAccel | 300 / 1.0 / 5000 | sideways steering speed = max(300, game speed × 1.0), so roughly 45°, and how fast steering ramps up |
| BranchDistance / BranchDuration | 130 / 0.15 | size of the forced jolt from a ground gap |
| RowGapStart / RowGapEnd | 280 / 210 | spacing between rows, easy to hard |
| DensityStart / DensityEnd | 0.40 / 0.65 | chance that a lane gets an obstacle |
| EmptyChance*, WallChance*, CrystalChance*, SolidChance*, BreakChance* | see editor | how often each row and obstacle type appears |
| BlockerChanceStart / End | 0.85 / 0.9 | chance that the crack's current lane gets blocked |
| CorridorStayChance | 0.2 | chance that the safe corridor doesn't move on a row |
| FirstRowOffset | 600 | empty warm-up distance at the start |
| PowerupChance / PowerupCooldownTime | 0.12 / 10 | how often power-ups appear |
| SlowTimeDuration / SlowTimeFactor | 4 / 0.6 | how long Slow Time lasts and how much it slows the world |
| StrengthMaxCharges | 3 | charges per Crack Strength pickup |
| PlanetDistanceStep | 1000 | planet N needs N × this many metres |
| PlanetDifficultyStart / PlanetDifficultyStep / PlanetProgressDifficulty | 0.15 / 0.2 / 0.2 | starting difficulty, extra difficulty per planet, extra difficulty within a planet |
| PlanetMaxSpeed | 520 | speed cap in Planet Breaker (Endless uses MaxSpeed 420) |
| ThemeCount | 5 | number of planet themes before they repeat (raise it when you add new planets) |
| WormChanceStart/End, WormSpeedStart/End | 0.03→0.12, 110→210 | how often worm rows appear and how fast worms move |
| FissureChanceStart/End, FissureClearance | 0.02→0.07, 1000 | how often ground gaps appear, and the empty distance after each one |
| BreakDuration | 2.0 | length of the planet-split sequence in seconds |
| GemChance / RiskyGemChance | 0.4 / 0.12 | chance of a crystal in the safe path per row, and of a risky one beside obstacles |
| ReviveInvulnerability / ReviveClearBehind / ReviveClearAhead | 2 / 250 / 750 | revive protection time and the area it clears |

## Shop data
Style names, prices and spark colours are in the global arrays `StyleNames`, `StylePrices` and `StyleSparkColors`. To add a style:
1. Add a `trail_<name>.png` and a `tip_<name>.png`.
2. Add a matching animation to `TrailSegment`, `CrackTip`, `ShopTrail` and `ShopTip`.
3. Add an entry to each of the three arrays.
4. Add a card to the Shop.
5. Add one more `0` to the `OwnedStyles` default. Older saves are padded automatically.

## Art and sound
All art and sound is **human-made**, from free CC0 (public domain) packs: **Kenney** (kenney.nl) art and sound effects, **Beatscribe** jingles and **Juhani Junkala** music. See `CREDITS.md` for which pack each file comes from and what was changed. Changes were limited to resizing, recolouring, cutting the planets in half and similar edits.
- Images are in `assets/` and sounds are in `audio/`. To replace one, overwrite it with a file of the same name.
- **Speaker button** (main menu and top-left of the HUD): mutes or unmutes everything. The setting is saved.
- Sounds play for branching, ground gaps, crystals, power-ups, smashing, crashing (plus a game-over jingle), breaking a planet (plus a victory jingle), the revive, and the shop.
- **Music:** two looping chiptune tracks by **Juhani Junkala** (CC0), one for the menus and one for runs. They play on channel 0 at volume 45; change `MUSIC_VOLUME` in the builder, or the "Play music on channel" actions in `MainMenu` and `EV_GameState`.

## Playgama integration
Everything Playgama requires is wired up through its official **Playgama Bridge** GDevelop extension (v2.4.0, under Extensions). Its settings live in the extension's `onFirstSceneLoaded` function and in `playgama-bridge-config.json` next to `game.json`. Playgama requires that file in every build, so keep both in step.
- **Saving:** progress (bests, crystals, owned and equipped styles, mute) is saved only through Bridge storage, which uses cloud saves where the platform has them. It loads once at start in one request and saves when something changes, in one request. If loading fails, the game still plays but doesn't save, so it can never wipe a real save.
- **Pause and sound:** when the platform pauses the game (tab hidden, browser minimised, an ad open), the game's time stops and the sound goes silent. When the platform says audio is off, the game stays silent. Your own mute button still works on top.
- **Ads:** an interstitial is requested when you leave the game-over screen (RESTART or MAIN MENU); Playgama decides whether one shows and how often. The revive uses a rewarded ad. Both are skipped quietly where ads aren't available.
- **Leaderboards:** `best_distance` (Endless Depth, metres) and `planets_broken` (Planet Breaker). A score is sent when you beat your best, and once per session from the menu so older bests count too. The LEADERBOARD button shows only where the platform has a leaderboard (on Playgama, and in Playgama's QA tool), so it is hidden in the GDevelop preview.
- **Game ready:** sent once saved progress has loaded and the menu can be used.
- **Analytics:** GDevelop's own anonymous usage ping is switched off (main menu, first action), as Playgama doesn't allow outside analytics.

## Notes for publishing on Playgama
- The game is English only. Playgama takes the player's language from the Bridge; when you fill in the publication form, declare English as the only language.
- The "Made with GDevelop" watermark (bottom left) can only be removed with a GDevelop subscription. On a square window it sits near the bottom buttons.
- Phone notches and safe areas are not handled specifically. The HUD starts about 40 px from the top.
- Saves made before this update (stored by GDevelop on your device) are not carried over to Bridge storage, since the game isn't published yet.
