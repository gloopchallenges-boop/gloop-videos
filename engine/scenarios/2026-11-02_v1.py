"""FIXED 2026-11-03: tongue now comes out of the mouth (was the forehead), caught blobs shrink into the mouth, no strike starts in the last 0.4 s, frog aims at older positions (less sniper-like). Re-rendered with seed 8 for TikTok; the YouTube upload used the old version (seed 11).
2026-11-02 v1 — WHO FIRST: the GIANT FROG. Gloop (orange) and two rival blobs (blue, green) are
passive rigid balls (Ball) bouncing on a mossy log floor between two stumps; they also collide with
each other (equal-mass elastic). A giant frog on a rock flicks its tongue at seeded-random times at
where a random remaining blob WAS a moment ago — the tongue tip catches whoever it touches (swept).
Gloop caught = fail. Timer ends with Gloop uneaten = win (rivals may be eaten)."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the giant frog'
SEED = int(os.environ.get('SEED', 8))
rng = random.Random(SEED)

class S: pass
S.HOOK2 = 'THE GIANT FROG?'; S.HOOK2_SIZE = 96; S.FAIL_WORD = 'GULP!'; S.FAIL_SIZE = 160
S.T_START = HOOK_T; S.TL = 13.0; S.T_END = S.T_START + S.TL
GROUND = 1610; R = 56; XMIN, XMAX = 160, 920
MOUTH = (540, 1112); TIP_R = 36; T_OUT, T_HOLD, T_BACK = 0.2, 0.06, 0.3
NAMES = ['GLOOP', 'BLIP', 'MOSSY']
SKINS = [('#ffd36b', '#ff8a1f', '#c45a00'), ('#9fd8ff', '#3c8ee0', '#1f4f8a'), ('#c6f08a', '#5fb33c', '#2f6b1f')]

TER = Terrain(GROUND, seed=SEED, bumps=4, amp=10, soft=False)
xs0 = rng.sample([250, 420, 600, 780], 3)
balls = [Ball(xs0[i], TER, R=R, seed=SEED * 3 + i, xmin=XMIN, xmax=XMAX, hop=rng.uniform(220, 300)) for i in range(3)]
STR = []; t = 0.45
while t < S.T_END - 0.4:   # no strike starts in the last 0.4 s (it couldn't finish before TIME)
    STR.append({'t': t}); t += rng.uniform(1.2, 2.1)
N0 = int(40 * FPS); POS = [], ; POS = []; EATEN_AT = [None, None, None]; T_FAIL = None; HIST = []
caught = {}   # blob -> strike index
def tongue_tip(s, t):
    k = t - s['t']
    if k < 0 or k > T_OUT + T_HOLD + T_BACK: return None
    tx, ty = s['tx'], s['ty']
    if k < T_OUT: a = ease(k / T_OUT)
    elif k < T_OUT + T_HOLD: a = 1
    else: a = 1 - ease((k - T_OUT - T_HOLD) / T_BACK)
    return lerp(MOUTH[0], tx, a), lerp(MOUTH[1], ty, a), k < T_OUT + T_HOLD
for f in range(N0):
    t = f / FPS
    HIST.append([(b.x, b.y) for b in balls])
    for si, s in enumerate(STR):
        if 'tx' not in s and t >= s['t'] - 0.001:
            alive = [i for i in range(3) if EATEN_AT[i] is None and i not in caught.values()]
            if s['t'] < S.T_START or not alive or T_FAIL is not None:
                s['tx'], s['ty'], s['who'] = rng.choice((XMIN + 20, XMAX - 20)), GROUND - 40, None
            else:
                w = rng.choice(alive); lag = int(rng.uniform(0.3, 0.55) * FPS)
                px, py = HIST[max(0, f - lag)][w]; s['tx'], s['ty'], s['who'] = px, py, w
    for i, b in enumerate(balls):
        if EATEN_AT[i] is None and i not in caught: b.step(t)
    for i in range(3):   # rival collisions
        for j in range(i + 1, 3):
            a, b = balls[i], balls[j]
            if EATEN_AT[i] is not None or EATEN_AT[j] is not None or i in caught or j in caught: continue
            dx, dy = b.x - a.x, b.y - a.y; d = math.hypot(dx, dy)
            if 0 < d < 2 * R:
                nx, ny = dx / d, dy / d; ov = 2 * R - d
                a.x -= nx * ov / 2; a.y -= ny * ov / 2; b.x += nx * ov / 2; b.y += ny * ov / 2
                rel = (a.vx - b.vx) * nx + (a.vy - b.vy) * ny
                if rel > 0:
                    j_ = rel * 0.95; a.vx -= j_ * nx; a.vy -= j_ * ny; b.vx += j_ * nx; b.vy += j_ * ny
    for si, s in enumerate(STR):   # tongue catches whoever the extending tip touches
        if 'tx' not in s or s['t'] < S.T_START or T_FAIL is not None and s['t'] > T_FAIL: continue
        tip = tongue_tip(s, t)
        if tip and tip[2] and si not in caught.values():
            for i, b in enumerate(balls):
                if EATEN_AT[i] is None and i not in caught and t < S.T_END and math.hypot(b.x - tip[0], b.y - tip[1]) < R + TIP_R:
                    caught[i] = si; s['got'] = i; s['tcatch'] = t
                    if i == 0 and T_FAIL is None: T_FAIL = t
                    break
    for i, si in list(caught.items()):
        s = STR[si]; tip = tongue_tip(s, t)
        if tip is None: EATEN_AT[i] = t; del caught[i]
    POS.append([(b.x, b.y) for b in balls])
S.OUTCOME = 'fail' if T_FAIL else 'win'
S.T_RES = T_FAIL if T_FAIL else S.T_END
END = S.END = Ending(S)
SPIT_T = (EATEN_AT[0] + 0.5) if T_FAIL else None
if T_FAIL:   # frog spits Gloop out dizzy & slimy onto the log
    sx, sy = 540, GROUND - R
    S.GRAB = (sx, sy)
else:
    gi = min(int(END.T_GRAB * FPS), N0 - 1); S.GRAB = POS[gi][0]
S.events = []
for s in STR:
    if s['t'] < S.T_RES + 0.1: S.events.append([s['t'], 'whoosh'])
    if 'got' in s and s['tcatch'] <= S.T_RES + 0.01: S.events.append([s['tcatch'], 'pop']); S.events.append([s['tcatch'] + 0.3, 'thump', 0.8])
for b in balls:
    for (tl, xl, imp) in b.landings:
        if tl < S.T_RES + 1.0: S.events.append([tl, 'hop'])
if T_FAIL: S.events.append([SPIT_T, 'splash'])
S.AMB = {'drone': 45, 'wind': 0.02}
def eaten(i, t): return EATEN_AT[i] is not None and t >= EATEN_AT[i]

def draw_bar(c, t, f):
    for i in range(3):
        x = W / 2 - 170 + i * 170; y = 232; gone = eaten(i, t) or (i in [s.get('got') for s in STR if s.get('tcatch', 99) <= t])
        sk = SKINS[i] if not gone else ('#5a5664', '#3a3644', '#2a2634')
        c.save(); c.translate(x, y)
        c.set_source_rgb(0, 0, 0); c.arc(0, 0, 36, 0, 2 * math.pi); c.fill()
        c.set_source_rgb(*rgb(sk[1])); c.arc(0, 0, 30, 0, 2 * math.pi); c.fill()
        c.set_source_rgb(1, 1, 1); c.arc(-10, -4, 7, 0, 2 * math.pi); c.fill(); c.arc(10, -4, 7, 0, 2 * math.pi); c.fill()
        c.set_source_rgb(0.1, 0.06, 0.05); c.arc(-9, -3, 3.5, 0, 2 * math.pi); c.fill(); c.arc(11, -3, 3.5, 0, 2 * math.pi); c.fill()
        if gone:
            c.set_source_rgb(*rgb('#ff4d4d')); c.set_line_width(8); c.move_to(-26, -26); c.line_to(26, 26); c.stroke(); c.move_to(26, -26); c.line_to(-26, 26); c.stroke()
        c.restore()
        if i == 0: text_at(c, 'YOU?', x, y + 52, 0.0001 + 22, rgb('#ffd36b'), lw=5) if False else None
S.draw_bar = draw_bar

stars = [(rng.uniform(0, W), rng.uniform(HEAD, 1000), rng.uniform(1.2, 2.4)) for _ in range(50)]
flies = [(rng.uniform(150, 930), rng.uniform(700, 1400), rng.uniform(0, 6.3)) for _ in range(8)]
def draw_bg(c, t):
    c.set_source_rgb(*rgb('#121a1c')); c.rectangle(0, HEAD, W, H - HEAD); c.fill()
    c.set_source_rgba(0.85, 0.9, 0.8, 0.45)
    for x, y, r in stars: c.arc(x, y, r, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#e0dcb8')); c.arc(860, 540, 48, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#1a2622'))
    for x in range(-40, W + 80, 150):   # flat tree silhouettes
        c.rectangle(x + 30, 700, 26, 700); c.fill(); c.arc(x + 43, 690, 95, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#1d3a36')); c.rectangle(0, 1380, W, H - 1380); c.fill()   # swamp water
    c.set_source_rgba(1, 1, 1, 0.05)
    for i in range(6): c.rectangle(0, 1420 + i * 80, W, 5); c.fill()
    # frog's rock
    c.set_source_rgb(*rgb('#3a3a40')); c.move_to(300, 1400); c.curve_to(330, 1120, 750, 1120, 780, 1400); c.close_path(); c.fill()
    for (x, y, ph) in flies:
        c.set_source_rgba(1, 0.95, 0.5, 0.5 + 0.4 * math.sin(t * 5 + ph)); c.arc(x + 20 * math.sin(t + ph), y + 14 * math.cos(t * 1.3 + ph), 5, 0, 2 * math.pi); c.fill()

def draw_frog(c, t, mouth_open, cheeks, blink):
    x, y = 540, 1160
    c.set_source_rgb(*rgb('#3f7a3a'))
    c.save(); c.translate(x, y); c.scale(230, 140); c.arc(0, 0, 1, math.pi, 2 * math.pi); c.restore(); c.fill()
    c.save(); c.translate(x, y - 6); c.scale(230, 30); c.arc(0, 0, 1, 0, math.pi); c.restore(); c.fill()
    for s in (-1, 1):   # legs
        c.save(); c.translate(x + s * 200, y + 10); c.scale(70, 40); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    c.set_source_rgb(*rgb('#7aa86a')); c.save(); c.translate(x, y - 10); c.scale(150, 60); c.arc(0, 0, 1, 0, math.pi); c.restore(); c.fill()
    if cheeks > 0:
        c.set_source_rgb(*rgb('#4f8a48'))
        for s in (-1, 1): c.arc(x + s * 170, y - 30, 40 * cheeks, 0, 2 * math.pi); c.fill()
    for s in (-1, 1):   # eyes on top
        c.set_source_rgb(*rgb('#3f7a3a')); c.arc(x + s * 120, y - 135, 60, 0, 2 * math.pi); c.fill()
        c.set_source_rgb(*rgb('#f0e6a0')); c.arc(x + s * 120, y - 140, 44, 0, 2 * math.pi); c.fill()
        if blink:
            c.set_source_rgb(*rgb('#3f7a3a')); c.rectangle(x + s * 120 - 46, y - 186, 92, 50); c.fill()
        else:
            c.set_source_rgb(0.05, 0.05, 0.05); c.save(); c.translate(x + s * 120, y - 136); c.scale(12, 30); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    c.set_source_rgb(*rgb('#2a4a26')); c.set_line_width(8)
    c.move_to(x - 150, y - 50); c.curve_to(x - 60, y - 20 + 30 * mouth_open, x + 60, y - 20 + 30 * mouth_open, x + 150, y - 50); c.stroke()
    if mouth_open > 0.05:
        c.set_source_rgb(*rgb('#5a1f2a')); c.save(); c.translate(MOUTH[0], MOUTH[1] - 14); c.scale(70, 34 * mouth_open); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()

def draw_floor(c):
    c.move_to(0, H)
    for x in range(0, W + 1, 6): c.line_to(x, TER.h[x])
    c.line_to(W, H); c.close_path(); c.set_source_rgb(*rgb('#4a3a2a')); c.fill()
    c.set_source_rgb(*rgb('#3f6b3a')); c.set_line_width(10)
    for x in range(0, W + 1, 6): (c.move_to if x == 0 else c.line_to)(x, TER.h[x] + 3)
    c.stroke()
    c.set_source_rgba(0, 0, 0, 0.2); c.set_line_width(4)
    for yy in range(GROUND + 70, H, 70): c.move_to(0, yy); c.line_to(W, yy); c.stroke()
    for (x0, x1) in ((0, XMIN - R), (XMAX + R, W)):   # stumps = walls
        c.set_source_rgb(*rgb('#5a4330')); c.rectangle(x0, 1060, x1 - x0, GROUND - 1050); c.fill()
        c.set_source_rgb(*rgb('#6e5440')); c.save(); c.translate((x0 + x1) / 2, 1060); c.scale((x1 - x0) / 2, 18); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
        c.set_source_rgb(*rgb('#3f6b3a')); c.arc((x0 + x1) / 2 + 20, 1100, 22, 0, 2 * math.pi); c.fill()

def render(f, c):
    t = f / FPS; fi = min(f, len(POS) - 1)
    c.save()
    draw_bg(c, t)
    active = None
    for s in STR:
        if s['t'] > S.T_RES + 0.05 and not (T_FAIL and s['t'] <= T_FAIL): continue
        tip = tongue_tip(s, t)
        if tip: active = (s, tip)
    mo = 1.0 if active else 0.0
    if SPIT_T and SPIT_T - 0.15 <= t < SPIT_T + 0.3: mo = 1.0
    cheeks = 0.0
    for i in range(3):
        if EATEN_AT[i] and EATEN_AT[i] <= t < EATEN_AT[i] + 1.2 and not (i == 0 and SPIT_T and t >= SPIT_T): cheeks = max(cheeks, 1 - (t - EATEN_AT[i]) / 1.2 * 0.5)
    draw_frog(c, t, mo, cheeks, (t % 4.1) < 0.12)
    if active:
        s, (tx, ty, out) = active
        c.set_source_rgb(*rgb('#d65a6a')); c.set_line_width(26); c.set_line_cap(cairo.LINE_CAP_ROUND)
        c.move_to(*MOUTH); c.line_to(tx, ty); c.stroke()
        c.set_source_rgb(*rgb('#e8798a')); c.arc(tx, ty, TIP_R, 0, 2 * math.pi); c.fill()
    draw_floor(c)
    for i in range(3):
        if eaten(i, t) and not (i == 0 and SPIT_T and t >= SPIT_T): continue
        x, y = POS[fi][i]
        for s in STR:   # being reeled in
            if s.get('got') == i and s['tcatch'] <= t:
                tip = tongue_tip(s, t)
                if tip: x, y = tip[0], tip[1]; s['_sc'] = clamp(math.hypot(x - MOUTH[0], y - MOUTH[1]) / 220, 0.25, 1)
        if i == 0 and SPIT_T and t >= SPIT_T:
            k = clamp((t - SPIT_T) / 0.5, 0, 1); x = lerp(MOUTH[0], S.GRAB[0], k); y = lerp(MOUTH[1], S.GRAB[1], k) - 260 * math.sin(math.pi * k)
            if t >= END.T_GRAB: x, y = S.GRAB
        if i == 0 and (END.carried(t) or (t >= END.T_GRAB)): x, y = (END.carry_xy(t) if END.carried(t) else S.GRAB)
        hh = max(0, TER.y(x) - R - y); kk = 1 / (1 + hh / 220)
        if not END.carried(t) or i:
            c.set_source_rgba(0, 0, 0, 0.25 * kk); c.save(); c.translate(x, TER.y(x) + 3); c.scale(R * (0.5 + 0.4 * kk), 8); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
        danger = active is not None and math.hypot(active[1][0] - x, active[1][1] - y) < 300
        if i == 0:
            mood = 'happy' if (t >= S.T_END and S.OUTCOME == 'win') else ('scared' if danger or T_FAIL and t >= T_FAIL else 'worried')
            slimy = SPIT_T and t >= SPIT_T
            draw_blob(c, t, x, y, mood, 0, R=R, skin=(('#d8f07a', '#9ac43c', '#5a7a1f') if slimy else SKINS[0]), dizzy=bool(slimy))
            if slimy:
                c.set_source_rgba(0.6, 0.85, 0.3, 0.7)
                for j in range(3): c.arc(x - 30 + j * 30, y + R * 0.8 + 10 * ((t * 1.5 + j * 0.3) % 1), 6, 0, 2 * math.pi); c.fill()
        else:
            sc = 1.0
            for s in STR:
                if s.get('got') == i and s['tcatch'] <= t: sc = s.get('_sc', 1.0)
            draw_blob(c, t + i, x, y, 'scared' if danger else 'worried', 0, R=R * sc, skin=SKINS[i], sweat=False)
    END.draw_claw(c, t)
    c.restore()
    END.header(c, t, fi)

if __name__ == '__main__':
    if sys.argv[1] == 'sim':
        print(SEED, S.OUTCOME, round(S.T_RES - S.T_START, 2), 'eaten', [(NAMES[i], round(EATEN_AT[i] - S.T_START, 1)) for i in range(3) if EATEN_AT[i]], 'strikes', len([s for s in STR if S.T_START <= s['t'] < S.T_RES]), 'dur', S.DUR); sys.exit()
    run(S, render)
