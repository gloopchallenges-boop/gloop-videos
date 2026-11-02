"""2026-11-02 v7 — DODGE – HEARTS: GIANT BOWLING BALLS in a bowling alley at night.
Gloop is a passive rigid ball (Ball) bouncing on the wooden lane between two walls. Seeded-random
bowling balls roll out of the ball-return tunnel in the right wall and across the lane into the
left tunnel (some sent when he is low, none steered). Every swept touch is a real momentum-transfer
collision; during the countdown each touch costs a heart. 0 hearts = fail."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the giant bowling balls'
SEED = int(os.environ.get('SEED', 10))
rng = random.Random(SEED)

class S: pass
S.HOOK2 = 'THE BOWLING BALLS?'; S.HOOK2_SIZE = 84; S.FAIL_WORD = 'STRIKE!'; S.FAIL_SIZE = 150
S.T_START = HOOK_T; S.TL = 13.0; S.T_END = S.T_START + S.TL
GROUND = 1600; R = 58; XMIN, XMAX = 150, 930; WALL_L, WALL_R = XMIN - R, XMAX + R

# --- seeded bowling balls: start time, radius, speed, small hop
BB = []; t = -0.55; iv = 2.3
while t < S.T_END - 0.4:
    r = rng.choice((55, 62, 62, 72)); sp = rng.uniform(650, 1050)
    BB.append({'t0': t, 'r': r, 'v': sp, 'col': rng.choice(('#2d3a66', '#5a2337', '#24503f', '#4a3a6b')), 'hit': False})
    t += rng.uniform(0.7, 1.3) * iv; iv = max(1.6, iv * 0.97)
X0, X1 = W + 120, -120
def bb_pos(b, t):
    x = X0 - b['v'] * (t - b['t0']); return x, GROUND - b['r']
def bb_on(b, t): return t >= b['t0'] and bb_pos(b, t)[0] > X1

TER = Terrain(GROUND, seed=SEED, bumps=0, amp=0, soft=False)
N0 = int(40 * FPS); GX, GYS, HEARTS, TH = [], [], [], []
ball = Ball(rng.uniform(380, 700), TER, R=R, seed=SEED, xmin=XMIN, xmax=XMAX, hop=rng.uniform(330, 390))
hearts = 3; HITS = []; T_FAIL = None; CONTACTS = []; SUB = 8
for f in range(N0):
    t = f / FPS
    live = T_FAIL is None and S.T_START <= t < S.T_END
    px, py = ball.x, ball.y
    ball.step(t)
    for b in BB:
        if b['hit'] or not bb_on(b, t) or (T_FAIL is not None and b['t0'] > T_FAIL): continue
        for k in range(1, SUB + 1):
            ts = t - 1 / FPS + k / (SUB * FPS)
            if ts < b['t0']: continue
            mx, my = bb_pos(b, ts); bx, by = lerp(px, ball.x, k / SUB), lerp(py, ball.y, k / SUB)
            d = math.hypot(bx - mx, by - my)
            if d < b['r'] + R * 0.95:
                b['hit'] = True; nx, ny = (bx - mx) / (d or 1), (by - my) / (d or 1)
                rel = (-b['v'] - ball.vx) * nx
                if rel > 0: j = min(1.3 * rel, 900); ball.push(j * nx, min(0, j * ny)); ball.vy = min(ball.vy, j * ny)
                CONTACTS.append((ts, bx - nx * R, by - ny * R))
                if live:
                    hearts -= 1; HITS.append(ts)
                    if hearts == 0: T_FAIL = ts
                break
    if T_FAIL is not None and t > T_FAIL:
        ball.vmin = 0; ball.e = 0.45; ball.vx *= 0.97     # knocked out: bounces die out, he settles dizzy on the lane
    GX.append(ball.x); GYS.append(ball.y); HEARTS.append(hearts)
S.OUTCOME = 'fail' if T_FAIL else 'win'
S.T_RES = T_FAIL if T_FAIL else S.T_END
S.GRAB = (540, GROUND - R)
END = S.END = Ending(S)
gi = min(int(END.T_GRAB * FPS), N0 - 1); S.GRAB = (GX[gi], GYS[gi])
S.events = [[0.05, 'rumble', 1.0]]
for b in BB:
    if b['t0'] < S.T_RES + 0.5: S.events.append([max(0, b['t0']), 'rumble', 1.3])
for h in HITS: S.events.append([h, 'heart']); S.events.append([h, 'crash'])
for (tc, _, _) in CONTACTS:
    if tc not in HITS: S.events.append([tc, 'thump', 0.8])
for (tl, xl, imp) in ball.landings:
    if tl < S.T_RES + 1.5: S.events.append([tl, 'hop'])
for tw in ball.walls:
    if tw < S.T_RES + 1.5: S.events.append([tw, 'thump', 0.4])
S.AMB = {'drone': 52}

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

BACK, BACK2, WOOD, WOOD_D, WALL, WALL_D = '#1b1626', '#231c31', '#8a6542', '#5e4430', '#3a2f45', '#2b2335'
def draw_bg(c, t):
    c.set_source_rgb(*rgb(BACK)); c.rectangle(0, HEAD, W, H - HEAD); c.fill()
    # far back: dim pin deck with a row of pins, one hanging lamp
    c.set_source_rgb(*rgb(BACK2)); c.rectangle(0, 1080, W, 340); c.fill()
    for i in range(10):
        x = 230 + i * 70; y = 1360
        c.set_source_rgb(*rgb('#cfc8bd')); c.save(); c.translate(x, y); c.scale(1, 2.2); c.arc(0, 0, 16, 0, 2 * math.pi); c.restore(); c.fill()
        c.arc(x, y - 46, 10, 0, 2 * math.pi); c.fill()
        c.set_source_rgb(*rgb('#a33a3a')); c.rectangle(x - 11, y - 32, 22, 5); c.fill()
    c.set_source_rgb(*rgb('#120f1a')); c.rectangle(0, 1080, W, 60); c.fill()
    font(c, 54); c.set_source_rgb(*rgb('#6a4d7a')); e = c.text_extents('LANE 7'); c.move_to(W / 2 - e.width / 2, 1125); c.show_text('LANE 7')
    c.set_source_rgb(*rgb('#5a5468')); c.set_line_width(4); c.move_to(W / 2, HEAD); c.line_to(W / 2, 560); c.stroke()
    c.set_source_rgb(*rgb('#3a3446')); c.move_to(W / 2 - 70, 620); c.line_to(W / 2 - 30, 560); c.line_to(W / 2 + 30, 560); c.line_to(W / 2 + 70, 620); c.close_path(); c.fill()
    c.set_source_rgba(1, 0.9, 0.7, 0.05); c.move_to(W / 2 - 70, 620); c.line_to(W / 2 - 380, GROUND); c.line_to(W / 2 + 380, GROUND); c.line_to(W / 2 + 70, 620); c.close_path(); c.fill()
    # lane (floor): flat planks with arrows
    c.set_source_rgb(*rgb(WOOD)); c.rectangle(0, GROUND, W, H - GROUND); c.fill()
    c.set_source_rgba(0, 0, 0, 0.18); c.set_line_width(3)
    for x in range(0, W, 54): c.move_to(x, GROUND); c.line_to(x, H); c.stroke()
    c.set_source_rgb(*rgb(WOOD_D)); c.rectangle(0, GROUND, W, 10); c.fill()
    c.set_source_rgb(*rgb('#6b3f2a'))
    for i in range(5):
        x = 260 + i * 140; y = GROUND + 120 + abs(i - 2) * 40
        c.move_to(x, y - 30); c.line_to(x + 20, y + 10); c.line_to(x - 20, y + 10); c.close_path(); c.fill()
    # side walls with ball-return tunnels at floor level
    for (x0, x1) in ((0, WALL_L), (WALL_R, W)):
        c.set_source_rgb(*rgb(WALL)); c.rectangle(x0, 1000, x1 - x0, GROUND - 1000); c.fill()
        c.set_source_rgb(*rgb(WALL_D))
        for yy in range(1000, GROUND, 60): c.rectangle(x0, yy, x1 - x0, 4); c.fill()
        c.set_source_rgb(*rgb('#0c0a11')); c.rectangle(x0, GROUND - 190, x1 - x0, 190); c.fill()

def draw_balls(c, t):
    for b in BB:
        if not bb_on(b, t) or b['t0'] > S.T_RES: continue
        x, y = bb_pos(b, t); r = b['r']
        c.set_source_rgba(0, 0, 0, 0.25); c.save(); c.translate(x, GROUND + 4); c.scale(r * 0.9, 9); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
        c.set_source_rgb(*rgb(b['col'])); c.arc(x, y, r, 0, 2 * math.pi); c.fill()
        c.set_source_rgba(1, 1, 1, 0.08); c.arc(x - r * 0.3, y - r * 0.35, r * 0.35, 0, 2 * math.pi); c.fill()
        ang = (X0 - x) / r * -1    # rolls left -> counter-clockwise
        c.set_source_rgb(*rgb('#0e0c12'))
        for k, (dx, dy, rr) in enumerate(((0.0, -0.45, 0.13), (-0.28, -0.22, 0.11), (0.28, -0.22, 0.11))):
            ca, sa = math.cos(ang), math.sin(ang)
            c.arc(x + (dx * ca - dy * sa) * r, y + (dx * sa + dy * ca) * r, rr * r, 0, 2 * math.pi); c.fill()
    # the tunnel lips are drawn over the balls so they come out of / go into the walls
    for (x0, x1) in ((0, WALL_L), (WALL_R, W)):
        c.set_source_rgb(*rgb(WALL)); c.rectangle(x0, GROUND - 210, x1 - x0, 24); c.fill()

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
        h = max(0, GROUND - R - gy); kk = 1 / (1 + h / 220)
        c.set_source_rgba(0, 0, 0, 0.25 * kk); c.save(); c.translate(gx, GROUND + 3); c.scale(R * (0.5 + 0.4 * kk), 9); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    danger = any(bb_on(b, t) and 0 < bb_pos(b, t)[0] - GX[fi] < 450 for b in BB)
    mood = 'happy' if (t >= S.T_END and S.OUTCOME == 'win') else ('scared' if danger or flat else 'worried')
    draw_blob(c, t, gx, gy, mood, 0, R=R, dizzy=flat and t > T_FAIL + 0.4)
    draw_balls(c, t)
    for (tc, cx, cy) in CONTACTS:
        if abs(t - tc) < 0.5 / FPS: PS.spawn(cx, cy, 14, (0.6, 0.5, 0.45), 380, 0.5, grav=600, r=7)
    PS.draw(c)
    END.draw_claw(c, t)
    c.restore()
    END.header(c, t, min(f, len(HEARTS) - 1))

if __name__ == '__main__':
    if sys.argv[1] == 'sim':
        print(SEED, S.OUTCOME, round(S.T_RES - S.T_START, 2), 'hits', [round(h - S.T_START, 1) for h in HITS], 'balls', len(BB), 'contacts', len(CONTACTS), 'dur', S.DUR); sys.exit()
    run(S, render)
