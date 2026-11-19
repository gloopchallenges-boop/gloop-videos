"""2026-11-19 v2 [STYLE] — DODGE – HEARTS: the GIANT APPLES in a sunny orchard (bright style-test scene; based on 2026-11-15 v1). Gloop is a passive
rigid ball (Ball) bouncing on packed dirt between two stone towers. Seeded-random iron cannonballs teeter on the
edge of the rampart walkway for a moment, then drop with gravity (some are chosen near where he is at that moment, none follow him).
Every swept touch of a falling book is a real momentum-transfer collision; during the countdown each touch costs
a heart. Cannonballs thud into the dirt (small dent). 0 hearts = fail (bonked & dizzy)."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the giant apples'
SEED = int(os.environ.get('SEED', 12))
rng = random.Random(SEED)

class S: pass
S.HOOK2 = 'THE GIANT APPLES?'; S.HOOK2_SIZE = 90; S.FAIL_WORD = 'BONK!'; S.FAIL_SIZE = 170
S.CARD = ['Every apple hit costs a *HEART|#ff3b5c*', 'Can Gloop keep *ONE*?']; S.STREAK = int(os.environ.get('STREAK', 1)); S.CTA = True
S.T_START = HOOK_T; S.TL = 13.0; S.T_END = S.T_START + S.TL
GROUND = 1600; R = 58; XMIN, XMAX = 190, 890; WALL_L, WALL_R = XMIN - R, XMAX + R
HANG = 620; WOB = 0.55; G = 2600.0; CR = 36
AIM = float(os.environ.get('AIM', 0.4)); IV = float(os.environ.get('IV', 0.95))

NUTS = []; t = -0.6
while t < S.T_END:
    NUTS.append({'t': t, 'r': rng.uniform(40, 50), 'aim': rng.random() < AIM, 'x': None, 'hit': False, 'land': None, 'rot': rng.uniform(0, 6)})
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

def draw_bg(c, t, f):
    # sunny orchard: flat sky, soft clouds, rolling hills, a row of small trees far away
    c.set_source_rgb(*rgb('#8ed3f2')); c.rectangle(0, HEAD, W, H - HEAD); c.fill()
    for (cx, cy, s) in ((200, 470, 1.0), (760, 540, 0.8)):
        x = cx + 12 * math.sin(t * 0.3 + cx)
        c.set_source_rgb(1, 1, 1)
        for (dx, dy, r) in ((0, 0, 48), (50, -18, 56), (105, 0, 44), (50, 14, 46)): c.arc(x + dx * s, cy + dy * s, r * s, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#9fdc8a')); c.move_to(0, 1250); c.curve_to(250, 1150, 520, 1230, 760, 1170); c.curve_to(900, 1140, 1000, 1180, W, 1160); c.line_to(W, GROUND); c.line_to(0, GROUND); c.fill()
    c.set_source_rgb(*rgb('#7cc874')); c.move_to(0, 1360); c.curve_to(300, 1300, 600, 1380, W, 1310); c.line_to(W, H); c.line_to(0, H); c.fill()
    for xx in (330, 470, 620, 760):   # little distant trees
        c.set_source_rgb(*rgb('#9a6a48')); c.rectangle(xx - 6, 1300, 12, 50); c.fill()
        c.set_source_rgb(*rgb('#5fb060')); c.arc(xx, 1290, 34, 0, 2 * math.pi); c.fill()
        c.set_source_rgb(*rgb('#e85a6a')); c.arc(xx - 12, 1284, 5, 0, 2 * math.pi); c.fill(); c.arc(xx + 14, 1296, 5, 0, 2 * math.pi); c.fill()
    # white picket fence in the middle
    c.set_source_rgb(*rgb('#fafaf2'))
    for xx in range(WALL_L + 20, WALL_R - 10, 46): c.move_to(xx, GROUND); c.line_to(xx, 1440); c.line_to(xx + 13, 1425); c.line_to(xx + 26, 1440); c.line_to(xx + 26, GROUND); c.fill()
    c.rectangle(WALL_L, 1470, WALL_R - WALL_L, 14); c.fill(); c.rectangle(WALL_L, 1540, WALL_R - WALL_L, 14); c.fill()
    # a wicker basket of apples
    c.set_source_rgb(*rgb('#e85a6a'))
    for (px, py) in ((700, 0), (735, 0), (718, 1)): c.arc(px, GROUND - 52 - py * 26, 18, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#c89a5a')); c.move_to(670, GROUND - 52); c.line_to(766, GROUND - 52); c.line_to(756, GROUND); c.line_to(680, GROUND); c.fill()
    c.set_source_rgb(*rgb('#a87a40')); c.set_line_width(3)
    for yy in range(int(GROUND - 44), GROUND, 12): c.move_to(674, yy); c.line_to(762, yy); c.stroke()
    TER.fill(c, SNAP[min(f, len(SNAP) - 1)], '#62b85a', '#8a5a3a', '#7ad070')   # grass over brown soil
    # two big tree trunks = walls
    for (x0, x1) in ((-20, WALL_L), (WALL_R, W + 20)):
        c.set_source_rgb(*rgb('#8a5a3a')); c.rectangle(x0, 640, x1 - x0, H - 640); c.fill()
        c.set_source_rgb(*rgb('#74482c')); c.set_line_width(5)
        for k in range(5):
            xx = x0 + 18 + k * (x1 - x0 - 30) / 4
            c.move_to(xx, 700 + k * 37); c.curve_to(xx + 8, 900, xx - 8, 1150, xx + 4, H); c.stroke()
        hx = (x0 + x1) / 2
        c.set_source_rgb(*rgb('#5a3820')); c.save(); c.translate(hx, 1180); c.scale(14, 22); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()

def draw_fronds(c, t):   # the leafy canopy across the top with apples hanging in it
    sw = 4 * math.sin(t * 1.3)
    c.set_source_rgb(*rgb('#4fa04e')); c.rectangle(-10, HEAD, W + 20, HANG - 30 - HEAD); c.fill()
    for k in range(13):
        x = -20 + k * 92; y = HANG - 20 + (k % 3) * 12
        c.set_source_rgb(*rgb('#5cb85a' if k % 2 else '#4fa04e')); c.arc(x + sw, y, 62, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#6cc868'))
    for k in range(9): c.arc(40 + k * 125 + sw, HANG - 70 + (k % 2) * 20, 30, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#7a4e30')); c.set_line_width(22); c.move_to(-10, HANG - 110); c.curve_to(300, HANG - 70, 700, HANG - 140, W + 10, HANG - 90); c.stroke()
    for k in range(7):   # resting apples in the leaves
        x = 90 + k * 150 + sw; y = HANG + 18 + (k * 37) % 26
        coconut(c, x, y, 24, 0)

def coconut(c, x, y, r, rot):   # a big shiny red apple (stem + leaf rotate with it)
    c.save(); c.translate(x, y); c.rotate(rot * 0.15)
    c.set_source_rgb(*rgb('#d92f3a'))
    c.move_to(0, -r * 0.72); c.curve_to(r * 0.6, -r * 1.12, r * 1.15, -r * 0.55, r * 1.0, r * 0.15)
    c.curve_to(r * 0.9, r * 0.8, r * 0.45, r * 1.02, 0, r * 0.88); c.curve_to(-r * 0.45, r * 1.02, -r * 0.9, r * 0.8, -r * 1.0, r * 0.15)
    c.curve_to(-r * 1.15, -r * 0.55, -r * 0.6, -r * 1.12, 0, -r * 0.72); c.close_path(); c.fill()
    c.set_source_rgba(1, 1, 1, 0.45); c.save(); c.translate(-r * 0.45, -r * 0.3); c.rotate(-0.5); c.scale(r * 0.16, r * 0.3); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    c.set_source_rgb(*rgb('#5a3a20')); c.set_line_width(max(3, r * 0.1)); c.move_to(0, -r * 0.7); c.line_to(r * 0.08, -r * 1.05); c.stroke()
    c.set_source_rgb(*rgb('#4cae48')); c.save(); c.translate(r * 0.3, -r * 0.98); c.rotate(-0.4); c.scale(r * 0.3, r * 0.13); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
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
            c.push_group(); coconut(c, n['x'], n['sy'] - n['r'] * 0.0, n['r'], n['rot']); c.pop_group_to_source(); c.paint_with_alpha(min(1, (1.6 - k) / 0.4))   # lands flat
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
