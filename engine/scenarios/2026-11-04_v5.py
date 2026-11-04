"""2026-11-04 v5 — DODGE – HEARTS: the FALLING ICICLES in an ice cave. Gloop is a passive rigid ball (Ball)
bouncing on the icy cave floor between two ice walls. Seeded-random icicles hang from the ceiling, wobble
for a moment, then drop with gravity (some are chosen near where he is at that moment, none follow him).
Every swept touch of a falling icicle is a real momentum-transfer collision; during the countdown each
touch costs a heart. Icicles shatter on the floor. 0 hearts = fail (frozen & dizzy)."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the falling icicles'
SEED = int(os.environ.get('SEED', 9))
rng = random.Random(SEED)

class S: pass
S.HOOK2 = 'THE FALLING ICICLES?'; S.HOOK2_SIZE = 84; S.FAIL_WORD = 'OUCH!'; S.FAIL_SIZE = 160
S.T_START = HOOK_T; S.TL = 13.0; S.T_END = S.T_START + S.TL
GROUND = 1600; R = 58; XMIN, XMAX = 170, 910; WALL_L, WALL_R = XMIN - R, XMAX + R
CEIL = 560; WOB = 0.55; G = 2600.0; AIM = float(os.environ.get('AIM', 0.45)); IV = float(os.environ.get('IV', 0.95))

ICE = []; t = -0.6
while t < S.T_END:
    ICE.append({'t': t, 'len': rng.uniform(170, 250), 'w': rng.uniform(52, 72), 'aim': rng.random() < AIM, 'x': None, 'hit': False, 'land': None})
    t += rng.uniform(0.6, 1.4) * IV
def ice_tip(ic, t):   # tip position of a released icicle
    k = max(0, t - ic['t'] - WOB); return ic['x'], CEIL + ic['len'] + 0.5 * G * k * k, G * k

TER = Terrain(GROUND, seed=SEED, bumps=3, amp=8, soft=False)
N0 = int(40 * FPS); GX, GYS, HEARTS = [], [], []
ball = Ball(rng.uniform(350, 730), TER, R=R, seed=SEED, xmin=XMIN, xmax=XMAX, hop=rng.uniform(300, 380))
hearts = 3; HITS = []; T_FAIL = None; CONTACTS = []; SUB = 8
for f in range(N0):
    t = f / FPS
    live = T_FAIL is None and S.T_START <= t < S.T_END
    for ic in ICE:
        if ic['x'] is None and t >= ic['t']:
            ic['x'] = clamp(ball.x + rng.uniform(-70, 70), XMIN - 20, XMAX + 20) if ic['aim'] else rng.uniform(XMIN - 20, XMAX + 20)
            if ic['t'] < S.T_START - WOB - 0.5: ic['x'] = clamp(ball.x + rng.choice((-1, 1)) * rng.uniform(300, 450), XMIN, XMAX) if abs(ball.x - 540) < 200 else (XMIN + 60 if ball.x > 540 else XMAX - 60)
    px, py = ball.x, ball.y
    ball.step(t)
    for ic in ICE:
        if ic['x'] is None or ic['land'] is not None or t < ic['t'] + WOB: continue
        if T_FAIL is not None and ic['t'] > T_FAIL: continue
        for k in range(1, SUB + 1):
            ts = t - 1 / FPS + k / (SUB * FPS)
            if ts < ic['t'] + WOB: continue
            tx, ty, vy = ice_tip(ic, ts)
            if ty >= TER.y(tx): ic['land'] = ts; ic['sy'] = TER.y(tx); break
            bx, by = lerp(px, ball.x, k / SUB), lerp(py, ball.y, k / SUB)
            # icicle body = segment from (tx, ty - len) to tip; distance from ball centre to that segment
            cy = clamp(by, ty - ic['len'], ty); wid = ic['w'] / 2 * (ty - cy) / ic['len']
            d = math.hypot(bx - tx, by - cy) - wid
            if d < R * 0.95:
                ic['hit'] = True; ic['land'] = ts; ic['sy'] = cy; nx, ny = (bx - tx) / (math.hypot(bx - tx, by - cy) or 1), (by - cy) / (math.hypot(bx - tx, by - cy) or 1)
                rel = (vy - ball.vy) * ny
                j = min(0.9 * max(rel, 200), 800); ball.push(nx * max(260, j * 0.6), 0); ball.vy = max(ball.vy, j * max(0.3, ny))
                CONTACTS.append((ts, bx - nx * R, by - ny * R))
                if live:
                    hearts -= 1; HITS.append(ts)
                    if hearts == 0: T_FAIL = ts
                break
    if T_FAIL is not None and t > T_FAIL: ball.vmin = 0; ball.e = 0.4; ball.vx *= 0.96
    GX.append(ball.x); GYS.append(ball.y); HEARTS.append(hearts)
S.OUTCOME = 'fail' if T_FAIL else 'win'
S.T_RES = T_FAIL if T_FAIL else S.T_END
S.GRAB = (540, GROUND - R)
END = S.END = Ending(S)
gi = min(int(END.T_GRAB * FPS), N0 - 1); S.GRAB = (GX[gi], GYS[gi])
VIS_END = S.T_RES if T_FAIL else S.T_END   # no new icicles after the result
S.events = [[0.05, 'crackle']]
for ic in ICE:
    if ic['t'] < VIS_END:
        S.events.append([max(0, ic['t']), 'creak'])
        if ic['land'] is not None and not ic['hit']: S.events.append([ic['land'], 'clink']); S.events.append([ic['land'], 'crackle'])
for h in HITS: S.events.append([h, 'heart']); S.events.append([h, 'clink']); S.events.append([h, 'thump', 0.9])
for (tc, _, _) in CONTACTS:
    if tc not in HITS: S.events.append([tc, 'clink'])
for (tl, xl, imp) in ball.landings:
    if tl < S.T_RES + 1.5: S.events.append([tl, 'hop'])
for tw in ball.walls:
    if tw < S.T_RES + 1.5: S.events.append([tw, 'thump', 0.4])
S.AMB = {'drone': 56, 'wind': 0.025}

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

def draw_bg(c, t):
    c.set_source_rgb(*rgb('#141c2c')); c.rectangle(0, HEAD, W, H - HEAD); c.fill()
    # back cave wall: big flat ice facets
    c.set_source_rgb(*rgb('#1a2740'))
    for i, (x, y, r) in enumerate(((120, 900, 260), (480, 820, 300), (860, 950, 280), (300, 1250, 240), (760, 1300, 260))):
        c.move_to(x - r, y + r * 0.5); c.line_to(x - r * 0.3, y - r * 0.6); c.line_to(x + r * 0.5, y - r * 0.4); c.line_to(x + r, y + r * 0.4); c.close_path(); c.fill()
    c.set_source_rgba(0.6, 0.85, 1, 0.05); c.move_to(380, CEIL); c.line_to(700, CEIL); c.line_to(900, GROUND); c.line_to(180, GROUND); c.close_path(); c.fill()
    # ceiling with small fixed icicles
    c.set_source_rgb(*rgb('#2a3d5c')); c.move_to(0, HEAD); c.line_to(W, HEAD); c.line_to(W, CEIL + 10)
    for x in range(W, -1, -60): c.line_to(x, CEIL + 10 * math.sin(x * 0.05))
    c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#3d5a80'))
    for x in range(20, W, 70): c.move_to(x - 12, CEIL); c.line_to(x + 12, CEIL); c.line_to(x, CEIL + 35 + (x * 13) % 30); c.close_path(); c.fill()
    # floor
    TER.fill(c, TER.h, '#9cc3e0', '#4a6a8c', '#d8eeff')
    c.set_source_rgba(1, 1, 1, 0.25); c.set_line_width(3)
    for x in range(80, W, 190): c.move_to(x, GROUND + 40); c.line_to(x + 60, GROUND + 70); c.line_to(x + 40, GROUND + 120); c.stroke()
    # ice walls
    for (x0, x1) in ((0, WALL_L), (WALL_R, W)):
        c.set_source_rgb(*rgb('#6f98c0')); c.rectangle(x0, CEIL, x1 - x0, GROUND - CEIL + 20); c.fill()
        c.set_source_rgba(1, 1, 1, 0.18)
        for yy in range(CEIL + 60, GROUND, 170): c.move_to(x0 + 10, yy); c.line_to(x1 - 10, yy + 50); c.line_to(x1 - 10, yy + 70); c.line_to(x0 + 10, yy + 20); c.close_path(); c.fill()

def icicle_path(c, x, tipy, ln, w):
    c.move_to(x - w / 2, tipy - ln); c.line_to(x + w / 2, tipy - ln); c.line_to(x + w * 0.12, tipy - ln * 0.3); c.line_to(x, tipy); c.line_to(x - w * 0.18, tipy - ln * 0.45); c.close_path()

def draw_ice(c, t):
    for ic in ICE:
        if ic['x'] is None or ic['t'] > t or ic['t'] >= VIS_END: continue
        if ic['land'] is not None and t >= ic['land']:
            k = (t - ic['land']) / 0.6
            if k < 1:   # shards scattering on the floor
                gy = ic['sy'] + 10
                for j in range(6):
                    a = -math.pi * (0.1 + 0.8 * j / 5); dx = math.cos(a) * 160 * k; dy = math.sin(a) * 120 * k + 300 * k * k
                    c.set_source_rgba(0.85, 0.95, 1, 1 - k); c.save(); c.translate(ic['x'] + dx, gy - 10 + dy); c.rotate(j + k * 6)
                    c.move_to(-12, 0); c.line_to(0, -16); c.line_to(12, 0); c.close_path(); c.fill(); c.restore()
            continue
        tx, ty, _ = ice_tip(ic, t)
        wob = 4 * math.sin(t * 60) if t < ic['t'] + WOB else 0
        c.set_source_rgb(*rgb('#cdeaff')); icicle_path(c, tx + wob, ty, ic['len'], ic['w']); c.fill()
        c.set_source_rgba(1, 1, 1, 0.6); c.move_to(tx + wob - ic['w'] * 0.3, ty - ic['len']); c.line_to(tx + wob - ic['w'] * 0.12, ty - ic['len']); c.line_to(tx + wob - 2, ty - ic['len'] * 0.25); c.close_path(); c.fill()
        if t >= ic['t'] + WOB:   # small shadow on the floor
            gy = TER.y(tx); k = clamp(1 - (gy - ty) / 1000, 0.2, 1)
            c.set_source_rgba(0, 0, 0, 0.25 * k); c.save(); c.translate(tx, gy + 4); c.scale(ic['w'] * 0.7 * k + 5, 6); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()

PS = Particles(9)
def render(f, c):
    t = f / FPS; shake = (0, 0)
    if any(abs(t - h) < 0.2 for h in HITS): shake = (rng.uniform(-4, 4), rng.uniform(-4, 4))
    c.save(); c.translate(*shake)
    fi = min(f, len(GX) - 1)
    draw_bg(c, t)
    flat = T_FAIL is not None and t >= T_FAIL
    if END.carried(t) or t >= END.T_GRAB:
        gx, gy = (END.carry_xy(t) if END.carried(t) else S.GRAB)
    else:
        gx, gy = GX[fi], GYS[fi]
        h = max(0, TER.y(gx) - R - gy); kk = 1 / (1 + h / 220)
        c.set_source_rgba(0, 0, 0, 0.25 * kk); c.save(); c.translate(gx, TER.y(gx) + 3); c.scale(R * (0.5 + 0.4 * kk), 9); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    danger = any(ic['x'] is not None and ic['t'] <= t < ic['t'] + WOB + 0.6 and abs(ic['x'] - GX[fi]) < 160 for ic in ICE)
    mood = 'happy' if (t >= S.T_END and S.OUTCOME == 'win') else ('scared' if danger or flat else 'worried')
    skin = ('#e0f2ff', '#8cc4ee', '#3f6f9a') if flat and t > T_FAIL + 0.2 else ('#ffd36b', '#ff8a1f', '#c45a00')
    draw_blob(c, t, gx, gy, mood, 0, R=R, skin=skin, dizzy=flat and t > T_FAIL + 0.4)
    draw_ice(c, t)
    for (tc, cx, cy) in CONTACTS:
        if abs(t - tc) < 0.5 / FPS: PS.spawn(cx, cy, 14, (0.85, 0.95, 1), 380, 0.5, grav=900, r=7)
    PS.draw(c)
    END.draw_claw(c, t)
    c.restore()
    END.header(c, t, min(f, len(HEARTS) - 1))

if __name__ == '__main__':
    if sys.argv[1] == 'sim':
        print(SEED, S.OUTCOME, round(S.T_RES - S.T_START, 2), 'hits', [round(h - S.T_START, 1) for h in HITS], 'icicles', len([i for i in ICE if i['t'] < VIS_END]), 'contacts', len(CONTACTS), 'dur', S.DUR); sys.exit()
    run(S, render)
