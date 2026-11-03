"""2026-11-03 v8 — WHO FIRST: the GIANT COBRA. Gloop (orange) and two rival blobs (pink, purple) are
passive rigid balls (Ball) bouncing on a rug in a night bazaar between two clay pots; they collide with
each other (equal-mass elastic). A giant cobra rises from a wicker basket at the back and strikes at
seeded-random times at where a random remaining blob WAS a moment ago — the snake's head catches
whoever it touches. Gloop caught = fail (swallowed, spat out dizzy). Timer ends uneaten = win."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the giant cobra'
SEED = int(os.environ.get('SEED', 1))
rng = random.Random(SEED)

class S: pass
S.HOOK2 = 'THE GIANT COBRA?'; S.HOOK2_SIZE = 92; S.FAIL_WORD = 'GULP!'; S.FAIL_SIZE = 160
S.T_START = HOOK_T; S.TL = 12.0; S.T_END = S.T_START + S.TL
GROUND = 1610; R = 56; XMIN, XMAX = 160, 920
MOUTH = (540, 1010); TIP_R = 40; T_OUT, T_HOLD, T_BACK = 0.22, 0.08, 0.35
NAMES = ['GLOOP', 'PINKY', 'GRAPE']
SKINS = [('#ffd36b', '#ff8a1f', '#c45a00'), ('#ffb3d1', '#e05a96', '#8a2a56'), ('#d2b3ff', '#8a5ae0', '#4a2a8a')]

TER = Terrain(GROUND, seed=SEED, bumps=4, amp=10, soft=False)
xs0 = rng.sample([250, 420, 600, 780], 3)
balls = [Ball(xs0[i], TER, R=R, seed=SEED * 3 + i, xmin=XMIN, xmax=XMAX, hop=rng.uniform(220, 300)) for i in range(3)]
STR = []; t = 0.45
while t < S.T_END + 1:
    STR.append({'t': t}); t += rng.uniform(1.2, 2.2)
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
    if s['t'] < S.T_RES + 0.1: S.events.append([s['t'], 'whoosh']); S.events.append([s['t'], 'sizzle'])
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

stars = [(rng.uniform(0, W), rng.uniform(HEAD, 900), rng.uniform(1.2, 2.4)) for _ in range(50)]
BASKET = (540, 1330)
def draw_bg(c, t):
    c.set_source_rgb(*rgb('#16121e')); c.rectangle(0, HEAD, W, H - HEAD); c.fill()
    c.set_source_rgba(0.9, 0.85, 0.75, 0.45)
    for x, y, r in stars: c.arc(x, y, r, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#e6d6ae')); c.arc(190, 560, 50, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#16121e')); c.arc(212, 546, 44, 0, 2 * math.pi); c.fill()
    for i, x in enumerate(range(-80, W + 100, 260)):   # flat bazaar tent silhouettes
        c.set_source_rgb(*rgb('#231c2c' if i % 2 else '#2a2133'))
        c.move_to(x - 30, 1400); c.line_to(x - 30, 980); c.line_to(x + 115, 860); c.line_to(x + 260, 980); c.line_to(x + 260, 1400); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#3a2e3e')); c.set_line_width(3); c.move_to(0, 820); c.curve_to(300, 900, 780, 900, W, 820); c.stroke()
    for j in range(6):   # hanging lanterns (one warm light colour)
        k = (j + 0.5) / 6; x = k * W; y = 820 + 4 * 80 * k * (1 - k) + 22
        c.set_source_rgba(1, 0.75, 0.4, 0.12); c.arc(x, y, 34, 0, 2 * math.pi); c.fill()
        c.set_source_rgb(*rgb('#e0a050')); rrect(c, x - 13, y - 18, 26, 36, 8); c.fill()
    c.set_source_rgb(*rgb('#2b2230')); c.rectangle(0, 1400, W, H - 1400); c.fill()

def snake_head(t):
    """Head position + mouth: idle sway at MOUTH, or the active strike's tip."""
    for s in STR:
        if s['t'] > S.T_RES + 0.05 and not (T_FAIL and s['t'] <= T_FAIL): continue
        tip = tongue_tip(s, t)
        if tip: return tip[0], tip[1], 1.0
    return MOUTH[0] + 26 * math.sin(t * 2.1), MOUTH[1] + 10 * math.sin(t * 4.2), 0.0

