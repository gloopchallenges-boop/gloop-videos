"""2026-11-25 v1 — DODGE – HEARTS: the FALLING BRICKS (based on 2026-11-19 v2 apples). Gloop is a passive rigid ball
(Ball) bouncing on the dirt of a construction site at night between two stacks of concrete blocks. Seeded-random bricks
teeter on the edge of a scaffolding plank, then drop with gravity (some are chosen near where he is at that moment,
none follow him). Every swept touch of a falling brick is a real momentum-transfer collision; during the countdown each
touch costs a heart. Bricks thud into the dirt (small dent). 0 hearts = fail (bonked & dizzy)."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the falling bricks'
SEED = int(os.environ.get('SEED', 5))
rng = random.Random(SEED)

class S: pass
S.HOOK2 = 'THE FALLING BRICKS?'; S.HOOK2_SIZE = 90; S.FAIL_WORD = 'BONK!'; S.FAIL_SIZE = 170
S.T_START = HOOK_T; S.TL = 12.5; S.T_END = S.T_START + S.TL
GROUND = 1600; R = 58; XMIN, XMAX = 190, 890; WALL_L, WALL_R = XMIN - R, XMAX + R
HANG = 620; WOB = 0.55; G = 2600.0; CR = 36
AIM = float(os.environ.get('AIM', 0.4)); IV = float(os.environ.get('IV', 0.95))

NUTS = []; t = -0.6
while t < S.T_END:
    NUTS.append({'t': t, 'r': rng.uniform(42, 50), 'aim': rng.random() < AIM, 'x': None, 'hit': False, 'land': None, 'rot': rng.uniform(0, 6)})
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
                n['land'] = ts; n['sy'] = TER.y(nx_) - n['r'] * 0.6; TER.dig(nx_, 26, 46); break
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
        if n['land'] is not None and not n['hit']: S.events.append([n['land'], 'thump', 0.9])
for h in HITS: S.events.append([h, 'heart']); S.events.append([h, 'thump', 1.0])
for (tc, _, _) in CONTACTS:
    if tc not in HITS: S.events.append([tc, 'thump', 0.7])
for (tl, xl, imp) in ball.landings:
    if tl < S.T_RES + 1.5: S.events.append([tl, 'hop'])
for tw in ball.walls:
    if tw < S.T_RES + 1.5: S.events.append([tw, 'thump', 0.4])
S.AMB = {'drone': 60, 'wind': 0.03, 'rumble': 0.0}

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


def blocks(c, x0, y0, x1, y1, seed):   # stacked grey concrete blocks
    c.set_source_rgb(*rgb('#4a4c54')); c.rectangle(x0, y0, x1 - x0, y1 - y0); c.fill()
    c.set_source_rgba(0, 0, 0, 0.35); c.set_line_width(4)
    for j, yy in enumerate(range(int(y0), int(y1), 70)):
        c.move_to(x0, yy); c.line_to(x1, yy); c.stroke()
        off = 0 if j % 2 else 60
        for xx in range(int(x0) + off, int(x1), 120): c.move_to(xx, yy); c.line_to(xx, min(yy + 70, y1)); c.stroke()
    c.set_source_rgba(0, 0, 0, 0.25)
    for j, yy in enumerate(range(int(y0) + 22, int(y1), 70)):
        off = 30 if j % 2 else 90
        for xx in range(int(x0) + off, int(x1) - 20, 120): c.rectangle(xx - 14, yy, 28, 26); c.fill()

def draw_bg(c, t, f):
    c.set_source_rgb(*rgb('#12141f')); c.rectangle(0, HEAD, W, H - HEAD); c.fill()
    for i in range(26):
        sx = (i * 263) % W; sy = HEAD + 30 + (i * 97) % 200
        c.set_source_rgba(1, 1, 0.9, 0.3 + 0.2 * math.sin(t * 2 + i)); c.arc(sx, sy, 2.4, 0, 2 * math.pi); c.fill()
    # unfinished building skeleton in the back (dim)
    c.set_source_rgb(*rgb('#1c1f2c')); c.rectangle(250, 820, 580, GROUND - 820); c.fill()
    c.set_source_rgb(*rgb('#262a38'))
    for yy in (820, 1010, 1200, 1390): c.rectangle(240, yy, 600, 18); c.fill()
    for xx in (250, 440, 630, 812): c.rectangle(xx, 820, 18, GROUND - 820); c.fill()
    c.set_source_rgb(*rgb('#2c2418'))
    for (xx, yy) in ((300, 1060), (500, 1250), (680, 1060)): c.rectangle(xx, yy, 110, 120); c.fill()
    # a work lamp on a tripod (the one quiet light)
    c.set_source_rgb(*rgb('#1a1a20')); c.set_line_width(6)
    for dx in (-40, 0, 40): c.move_to(700, 1390); c.line_to(700 + dx, GROUND); c.stroke()
    c.set_source_rgb(*rgb('#e8d9a0')); rrect(c, 676, 1360, 48, 34, 6); c.fill()
    # a wheelbarrow
    c.set_source_rgb(*rgb('#3a6a8a')); c.move_to(360, GROUND - 70); c.line_to(470, GROUND - 70); c.line_to(450, GROUND - 30); c.line_to(380, GROUND - 30); c.fill()
    c.set_source_rgb(*rgb('#1a1a20')); c.arc(415, GROUND - 22, 18, 0, 2 * math.pi); c.fill()
    c.set_line_width(6); c.move_to(470, GROUND - 66); c.line_to(530, GROUND - 46); c.stroke()
    TER.fill(c, SNAP[min(f, len(SNAP) - 1)], '#4a3c30', '#2c241c', '#5c4c3c')   # packed dirt
    for (x0, x1) in ((-20, WALL_L), (WALL_R, W + 20)): blocks(c, x0, 700, x1, GROUND + 60, int(x0))

def draw_fronds(c, t):   # scaffolding with a plank across the top: bricks teeter off its edge
    c.set_source_rgb(*rgb('#3a3e48'))
    for xx in (40, 300, 560, 820, 1040): c.rectangle(xx - 8, HEAD, 16, HANG - HEAD); c.fill()
    c.set_source_rgb(*rgb('#3a3e48')); c.set_line_width(10)
    for xx in (40, 300, 560, 820): c.move_to(xx, HANG - 30); c.line_to(xx + 260, HEAD + 60); c.stroke()
    c.rectangle(-10, HEAD + 50, W + 20, 14); c.fill()
    c.set_source_rgb(*rgb('#8a6a40')); c.rectangle(-10, HANG - 30, W + 20, 34); c.fill()
    c.set_source_rgba(0, 0, 0, 0.3); c.set_line_width(3)
    for xx in range(0, W, 220): c.move_to(xx, HANG - 30); c.line_to(xx, HANG + 4); c.stroke()
    c.set_source_rgb(*rgb('#6a5030')); c.rectangle(-10, HANG + 4, W + 20, 8); c.fill()
    # a pallet of resting bricks on the plank
    for k in range(6):
        for j in range(2): coconut(c, 150 + k * 58 + j * 29, HANG - 52 - j * 30, 28, 0)
    for k in range(4): coconut(c, 700 + k * 62, HANG - 54, 30, 0)
    # little yellow-black hazard tape
    for xx in range(0, W, 60):
        c.set_source_rgb(*rgb('#d8b830' if (xx // 60) % 2 else '#1a1a1a')); c.rectangle(xx, HANG + 12, 60, 10); c.fill()

def coconut(c, x, y, r, rot):   # a red clay brick (collision radius r = half its length)
    c.save(); c.translate(x, y); c.rotate(rot * 0.12)
    w, h = r * 2.0, r * 1.05
    c.set_source_rgb(*rgb('#a8503a')); c.rectangle(-w / 2, -h / 2, w, h); c.fill()
    c.set_source_rgb(*rgb('#c4664c')); c.rectangle(-w / 2, -h / 2, w, h * 0.22); c.fill()
    c.set_source_rgb(*rgb('#7a3426'))
    for dx in (-0.45, 0, 0.45): c.arc(dx * w * 0.75, 0.05 * h, h * 0.13, 0, 2 * math.pi); c.fill()
    c.set_source_rgba(0, 0, 0, 0.3); c.set_line_width(3); c.rectangle(-w / 2, -h / 2, w, h); c.stroke()
    c.restore()

def draw_nuts(c, t):
    for n in NUTS:
        if n['x'] is None or n['t'] > t or n['t'] >= VIS_END: continue
        if n['land'] is not None and t >= n['land']:
            k = t - n['land']
            if n['hit']:
                if k > 1.2: continue
                bvx, bvy = n['bounce']; x = n['x'] + bvx * k; y = n['sy'] + bvy * k + 0.5 * G * k * k
                gy = TER.y(x) - n['r'] * 0.8
                if y > gy: y = gy
                coconut(c, x, y, n['r'], n['rot'] + k * 5); continue
            if k > 1.6: continue
            c.push_group(); coconut(c, n['x'], n['sy'] - n['r'] * 0.0, n['r'], n['rot']); c.pop_group_to_source(); c.paint_with_alpha(min(1, (1.6 - k) / 0.4))   # lands flat
            continue
        x, y, _ = nut_pos(n, t)
        wob = 0.25 * math.sin(t * 40) if t < n['t'] + WOB else 0
        fall = max(0, t - n['t'] - WOB)
        coconut(c, x + wob * 20, y, n['r'], wob + fall * (0.8 if int(n['rot'] * 10) % 2 else -0.8))
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
            PS.spawn(n['x'], n['sy'] + n['r'] * 0.6, 10, (0.55, 0.45, 0.38), 300, 0.5, grav=1400, r=6)
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
