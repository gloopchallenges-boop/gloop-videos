# Gloop daily video job

Every day new Gloop survival Shorts are made and pushed to this repo. A Make.com
scenario ("Gloop daily YouTube upload", runs 12:00 Europe/Warsaw) downloads them from
`raw.githubusercontent.com` and uploads them to the Gloop YouTube channel.
**Never edit the Make scenario from the daily job.** Only produce files.

## How many videos

- **Normal day: 3 videos** (minimum 3, never fewer unless something is broken).
- **Launch period 2026-11-01 … 2026-11-14 (inclusive): 8 videos per day** instead of 3.
  Not more: on Oct 31 YouTube rejected every upload after the 8th, and Make's error handler
  hides that. Use the 8-video posting times below. From 2026-11-15 go back to 3/day.
- **Carry-over:** if `queue/<today>/meta.json` already exists when the job starts (e.g. videos
  that failed to upload yesterday were re-queued), KEEP those entries and files untouched,
  number your new videos after them, and only make enough new ones to reach the day's total
  (8 during the launch period, otherwise 3; 10 on special days).
- **Special days cap: 8 videos** until the channel can upload more (same YouTube limit).
- **Special day: 10 videos**, all themed for the occasion (costumes, decorations, setting,
  themed threats — e.g. Halloween: pumpkins, ghosts, haunted house, witch cauldron, skeleton
  hands, bats; Christmas: chimney, Santa's sleigh, giant snowball, gingerbread trap…). Hook
  and titles mention the occasion ("🎃 Halloween special").
  Special days (Europe/Warsaw date): Oct 31 Halloween, Dec 24 Christmas Eve, Dec 25 Christmas,
  Dec 31 New Year's Eve, Jan 1 New Year, Feb 14 Valentine's Day, Apr 1 April Fools,
  Easter Sunday (compute it for the year).
  **Themed Gloop skin on special days** (same blob + face, recolored and wearing a costume
  drawn on top in cairo) — vary the skin across the 10 videos:
  - Halloween: pumpkin-orange with carved-pumpkin stem + leaf hat, witch hat (purple),
    ghost sheet (white, translucent), vampire cape + fangs, mummy bandages, black-cat ears.
  - Christmas Eve / Christmas: Santa hat, reindeer antlers + red nose, elf hat (green),
    snowman (white skin + carrot nose + scarf), gift-wrapped (ribbon bow on top).
  - New Year's Eve / New Year: party hat + glasses with "20XX", gold glitter skin, confetti.
  - Valentine's: pink skin, heart-shaped antenna, cupid wings.
  - April Fools: clown nose + rainbow wig, upside-down jokes, rubber-chicken threat.
  - Easter: bunny ears, pastel egg-pattern skin.
  The claw, header and outro also get a light theme touch (e.g. orange/purple header accents
  on Halloween, snow on the claw at Christmas).
  On special days work fast: reuse one themed scene/engine and vary threat + hazard + action
  + skin + outcome per video so all 10 get done before the deadline.

## Output contract (what Make expects)

For today's date in **Europe/Warsaw** (`TZ=Europe/Warsaw date +%F`):

```
queue/YYYY-MM-DD/v1.mp4 ... vN.mp4
queue/YYYY-MM-DD/meta.json
```

`meta.json`:
```json
{"videos": [
  {"file": "v1.mp4", "title": "...", "description": "...", "publishAt": "2026-10-31T12:00:00+01:00"},
  ...
]}
```
- `title`: max 100 chars, no `<` or `>`, ends with `#shorts`.
- `description`: hook line, "New Gloop challenges every day!",
  "See you next challenge 👋", then 6–8 hashtags incl. #shorts #gloop #survival #challenge
  (plus occasion hashtags on special days).
- `publishAt`: Warsaw time with correct offset (`TZ=Europe/Warsaw date +%:z`).
  Post when people watch most (covers EU lunch + evening and the US afternoon/evening):
  - Normal weekday: `12:00`, `18:00`, `21:00`.
  - Normal Sat/Sun: `14:00`, `18:00`, `21:00`.
  - Special day (10 videos): `12:00, 13:00, 14:00, 15:00, 16:00, 17:00, 18:00, 19:00, 20:00, 21:00`.
  - 8 videos (launch period / capped special day): `12:00, 13:00, 14:00, 16:00, 17:00, 18:00, 20:00, 21:00`.
  - If there are extra videos, add `16:00` and `23:00`.
  Make uploads everything at 12:00 as scheduled-private; YouTube publishes each at its time
  (immediately if the time has passed).
- Only list files that actually exist and finished correctly.
- Videos: 1080x1920, 30 fps, H.264 yuv420p, AAC, `-movflags +faststart`, **18–22 s** (min 18, aim ~18–20 — shorter = higher % watched),
  **file size under 4.5 MB** (Make free plan limit is 5 MB; use `-crf 24`, raise if needed).
- Must be on `main` and pushed **before 11:50 Warsaw time**.

## Challenge TYPES — mix them! (most important variety rule)

The croc/rope example is only ONE type. Every day must use **at least 2 different types**
(3 videos → 3 different types when possible; 10 videos → at least 6 types), and never the
same type for 2 videos in a row. Check `history.md` and favour types used least recently.
Write the type in the history table's "Hazard bar" column, e.g. `STEALTH – DETECTED %`.

1. **DAMAGE BAR** (the croc one): each Gloop action damages what holds him (rope, branch,
   ice, bubble). Bar goes DOWN; 0% = fail.
2. **STEALTH – "Will Gloop stay unseen?"**: a guard / ghost / robot / owl / security camera
   holds a **flashlight or searchlight whose beam sweeps** (up-down or left-right, changing
   speed, sometimes pausing, reversing or faking out). Header shows `SURVIVE: 14.2s` and a
   `DETECTED 37%` bar that fills red. **While Gloop is inside the light beam the % goes UP fast
   (~35–45%/s); when he's out of it the % goes DOWN, but slower (~10–15%/s).** The scene has
   **hiding spots** Gloop hops between: crates, barrels, bushes, tombstones, curtains, boxes,
   trash cans, a sofa, a tree trunk. Behind cover = blocked from the light (beam visibly
   stops at the object / object casts a shadow). Gloop sneaks with squishy hops, peeks out,
   sometimes gets caught mid-move. Show an eye icon next to the bar that opens when he's
   seen, `!` popups when % jumps. 100% → `SPOTTED!` + alarm flash + cage drops / guard grabs
   him = fail. Timer runs out first = win → claw.
   **Reference implementation: `engine/examples/stealth_flashlight.py` (+ `_sfx.py`)** — the
   detection % is simulated from the real beam angle and Gloop's position, so tune the beam
   keyframes/path and re-run the sim until the % curve tells the story you want.
3. **RISING DANGER – climb/escape**: lava / water / slime / sand rises; `HEIGHT` or
   `AIR` meter; Gloop jumps platform to platform, some crumble.
4. **DODGE – hearts**: falling anvils, saws, meteors, arrows; `❤❤❤` lives in the header
   (draw hearts as shapes, not emoji), lose one per hit, 0 hearts = fail.
5. **TEMPERATURE**: `FREEZE %` or `MELT %`; Gloop moves between a heater and a fan / sun and
   shade; bar rises in the bad zone, falls slowly in the safe one.
6. **GRIP / TUG**: magnet, vacuum, tornado or a giant hand pulls Gloop; `GRIP %` drains while
   he holds on to a pole/ledge; brief regrips.
7. **BALANCE**: Gloop on a seesaw / plank / floating log; `TILT` meter must stay out of the
   red zones while things land on either side.
8. **RACE**: Gloop vs a threat to a finish line / door; `DISTANCE` bars for both, obstacles
   slow Gloop down.
9. **WHO FIRST**: two or three colored blob rivals (not Gloop clones — Gloop is always the
   orange one) in the same trap; "WHO GETS EATEN FIRST?" style, Gloop may or may not be the
   last one standing.

10. **NOISE / WAKE-UP**: Gloop must sneak past something sleeping (a bear, a dragon, a giant,
    a guard dog, a grumpy grandpa robot) to reach a key/exit. `WAKE 0%` bar: every landing /
    bump makes noise (+X%, sound-wave rings + "Z" bubbles stop), it slowly settles back when
    he's quiet. Creaky floorboards, a squeaky toy or falling pots make big jumps. 100% =
    `WOKEN UP!` → chase / grab = fail.
11. **ITEMS LEFT**: a countdown of things that protect Gloop — `12 PLANKS LEFT`,
    `8 BALLOONS LEFT`, `5 ICE BLOCKS LEFT`. Each hit/bounce removes one; reach the timer
    end with at least 1 left = win.
12. **HEIGHT / DISTANCE GAUGE**: a measured number with a line marker, e.g. `WALL 7.6 m`,
    `WATER 4.2 m` or `GAP 3.1 m` — Gloop must bounce higher / jump further than the line,
    each try shows the reached height with a ruler on the side; or something climbs toward
    him and the meter counts the distance left.
13. **FALLING OBJECT ABOVE**: a chandelier / piano / anvil hangs above Gloop on a chain that
    loses links (`CHAIN 6 LINKS`) while he's stuck below (sticky floor, net, trapped foot)
    and has to wiggle free before it drops.

**Outcomes: Gloop must NOT always win — and it must never look staged.**
- **Let the simulation decide.** Every video runs a real sim: random-but-seeded events
  (damage amounts, beam sweeps, threat attacks, Gloop's moves) drive the bar/% frame by
  frame, and whatever happens at the end IS the outcome. Never hand-place "the rope snaps
  exactly as the claw grabs him" or "100% at 0.1s". If the day's mix is off (e.g. all wins),
  re-roll the **seed** and keep what the sim gives — don't edit the ending to force it.
- Aim for roughly **half wins, half fails** each day (3 videos → 1–2 fails; 10 → 4–6).
- **Vary the margins.** Wins: some comfortable (bar still 30–60%, timer ends calmly), some
  medium, only occasionally a nail-biter. Fails: some early and sudden (a big unlucky hit at
  9s), some mid-way, only occasionally at the very end. Max **1 in 5** videos may be decided
  in the last second.
- **No convenient coincidences.** The bar should never sit at 1–3% for ages, the threat
  shouldn't conveniently miss at the last instant, and nothing breaks "just after" the
  rescue. When Gloop wins, the claw just picks him up — the hazard stays intact.
- Damage/detection must look consistent: same kind of hit = similar damage, rates don't
  secretly change near the end.
- Fails stay cartoony and non-gory (caught in a cage, frozen in an ice cube, swallowed and
  spat out dizzy, launched into the sky, covered in goo), header `GLOOP FAILED!`, the claw
  still collects him, same outro.

## The Gloop format (keep it consistent)

- **Gloop**: orange jelly blob (see `engine/examples/croc_rope_timer.py` → `draw_blob`),
  moods `worried` / `scared` / `happy`. Never use any existing brand or character.
- **Header** (top 330 px, near-black `#0d0b14`, Poppins Bold with black outline):
  - first **1.5 s** (`HOOK_T`): hook text `WILL GLOOP SURVIVE` / `<THE THREAT>?` shown **over action
    that is already moving from frame 0** (meteor already falling, beam already sweeping, lava
    already bubbling) — never a calm/static opening; that's where viewers swipe away. Hazard
    events before `T_START` must not affect the bar (e.g. pre-start meteors land far from Gloop).
  - then `SURVIVE: 12.4s` countdown (white → yellow <5s → red <2s, pulse each second)
    plus a hazard bar under it (e.g. `ROPE 63%`, `ICE 40%`, `OXYGEN 22%`, `SHIELD 51%`).
- **Mechanic**: the timer races the hazard bar. Each Gloop action (bounce, wiggle, jump,
  push) damages the bar with a red `-X%` popup + tiny particles + small screen shake.
  The threat (croc, lava, saw, piranhas, shark, falling spikes, rising water…) builds up
  and makes near-miss attempts.
- **Ending**: at 0.0 s → `TIME!` → the **claw machine** drops in and grabs Gloop
  (it's the recurring "system"), header `GLOOP SURVIVED!` → `SEE YOU NEXT` / `CHALLENGE!`.
  About HALF of the videos Gloop **fails** (see Outcomes above): keep it cartoony and non-gory
  (e.g. croc gulps him and spits him out dizzy, he gets frozen in an ice cube, launched
  off-screen) → header `GLOOP FAILED!` → claw still collects him → same outro.
  **Keep the ending short** (~3.8 s from result to the last frame: claw in at +0.6 s, outro at
  +2.3 s).
- **Engagement features (automatic in `engine/scenarios/gloop_common.py`, keep them on):**
  - **Guess prompt**: `SURVIVE OR FAIL?` / `COMMENT YOUR GUESS!` panel ~2.2 s after the timer
    starts, for 1.8 s (skipped automatically if the result comes too soon after it).
  - **Record badge**: top-left `GLOOP RECORD 11W - 6L`, counted from `history.md`; it ticks up
    (+1 W or +1 L) when the result text appears. So **append each video's history row right
    after building it** — then the next video's record includes it (or set env `RECORD=W-L`).
  - **Seamless loop**: the last 0.4 s crossfade into frame 0, so the Short loops (rewatches).
- **Voice** (Kokoro TTS, voice `am_michael`, speed 1.0) — ONLY two lines:
  `"Will Gloop survive <the threat>?"` at 0.2 s and `"See you next challenge!"` at the outro.
  No other narration, no commentary.
- **Sound**: synthesized only (numpy) — soft drone, soft thumps per damage hit, threat
  sounds, last-5-seconds ticks, time-up ding, claw whir + clank, outro chime. No music,
  nothing copyrighted, nothing harsh/buzzy.
- **Variety**: never repeat a threat+hazard combo listed in `history.md`. Vary setting
  (jungle night, volcano, ocean, factory, ice cave, space, kitchen…), timer length
  (11–15 s), threat, hazard, Gloop's action and the outcome.

## How to build (follow every time)

1. Setup:
   ```
   pip install --break-system-packages -q pycairo kokoro-onnx soundfile numpy
   mkdir -p /tmp/tts && cd /tmp/tts && for f in kokoro-v1.0.int8.onnx voices-v1.0.bin; do
     curl -sSL -o $f https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/$f; done
   ```
   Font: Poppins Bold (`fc-list | grep -i poppins`); if missing, use DejaVu Sans Bold.
2. Read `history.md`. Check if today is a special day. Pick 3 (or 10) new challenges.
3. Build every scenario on the shared engine `engine/scenarios/gloop_common.py` (blob, header,
   claw ending, record badge, guess prompt, loop crossfade, `run()`), with
   `engine/scenarios/gloop_sfx.py` (generic event-driven sfx) and
   `engine/scenarios/gloop_build.sh <scenario.py> <out.mp4>` (render + sfx + voice + mix + size
   check; set `SEED=` env). Good templates, one per type: `engine/scenarios/2026-11-01_v3.py`
   (stealth), `_v4` (dodge hearts), `_v5` (temperature), `_v6` (rising danger), `_v7`
   (noise/wake), `_v8` (falling object). Each defines `SAY = '<the threat>'`, a seeded sim, and
   prints a summary with `python3 scenario.py sim x` — scan seeds with that to get the day's
   win/fail mix, then render. **New scenarios: `S.T_START = HOOK_T`, timer 11–15 s, hazard in
   motion from t=0.** (The 2026-11-01 files still use the old 2.6 s hook / 15–16 s timer.)
   `engine/examples/` holds the older standalone references.
   **Gloop must move physically, never on a fixed path** (scripted glides/identical hops look
   fake): drive him with `Body` from `gloop_common.py` — gravity, random hop heights/lengths,
   rolls (body + face spin with distance, overshoot, settle upright), random flips, squash on
   landing, fidgety idle hops/shuffles, `body.push()` for shoves. Step the body once per frame
   INSIDE the sim and use `body.x`/`body.y` for every hit/detection check; draw with
   `draw_blob(..., b.sq, rot=b.rot)` at `b.draw_y()`. Reference with everything wired up:
   **`engine/scenarios/example_body_dodge.py`** (start new scenarios from it).
4. **Check frames before rendering**: render ~8 stills at key moments
   (`python3 scenario.py out/st events.json 1,4,9,13,16.5,17.6,19,21`), tile them and LOOK
   at them. Fix anything broken (things off-screen, overlapping text, wrong timing).
5. Render video, render sfx, render voice (`python3 engine/vo.py /tmp/tts lines.json vo.wav am_michael <dur>`),
   mix exactly like this:
   ```
   ffmpeg -y -i v.mp4 -i sfx.wav -i vo.wav -filter_complex "[2:a]aresample=44100,asplit=2[v1][v2];[1:a]volume=0.7[s];[s][v1]sidechaincompress=threshold=0.03:ratio=6:attack=5:release=250[d];[d][v2]amix=inputs=2:weights='1 1.6':normalize=0,alimiter=limit=0.95[a]" -map 0:v -map "[a]" -c:v libx264 -preset veryfast -crf 24 -pix_fmt yuv420p -c:a aac -b:a 128k -movflags +faststart -shortest out.mp4
   ```
6. Write `meta.json`, append all challenges to `history.md` (date, title, threat, hazard,
   outcome), save the scenario scripts to `engine/scenarios/YYYY-MM-DD_v1.py` etc.
7. Delete `queue/` folders older than 3 days (keeps the repo small).
8. `git pull --rebase origin main`, commit, `git push origin main`. Verify with
   `git ls-remote origin main` that the push landed.
