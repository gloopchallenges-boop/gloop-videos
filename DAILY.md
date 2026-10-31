# Gloop daily video job

Every day two new Gloop survival Shorts are made and pushed to this repo. A Make.com
scenario ("Gloop daily YouTube upload", runs 12:00 Europe/Warsaw) downloads them from
`raw.githubusercontent.com` and uploads them to the Gloop YouTube channel.
**Never edit the Make scenario from the daily job.** Only produce files.

## Output contract (what Make expects)

For today's date in **Europe/Warsaw** (`TZ=Europe/Warsaw date +%F`):

```
queue/YYYY-MM-DD/v1.mp4     # video 1
queue/YYYY-MM-DD/v2.mp4     # video 2
queue/YYYY-MM-DD/meta.json  # {"t1","d1","t2","d2","publishAt"}
```

- `meta.json` keys: `t1`/`t2` titles (max 100 chars, no `<` or `>`, end with `#shorts`),
  `d1`/`d2` descriptions (hook line, "New Gloop challenge every day at 12:00!",
  "See you next challenge 👋", then 6–8 hashtags incl. #shorts #gloop #survival #challenge),
  `publishAt`: today at 12:00 Warsaw time with the correct offset, e.g.
  `"2026-10-31T12:00:00+01:00"` (offset from `TZ=Europe/Warsaw date +%:z`). Make uploads the
  videos as scheduled and YouTube makes them public at that time (immediately if it's past).
- Videos: 1080x1920, 30 fps, H.264 yuv420p, AAC, `-movflags +faststart`, **18–30 s**,
  **file size under 4.5 MB** (Make free plan limit is 5 MB; use `-crf 24`, raise if needed).
- Must be on `main` and pushed **before 11:50 Warsaw time**.

## The Gloop format (keep it consistent)

- **Gloop**: orange jelly blob (see `engine/examples/croc_rope_timer.py` → `draw_blob`),
  moods `worried` / `scared` / `happy`. Never use any existing brand or character.
- **Header** (top 330 px, near-black `#0d0b14`, Poppins Bold with black outline):
  - first ~2.6 s: hook text `WILL GLOOP SURVIVE` / `<THE THREAT>?`
  - then `SURVIVE: 12.4s` countdown (white → yellow <5s → red <2s, pulse each second)
    plus a hazard bar under it (e.g. `ROPE 63%`, `ICE 40%`, `OXYGEN 22%`, `SHIELD 51%`).
- **Mechanic**: the timer races the hazard bar. Each Gloop action (bounce, wiggle, jump,
  push) damages the bar with a red `-X%` popup + tiny particles + small screen shake.
  The threat (croc, lava, saw, piranhas, shark, falling spikes, rising water…) builds up
  and makes near-miss attempts.
- **Ending**: at 0.0 s → `TIME!` → the **claw machine** drops in and grabs Gloop
  (it's the recurring "system"), header `GLOOP SURVIVED!` → `SEE YOU NEXT` / `CHALLENGE!`.
  About 1 in 3 videos Gloop **fails** (bar hits 0 first): keep it cartoony and non-gory
  (e.g. croc gulps him and spits him out dizzy, he gets frozen in an ice cube, launched
  off-screen) → header `GLOOP FAILED!` → claw still collects him → same outro.
- **Voice** (Kokoro TTS, voice `am_michael`, speed 1.0) — ONLY two lines:
  `"Will Gloop survive <the threat>?"` at 0.2 s and `"See you next challenge!"` at the outro.
  No other narration, no commentary.
- **Sound**: synthesized only (numpy) — soft drone, soft thumps per damage hit, threat
  sounds, last-5-seconds ticks, time-up ding, claw whir + clank, outro chime. No music,
  nothing copyrighted, nothing harsh/buzzy.
- **Variety**: never repeat a threat+hazard combo listed in `history.md`. Vary setting
  (jungle night, volcano, ocean, factory, ice cave, space, kitchen…), timer length
  (10–20 s), threat, hazard, Gloop's action and the outcome.

## How to build (follow every time)

1. Setup:
   ```
   pip install --break-system-packages -q pycairo kokoro-onnx soundfile numpy
   mkdir -p /tmp/tts && cd /tmp/tts && for f in kokoro-v1.0.int8.onnx voices-v1.0.bin; do
     curl -sSL -o $f https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/$f; done
   ```
   Font: Poppins Bold (`fc-list | grep -i poppins`); if missing, use DejaVu Sans Bold.
2. Read `history.md`. Pick 2 new challenges.
3. Copy `engine/examples/croc_rope_timer.py` as a starting point for each scenario,
   change the scene/threat/hazard/mechanic. Keep helpers (`draw_blob`, `text_center`,
   claw, header layout). Write each scenario's sfx script like
   `engine/examples/croc_rope_timer_sfx.py` driven by the events JSON the renderer writes.
4. **Check frames before rendering**: render ~8 stills at key moments
   (`python3 scenario.py out/st events.json 1,4,9,13,16.5,17.6,19,21`), tile them and LOOK
   at them. Fix anything broken (things off-screen, overlapping text, wrong timing).
5. Render video, render sfx, render voice (`python3 engine/vo.py /tmp/tts lines.json vo.wav am_michael <dur>`),
   mix exactly like this:
   ```
   ffmpeg -y -i v.mp4 -i sfx.wav -i vo.wav -filter_complex "[2:a]aresample=44100,asplit=2[v1][v2];[1:a]volume=0.7[s];[s][v1]sidechaincompress=threshold=0.03:ratio=6:attack=5:release=250[d];[d][v2]amix=inputs=2:weights='1 1.6':normalize=0,alimiter=limit=0.95[a]" -map 0:v -map "[a]" -c:v libx264 -preset veryfast -crf 24 -pix_fmt yuv420p -c:a aac -b:a 128k -movflags +faststart -shortest out.mp4
   ```
6. Write `meta.json`, append both challenges to `history.md` (date, title, threat, hazard,
   outcome), save the scenario scripts to `engine/scenarios/YYYY-MM-DD_v1.py` etc.
7. Delete `queue/` folders older than 3 days (keeps the repo small).
8. `git pull --rebase origin main`, commit, `git push origin main`. Verify with
   `git ls-remote origin main` that the push landed.
