"""2026-11-07 v4 — DODGE – HEARTS: the GIANT ACORNS in an oak forest at night. Gloop is a passive rigid
ball (Ball) bouncing on soft leaf litter between two oak trunks (walls). Seeded-random giant acorns hang
under the oak branches, wobble for a moment, then drop with gravity (some are chosen near where he is at
that moment, none follow him). Every swept touch of a falling acorn is a real momentum-transfer
collision; during the countdown each touch costs a heart. Acorns thud into the ground (crater).
0 hearts = fail (bonked & dizzy)."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the giant acorns'
SEED = int(os.environ.get('SEED', 24))
rng = random.Random(SEED)

class S: pass
S.HOOK2 = 'THE GIANT ACORNS?'; S.HOOK2_SIZE = 92; S.FAIL_WORD = 'BONK!'; S.FAIL_SIZE = 170
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

FLIES = [(rng.uniform(150, 930), rng.uniform(800, 1450), rng.uniform(0, 6.3)) for _ in range(9)]
def draw_bg(c, t, f):
    c.set_source_rgb(*rgb('#111a1c')); c.rectangle(0, HEAD, W, H - HEAD); c.fill()
    c.set_source_rgb(*rgb('#d8d4c0')); c.arc(560, 860, 54, 0, 2 * math.pi); c.fill()   # moon
    for (x, w_, col) in ((300, 60, '#18242a'), (470, 44, '#16222a'), (700, 70, '#18242a'), (830, 40, '#1a262c')):   # far trunks
        c.set_source_rgb(*rgb(col)); c.rectangle(x, HEAD, w_, GROUND - HEAD); c.fill()
    c.set_source_rgb(*rgb('#1c2a26')); c.move_to(0, GROUND)
    for x in range(0, W + 1, 30): c.line_to(x, 1380 - 30 * math.sin(x / 90) - 20 * math.sin(x / 37))
    c.line_to(W, GROUND); c.close_path(); c.fill()   # bushes
    for (x, y, ph) in FLIES:   # fireflies
        a = 0.5 + 0.5 * math.sin(t * 3 + ph)
        c.set_source_rgba(0.9, 1, 0.5, 0.6 * a); c.arc(x + 20 * math.sin(t * 0.7 + ph), y + 14 * math.cos(t * 0.9 + ph), 4, 0, 2 * math.pi); c.fill()
    TER.fill(c, SNAP[min(f, len(SNAP) - 1)], '#5a3e2a', '#2e2016', '#7a5434')
    # oak trunks = walls
    for (x0, x1) in ((0, WALL_L), (WALL_R, W)):
        c.set_source_rgb(*rgb('#4a3a2e')); c.rectangle(x0, HANG - 160, x1 - x0, GROUND - HANG + 200); c.fill()
        c.set_source_rgb(*rgb('#3a2c22')); c.set_line_width(6)
        for k in range(4):
            xx = x0 + (x1 - x0) * (k + 0.5) / 4; c.move_to(xx, HANG - 140)
            for yy in range(HANG - 140, GROUND + 40, 60): c.line_to(xx + 8 * math.sin(yy * 0.03 + k), yy)
            c.stroke()

def draw_fronds(c, t):   # oak branches + leaf clusters across the top
    c.set_source_rgb(*rgb('#3e3026')); c.set_line_width(26)
    c.move_to(WALL_L, HANG - 120); c.curve_to(300, HANG - 90, 600, HANG - 60, WALL_R, HANG - 130); c.stroke()
    c.set_line_width(14); c.move_to(400, HANG - 80); c.curve_to(450, HANG - 160, 520, HANG - 200, 560, HANG - 260); c.stroke()
    for i in range(14):
        x = 40 + i * 78; y = HANG - 150 - 50 * math.sin(i * 1.7); sw = 4 * math.sin(t * 1.2 + i)
        c.set_source_rgb(*(rgb('#24402a') if i % 2 else rgb('#2c4a30'))); c.arc(x + sw, y, 70 + 15 * math.sin(i * 2.3), 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#3e3026'))
    for x in range(160, W - 140, 95): c.arc(x, HANG - 30, 6, 0, 2 * math.pi); c.fill()

def coconut(c, x, y, r, rot):   # giant acorn
    c.save(); c.translate(x, y); c.rotate(rot * 0.2)
    c.set_source_rgb(*rgb('#a0682e')); c.save(); c.scale(0.9, 1.05); c.arc(0, r * 0.08, r, 0, 2 * math.pi); c.restore(); c.fill()
    c.set_source_rgb(*rgb('#c08440')); c.arc(-r * 0.3, r * 0.1, r * 0.35, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#6a4a2a')); c.save(); c.scale(1.08, 0.62); c.arc(0, -r * 0.62, r, math.pi, 2 * math.pi); c.restore(); c.fill()   # cap
    c.rectangle(-r * 1.08, -r * 0.42, r * 2.16, r * 0.16); c.fill()
    c.set_source_rgba(0, 0, 0, 0.25)
    for k in range(-2, 3): c.arc(k * r * 0.38, -r * 0.6, r * 0.09, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#5a3e22')); c.rectangle(-r * 0.08, -r * 1.12, r * 0.16, r * 0.4); c.fill()   # stem
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
            PS.spawn(n['x'], n['sy'] + n['r'] * 0.6, 14, (0.55, 0.38, 0.22), 380, 0.55, grav=1400, r=7)
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
