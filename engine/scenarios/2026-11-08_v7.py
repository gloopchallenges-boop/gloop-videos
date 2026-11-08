"""2026-11-08 v7 — DODGE – HEARTS: the FALLING FLOWER POTS in a city alley at night. Gloop is a passive rigid
ball (Ball) bouncing on the cobbles between two brick building walls. Seeded-random terracotta flower pots sit on
the long balcony ledge above, wobble for a moment, then drop with gravity (some are chosen near where he is at
that moment, none follow him). Every swept touch of a falling pot is a real momentum-transfer collision; during
the countdown each touch costs a heart. Pots smash on the cobbles (shards + small dent).
0 hearts = fail (bonked & dizzy)."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the falling flower pots'
SEED = int(os.environ.get('SEED', 24))
rng = random.Random(SEED)

class S: pass
S.HOOK2 = 'THE FALLING FLOWER POTS?'; S.HOOK2_SIZE = 70; S.FAIL_WORD = 'BONK!'; S.FAIL_SIZE = 170
S.T_START = HOOK_T; S.TL = 12.0; S.T_END = S.T_START + S.TL
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
        if n['land'] is not None and not n['hit']: S.events.append([n['land'], 'thump', 0.8]); S.events.append([n['land'], 'crackle'])
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

WINS = [(x, y, rng.random() < 0.35) for x in (330, 470, 610, 750) for y in (800, 1010, 1220)]
def draw_bg(c, t, f):
    c.set_source_rgb(*rgb('#121420')); c.rectangle(0, HEAD, W, H - HEAD); c.fill()
    c.set_source_rgb(*rgb('#d8d4c0')); c.arc(540, 420, 40, 0, 2 * math.pi); c.fill()   # moon over the alley
    # back building at the end of the alley
    c.set_source_rgb(*rgb('#22202c')); c.rectangle(WALL_L, 520, WALL_R - WALL_L, GROUND - 520); c.fill()
    c.set_source_rgb(*rgb('#1c1a26'))
    for yy in range(540, GROUND, 36): c.rectangle(WALL_L, yy, WALL_R - WALL_L, 3); c.fill()
    for (x, y, lit) in WINS:
        c.set_source_rgb(*(rgb('#c9a45a') if lit else rgb('#16182a'))); c.rectangle(x - 40, y, 80, 110); c.fill()
        c.set_source_rgb(*rgb('#2e2a38')); c.set_line_width(6); c.rectangle(x - 40, y, 80, 110); c.stroke(); c.move_to(x, y); c.line_to(x, y + 110); c.stroke()
    # street lamp (one quiet light)
    c.set_source_rgb(*rgb('#2e2c36')); c.set_line_width(10); c.move_to(840, GROUND); c.line_to(840, 1280); c.stroke()
    c.set_line_width(6); c.move_to(840, 1280); c.curve_to(840, 1240, 800, 1230, 790, 1260); c.stroke()
    c.set_source_rgb(*rgb('#e8c46a')); c.arc(790, 1272, 12, 0, 2 * math.pi); c.fill()
    c.set_source_rgba(1, 0.9, 0.6, 0.05); c.move_to(770, 1280); c.line_to(620, GROUND); c.line_to(960, GROUND); c.line_to(810, 1280); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#2a2a34')); rrect(c, 230, GROUND - 120, 110, 120, 10); c.fill()   # trash bin
    c.set_source_rgb(*rgb('#34343e')); rrect(c, 222, GROUND - 132, 126, 20, 6); c.fill()
    TER.fill(c, SNAP[min(f, len(SNAP) - 1)], '#3e3c44', '#24222a', '#55525c')
    c.set_source_rgba(0, 0, 0, 0.18); c.set_line_width(3)   # cobbles
    for j, yy in enumerate(range(GROUND + 40, H, 50)):
        for x in range((j % 2) * 40, W, 80): c.arc(x, yy, 30, math.pi * 1.1, math.pi * 1.9); c.stroke()
    # brick building walls = walls
    for (x0, x1) in ((0, WALL_L), (WALL_R, W)):
        c.set_source_rgb(*rgb('#4a2e2a')); c.rectangle(x0, HEAD, x1 - x0, GROUND - HEAD + 40); c.fill()
        c.set_source_rgb(*rgb('#3a2420'))
        for j, yy in enumerate(range(HEAD, GROUND + 40, 34)):
            c.rectangle(x0, yy, x1 - x0, 4); c.fill()
            for xx in range(int(x0) + (j % 2) * 30, int(x1), 60): c.rectangle(xx, yy, 4, 34); c.fill()
        c.set_source_rgb(*rgb('#2a1c1a')); c.rectangle(x1 - 14 if x0 == 0 else x0, HEAD, 14, GROUND - HEAD + 40); c.fill()

def draw_fronds(c, t):   # long balcony ledge with a rail across the top
    c.set_source_rgb(*rgb('#3a3640')); c.rectangle(0, HANG - 40, W, 40); c.fill()
    c.set_source_rgb(*rgb('#2a2630')); c.rectangle(0, HANG - 8, W, 12); c.fill()
    c.set_source_rgb(*rgb('#1e1c24')); c.set_line_width(6)
    c.move_to(0, HANG - 180); c.line_to(W, HANG - 180); c.stroke()
    for x in range(10, W, 44): c.move_to(x, HANG - 180); c.line_to(x, HANG - 40); c.stroke()
    for i, x in enumerate(range(60, W, 170)):   # hanging ivy
        c.set_source_rgb(*rgb('#2c4a30' if i % 2 else '#24402a'))
        for k in range(5): c.arc(x + 6 * math.sin(t + i + k), HANG - 30 + k * 26, 16 - k * 2, 0, 2 * math.pi); c.fill()

def coconut(c, x, y, r, rot):   # terracotta flower pot with a plant
    c.save(); c.translate(x, y); c.rotate(rot * 0.15)
    for (a, col) in ((-0.5, '#3e6a3a'), (0, '#4a7a42'), (0.5, '#3e6a3a')):   # leaves
        c.save(); c.translate(0, -r * 0.7); c.rotate(a); c.set_source_rgb(*rgb(col)); c.save(); c.scale(r * 0.28, r * 0.6); c.arc(0, -1, 1, 0, 2 * math.pi); c.restore(); c.fill(); c.restore()
    c.set_source_rgb(*rgb('#e06a7a')); c.arc(0, -r * 1.35, r * 0.2, 0, 2 * math.pi); c.fill()   # flower
    c.set_source_rgb(*rgb('#b0603a')); c.move_to(-r * 0.85, -r * 0.5); c.line_to(r * 0.85, -r * 0.5); c.line_to(r * 0.62, r); c.line_to(-r * 0.62, r); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#c8744a')); rrect(c, -r * 0.98, -r * 0.78, r * 1.96, r * 0.36, 4); c.fill()   # rim
    c.set_source_rgba(0, 0, 0, 0.15); c.move_to(r * 0.3, -r * 0.42); c.line_to(r * 0.85, -r * 0.42); c.line_to(r * 0.62, r); c.line_to(r * 0.2, r); c.close_path(); c.fill()
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
            if k > 1.6: continue
            c.set_source_rgba(0.69, 0.38, 0.23, min(1, (1.6 - k) / 0.4))   # broken shards + spilled soil
            for q in range(5):
                sx = n['x'] + (q - 2) * n['r'] * 0.55; sy = TER.y(sx) - 6
                c.save(); c.translate(sx, sy); c.rotate(q * 1.3); c.move_to(-12, 6); c.line_to(12, 6); c.line_to(4, -10); c.close_path(); c.restore(); c.fill()
            c.set_source_rgba(0.2, 0.15, 0.1, min(1, (1.6 - k) / 0.4)); c.save(); c.translate(n['x'], TER.y(n['x']) - 2); c.scale(n['r'] * 0.9, 9); c.arc(0, 0, 1, math.pi, 2 * math.pi); c.restore(); c.fill()
            continue
        x, y, _ = nut_pos(n, t)
        wob = 0.25 * math.sin(t * 40) if t < n['t'] + WOB else 0
        if t < n['t'] + WOB:
            c.set_source_rgb(*rgb('#3e3026')); c.set_line_width(6); c.move_to(x, HANG - 30); c.line_to(x + wob * 20, y - n['r']); c.stroke()
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
            PS.spawn(n['x'], n['sy'] + n['r'] * 0.6, 14, (0.72, 0.4, 0.25), 380, 0.55, grav=1400, r=7)
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