def draw_snake(c, t, hx, hy, mo, bulge):
    bx, by = BASKET
    c.set_line_cap(cairo.LINE_CAP_ROUND)
    c1 = (bx - 40 * math.sin(t * 2.1), by - 170); c2 = (lerp(bx, hx, 0.4), lerp(by - 260, hy, 0.6))
    for wdt, col in ((74, '#2f4a2a'), (54, '#4f7a3a')):
        c.set_source_rgb(*rgb(col)); c.set_line_width(wdt); c.move_to(bx, by - 60); c.curve_to(*c1, *c2, hx, hy + 30); c.stroke()
    c.set_source_rgb(*rgb('#c9b878')); c.set_line_width(20); c.move_to(bx, by - 60); c.curve_to(*c1, *c2, hx, hy + 30); c.stroke()   # belly stripe
    if bulge > 0:
        mx = 0.125 * bx + 0.375 * c1[0] + 0.375 * c2[0] + 0.125 * hx; my = 0.125 * (by - 60) + 0.375 * c1[1] + 0.375 * c2[1] + 0.125 * (hy + 30)
        c.set_source_rgb(*rgb('#4f7a3a')); c.arc(mx, my, 50 * bulge, 0, 2 * math.pi); c.fill()
    # hood
    c.set_source_rgb(*rgb('#3f6230')); c.save(); c.translate(hx, hy + 40); c.scale(1.0 - 0.35 * mo, 1); c.scale(105, 120); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    c.set_source_rgb(*rgb('#c9b878')); c.save(); c.translate(hx, hy + 60); c.scale(1.0 - 0.35 * mo, 1); c.scale(40, 70); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    # head
    c.set_source_rgb(*rgb('#5a8a44')); c.save(); c.translate(hx, hy); c.scale(62, 50); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    for sd in (-1, 1):
        c.set_source_rgb(*rgb('#f0d060')); c.arc(hx + sd * 28, hy - 14, 12, 0, 2 * math.pi); c.fill()
        c.set_source_rgb(0.05, 0.05, 0.05); c.save(); c.translate(hx + sd * 28, hy - 14); c.scale(3.5, 10); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    if mo > 0.05:
        c.set_source_rgb(*rgb('#5a1f2a')); c.save(); c.translate(hx, hy + 22); c.scale(40, 26 * mo); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
        c.set_source_rgb(*rgb('#eee8d8'))
        for sd in (-1, 1): c.move_to(hx + sd * 22, hy + 4); c.line_to(hx + sd * 16, hy + 26); c.line_to(hx + sd * 10, hy + 4); c.close_path(); c.fill()
    elif (t * 1.3) % 1 < 0.25:   # flicking forked tongue
        c.set_source_rgb(*rgb('#c0404f')); c.set_line_width(5); c.move_to(hx, hy + 40); c.line_to(hx, hy + 70); c.line_to(hx - 10, hy + 84); c.move_to(hx, hy + 70); c.line_to(hx + 10, hy + 84); c.stroke()
    # basket in front of the body
    c.set_source_rgb(*rgb('#8a6a3a')); c.move_to(bx - 150, by - 70); c.line_to(bx + 150, by - 70); c.line_to(bx + 120, by + 70); c.line_to(bx - 120, by + 70); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#6b5030')); c.set_line_width(6)
    for yy in range(int(by - 50), int(by + 70), 26): c.move_to(bx - 150 + (yy - by + 70) * 0.2, yy); c.line_to(bx + 150 - (yy - by + 70) * 0.2, yy); c.stroke()
    c.set_source_rgb(*rgb('#a0804a')); c.save(); c.translate(bx, by - 70); c.scale(155, 22); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    c.set_source_rgb(*rgb('#2f4a2a')); c.save(); c.translate(bx, by - 70); c.scale(80, 12); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()

