"""2026-11-10 v2 — DODGE – HEARTS: the HAILSTORM at a mountain campsite at night. Gloop is a passive rigid
ball (Ball) bouncing on the dirt between two big boulders. Seeded-random giant hailstones form under the storm
cloud, wobble for a moment, then drop with gravity (some are chosen near where he is at that moment, none follow
him). Every swept touch of a falling hailstone is a real momentum-transfer collision; during the countdown each
touch costs a heart. Hailstones shatter on the ground (ice chips + small dent).
0 hearts = fail (bonked & dizzy)."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the hailstorm'
SEED = int(os.environ.get('SEED', 24))
rng = random.Random(SEED)

class S: pass
S.HOOK2 = 'THE HAILSTORM?'; S.HOOK2_SIZE = 96; S.FAIL_WORD = 'BONK!'; S.FAIL_SIZE = 170
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

STARS = [(rng.uniform(0, W), rng.uniform(HEAD + 380, 1000), rng.uniform(1, 2)) for _ in range(20)]
PINES = [(x, rng.uniform(1080, 1180), rng.uniform(0.8, 1.3)) for x in range(-20, W + 60, 70)]
def pine(c, x, y, s, col):
    c.set_source_rgb(*rgb(col)); c.move_to(x, y - 260 * s)
    for k in range(4):
        w = 40 * s + k * 26 * s; yy = y - 260 * s + (k + 1) * 60 * s
        c.line_to(x + w, yy); c.line_to(x + w * 0.45, yy)
    c.line_to(x + 12 * s, y); c.line_to(x - 12 * s, y)
    for k in range(3, -1, -1):
        w = 40 * s + k * 26 * s; yy = y - 260 * s + (k + 1) * 60 * s
        c.line_to(x - w * 0.45, yy); c.line_to(x - w, yy)
    c.close_path(); c.fill()
def draw_bg(c, t, f):
    c.set_source_rgb(*rgb('#141822')); c.rectangle(0, HEAD, W, H - HEAD); c.fill()
    c.set_source_rgba(0.8, 0.85, 0.9, 0.3)
    for x, y, r in STARS: c.arc(x, y, r, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#1c2230')); c.move_to(0, 1150); c.line_to(220, 900); c.line_to(420, 1080); c.line_to(640, 860); c.line_to(880, 1060); c.line_to(W, 940); c.line_to(W, GROUND); c.line_to(0, GROUND); c.close_path(); c.fill()
    for (x, y, sc) in PINES: pine(c, x, y + 160, sc, '#161c24')
    # tent + lantern (one quiet light)
    c.set_source_rgb(*rgb('#5a6a4a')); c.move_to(600, GROUND); c.line_to(720, GROUND - 170); c.line_to(840, GROUND); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#2a3024')); c.move_to(700, GROUND); c.line_to(720, GROUND - 110); c.line_to(740, GROUND); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#3a3026')); c.set_line_width(5); c.move_to(400, GROUND); c.line_to(400, GROUND - 120); c.stroke()
    c.set_source_rgb(*rgb('#e8c46a')); rrect(c, 388, GROUND - 150, 24, 32, 6); c.fill()
    TER.fill(c, SNAP[min(f, len(SNAP) - 1)], '#3e3a32', '#26221c', '#504a3e')
    c.set_source_rgba(0, 0, 0, 0.15)
    for i in range(50): c.arc((i * 137) % W, GROUND + 50 + (i * 53) % (H - GROUND - 70), 5, 0, 2 * math.pi); c.fill()
    # two big boulders = walls
    for (x0, x1) in ((-90, WALL_L), (WALL_R, W + 90)):
        c.set_source_rgb(*rgb('#4a4a52')); rrect(c, x0, 1050, x1 - x0, GROUND + 40 - 1050, 70); c.fill()
        c.set_source_rgb(*rgb('#3c3c44')); rrect(c, x0 + 20, 1300, x1 - x0 - 40, GROUND - 1300, 40); c.fill()
        c.set_source_rgb(*rgb('#5a5a64')); c.save(); c.translate((max(x0, 0) + min(x1, W)) / 2, 1090); c.scale(34, 10); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()

CLOUD = [(x, rng.uniform(0, 30), rng.uniform(80, 130)) for x in range(-40, W + 80, 110)]
def draw_fronds(c, t):   # dark storm cloud across the top, hail forms under it
    fl = 0.0
    for k in range(6):
        tf = 1.3 + k * 2.9
        if 0 <= t - tf < 0.12: fl = 0.12
    for (x, dy, r) in CLOUD:
        c.set_source_rgb(*rgb('#2a2e3a')); c.arc(x + 8 * math.sin(t * 0.7 + x), HANG - 120 + dy, r, 0, 2 * math.pi); c.fill()
    for (x, dy, r) in CLOUD:
        c.set_source_rgb(0.21 + fl, 0.23 + fl, 0.29 + fl); c.arc(x + 20 + 8 * math.sin(t * 0.7 + x), HANG - 70 + dy * 0.5, r * 0.75, 0, 2 * math.pi); c.fill()

def coconut(c, x, y, r, rot):   # big lumpy hailstone
    c.save(); c.translate(x, y); c.rotate(rot * 0.3)
    c.set_source_rgb(*rgb('#c8dcea'))
    c.move_to(r, 0)
    for k in range(1, 9):
        a = k * math.pi / 4; rr = r * (0.92 if k % 2 else 1.0); c.line_to(rr * math.cos(a), rr * math.sin(a))
    c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#a8c0d4')); c.arc(r * 0.2, r * 0.25, r * 0.55, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#dceaf4')); c.arc(-r * 0.3, -r * 0.3, r * 0.3, 0, 2 * math.pi); c.fill()
    c.set_source_rgba(1, 1, 1, 0.7); c.arc(-r * 0.38, -r * 0.4, r * 0.12, 0, 2 * math.pi); c.fill()
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
            c.set_source_rgba(0.78, 0.86, 0.92, min(1, (1.6 - k) / 0.4))   # ice chips
            for q in range(5):
                sx = n['x'] + (q - 2) * n['r'] * 0.55; sy = TER.y(sx) - 6
                c.save(); c.translate(sx, sy); c.rotate(q * 1.3); c.move_to(-12, 6); c.line_to(12, 6); c.line_to(4, -10); c.close_path(); c.restore(); c.fill()
            c.set_source_rgba(0.6, 0.7, 0.8, 0.5 * min(1, (1.6 - k) / 0.4)); c.save(); c.translate(n['x'], TER.y(n['x']) - 2); c.scale(n['r'] * 0.9, 9); c.arc(0, 0, 1, math.pi, 2 * math.pi); c.restore(); c.fill()
            continue
        x, y, _ = nut_pos(n, t)
        wob = 0.25 * math.sin(t * 40) if t < n['t'] + WOB else 0
        if t < n['t'] + WOB:
            pass
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
            PS.spawn(n['x'], n['sy'] + n['r'] * 0.6, 14, (0.8, 0.88, 0.95), 380, 0.55, grav=1400, r=7)
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
