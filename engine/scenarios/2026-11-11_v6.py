"""2026-11-11 v6 — DODGE – HEARTS: the FALLING BOOKS in an old library at night. Gloop is a passive rigid ball
(Ball) bouncing on a thick carpet between two tall bookcases. Seeded-random heavy books wobble on the high top
shelf for a moment, then drop with gravity (some are chosen near where he is at that moment, none follow him).
Every swept touch of a falling book is a real momentum-transfer collision; during the countdown each touch costs
a heart. Books thud flat onto the carpet (small dent). 0 hearts = fail (bonked & dizzy)."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the falling books'
SEED = int(os.environ.get('SEED', 16))
rng = random.Random(SEED)

class S: pass
S.HOOK2 = 'THE FALLING BOOKS?'; S.HOOK2_SIZE = 90; S.FAIL_WORD = 'BONK!'; S.FAIL_SIZE = 170
S.T_START = HOOK_T; S.TL = 12.0; S.T_END = S.T_START + S.TL
GROUND = 1600; R = 58; XMIN, XMAX = 190, 890; WALL_L, WALL_R = XMIN - R, XMAX + R
HANG = 620; WOB = 0.55; G = 2600.0; CR = 36
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
        if n['land'] is not None and not n['hit']: S.events.append([n['land'], 'thump', 0.9])
for h in HITS: S.events.append([h, 'heart']); S.events.append([h, 'thump', 1.0])
for (tc, _, _) in CONTACTS:
    if tc not in HITS: S.events.append([tc, 'thump', 0.7])
for (tl, xl, imp) in ball.landings:
    if tl < S.T_RES + 1.5: S.events.append([tl, 'hop'])
for tw in ball.walls:
    if tw < S.T_RES + 1.5: S.events.append([tw, 'thump', 0.4])
S.AMB = {'drone': 46, 'wind': 0.05, 'rumble': 0.03}

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

BOOKC = ['#7a3a3a', '#3a5a7a', '#4a6a3a', '#7a6a3a', '#5a3a6a', '#6a4a2a']
def shelf_books(c, x0, x1, y, seed):
    rr = random.Random(seed); x = x0
    while x < x1 - 20:
        w = rr.uniform(18, 34); h = rr.uniform(70, 100); col = rgb(rr.choice(BOOKC))
        c.set_source_rgb(*[v * 0.75 for v in col]); c.rectangle(x, y - h, w - 3, h); c.fill()
        c.set_source_rgba(1, 0.9, 0.6, 0.25); c.rectangle(x + 3, y - h + 12, w - 9, 4); c.fill()
        x += w
def draw_bg(c, t, f):
    c.set_source_rgb(*rgb('#1a1418')); c.rectangle(0, HEAD, W, H - HEAD); c.fill()
    # back wall bookcases (dim)
    c.set_source_rgb(*rgb('#24191a')); c.rectangle(60, 760, 960, GROUND - 760); c.fill()
    for k, yy in enumerate(range(880, GROUND - 40, 150)):
        c.set_source_rgb(*rgb('#2e2018')); c.rectangle(60, yy, 960, 14); c.fill()
        c.save(); c.push_group(); shelf_books(c, 70, 1010, yy, k * 7 + 3); c.pop_group_to_source(); c.paint_with_alpha(0.18); c.restore()
    # arched window with moon in the middle
    c.set_source_rgb(*rgb('#141c30')); c.move_to(420, 1120); c.line_to(420, 900); c.arc(540, 900, 120, math.pi, 2 * math.pi); c.line_to(660, 1120); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#e6dfc4')); c.arc(580, 880, 34, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#3a2a20')); c.set_line_width(8); c.move_to(540, 780); c.line_to(540, 1120); c.stroke(); c.move_to(420, 960); c.line_to(660, 960); c.stroke()
    c.rectangle(420, 780, 240, 340); c.set_line_width(6); c.stroke()
    # reading desk + green lamp (one quiet light)
    c.set_source_rgb(*rgb('#3a2818')); c.rectangle(380, GROUND - 150, 320, 26); c.fill(); c.rectangle(400, GROUND - 124, 20, 124); c.fill(); c.rectangle(660, GROUND - 124, 20, 124); c.fill()
    c.set_source_rgb(*rgb('#2a2a20')); c.rectangle(600, GROUND - 210, 8, 60); c.fill()
    c.set_source_rgb(*rgb('#2e6a4a')); c.move_to(570, GROUND - 200); c.line_to(640, GROUND - 200); c.line_to(625, GROUND - 230); c.line_to(585, GROUND - 230); c.close_path(); c.fill()
    c.set_source_rgba(1, 0.85, 0.5, 0.12); c.move_to(575, GROUND - 200); c.line_to(635, GROUND - 200); c.line_to(670, GROUND - 150); c.line_to(540, GROUND - 150); c.close_path(); c.fill()
    TER.fill(c, SNAP[min(f, len(SNAP) - 1)], '#5a2a2e', '#38181c', '#6e3a3c')   # thick red carpet
    c.set_source_rgba(0.85, 0.7, 0.3, 0.25); c.set_line_width(4)
    for yy in (GROUND + 50, GROUND + 70): c.move_to(0, yy); c.line_to(W, yy); c.stroke()
    # two tall bookcases = walls
    for (x0, x1) in ((-20, WALL_L), (WALL_R, W + 20)):
        c.set_source_rgb(*rgb('#3e2a1c')); c.rectangle(x0, 820, x1 - x0, GROUND + 40 - 820); c.fill()
        for k, yy in enumerate(range(960, GROUND, 130)):
            c.set_source_rgb(*rgb('#2a1c12')); c.rectangle(x0 + 10, yy - 110, x1 - x0 - 20, 110); c.fill()
            shelf_books(c, max(x0 + 14, 0), min(x1 - 10, W), yy, int(x0) + k)
            c.set_source_rgb(*rgb('#4e3624')); c.rectangle(x0, yy, x1 - x0, 14); c.fill()

def draw_fronds(c, t):   # the high top shelf running across the room, books wobble off its edge
    c.set_source_rgb(*rgb('#3e2a1c')); c.rectangle(-10, HANG - 20, W + 20, 24); c.fill()
    c.set_source_rgb(*rgb('#2a1c12')); c.rectangle(-10, HANG + 4, W + 20, 8); c.fill()
    for bx in range(60, W, 240):
        c.set_source_rgb(*rgb('#2a1c12')); c.move_to(bx, HANG + 4); c.line_to(bx + 30, HANG + 4); c.line_to(bx, HANG + 50); c.close_path(); c.fill()   # brackets
    shelf_books(c, 0, W, HANG - 20, 99)

def coconut(c, x, y, r, rot):   # a big heavy book tumbling down
    c.save(); c.translate(x, y); c.rotate(rot)
    col = rgb(BOOKC[int(r * 10) % len(BOOKC)])
    c.set_source_rgb(*col); rrect(c, -r * 1.15, -r * 0.8, r * 2.3, r * 1.6, 6); c.fill()
    c.set_source_rgb(*rgb('#e8dcc0')); c.rectangle(-r * 1.0, r * 0.5, r * 2.05, r * 0.22); c.fill()   # page edges
    c.set_source_rgb(*[v * 0.7 for v in col]); c.rectangle(-r * 1.15, -r * 0.8, r * 0.3, r * 1.6); c.fill()   # spine
    c.set_source_rgba(0.9, 0.75, 0.3, 0.8); c.rectangle(-r * 0.4, -r * 0.4, r * 0.9, r * 0.12); c.fill(); c.rectangle(-r * 0.3, -r * 0.15, r * 0.7, r * 0.08); c.fill()
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
                coconut(c, x, y, n['r'], n['rot'] + k * 8); continue
            if k > 1.6: continue
            c.push_group(); coconut(c, n['x'], TER.y(n['x']) - n['r'] * 0.8, n['r'], 0); c.pop_group_to_source(); c.paint_with_alpha(min(1, (1.6 - k) / 0.4))   # lands flat
            continue
        x, y, _ = nut_pos(n, t)
        wob = 0.25 * math.sin(t * 40) if t < n['t'] + WOB else 0
        fall = max(0, t - n['t'] - WOB)
        coconut(c, x + wob * 20, y, n['r'], wob + fall * (2.5 if int(n['rot'] * 10) % 2 else -2.5))
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
            PS.spawn(n['x'], n['sy'] + n['r'] * 0.6, 10, (0.6, 0.5, 0.45), 300, 0.5, grav=1400, r=6)
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
