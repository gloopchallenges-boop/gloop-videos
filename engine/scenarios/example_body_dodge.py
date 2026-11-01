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
GROUND = 1590; R = 80; GY = GROUND - R * 0.9; XMIN, XMAX = 130, 950
WARN, FALL = 1.05, 0.75; SPEED = 760; HIT_R = 0.0

# --- seeded meteors
MET = []; t = 0.9; iv = 1.45
while t < S.T_END - 0.2:
    big = rng.random() < 0.25
    x = rng.uniform(150, 930) if t > S.T_START + 0.5 else rng.choice((rng.uniform(150, 300), rng.uniform(780, 930)))
    MET.append({'t': t, 'x': x, 'r': 120 if big else 85, 'big': big})
    t += rng.uniform(0.55, 1.15) * iv; iv = max(0.8, iv * 0.96)

# --- simulate: Gloop is NOT psychic. He wanders on his own, only sometimes notices a meteor (after a
# random delay, sometimes panicking the wrong way); ~40% of meteors are aimed at where he is when they
# appear, the rest land anywhere. Blasts knock him back; a hit launches him tumbling.
N0 = int(40 * FPS); GX, GYS, ROT, SQ, SHB = [], [], [], [], []
body = Body(rng.uniform(300, 780), GROUND, R=R, seed=SEED, speed=SPEED, xmin=XMIN, xmax=XMAX)
target = body.x; next_wander = 0.0; hearts = 3; HITS = []; inv_until = -1; HEARTS = []; T_FAIL = None
for m in MET:
    m['aim'] = rng.random() < 0.28; m['notice'] = rng.random() < 0.7
    m['delay'] = rng.uniform(0.25, 0.85); m['panic'] = rng.random() < 0.2; m['set'] = False
for f in range(N0):
    t = f / FPS
    if t >= next_wander and T_FAIL is None:            # wander around on his own
        target = clamp(body.x + rng.uniform(-380, 380), XMIN, XMAX); next_wander = t + rng.uniform(1.2, 3.2)
    for m in MET:
        if not m['set'] and t >= m['t'] - WARN:          # meteor appears: aimed ones target his position now
            if m['aim'] and t > S.T_START - 0.3: m['x'] = clamp(body.x + rng.uniform(-70, 70), 150, 930)
            m['set'] = True
        if m['set'] and m['notice'] and T_FAIL is None and abs(t - (m['t'] - WARN + m['delay'])) < 0.5 / FPS and t < m['t']:
            side = (1 if body.x >= m['x'] else -1) * (-1 if m['panic'] else 1)
            target = clamp(m['x'] + side * (m['r'] + rng.uniform(150, 320)), XMIN, XMAX); next_wander = t + rng.uniform(1.0, 2.0)
        if abs(m['t'] - t) < 0.5 / FPS:
            d = body.x - m['x']; away = 1 if d >= 0 else -1
            live = T_FAIL is None and S.T_START <= t < S.T_END
            m['hit'] = live and abs(d) < m['r'] + R * 0.55 and body.height() < 140 and t > inv_until
            if m['hit']:
                body.push(away * rng.uniform(500, 800), -rng.uniform(900, 1200)); hearts -= 1; HITS.append(t); inv_until = t + 0.9
                if hearts == 0: T_FAIL = t
            elif abs(d) < m['r'] + 260 and T_FAIL is None:   # near miss: blast shove
                k = 1 - (abs(d) - m['r']) / 260; body.push(away * 420 * k, -380 * k)
    body.step(t, target, active=T_FAIL is None and t < S.T_END + 0.3)
    GX.append(body.x); GYS.append(body.draw_y()); ROT.append(body.rot); SQ.append(body.sq); SHB.append((body.x, body.height()))
    HEARTS.append(hearts)
S.OUTCOME = 'fail' if T_FAIL else 'win'
S.T_RES = T_FAIL if T_FAIL else S.T_END
S.GRAB = (540, GROUND - R)
END = S.END = Ending(S)
gi = min(int(END.T_GRAB * FPS), N0 - 1); S.GRAB = (GX[gi], GYS[gi] + 25)
S.events = [[S.T_START + 0.1, 'rumble', 1.2]]
for m in MET:
    if m['t'] - FALL < S.T_RES + 0.3: S.events.append([m['t'] - FALL, 'whoosh'])
    if m['t'] <= S.T_RES + 0.3:
        S.events.append([m['t'], 'crash'])
        if m.get('hit'): S.events.append([m['t'] + 0.05, 'heart'])
for (tl, xl, imp) in body.landings:
    if tl < S.T_RES + 1.0 and imp > 0.06: S.events.append([tl, 'thump', min(0.6, imp * 2)])
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
            c.set_source_rgba(0, 0, 0, 0.3 * k); c.save(); c.translate(m['x'], GROUND + 6); c.scale(m['r'] * (0.5 + 0.5 * k), 14 * (0.5 + 0.5 * k)); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
        if m['t'] <= t < m['t'] + 0.5 and m['t'] <= S.T_RES + 0.3:   # shock ring
            k = (t - m['t']) / 0.5
            c.set_source_rgba(1, 0.85, 0.6, 0.6 * (1 - k)); c.set_line_width(10 * (1 - k) + 2)
            c.save(); c.translate(m['x'], GROUND); c.scale(1, 0.22); c.arc(0, 0, m['r'] + 330 * k, 0, 2 * math.pi); c.restore(); c.stroke()

def draw_meteors(c, t):
    for m in MET:
        if m['t'] - FALL <= t < m['t'] and m['t'] <= S.T_RES + 0.3:
            k = (t - (m['t'] - FALL)) / FALL
            sx, sy = m['x'] + 520, HEAD - 150; ex, ey = m['x'], GROUND - m['r'] * 0.5
            x, y = lerp(sx, ex, k * k), lerp(sy, ey, k * k)
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
    if END.carried(t):
        gx, gy = END.carry_xy(t); gy += 20; sq = 0.0; rot = 0
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
