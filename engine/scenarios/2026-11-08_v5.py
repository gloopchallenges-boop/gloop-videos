"""2026-11-08 v5 — WHO FIRST: the GIANT VACUUM. Gloop (orange) and two rival blobs (blue, pink) are passive
rigid balls (Ball) bouncing on the wooden floor of a living room at night between a sofa arm and a bookshelf;
they collide with each other (equal-mass elastic). A giant canister vacuum at the back swings its hose nozzle
down at seeded-random times at where a random remaining blob WAS a moment ago — the nozzle slurps whoever it
touches. Gloop slurped = fail (sucked up, spat back out dusty & dizzy). Timer ends unslurped = win."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the giant vacuum'
SEED = int(os.environ.get('SEED', 21))
rng = random.Random(SEED)

class S: pass
S.HOOK2 = 'THE GIANT VACUUM?'; S.HOOK2_SIZE = 92; S.FAIL_WORD = 'SLURP!'; S.FAIL_SIZE = 160
S.T_START = HOOK_T; S.TL = 13.0; S.T_END = S.T_START + S.TL
GROUND = 1610; R = 56; XMIN, XMAX = 160, 920
MOUTH = (540, 1060); TIP_R = 46; T_OUT, T_HOLD, T_BACK = 0.22, 0.08, 0.35
NAMES = ['GLOOP', 'BLUE', 'ROSIE']
SKINS = [('#ffd36b', '#ff8a1f', '#c45a00'), ('#b8dcff', '#4a90d0', '#2a5a8a'), ('#ffd0e4', '#e070a0', '#8a3a5a')]

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
if T_FAIL:   # flytrap spits Gloop out dizzy & slimy onto the log
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
if T_FAIL: S.events.append([SPIT_T, 'pop'])
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


stars = [(rng.uniform(560, 900), rng.uniform(520, 820), rng.uniform(1.2, 2.4)) for _ in range(14)]
POT = (540, 1360)
def draw_bg(c, t):
    c.set_source_rgb(*rgb('#1c1a24')); c.rectangle(0, HEAD, W, H - HEAD); c.fill()
    # striped wallpaper
    c.set_source_rgb(*rgb('#201e2a'))
    for x in range(0, W, 90): c.rectangle(x, HEAD, 40, 1300 - HEAD); c.fill()
    # window with moon
    c.set_source_rgb(*rgb('#141c2e')); c.rectangle(560, 500, 340, 340); c.fill()
    c.set_source_rgba(0.85, 0.9, 0.95, 0.45)
    for x, y, r in stars: c.arc(x, y, r, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#e2e0cc')); c.arc(820, 590, 40, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#3a3446')); c.set_line_width(14); c.rectangle(560, 500, 340, 340); c.stroke()
    c.move_to(730, 500); c.line_to(730, 840); c.stroke(); c.move_to(560, 670); c.line_to(900, 670); c.stroke()
    c.set_source_rgb(*rgb('#3e2a3a')); c.rectangle(520, 470, 50, 420); c.fill(); c.rectangle(890, 470, 50, 420); c.fill()   # curtains
    # picture frame + floor lamp (one quiet light)
    c.set_source_rgb(*rgb('#4a3a2a')); c.rectangle(170, 560, 220, 160); c.fill(); c.set_source_rgb(*rgb('#2a3a3a')); c.rectangle(186, 576, 188, 128); c.fill()
    c.set_source_rgb(*rgb('#3a4a3a')); c.move_to(186, 704); c.line_to(260, 620); c.line_to(320, 680); c.line_to(374, 640); c.line_to(374, 704); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#2e2c36')); c.set_line_width(8); c.move_to(160, 1300); c.line_to(160, 900); c.stroke()
    c.set_source_rgb(*rgb('#c9a45a')); c.move_to(110, 900); c.line_to(210, 900); c.line_to(185, 830); c.line_to(135, 830); c.close_path(); c.fill()
    c.set_source_rgba(1, 0.9, 0.6, 0.04); c.move_to(110, 900); c.line_to(20, 1300); c.line_to(300, 1300); c.line_to(210, 900); c.close_path(); c.fill()
    # skirting board + back floor
    c.set_source_rgb(*rgb('#2e2a34')); c.rectangle(0, 1290, W, 30); c.fill()
    c.set_source_rgb(*rgb('#3a2e28')); c.rectangle(0, 1320, W, H - 1320); c.fill()

def snake_head(t):
    """Nozzle position + suction amount: idle sway at MOUTH, or the active lunge's tip."""
    for s in STR:
        if s['t'] > S.T_RES + 0.05 and not (T_FAIL and s['t'] <= T_FAIL): continue
        tip = tongue_tip(s, t)
        if tip: return tip[0], tip[1], (1.0 if tip[2] else 0.15)
    return MOUTH[0] + 26 * math.sin(t * 2.1), MOUTH[1] + 10 * math.sin(t * 4.2), 0.35 + 0.15 * math.sin(t * 3)

