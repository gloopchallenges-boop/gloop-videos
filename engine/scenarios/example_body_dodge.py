"""REFERENCE (new format + rigid-ball physics on soft Terrain) — DODGE – HEARTS: METEOR SHOWER.
Gloop is a passive rigid bouncy ball (Ball): parabolic arcs, bounces off the real ground slope,
walls reflect, every landing dents the soft sand, meteor impacts dig real craters that change his
later bounces. Meteors are seeded-random (some aimed at where he is). Hits come from positions."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the meteor shower'
SEED = int(os.environ.get('SEED', 3))
rng = random.Random(SEED)

class S: pass
S.HOOK2 = 'THE METEOR SHOWER?'; S.HOOK2_SIZE = 86; S.FAIL_WORD = 'SQUASHED!'; S.FAIL_SIZE = 140
S.T_START = HOOK_T; S.TL = 13.0; S.T_END = S.T_START + S.TL
GROUND = 1590; R = 58; GY = GROUND - R * 0.9; XMIN, XMAX = 165, 915; WALL_L, WALL_R = XMIN - R, XMAX + R
WARN, FALL = 1.05, 0.75; SPEED = 760; HIT_R = 0.0

# --- seeded meteors
MET = []; t = 0.9; iv = 1.4
while t < S.T_END - 0.2:
    big = rng.random() < 0.25
    x = rng.uniform(150, 930) if t > S.T_START + 0.5 else rng.choice((rng.uniform(150, 300), rng.uniform(780, 930)))
    MET.append({'t': t, 'x': x, 'r': 120 if big else 85, 'big': big})
    t += rng.uniform(0.55, 1.15) * iv; iv = max(0.8, iv * 0.96)

# --- simulate: Gloop is a passive bouncy ball (Ball) — he keeps bouncing the same way and only
# changes direction when he hits a rock wall or something hits him. Meteors fall at random spots
# (~30% aimed at where he is when they appear). A meteor touching him on the way down = hit
# (-1 heart, knocked away); a ground blast near him shoves him.
TER = Terrain(GROUND, seed=SEED, bumps=5, amp=16)
def meteor_pos(m, t):
    k = clamp((t - (m['t'] - FALL)) / FALL, 0, 1)
    sx, sy = m['x'] + 520, HEAD - 150; ex, ey = m['x'], TER.y(m['x']) - m['r'] * 0.3
    return lerp(sx, ex, k * k), lerp(sy, ey, k * k)
N0 = int(40 * FPS); GX, GYS, ROT, SQ, SHB = [], [], [], [], []
ball = Ball(rng.uniform(320, 760), TER, R=R, seed=SEED, xmin=XMIN, xmax=XMAX); TH = []
hearts = 3; HITS = []; inv_until = -1; HEARTS = []; T_FAIL = None
for m in MET: m['aim'] = rng.random() < 0.3; m['set'] = False; m['hit'] = False
for f in range(N0):
    t = f / FPS
    live = T_FAIL is None and S.T_START <= t < S.T_END
    for m in MET:
        if not m['set'] and t >= m['t'] - WARN:
            if m['aim'] and t > S.T_START - 0.3: m['x'] = clamp(ball.x + rng.uniform(-60, 60), 150, 930)
            m['set'] = True
        if m['t'] - FALL <= t < m['t'] and not m['hit']:
            mx, my = meteor_pos(m, t)
            d = math.hypot(ball.x - mx, ball.y - my)
            if d < m['r'] * 0.62 + R * 0.7 and live and t > inv_until:
                m['hit'] = True; nx, ny = (ball.x - mx) / (d or 1), (ball.y - my) / (d or 1)
                ball.push(nx * 650 + (-300 if mx > ball.x else 300), min(-500, ny * 900))
                hearts -= 1; HITS.append(t); inv_until = t + 0.9
                if hearts == 0: T_FAIL = t
        if abs(m['t'] - t) < 0.5 / FPS:
            TER.dig(m['x'], 55 if m['big'] else 38, m['r'] * 0.75)          # real crater in the sand
        if abs(m['t'] - t) < 0.5 / FPS and not m['hit']:
            dx = ball.x - m['x']
            if abs(dx) < m['r'] + 240 and ball.height() < 200:
                k = 1 - max(0, abs(dx) - m['r']) / 240; ball.push((1 if dx >= 0 else -1) * 380 * k, -420 * k)
    ball.step(t)
    GX.append(ball.x); GYS.append(ball.y); ROT.append(0); SQ.append(0); SHB.append((ball.x, ball.height())); TH.append(TER.snapshot())
    HEARTS.append(hearts)
S.OUTCOME = 'fail' if T_FAIL else 'win'
S.T_RES = T_FAIL if T_FAIL else S.T_END
S.GRAB = (540, GROUND - R)
END = S.END = Ending(S)
gi = min(int(END.T_GRAB * FPS), N0 - 1); S.GRAB = (GX[gi], GYS[gi])
S.events = [[S.T_START + 0.1, 'rumble', 1.2]]
for m in MET:
    if m['t'] - FALL < S.T_RES + 0.3: S.events.append([m['t'] - FALL, 'whoosh'])
    if m['t'] <= S.T_RES + 0.3: S.events.append([m['t'], 'crash'])
for h in HITS: S.events.append([h, 'heart']); S.events.append([h, 'thump', 0.8])
for (tl, xl, imp) in ball.landings:
    if tl < S.T_RES + 1.5: S.events.append([tl, 'hop'])
for tw in ball.walls:
    if tw < S.T_RES + 1.5: S.events.append([tw, 'thump', 0.4])
S.AMB = {'drone': 48, 'wind': 0.025}

def draw_bar(c, t, f):
    hp = HEARTS[f]; lost = [h for h in HITS if h <= t]
    pop = max(0, 1 - (t - lost[-1]) / 0.35) if lost else 0
    for i in range(3):
        x = W / 2 - 150 + i * 150; y = 235
        full = i < hp
        sc = 1.0 + (0.35 * pop if i == hp and pop > 0 else 0)
        c.save(); c.translate(x, y); c.scale(sc, sc)
        heart_path(c, 0, 0, 40)
        c.set_source_rgb(0, 0, 0); c.set_line_width(10); c.stroke_preserve()
        c.set_source_rgb(*(rgb('#ff3b5c') if full else rgb('#3a3446'))); c.fill()
        if full:
            c.set_source_rgba(1, 1, 1, 0.5); c.arc(-14, -10, 8, 0, 2 * math.pi); c.fill()
        c.restore()
S.draw_bar = draw_bar

# ---- flat, muted, minimal art (style: dark night, few flat shapes, one light source) ----
stars = [(rng.uniform(0, W), rng.uniform(HEAD, 1250), rng.uniform(1.2, 2.6)) for _ in range(60)]
hills = [(x, rng.uniform(80, 170)) for x in range(-100, W + 200, 260)]
SKY, HILL, HILL2, SAND, SAND_D, RIM, WALL, WALL_D = '#17141f', '#231d2b', '#2b2333', '#6b4a35', '#3a281d', '#7d5940', '#3b302c', '#2e2522'

def draw_bg(c, t, th):
    c.set_source_rgb(*rgb(SKY)); c.rectangle(0, HEAD, W, H - HEAD); c.fill()
    c.set_source_rgba(0.85, 0.82, 0.75, 0.5)
    for x, y, r in stars: c.arc(x, y, r, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#e6d6ae')); c.arc(800, 600, 58, 0, 2 * math.pi); c.fill()          # flat crescent moon
    c.set_source_rgb(*rgb(SKY)); c.arc(828, 584, 52, 0, 2 * math.pi); c.fill()
    for i, (x, hh) in enumerate(hills):
        c.set_source_rgb(*rgb(HILL if i % 2 else HILL2))
        c.move_to(x - 260, GROUND); c.curve_to(x - 120, GROUND - hh, x + 120, GROUND - hh, x + 260, GROUND); c.close_path(); c.fill()
    c.set_source_rgb(*rgb(SAND_D)); c.rectangle(0, GROUND - 30, W, H - GROUND + 30); c.fill()   # crater back walls
    c.move_to(0, H)
    for x in range(0, W + 1, 6): c.line_to(x, th[x])
    c.line_to(W, H); c.close_path(); c.set_source_rgb(*rgb(SAND)); c.fill()
    c.set_line_width(4); c.set_source_rgb(*rgb(RIM))
    for x in range(0, W + 1, 6): (c.move_to if x == 0 else c.line_to)(x, th[x])
    c.stroke()
    c.set_source_rgba(0, 0, 0, 0.12); c.set_line_width(3)
    for yy in range(GROUND + 70, H, 70): c.move_to(0, yy); c.line_to(W, yy); c.stroke()
    for (x0, x1) in ((0, WALL_L), (WALL_R, W)):
        c.set_source_rgb(*rgb(WALL)); c.rectangle(x0, 1040, x1 - x0, GROUND + 40 - 1040); c.fill()
        c.set_source_rgb(*rgb(WALL_D))
        for yy in range(1040, GROUND + 40, 64): c.rectangle(x0, yy, x1 - x0, 4); c.fill()

def draw_craters(c, t):
    for m in MET:
        if m['t'] <= t < m['t'] + 1.2 and m['t'] <= S.T_RES + 0.3:
            k = (t - m['t']) / 1.2
            c.set_source_rgba(0.35, 0.28, 0.24, 0.5 * (1 - k))
            for j in range(4): c.arc(m['x'] + (j - 1.5) * 34, GROUND - 40 - k * 90 - j * 8, 22 + k * 26, 0, 2 * math.pi); c.fill()

def draw_warnings(c, t):
    for m in MET:   # just the meteor's flat shadow growing on the sand
        if m['t'] - FALL <= t < m['t'] and m['t'] <= S.T_RES + 0.3:
            k = (t - (m['t'] - FALL)) / FALL; k = k * k
            c.set_source_rgba(0, 0, 0, 0.18 * k); c.save(); c.translate(m['x'], GROUND + 4); c.scale(m['r'] * (0.4 + 0.5 * k), 12); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()

def draw_meteors(c, t):
    for m in MET:
        if m['t'] - FALL <= t < m['t'] and m['t'] <= S.T_RES + 0.3:
            sx, sy = m['x'] + 520, HEAD - 150; ex, ey = m['x'], GROUND
            x, y = meteor_pos(m, t); ang = math.atan2(ey - sy, ex - sx); r = m['r'] * 0.62
            c.save(); c.translate(x, y); c.rotate(ang)
            c.set_source_rgba(0.85, 0.5, 0.25, 0.55); c.move_to(0, -r * 0.8); c.line_to(-r * 4.5, 0); c.line_to(0, r * 0.8); c.close_path(); c.fill()
            c.set_source_rgba(0.95, 0.75, 0.4, 0.6); c.move_to(0, -r * 0.4); c.line_to(-r * 2.5, 0); c.line_to(0, r * 0.4); c.close_path(); c.fill()
            c.restore()
            c.set_source_rgb(*rgb('#4a3d36')); c.arc(x, y, r, 0, 2 * math.pi); c.fill()
            c.set_source_rgb(*rgb('#3a2f2a'))
            for dx, dy, rr in ((-0.3, -0.2, 0.25), (0.32, 0.22, 0.2), (0.05, -0.5, 0.13)): c.arc(x + dx * r, y + dy * r, rr * r, 0, 2 * math.pi); c.fill()

PS = Particles(9)
def render(f, c):
    t = f / FPS; shake = (0, 0)
    for m in MET:
        if m['t'] <= t < m['t'] + 0.25 and m['t'] <= S.T_RES + 0.3:
            a = 5 if m['big'] else 3; shake = (rng.uniform(-a, a), rng.uniform(-a, a))
        if f == int(round(m['t'] * FPS)) and m['t'] <= S.T_RES + 0.3:
            PS.spawn(m['x'], TH[min(f, len(TH) - 1)][int(m['x'])] - 6, 22, (0.42, 0.29, 0.21), 600, 0.9, grav=2400, r=8)
    c.save(); c.translate(*shake)
    fi = min(f, len(GX) - 1)
    draw_bg(c, t, TH[fi]); draw_craters(c, t); draw_warnings(c, t)
    hits = [h for h in HITS if h <= t]
    flat = T_FAIL is not None and t >= T_FAIL
    if END.carried(t) or t >= END.T_GRAB:
        gx, gy = (END.carry_xy(t) if END.carried(t) else END.S.GRAB); gy += (0 if t < END.T_LIFT else 0); sq = 0.0; rot = ROT[min(fi, int(END.T_GRAB * FPS))]
    else:
        gx = GX[fi]; gy = GYS[fi]; sq = SQ[fi]; rot = ROT[fi]
        sx, sh = SHB[fi]; kk = 1 / (1 + sh / 220)
        c.set_source_rgba(0, 0, 0, 0.22 * kk); c.save(); c.translate(sx, TH[fi][int(clamp(sx, 0, W - 1))] + 2); c.scale(R * (0.5 + 0.4 * kk), 9); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    blink = False
    danger = any(m['t'] - WARN <= t < m['t'] and abs(m['x'] - GX[fi]) < 300 for m in MET)
    mood = 'happy' if (t >= S.T_END and S.OUTCOME == 'win') else ('scared' if danger or flat else 'worried')
    if not blink:
        draw_blob(c, t, gx, gy, mood, 0, R=R, dizzy=flat and t > T_FAIL + 0.4)
    draw_meteors(c, t)
    PS.draw(c)
    END.draw_claw(c, t)
    c.restore()
    END.header(c, t, min(f, len(HEARTS) - 1))

if __name__ == '__main__':
    if sys.argv[1] == 'sim':
        print(SEED, S.OUTCOME, round(S.T_RES, 2), 'hits', [round(h - S.T_START, 1) for h in HITS], 'mets', len(MET), 'dur', S.DUR); sys.exit()
    run(S, render)
