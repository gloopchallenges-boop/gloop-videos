"""2026-11-05 v3 — DODGE – HEARTS: the FALLING COCONUTS on a tropical beach at night. Gloop is a passive
rigid ball (Ball) bouncing on soft sand between two palm trunks (walls). Seeded-random coconuts hang under
the palm fronds, wobble for a moment, then drop with gravity (some are chosen near where he is at that
moment, none follow him). Every swept touch of a falling coconut is a real momentum-transfer collision;
during the countdown each touch costs a heart. Coconuts thud into the sand (crater). 0 hearts = fail
(bonked & dizzy)."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the falling coconuts'
SEED = int(os.environ.get('SEED', 24))
rng = random.Random(SEED)

class S: pass
S.HOOK2 = 'THE FALLING COCONUTS?'; S.HOOK2_SIZE = 80; S.FAIL_WORD = 'BONK!'; S.FAIL_SIZE = 170
S.T_START = HOOK_T; S.TL = 13.0; S.T_END = S.T_START + S.TL
GROUND = 1600; R = 58; XMIN, XMAX = 190, 890; WALL_L, WALL_R = XMIN - R, XMAX + R
HANG = 640; WOB = 0.55; G = 2600.0; CR = 36
AIM = float(os.environ.get('AIM', 0.4)); IV = float(os.environ.get('IV', 0.95))

NUTS = []; t = -0.6
while t < S.T_END:
    NUTS.append({'t': t, 'r': rng.uniform(44, 52), 'aim': rng.random() < AIM, 'x': None, 'hit': False, 'land': None, 'rot': rng.uniform(0, 6)})
    t += rng.uniform(0.6, 1.4) * IV
def nut_pos(n, t):
    k = max(0, t - n['t'] - WOB); return n['x'], HANG + n['r'] + 0.5 * G * k * k, G * k

TER = Terrain(GROUND, seed=SEED, bumps=3, amp=10, soft=True)
N0 = int(40 * FPS); GX, GYS, HEARTS, SNAP = [], [], [], []
ball = Ball(rng.uniform(350, 730), TER, R=R, seed=SEED, xmin=XMIN, xmax=XMAX, hop=rng.uniform(300, 380), dent=0.004)
hearts = 3; HITS = []; T_FAIL = None; CONTACTS = []; SUB = 8
for f in range(N0):
    t = f / FPS
    live = T_FAIL is None and S.T_START <= t < S.T_END
    for n in NUTS:
        if n['x'] is None and t >= n['t']:
            n['x'] = clamp(ball.x + rng.uniform(-70, 70), XMIN - 20, XMAX + 20) if n['aim'] else rng.uniform(XMIN - 20, XMAX + 20)
            if n['t'] < S.T_START - WOB - 0.5: n['x'] = clamp(ball.x + rng.choice((-1, 1)) * rng.uniform(300, 450), XMIN, XMAX) if abs(ball.x - 540) < 200 else (XMIN + 60 if ball.x > 540 else XMAX - 60)
    px, py = ball.x, ball.y
    ball.step(t)
    for n in NUTS:
        if n['x'] is None or n['land'] is not None or t < n['t'] + WOB: continue
        if T_FAIL is not None and n['t'] > T_FAIL: continue
        for k in range(1, SUB + 1):
            ts = t - 1 / FPS + k / (SUB * FPS)
            if ts < n['t'] + WOB: continue
            nx_, ny_, vy = nut_pos(n, ts)
            if ny_ + n['r'] >= TER.y(nx_):
                n['land'] = ts; n['sy'] = TER.y(nx_) - n['r'] * 0.6; TER.dig(nx_, 22, 40); break
            bx, by = lerp(px, ball.x, k / SUB), lerp(py, ball.y, k / SUB)
            dd = math.hypot(bx - nx_, by - ny_)
            if dd < R + n['r']:
                n['hit'] = True; n['land'] = ts; n['sy'] = ny_
                nx, ny = (bx - nx_) / (dd or 1), (by - ny_) / (dd or 1)
                rel = (vy - ball.vy) * ny
                j = min(0.9 * max(rel, 200), 800); ball.push(nx * max(260, j * 0.6), 0); ball.vy = max(ball.vy, j * max(0.3, ny))
                n['bounce'] = (-nx * 300 + rng.uniform(-80, 80), -500)
                CONTACTS.append((ts, bx - nx * R, by - ny * R))
                if live:
                    hearts -= 1; HITS.append(ts)
                    if hearts == 0: T_FAIL = ts
                break
    if T_FAIL is not None and t > T_FAIL: ball.vmin = 0; ball.e = 0.4; ball.vx *= 0.96
    GX.append(ball.x); GYS.append(ball.y); HEARTS.append(hearts); SNAP.append(TER.snapshot())
S.OUTCOME = 'fail' if T_FAIL else 'win'
S.T_RES = T_FAIL if T_FAIL else S.T_END
S.GRAB = (540, GROUND - R)
END = S.END = Ending(S)
gi = min(int(END.T_GRAB * FPS), N0 - 1); S.GRAB = (GX[gi], GYS[gi])
VIS_END = S.T_RES if T_FAIL else S.T_END
S.events = [[0.05, 'rumble', 0.6]]
for n in NUTS:
    if n['t'] < VIS_END:
        S.events.append([max(0, n['t']), 'creak'])
        if n['land'] is not None and not n['hit']: S.events.append([n['land'], 'thump', 0.8])
for h in HITS: S.events.append([h, 'heart']); S.events.append([h, 'thump', 1.0])
for (tc, _, _) in CONTACTS:
    if tc not in HITS: S.events.append([tc, 'thump', 0.7])
for (tl, xl, imp) in ball.landings:
    if tl < S.T_RES + 1.5: S.events.append([tl, 'hop'])
for tw in ball.walls:
    if tw < S.T_RES + 1.5: S.events.append([tw, 'thump', 0.4])
S.AMB = {'drone': 50, 'wind': 0.035}

def draw_bar(c, t, f):
    hp = HEARTS[f]; lost = [h for h in HITS if h <= t]
    pop = max(0, 1 - (t - lost[-1]) / 0.35) if lost else 0
    for i in range(3):
        x = W / 2 - 150 + i * 150; y = 235; full = i < hp
        sc = 1.0 + (0.35 * pop if i == hp and pop > 0 else 0)
        c.save(); c.translate(x, y); c.scale(sc, sc); heart_path(c, 0, 0, 40)
        c.set_source_rgb(0, 0, 0); c.set_line_width(10); c.stroke_preserve()
        c.set_source_rgb(*(rgb('#ff3b5c') if full else rgb('#3a3446'))); c.fill()
        if full: c.set_source_rgba(1, 1, 1, 0.5); c.arc(-14, -10, 8, 0, 2 * math.pi); c.fill()
        c.restore()
S.draw_bar = draw_bar

stars = [(rng.uniform(0, W), rng.uniform(HEAD, 1050), rng.uniform(1.2, 2.6)) for _ in range(55)]
def draw_bg(c, t, f):
    c.set_source_rgb(*rgb('#141a2c')); c.rectangle(0, HEAD, W, H - HEAD); c.fill()
    c.set_source_rgba(0.85, 0.88, 0.95, 0.5)
    for x, y, r in stars: c.arc(x, y, r, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#e6e2cc')); c.arc(560, 980, 60, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#173048')); c.rectangle(0, 1180, W, GROUND - 1180 + 40); c.fill()   # sea
    c.set_source_rgba(0.9, 0.9, 0.8, 0.13)
    for i in range(8): c.rectangle(560 - 80 + 14 * math.sin(t * 2 + i), 1200 + i * 26, 160 - i * 14, 5); c.fill()
    c.set_source_rgba(1, 1, 1, 0.07)
    for i in range(5): c.rectangle(0, 1260 + i * 70 + 6 * math.sin(t * 1.5 + i), W, 4); c.fill()
    # shoreline foam
    c.set_source_rgba(0.85, 0.9, 0.95, 0.35); c.set_line_width(6)
    for x in range(0, W + 20, 20): (c.move_to if x == 0 else c.line_to)(x, GROUND - 60 + 6 * math.sin(x * 0.03 + t * 2))
    c.stroke()
    TER.fill(c, SNAP[min(f, len(SNAP) - 1)], '#c9ad7d', '#6e5a3e', '#e0c99a')
    # palm trunks = walls
    for (x0, x1, side) in ((0, WALL_L, -1), (WALL_R, W, 1)):
        c.set_source_rgb(*rgb('#5a4330')); c.rectangle(x0, HANG - 120, x1 - x0, GROUND - HANG + 160); c.fill()
        c.set_source_rgb(*rgb('#3f2f22'))
        for yy in range(HANG - 100, GROUND + 40, 70):
            c.move_to(x0, yy); c.line_to(x1, yy - 16); c.line_to(x1, yy - 4); c.line_to(x0, yy + 12); c.close_path(); c.fill()

def draw_fronds(c, t):
    for (cx, side) in ((WALL_L / 2 + 10, 1), (WALL_R + (W - WALL_R) / 2 - 10, -1)):
        for i in range(6):
            a = -0.3 + i * 0.32; sway = 0.04 * math.sin(t * 1.3 + i)
            c.save(); c.translate(cx, HANG - 150); c.scale(side, 1); c.rotate(a + sway)
            c.set_source_rgb(*rgb('#2f4a2e') if i % 2 else rgb('#355536'))
            c.move_to(0, 0); c.curve_to(200, -90, 420, -40, 560, 80); c.curve_to(420, 10, 200, -20, 0, 30); c.close_path(); c.fill()
            c.restore()
    c.set_source_rgb(*rgb('#3a2c1e'))
    for x in range(140, W - 120, 95): c.arc(x, HANG - 30, 6, 0, 2 * math.pi); c.fill()

def coconut(c, x, y, r, rot):
    c.save(); c.translate(x, y); c.rotate(rot)
    c.set_source_rgb(*rgb('#7a5030')); c.arc(0, 0, r, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#9a6a40')); c.arc(-r * 0.25, -r * 0.25, r * 0.55, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#2a1a10'))
    for a in (0, 2.1, 4.2): c.arc(r * 0.45 * math.cos(a), r * 0.45 * math.sin(a), r * 0.12, 0, 2 * math.pi); c.fill()
    c.restore()

def draw_nuts(c, t):
    for n in NUTS:
        if n['x'] is None or n['t'] > t or n['t'] >= VIS_END: continue
        if n['land'] is not None and t >= n['land']:
            k = t - n['land']
            if n['hit']:
                if k > 1.2: continue
                bvx, bvy = n['bounce']; x = n['x'] + bvx * k; y = n['sy'] + bvy * k + 0.5 * G * k * k
                gy = TER.y(x) - n['r']
                if y > gy: y = gy
                coconut(c, x, y, n['r'], n['rot'] + k * 8); continue
            if k > 2.0: continue
            c.save(); c.push_group(); coconut(c, n['x'], n['sy'], n['r'], n['rot']); c.pop_group_to_source(); c.paint_with_alpha(min(1, (2.0 - k) / 0.4)); c.restore()
            continue
        x, y, _ = nut_pos(n, t)
        wob = 0.25 * math.sin(t * 40) if t < n['t'] + WOB else 0
        if t < n['t'] + WOB:
            c.set_source_rgb(*rgb('#3a5a33')); c.set_line_width(5); c.move_to(x, HANG - 30); c.line_to(x + wob * 20, y - n['r']); c.stroke()
        coconut(c, x + wob * 20, y, n['r'], n['rot'] + wob)
        if t >= n['t'] + WOB:
            gy = TER.y(x); k = clamp(1 - (gy - y) / 1000, 0.2, 1)
            c.set_source_rgba(0, 0, 0, 0.25 * k); c.save(); c.translate(x, gy + 4); c.scale(n['r'] * 1.1 * k + 5, 6); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()

PS = Particles(9)
def render(f, c):
    t = f / FPS; shake = (0, 0)
    if any(abs(t - h) < 0.2 for h in HITS): shake = (rng.uniform(-4, 4), rng.uniform(-4, 4))
    c.save(); c.translate(*shake)
    fi = min(f, len(GX) - 1)
    draw_bg(c, t, fi)
    flat = T_FAIL is not None and t >= T_FAIL
    if END.carried(t) or t >= END.T_GRAB:
        gx, gy = (END.carry_xy(t) if END.carried(t) else S.GRAB)
    else:
        gx, gy = GX[fi], GYS[fi]
        h = max(0, TER.y(gx) - R - gy); kk = 1 / (1 + h / 220)
        c.set_source_rgba(0, 0, 0, 0.25 * kk); c.save(); c.translate(gx, TER.y(gx) + 3); c.scale(R * (0.5 + 0.4 * kk), 9); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    danger = any(n['x'] is not None and n['t'] <= t < n['t'] + WOB + 0.6 and abs(n['x'] - GX[fi]) < 160 for n in NUTS)
    mood = 'happy' if (t >= S.T_END and S.OUTCOME == 'win') else ('scared' if danger or flat else 'worried')
    draw_blob(c, t, gx, gy, mood, 0, R=R, dizzy=flat and t > T_FAIL + 0.3)
    draw_nuts(c, t)
    draw_fronds(c, t)
    for n in NUTS:
        if n['land'] is not None and not n['hit'] and abs(t - n['land']) < 0.5 / FPS and n['t'] < VIS_END:
            PS.spawn(n['x'], n['sy'] + n['r'] * 0.6, 14, (0.82, 0.7, 0.5), 380, 0.55, grav=1400, r=7)
    for (tc, cx, cy) in CONTACTS:
        if abs(t - tc) < 0.5 / FPS: PS.spawn(cx, cy, 12, (0.85, 0.75, 0.55), 340, 0.45, grav=900, r=6)
    PS.draw(c)
    END.draw_claw(c, t)
    c.restore()
    END.header(c, t, min(f, len(HEARTS) - 1))

if __name__ == '__main__':
    if sys.argv[1] == 'sim':
        print(SEED, S.OUTCOME, round(S.T_RES - S.T_START, 2), 'hits', [round(h - S.T_START, 1) for h in HITS], 'nuts', len([n for n in NUTS if n['t'] < VIS_END]), 'contacts', len(CONTACTS), 'dur', S.DUR); sys.exit()
    run(S, render)