def draw_snake(c, t, hx, hy, mo, bulge):   # the giant vacuum: canister at the back, hose, wide nozzle
    bx, by = POT
    # canister body
    c.set_source_rgb(*rgb('#8a3a3a')); rrect(c, bx - 150, by - 230, 300, 210, 70); c.fill()
    c.set_source_rgb(*rgb('#6e2c2c')); rrect(c, bx - 150, by - 110, 300, 90, 40); c.fill()
    c.set_source_rgb(*rgb('#2a2a30'))
    for dx in (-110, 110): c.arc(bx + dx, by - 18, 34, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#5a5a64'))
    for dx in (-110, 110): c.arc(bx + dx, by - 18, 12, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#d8d4cc')); rrect(c, bx - 70, by - 200, 140, 40, 10); c.fill()
    font(c, 28); c.set_source_rgb(*rgb('#8a3a3a')); e = c.text_extents('SUCKMAX'); c.move_to(bx - e.width / 2, by - 170); c.show_text('SUCKMAX')
    on = (t * 3) % 1 < 0.5
    c.set_source_rgb(*(rgb('#7dff8a') if on else rgb('#2a5a2a'))); c.arc(bx + 110, by - 180, 10, 0, 2 * math.pi); c.fill()
    # hose
    c.set_line_cap(cairo.LINE_CAP_ROUND)
    n0 = (bx, by - 230); c1 = (bx + 40 - 30 * math.sin(t * 2.1), by - 520); c2 = (lerp(bx, hx, 0.6), lerp(by - 520, hy - 300, 0.6))
    hd = (hx, hy - 70)
    c.set_source_rgb(*rgb('#4a4a54')); c.set_line_width(44); c.move_to(*n0); c.curve_to(*c1, *c2, *hd); c.stroke()
    c.set_source_rgb(*rgb('#3a3a44')); c.set_line_width(44); c.set_dash([8, 22]); c.move_to(*n0); c.curve_to(*c1, *c2, *hd); c.stroke(); c.set_dash([])
    if bulge > 0:
        mx = 0.125 * n0[0] + 0.375 * c1[0] + 0.375 * c2[0] + 0.125 * hd[0]; my = 0.125 * n0[1] + 0.375 * c1[1] + 0.375 * c2[1] + 0.125 * hd[1]
        c.set_source_rgb(*rgb('#4a4a54')); c.arc(mx, my, 44 * bulge, 0, 2 * math.pi); c.fill()
    # metal wand + wide nozzle head (mouth faces down at the tip)
    c.set_source_rgb(*rgb('#9aa0aa')); c.rectangle(hx - 14, hy - 110, 28, 60); c.fill()
    c.set_source_rgb(*rgb('#6a3030')); rrect(c, hx - 95, hy - 60, 190, 50, 14); c.fill()
    c.set_source_rgb(*rgb('#2a2a30')); rrect(c, hx - 85, hy - 18, 170, 16, 6); c.fill()
    if mo > 0.5:   # suction lines into the mouth
        c.set_source_rgba(0.85, 0.85, 0.9, 0.45); c.set_line_width(4)
        for j in range(5):
            k = (t * 4 + j / 5) % 1; dx = (j - 2) * 40
            c.move_to(hx + dx * (1.6 - k), hy + 70 * (1 - k)); c.line_to(hx + dx * (1.3 - k * 0.8), hy + 70 * (1 - k) - 26); c.stroke()

def draw_floor(c):
    c.move_to(0, H)
    for x in range(0, W + 1, 6): c.line_to(x, TER.h[x])
    c.line_to(W, H); c.close_path(); c.set_source_rgb(*rgb('#5a4232')); c.fill()
    c.set_source_rgb(*rgb('#6e5240')); c.set_line_width(10)
    for x in range(0, W + 1, 6): (c.move_to if x == 0 else c.line_to)(x, TER.h[x] + 3)
    c.stroke()
    c.set_source_rgba(0, 0, 0, 0.25); c.set_line_width(3)
    for yy in range(GROUND + 50, H, 55): c.move_to(0, yy); c.line_to(W, yy); c.stroke()
    for j, yy in enumerate(range(GROUND + 50, H, 55)):
        for x in range((j % 2) * 150, W, 300): c.move_to(x, yy); c.line_to(x, yy + 55); c.stroke()
    c.set_source_rgb(*rgb('#3e4a5a')); c.save(); c.translate(540, GROUND + 140); c.scale(330, 60); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()   # round rug
    c.set_source_rgb(*rgb('#4a5a6a')); c.save(); c.translate(540, GROUND + 140); c.scale(250, 40); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    for (x0, x1, s) in ((0, XMIN - R, 1), (XMAX + R, W, -1)):   # sofa arm (left) and bookshelf (right) = walls
        wdt = x1 - x0
        if s == 1:
            c.set_source_rgb(*rgb('#3a4a5e')); rrect(c, x0 - 20, GROUND - 420, wdt + 20, 440, 30); c.fill()
            c.set_source_rgb(*rgb('#33425a')); rrect(c, x0 - 20, GROUND - 440, wdt + 20, 90, 40); c.fill()
        else:
            c.set_source_rgb(*rgb('#4a3424')); c.rectangle(x0, GROUND - 640, wdt + 10, 660); c.fill()
            for j, yy in enumerate(range(GROUND - 620, GROUND - 20, 150)):
                c.set_source_rgb(*rgb('#2e2018')); c.rectangle(x0 + 10, yy, wdt - 10, 130); c.fill()
                for k in range(4):
                    c.set_source_rgb(*rgb(('#6a3a3a', '#3a5a6a', '#6a6a3a', '#4a3a6a')[(j + k) % 4])); c.rectangle(x0 + 16 + k * (wdt - 24) / 4, yy + 30 + (k % 2) * 10, (wdt - 24) / 4 - 4, 100 - (k % 2) * 10); c.fill()

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
            draw_blob(c, t, x, y, mood, 0, R=R, skin=(('#d8c8b0', '#b08a6a', '#6a5040') if slimy else SKINS[0]), dizzy=bool(slimy))
            if slimy:
                c.set_source_rgba(0.6, 0.58, 0.55, 0.6)
                for j in range(4): c.arc(x - 45 + j * 30, y - R - 10 - 30 * ((t * 1.2 + j * 0.27) % 1), 7, 0, 2 * math.pi); c.fill()
        else:
            draw_blob(c, t + i, x, y, 'scared' if danger else 'worried', 0, R=R, skin=SKINS[i], sweat=False)
    END.draw_claw(c, t)
    c.restore()
    END.header(c, t, fi)

if __name__ == '__main__':
    if sys.argv[1] == 'sim':
        print(SEED, S.OUTCOME, round(S.T_RES - S.T_START, 2), 'eaten', [(NAMES[i], round(EATEN_AT[i] - S.T_START, 1)) for i in range(3) if EATEN_AT[i]], 'strikes', len([s for s in STR if S.T_START <= s['t'] < S.T_RES]), 'dur', S.DUR); sys.exit()
    run(S, render)
