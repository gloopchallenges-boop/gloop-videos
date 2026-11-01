"""REFERENCE (new format + Body physics) — DODGE – HEARTS: METEOR SHOWER on an alien desert. Meteors are seeded-random
(time, target, size); Gloop reacts to each warning shadow with a random reaction delay and runs
with a capped speed — whether a meteor hits is simulated from positions."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the meteor shower'
SEED = int(os.environ.get('SEED', 3))
rng = random.Random(SEED)

class S: pass
S.HOOK2 = 'THE METEOR SHOWER?'; S.HOOK2_SIZE = 86; S.FAIL_WORD = 'SQUASHED!'; S.FAIL_SIZE = 140
S.T_START = HOOK_T; S.TL = 13.0; S.T_END = S.T_START + S.TL
GROUND = 1590; R = 80; GY = GROUND - R * 0.9; XMIN, XMAX = 165, 915; WALL_L, WALL_R = XMIN - R, XMAX + R
WARN, FALL = 1.05, 0.75; SPEED = 760; HIT_R = 0.0

# --- seeded meteors
MET = []; t = 0.9; iv = 1.9
while t < S.T_END - 0.2:
    big = rng.random() < 0.25
    x = rng.uniform(150, 930) if t > S.T_START + 0.5 else rng.choice((rng.uniform(150, 300), rng.uniform(780, 930)))
    MET.append({'t': t, 'x': x, 'r': 120 if big else 85, 'big': big})
    t += rng.uniform(0.55, 1.15) * iv; iv = max(1.05, iv * 0.96)

# --- simulate: Gloop is a passive bouncy ball (Ball) — he keeps bouncing the same way and only
# changes direction when he hits a rock wall or something hits him. Meteors fall at random spots
# (~30% aimed at where he is when they appear). A meteor touching him on the way down = hit
# (-1 heart, knocked away); a ground blast near him shoves him.
def meteor_pos(m, t):
    k = clamp((t - (m['t'] - FALL)) / FALL, 0, 1)
    sx, sy = m['x'] + 520, HEAD - 150; ex, ey = m['x'], GROUND - m['r'] * 0.5
    return lerp(sx, ex, k * k), lerp(sy, ey, k * k)
N0 = int(40 * FPS); GX, GYS, ROT, SQ, SHB = [], [], [], [], []
ball = Ball(rng.uniform(320, 760), GROUND, R=R, seed=SEED, xmin=XMIN, xmax=XMAX)
hearts = 3; HITS = []; inv_until = -1; HEARTS = []; T_FAIL = None
for m in MET: m['aim'] = rng.random() < 0.22; m['set'] = False; m['hit'] = False
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
        if abs(m['t'] - t) < 0.5 / FPS and not m['hit']:
            dx = ball.x - m['x']
            if abs(dx) < m['r'] + 240 and ball.height() < 200:
                k = 1 - max(0, abs(dx) - m['r']) / 240; ball.push((1 if dx >= 0 else -1) * 380 * k, -420 * k)
    ball.step(t)
    GX.append(ball.x); GYS.append(ball.draw_y()); ROT.append(ball.rot); SQ.append(ball.sq); SHB.append((ball.x, ball.height()))
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

stars = [(rng.uniform(0, W), rng.uniform(HEAD, 1200), rng.uniform(1, 3), rng.uniform(0, 6)) for _ in range(90)]
dunes = [(rng.uniform(-100, W + 100), rng.uniform(140, 260)) for _ in range(6)]
rocks = [(rng.uniform(40, W - 40), rng.uniform(GROUND + 40, H - 40), rng.uniform(10, 26)) for _ in range(18)]

def draw_bg(c, t):
    gr = cairo.LinearGradient(0, HEAD, 0, GROUND)
    gr.add_color_stop_rgb(0, *rgb('#1a0f33')); gr.add_color_stop_rgb(0.7, *rgb('#4a2357')); gr.add_color_stop_rgb(1, *rgb('#a2456a'))
    c.set_source(gr); c.rectangle(0, HEAD, W, GROUND - HEAD); c.fill()
    for x, y, r, ph in stars:
        c.set_source_rgba(1, 1, 0.95, 0.35 + 0.35 * math.sin(t * 2 + ph)); c.arc(x, y, r, 0, 2 * math.pi); c.fill()
    # planet + moon
    c.set_source_rgba(*hexc('#7fd3ff', 0.12)); c.arc(820, 600, 170, 0, 2 * math.pi); c.fill()
    gp = cairo.RadialGradient(780, 560, 20, 820, 600, 140); gp.add_color_stop_rgb(0, *rgb('#9fe3ff')); gp.add_color_stop_rgb(1, *rgb('#3a7bbf'))
    c.set_source(gp); c.arc(820, 600, 140, 0, 2 * math.pi); c.fill()
    c.set_source_rgba(1, 1, 1, 0.35); c.set_line_width(10); c.save(); c.translate(820, 600); c.rotate(-0.3); c.scale(1, 0.25); c.arc(0, 0, 220, 0.15, math.pi - 0.15); c.restore(); c.stroke()
    c.set_source_rgb(*rgb('#e8d8ff')); c.arc(260, 520, 42, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#c6b4e8')); c.arc(250, 510, 9, 0, 2 * math.pi); c.fill()
    for i, (x, h) in enumerate(dunes):
        c.set_source_rgb(*rgb('#6d2f5e' if i % 2 else '#5c2852'))
        c.move_to(x - 420, GROUND); c.curve_to(x - 200, GROUND - h, x + 200, GROUND - h, x + 420, GROUND); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#c4683f')); c.rectangle(0, GROUND, W, H - GROUND); c.fill()
    for (x0, x1) in ((0, WALL_L), (WALL_R, W)):
        c.set_source_rgb(*rgb('#7a3b26')); c.move_to(x0, GROUND + 30); c.line_to(x0, 1050); c.curve_to(x0 + 20, 1000, x1 - 10, 1010, x1, 1080); c.line_to(x1, GROUND + 30); c.close_path(); c.fill()
        c.set_source_rgba(1, 0.75, 0.5, 0.18); c.rectangle((x1 - 14) if x0 == 0 else x0, 1090, 14, GROUND - 1090); c.fill()
        c.set_source_rgba(0, 0, 0, 0.18)
        for yy in range(1130, GROUND, 110): c.rectangle(x0 + 10, yy, x1 - x0 - 20, 8); c.fill()
    c.set_source_rgb(*rgb('#e08a55')); c.rectangle(0, GROUND, W, 12); c.fill()
    for x, y, r in rocks:
        c.set_source_rgb(*rgb('#9c4f30')); c.save(); c.translate(x, y); c.scale(1, 0.55); c.arc(0, 0, r, 0, 2 * math.pi); c.restore(); c.fill()

def draw_craters(c, t):
    for m in MET:
        if m['t'] <= t and m['t'] <= S.T_RES + 0.3:
            c.set_source_rgb(*rgb('#7a3a24')); c.save(); c.translate(m['x'], GROUND + 6); c.scale(1, 0.22); c.arc(0, 0, m['r'] * 0.95, 0, 2 * math.pi); c.restore(); c.fill()
            c.set_source_rgb(*rgb('#5a2818')); c.save(); c.translate(m['x'], GROUND + 10); c.scale(1, 0.16); c.arc(0, 0, m['r'] * 0.6, 0, 2 * math.pi); c.restore(); c.fill()
            k = t - m['t']
            if k < 1.4:  # smoke
                for j in range(5):
                    c.set_source_rgba(0.4, 0.35, 0.4, 0.35 * (1 - k / 1.4))
                    c.arc(m['x'] + (j - 2) * 30, GROUND - 30 - k * 120 - j * 12, 30 + k * 30, 0, 2 * math.pi); c.fill()

def draw_warnings(c, t):
    for m in MET:
        if m['t'] - FALL <= t < m['t'] and m['t'] <= S.T_RES + 0.3:
            k = (t - (m['t'] - FALL)) / FALL; k = k * k
            gr = cairo.RadialGradient(0, 0, 0, 0, 0, 1)
            gr.add_color_stop_rgba(0, 1, 0.45, 0.1, 0.22 * k); gr.add_color_stop_rgba(1, 1, 0.4, 0.1, 0)
            c.save(); c.translate(m['x'], GROUND + 4); c.scale(m['r'] * (2.6 - 1.2 * k), 70); c.set_source(gr); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
            c.set_source_rgba(0, 0, 0, 0.13 * k); c.save(); c.translate(m['x'], GROUND + 6); c.scale(m['r'] * (0.5 + 0.5 * k), 14 * (0.5 + 0.5 * k)); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
        if m['t'] <= t < m['t'] + 0.5 and m['t'] <= S.T_RES + 0.3:   # shock ring
            k = (t - m['t']) / 0.5
            c.set_source_rgba(1, 0.85, 0.6, 0.6 * (1 - k)); c.set_line_width(10 * (1 - k) + 2)
            c.save(); c.translate(m['x'], GROUND); c.scale(1, 0.22); c.arc(0, 0, m['r'] + 330 * k, 0, 2 * math.pi); c.restore(); c.stroke()

def draw_meteors(c, t):
    for m in MET:
        if m['t'] - FALL <= t < m['t'] and m['t'] <= S.T_RES + 0.3:
            sx, sy = m['x'] + 520, HEAD - 150; ex, ey = m['x'], GROUND - m['r'] * 0.5
            x, y = meteor_pos(m, t)
            ang = math.atan2(ey - sy, ex - sx)
            r = m['r'] * 0.62
            c.save(); c.translate(x, y); c.rotate(ang)
            gr = cairo.LinearGradient(0, 0, -r * 6, 0)
            gr.add_color_stop_rgba(0, 1, 0.75, 0.3, 0.9); gr.add_color_stop_rgba(1, 1, 0.3, 0.1, 0)
            c.set_source(gr); c.move_to(0, -r); c.line_to(-r * 6, 0); c.line_to(0, r); c.close_path(); c.fill()
            c.restore()
            c.set_source_rgba(1, 0.6, 0.2, 0.35); c.arc(x, y, r * 1.35, 0, 2 * math.pi); c.fill()
            c.set_source_rgb(*rgb('#6b4a3a')); c.arc(x, y, r, 0, 2 * math.pi); c.fill()
            c.save(); c.translate(x, y); c.rotate(t * 7 + m['x']); c.translate(-x, -y)
            c.set_source_rgb(*rgb('#4d3226'))
            for dx, dy, rr in ((-0.3, -0.2, 0.25), (0.3, 0.25, 0.2), (0.1, -0.45, 0.14)): c.arc(x + dx * r, y + dy * r, rr * r, 0, 2 * math.pi); c.fill()
            c.restore()
            hl = cairo.RadialGradient(x - r * 0.5, y + r * 0.4, 0, x, y, r)   # lit from below-front by its own heat
            hl.add_color_stop_rgba(0, 1, 0.7, 0.3, 0.55); hl.add_color_stop_rgba(1, 1, 0.4, 0.1, 0)
            c.set_source(hl); c.arc(x, y, r, 0, 2 * math.pi); c.fill()
            c.set_source_rgba(1, 0.55, 0.15, 0.8); c.set_line_width(6); c.arc(x, y, r, 0, 2 * math.pi); c.stroke()

PS = Particles(9)
def render(f, c):
    t = f / FPS; shake = (0, 0)
    for m in MET:
        if m['t'] <= t < m['t'] + 0.25 and m['t'] <= S.T_RES + 0.3:
            a = 14 if m['big'] else 9; shake = (rng.uniform(-a, a), rng.uniform(-a, a))
        if f == int(round(m['t'] * FPS)) and m['t'] <= S.T_RES + 0.3:
            PS.spawn(m['x'], GROUND - 10, 26, (1, 0.6, 0.25), 750, 0.6, r=7); PS.spawn(m['x'], GROUND - 10, 16, (0.45, 0.3, 0.25), 520, 1.1, grav=1800, r=12)
    c.save(); c.translate(*shake)
    draw_bg(c, t); draw_craters(c, t); draw_warnings(c, t)
    fi = min(f, len(GX) - 1)
    hits = [h for h in HITS if h <= t]
    flat = T_FAIL is not None and t >= T_FAIL
    if END.carried(t) or t >= END.T_GRAB:
        gx, gy = (END.carry_xy(t) if END.carried(t) else END.S.GRAB); gy += (0 if t < END.T_LIFT else 0); sq = 0.0; rot = ROT[min(fi, int(END.T_GRAB * FPS))]
    else:
        gx = GX[fi]; gy = GYS[fi]; sq = SQ[fi]; rot = ROT[fi]
        sx, sh = SHB[fi]; kk = 1 / (1 + sh / 220)
        sg = cairo.RadialGradient(0, 0, 0, 0, 0, 1); sg.add_color_stop_rgba(0, 0, 0, 0, 0.4 * kk); sg.add_color_stop_rgba(1, 0, 0, 0, 0)
        c.save(); c.translate(sx, GROUND + 4); c.scale(R * 1.15 * (0.6 + 0.4 * kk), R * 0.22); c.set_source(sg); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    blink = hits and t - hits[-1] < 0.5 and (t * 12) % 1 < 0.35 and not flat
    danger = any(m['t'] - WARN <= t < m['t'] and abs(m['x'] - GX[fi]) < 300 for m in MET)
    mood = 'happy' if (t >= S.T_END and S.OUTCOME == 'win') else ('scared' if danger or flat else 'worried')
    if not blink:
        draw_blob(c, t, gx, gy, mood, sq, R=R, dizzy=flat and t > T_FAIL + 1.1, rot=rot)
    draw_meteors(c, t)
    PS.draw(c)
    for h in hits:
        if h <= t < h + 0.7 and (T_FAIL is None or h < T_FAIL):
            k = (t - h) / 0.7; text_at(c, '-1', GX[min(len(GX) - 1, int((h + 0.2) * FPS))] + 60, GY - 230 - 60 * k, 90, rgb('#ff4d6a'))
    if hits and t - hits[-1] < 0.15:
        c.set_source_rgba(1, 0.1, 0.1, 0.25); c.rectangle(0, HEAD, W, H - HEAD); c.fill()
    END.draw_claw(c, t)
    c.restore()
    END.header(c, t, min(f, len(HEARTS) - 1))

if __name__ == '__main__':
    if sys.argv[1] == 'sim':
        print(SEED, S.OUTCOME, round(S.T_RES, 2), 'hits', [round(h - S.T_START, 1) for h in HITS], 'mets', len(MET), 'dur', S.DUR); sys.exit()
    run(S, render)