def draw_floor(c):
    c.move_to(0, H)
    for x in range(0, W + 1, 6): c.line_to(x, TER.h[x])
    c.line_to(W, H); c.close_path(); c.set_source_rgb(*rgb('#5a2e30')); c.fill()
    c.set_source_rgb(*rgb('#7a4a3a')); c.set_line_width(10)
    for x in range(0, W + 1, 6): (c.move_to if x == 0 else c.line_to)(x, TER.h[x] + 3)
    c.stroke()
    c.set_source_rgba(0.85, 0.65, 0.35, 0.35); c.set_line_width(6)
    for yy in (GROUND + 60, GROUND + 230):
        c.move_to(XMIN - R, yy)
        for x in range(int(XMIN - R), int(XMAX + R), 40): c.line_to(x + 20, yy + 18); c.line_to(x + 40, yy)
        c.stroke()
    for (x0, x1) in ((0, XMIN - R), (XMAX + R, W)):   # stacked clay pots = walls
        cx = (x0 + x1) / 2; wdt = (x1 - x0)
        c.set_source_rgb(*rgb('#3a2a2e')); c.rectangle(x0, GROUND - 640, wdt, 640); c.fill()
        for j, yy in enumerate((GROUND - 105, GROUND - 315, GROUND - 525)):
            c.set_source_rgb(*rgb('#9a5a3a' if j % 2 == 0 else '#87503a'))
            c.save(); c.translate(cx, yy); c.scale(wdt / 2 + 6, 105); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
            c.set_source_rgb(*rgb('#6b3a26')); c.rectangle(cx - wdt * 0.3, yy - 118, wdt * 0.6, 22); c.fill()
            c.set_source_rgba(0, 0, 0, 0.15); c.rectangle(x0, yy + 10, wdt, 10); c.fill()

def render(f, c):
    t = f / FPS; fi = min(f, len(POS) - 1)
    c.save()
    draw_bg(c, t)
    hx, hy, mo = snake_head(t)
    active = (None, (hx, hy, True)) if mo > 0 else None
    if SPIT_T and SPIT_T - 0.15 <= t < SPIT_T + 0.3: mo = 1.0
    bulge = 0.0
    for i in range(3):
        if EATEN_AT[i] and EATEN_AT[i] <= t < EATEN_AT[i] + 1.4 and not (i == 0 and SPIT_T and t >= SPIT_T): bulge = max(bulge, 1 - (t - EATEN_AT[i]) / 1.4 * 0.6)
    draw_snake(c, t, hx, hy, mo, bulge)
    draw_floor(c)
    for i in range(3):
        if eaten(i, t) and not (i == 0 and SPIT_T and t >= SPIT_T): continue
        x, y = POS[fi][i]
        for s in STR:   # being reeled in
            if s.get('got') == i and s['tcatch'] <= t:
                tip = tongue_tip(s, t)
                if tip: x, y = tip[0], tip[1]
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
            draw_blob(c, t + i, x, y, 'scared' if danger else 'worried', 0, R=R, skin=SKINS[i], sweat=False)
    END.draw_claw(c, t)
    c.restore()
    END.header(c, t, fi)

if __name__ == '__main__':
    if sys.argv[1] == 'sim':
        print(SEED, S.OUTCOME, round(S.T_RES - S.T_START, 2), 'eaten', [(NAMES[i], round(EATEN_AT[i] - S.T_START, 1)) for i in range(3) if EATEN_AT[i]], 'strikes', len([s for s in STR if S.T_START <= s['t'] < S.T_RES]), 'dur', S.DUR); sys.exit()
    run(S, render)
