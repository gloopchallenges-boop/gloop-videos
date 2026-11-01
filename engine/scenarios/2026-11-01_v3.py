"""2026-11-01 v3 — STEALTH – DETECTED %: the NIGHT OWL's lantern sweeps a moonlit forest floor.
Beam path + Gloop's move schedule are seeded-random; detection is simulated from beam angle vs Gloop."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the night owl'
SEED = int(os.environ.get('SEED', 4))
rng = random.Random(SEED)

class S: pass
S.HOOK1 = 'WILL GLOOP'; S.HOOK2 = 'STAY UNSEEN?'; S.HOOK2_SIZE = 100; S.FAIL_WORD = 'SPOTTED!'; S.FAIL_SIZE = 150
S.T_START = 2.6; S.TL = 15.0; S.T_END = S.T_START + S.TL
FLOOR = 1600; R = 74; HIDE_Y = FLOOR - R * 0.75
LIGHT = (365, 845); HALF = math.radians(8.0); UP, DOWN = 45.0, 11.0
COVERS = [(275, 445, FLOOR - 200, 'bush'), (515, 665, FLOOR - 175, 'stump'), (725, 875, FLOOR - 190, 'rock'), (915, 1065, FLOOR - 205, 'bush')]
SPOTS = [360, 590, 800, 990]

# --- seeded beam path: random targets in 38..80 deg, random sweep durations, some pauses
BEAM = [(0, rng.uniform(55, 75))]; tt = 0
while tt < 30:
    d = rng.uniform(0.7, 1.8); tt += d; BEAM.append((tt, rng.uniform(38, 80)))
    if rng.random() < 0.3: tt += rng.uniform(0.3, 0.9); BEAM.append((tt, BEAM[-1][1]))
def beam_angle(t):
    for (t0, a0), (t1, a1) in zip(BEAM, BEAM[1:]):
        if t0 <= t <= t1: return math.radians(lerp(a0, a1, ease((t - t0) / (t1 - t0))))
    return math.radians(BEAM[-1][1])

# --- seeded Gloop plan: 5 moves between neighbouring covers at random times, random peeks
NMOV = 5; HOPD = 1.0
hop_ts = sorted(rng.uniform(S.T_START + 0.8, S.T_END - 1.2) for _ in range(NMOV))
for i in range(1, NMOV):
    if hop_ts[i] - hop_ts[i - 1] < 1.5: hop_ts[i] = hop_ts[i - 1] + 1.5
idx = 0; PATH = [(0, SPOTS[0])]; HOPS = []
for h in hop_ts:
    nxt = idx + 1 if idx == 0 else (idx - 1 if idx == 3 else idx + rng.choice((-1, 1, 1)))
    PATH += [(h, SPOTS[idx]), (h + HOPD, SPOTS[nxt])]; HOPS.append((h, h + HOPD)); idx = nxt
PATH.append((99, SPOTS[idx])); S.LAST = SPOTS[idx]
PEEKS = [(0.3, 2.3)]
for _ in range(5):
    p = rng.uniform(S.T_START + 0.5, S.T_END - 1)
    if all(abs(p - h - 0.5) > 1.1 for h in hop_ts) and all(abs(p - q[0]) > 1.2 for q in PEEKS): PEEKS.append((p, p + 0.9))

def gloop_pos(t):
    x = PATH[-1][1]; moving = False
    for (t0, x0), (t1, x1) in zip(PATH, PATH[1:]):
        if t0 <= t <= t1: x = lerp(x0, x1, ease((t - t0) / (t1 - t0))); moving = x0 != x1; break
    y = HIDE_Y
    if moving: y -= abs(math.sin(t * 7.0 * math.pi)) * 90 + 30
    peek = 0
    for p0, p1 in PEEKS:
        if p0 <= t <= p1: peek = math.sin(math.pi * (t - p0) / (p1 - p0))
    return x, y - peek * 125, moving, peek

def hidden(t):
    x, y, moving, peek = gloop_pos(t)
    return not moving and peek <= 0.35
def in_cone(px, py, t):
    a = beam_angle(t); ang = math.atan2(py - LIGHT[1], px - LIGHT[0])
    return abs(ang - a) < HALF + math.atan2(R * 0.6, math.hypot(px - LIGHT[0], py - LIGHT[1]))
def seen(t):
    x, y, _, _ = gloop_pos(t); return in_cone(x, y, t) and not hidden(t)

N0 = int(40 * FPS); DET, SEEN = [], []; d = 0.0; T_SPOT = None
for f in range(N0):
    t = f / FPS
    s = S.T_START <= t < S.T_END and T_SPOT is None and seen(t)
    if T_SPOT is None and S.T_START <= t < S.T_END:
        d = clamp(d + (UP if s else -DOWN) / FPS, 0, 100)
        if d >= 100: T_SPOT = t
    DET.append(d); SEEN.append(s)
S.OUTCOME = 'fail' if T_SPOT else 'win'
S.T_RES = T_SPOT if T_SPOT else S.T_END
S.PEAK = max(DET[:int(S.T_RES * FPS)])
if T_SPOT: S.GRAB = (gloop_pos(T_SPOT)[0], FLOOR - 120)
else: S.GRAB = (S.LAST, HIDE_Y)
END = S.END = Ending(S)
T_CAGE = S.T_RES + 0.05
seen_starts = [i / FPS for i in range(1, N0) if SEEN[i] and not SEEN[i - 1]]
S.events = [[s, 'blip'] for s in seen_starts if s < S.T_RES]
for h0, h1 in HOPS:
    if h0 < S.T_RES:
        k = h0
        while k < min(h1, S.T_RES): S.events.append([k, 'hop']); k += 1 / 3.5
if T_SPOT: S.events += [[T_SPOT, 'siren'], [T_CAGE + 0.35, 'slam']]
S.events += [[2.9, 'snore'] if False else [3.0, 'whoosh']]
S.AMB = {'drone': 52, 'wind': 0.02}
S.cage_x = S.GRAB[0]

def draw_bar(c, t, f):
    d = DET[f]; s = SEEN[f]
    bx = bar(c, d / 100, f'DETECTED {int(d)}%', bad_col(d / 100), 0.15 if s else 0, bw=620, x_off=40)
    eye_icon(c, bx - 60, 231, s)
S.draw_bar = draw_bar

def eye_icon(c, x, y, open_):
    c.save(); c.translate(x, y); col = rgb('#ff4d4d') if open_ else (0.55, 0.55, 0.6)
    c.set_line_width(6); c.set_source_rgb(*col)
    c.move_to(-34, 0); c.curve_to(-14, -26 if open_ else -4, 14, -26 if open_ else -4, 34, 0)
    if open_:
        c.curve_to(14, 26, -14, 26, -34, 0); c.close_path(); c.stroke(); c.arc(0, 0, 11, 0, 2 * math.pi); c.fill()
    else:
        c.stroke()
        for dx in (-18, 0, 18): c.move_to(dx, 2); c.line_to(dx * 1.2, 14); c.stroke()
    c.restore()

stars = [(rng.uniform(0, W), rng.uniform(HEAD, 1000), rng.uniform(1, 3), rng.uniform(0, 6)) for _ in range(70)]
trees = [(x, rng.uniform(0.7, 1.2)) for x in range(-40, W + 80, 95)]
flies = [(rng.uniform(300, W), rng.uniform(900, 1450), rng.uniform(0, 6)) for _ in range(12)]
grass = [(x, rng.uniform(14, 30)) for x in range(0, W, 14)]

def draw_bg(c, t):
    gr = cairo.LinearGradient(0, HEAD, 0, FLOOR)
    gr.add_color_stop_rgb(0, *rgb('#0e1430')); gr.add_color_stop_rgb(1, *rgb('#1d2a4a'))
    c.set_source(gr); c.rectangle(0, HEAD, W, FLOOR - HEAD); c.fill()
    for x, y, r, ph in stars:
        c.set_source_rgba(1, 1, 0.9, 0.4 + 0.4 * math.sin(t * 2 + ph)); c.arc(x, y, r, 0, 2 * math.pi); c.fill()
    c.set_source_rgba(*hexc('#fff3c4', 0.12)); c.arc(880, 520, 125, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#fff3c4')); c.arc(880, 520, 72, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#e9dca8')); c.arc(860, 505, 12, 0, 2 * math.pi); c.fill(); c.arc(905, 545, 8, 0, 2 * math.pi); c.fill()
    for col, lst, base, hgt in (('#162040', trees, 1350, 300), ('#121a35', trees[::2], 1480, 240)):
        c.set_source_rgb(*rgb(col))
        for x, s in lst:
            top = base - hgt * s
            for k in range(3):
                yy = top + k * 70 * s
                c.move_to(x - (40 + k * 25) * s, yy + 110 * s); c.line_to(x, yy); c.line_to(x + (40 + k * 25) * s, yy + 110 * s); c.close_path(); c.fill()
            c.rectangle(x - 8, top + 250 * s, 16, FLOOR); c.fill()
    # owl's tree
    c.set_source_rgb(*rgb('#3a2a20')); c.rectangle(0, HEAD, 110, FLOOR - HEAD); c.fill()
    c.move_to(90, 900); c.curve_to(200, 880, 330, 870, 430, 885); c.line_to(430, 912); c.curve_to(330, 905, 200, 915, 90, 950); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#4b382b'))
    for yy in range(HEAD + 40, FLOOR, 90): c.rectangle(30, yy, 8, 50); c.fill()
    for (lx, ly, r) in [(50, 400, 120), (190, 380, 85), (60, 620, 70)]:
        c.set_source_rgb(*rgb('#1f4a2c')); c.arc(lx, ly, r, 0, 2 * math.pi); c.fill()
    for x, y, ph in flies:
        a = 0.5 + 0.5 * math.sin(t * 3 + ph)
        c.set_source_rgba(0.85, 1, 0.4, 0.15 * a); c.arc(x + 20 * math.sin(t + ph), y, 14, 0, 2 * math.pi); c.fill()
        c.set_source_rgba(0.9, 1, 0.5, 0.8 * a); c.arc(x + 20 * math.sin(t + ph), y, 4, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#1c3320')); c.rectangle(0, FLOOR, W, H - FLOOR); c.fill()
    c.set_source_rgb(*rgb('#264a2b'))
    for x, h in grass:
        c.move_to(x, FLOOR + 4); c.line_to(x + 5, FLOOR - h); c.line_to(x + 10, FLOOR + 4); c.close_path(); c.fill()
    c.set_source_rgba(0, 0, 0, 0.18)
    for yy in range(FLOOR + 60, H, 70): c.rectangle(0, yy, W, 6); c.fill()

def draw_covers(c, t):
    for x0, x1, top, kind in COVERS:
        if kind == 'bush':
            for k, (dx, dy, r) in enumerate([(0.2, 0.55, 0.32), (0.55, 0.35, 0.38), (0.85, 0.6, 0.3), (0.5, 0.75, 0.45)]):
                c.set_source_rgb(*rgb('#2f7a3a' if k % 2 else '#276b33'))
                c.arc(x0 + (x1 - x0) * dx, top + (FLOOR - top) * dy, (x1 - x0) * r, 0, 2 * math.pi); c.fill()
            c.set_source_rgb(*rgb('#276b33')); c.rectangle(x0, top + (FLOOR - top) * 0.6, x1 - x0, (FLOOR - top) * 0.4 + 4); c.fill()
            c.set_source_rgb(*rgb('#d94a5a'))
            for dx, dy in ((0.3, 0.4), (0.7, 0.3), (0.55, 0.65)): c.arc(x0 + (x1 - x0) * dx, top + (FLOOR - top) * dy, 7, 0, 2 * math.pi); c.fill()
        elif kind == 'stump':
            c.set_source_rgb(*rgb('#6b4524')); c.rectangle(x0, top + 20, x1 - x0, FLOOR - top - 20); c.fill()
            c.set_source_rgb(*rgb('#c9a06a')); c.save(); c.translate((x0 + x1) / 2, top + 20); c.scale((x1 - x0) / 2, 22); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
            c.set_source_rgb(*rgb('#8a6038')); c.set_line_width(3)
            for r in (0.3, 0.6): c.save(); c.translate((x0 + x1) / 2, top + 20); c.scale((x1 - x0) / 2 * r, 22 * r); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.stroke()
            c.set_source_rgba(0, 0, 0, 0.25); c.set_line_width(5)
            for xx in range(x0 + 25, x1 - 10, 30): c.move_to(xx, top + 50); c.line_to(xx + 4, FLOOR - 10); c.stroke()
        elif kind == 'rock':
            c.set_source_rgb(*rgb('#5d6475'))
            c.move_to(x0, FLOOR); c.curve_to(x0 - 5, top + 60, x0 + 50, top, (x0 + x1) / 2, top); c.curve_to(x1 - 30, top, x1 + 5, top + 70, x1, FLOOR); c.close_path(); c.fill()
            c.set_source_rgba(1, 1, 1, 0.12); c.arc(x0 + 60, top + 50, 22, 0, 2 * math.pi); c.fill()
            c.set_source_rgb(*rgb('#3f6e3a')); c.arc(x1 - 40, top + 30, 18, 0, 2 * math.pi); c.fill()

def draw_beam(c, t):
    a = beam_angle(t); L = 2600; alarm = T_SPOT is not None and t >= T_SPOT
    c.save(); c.rectangle(0, HEAD, W, H - HEAD); c.clip()
    gr = cairo.LinearGradient(LIGHT[0], LIGHT[1], LIGHT[0] + math.cos(a) * 1300, LIGHT[1] + math.sin(a) * 1300)
    col = (1, 0.25, 0.2) if alarm else (1, 0.9, 0.5)
    gr.add_color_stop_rgba(0, *col, 0.55); gr.add_color_stop_rgba(1, *col, 0.1)
    c.move_to(*LIGHT); c.line_to(LIGHT[0] + math.cos(a - HALF) * L, LIGHT[1] + math.sin(a - HALF) * L)
    c.line_to(LIGHT[0] + math.cos(a + HALF) * L, LIGHT[1] + math.sin(a + HALF) * L); c.close_path()
    c.set_source(gr); c.set_operator(cairo.OPERATOR_ADD); c.fill(); c.set_operator(cairo.OPERATOR_OVER); c.restore()

def draw_owl(c, t, gx, gy):
    ox, oy = 215, 760; alarm = T_SPOT is not None and t >= T_SPOT
    c.set_source_rgb(*rgb('#7a5434')); c.save(); c.translate(ox, oy); c.scale(1, 1.25); c.arc(0, 0, 105, 0, 2 * math.pi); c.restore(); c.fill()
    c.set_source_rgb(*rgb('#c9a57a')); c.save(); c.translate(ox, oy + 35); c.scale(1, 1.2); c.arc(0, 0, 65, 0, 2 * math.pi); c.restore(); c.fill()
    c.set_source_rgb(*rgb('#9a7650')); c.set_line_width(4)
    for yy in range(-10, 90, 24):
        for xx in (-30, 0, 30): c.arc(ox + xx, oy + 20 + yy, 10, 0.2, math.pi - 0.2); c.stroke()
    c.set_source_rgb(*rgb('#6a462a'))
    for s in (-1, 1):
        c.move_to(ox + s * 50, oy - 105); c.line_to(ox + s * 95, oy - 175); c.line_to(ox + s * 95, oy - 90); c.close_path(); c.fill()
    for s in (-1, 1):
        ex, ey = ox + s * 45, oy - 60
        c.set_source_rgb(*rgb('#e9d6b0')); c.arc(ex, ey, 44, 0, 2 * math.pi); c.fill()
        c.set_source_rgb(*(rgb('#ff4d4d') if alarm else rgb('#ffcf3a'))); c.arc(ex, ey, 32, 0, 2 * math.pi); c.fill()
        dx, dy = gx - ex, gy - ey; dd = math.hypot(dx, dy) or 1
        a = beam_angle(t); px, py = math.cos(a), math.sin(a)
        c.set_source_rgb(0.05, 0.05, 0.05); c.arc(ex + px * 12, ey + py * 12, 16, 0, 2 * math.pi); c.fill()
        c.set_source_rgb(1, 1, 1); c.arc(ex + px * 12 + 6, ey + py * 12 - 6, 5, 0, 2 * math.pi); c.fill()
        lid = 0.0 if alarm else 0.25
        c.set_source_rgb(*rgb('#7a5434')); c.rectangle(ex - 46, ey - 46, 92, 92 * lid); c.fill()
    c.set_source_rgb(*rgb('#f0a03a')); c.move_to(ox - 14, oy - 30); c.line_to(ox + 14, oy - 30); c.line_to(ox, oy + 2); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#e0a040'))
    for s in (-1, 1):
        for k in (-1, 0, 1): c.arc(ox + s * 35 + k * 12, oy + 128, 8, 0, 2 * math.pi); c.fill()
    # wing holding lantern
    a = beam_angle(t)
    c.set_source_rgb(*rgb('#6a462a')); c.move_to(ox + 70, oy - 30); c.curve_to(ox + 150, oy - 10, LIGHT[0] - 10, LIGHT[1] - 50, LIGHT[0] - 20, LIGHT[1] - 10); c.curve_to(LIGHT[0] - 50, LIGHT[1] + 10, ox + 110, oy + 80, ox + 70, oy + 90); c.close_path(); c.fill()
    c.save(); c.translate(*LIGHT); c.rotate(a)
    c.set_source_rgb(*rgb('#3a3f52')); rrect(c, -55, -22, 60, 44, 10); c.fill()
    c.set_source_rgb(*rgb('#ffe9a0')); rrect(c, -4, -26, 14, 52, 5); c.fill()
    c.restore()

def cage_top(t):
    if not T_SPOT or t < T_CAGE: return None
    tgt = FLOOR - 210; k = (t - T_CAGE) / 0.35
    if k < 1: return lerp(HEAD - 260, tgt, k * k)
    if not END.carried(t): return tgt
    return END.carry_xy(t)[1] - 40

def draw_cage(c, t):
    ct = cage_top(t)
    if ct is None: return
    cx = END.carry_xy(t)[0] if END.carried(t) else S.cage_x
    x0, x1 = cx - 95, cx + 95
    c.set_source_rgb(*rgb('#b9c0d0')); c.set_line_width(8)
    for i in range(7):
        x = x0 + i * (x1 - x0) / 6; c.move_to(x, ct); c.line_to(x, ct + 210); c.stroke()
    c.set_source_rgb(*rgb('#7d8596')); rrect(c, x0 - 10, ct - 16, x1 - x0 + 20, 22, 8); c.fill(); rrect(c, x0 - 10, ct + 196, x1 - x0 + 20, 16, 6); c.fill()
    c.set_line_width(9); c.set_source_rgb(*rgb('#c9d0de')); c.arc(cx, ct - 34, 20, math.pi, 2 * math.pi); c.stroke()

PS = Particles()
def render(f, c):
    t = f / FPS; shake = (0, 0)
    if T_SPOT and T_SPOT <= t < T_SPOT + 0.3: shake = (rng.uniform(-12, 12), rng.uniform(-12, 12))
    if T_SPOT and T_CAGE + 0.35 <= t < T_CAGE + 0.55: shake = (rng.uniform(-16, 16), rng.uniform(-16, 16))
    if T_SPOT and f == int((T_CAGE + 0.35) * FPS): PS.spawn(S.cage_x, FLOOR - 5, 26, (0.6, 0.75, 0.6), 500, 0.7)
    c.save(); c.translate(*shake)
    draw_bg(c, t)
    if END.carried(t):
        gx, gy = END.carry_xy(t); gy = gy + (130 if T_SPOT else 40); moving = False; peek = 0
    elif T_SPOT and t >= T_SPOT:
        gx, gy, moving, peek = gloop_pos(T_SPOT); gy = min(FLOOR - R * 0.95, gy + (t - T_SPOT) * 900)
    else:
        gx, gy, moving, peek = gloop_pos(t)
    s = SEEN[min(f, len(SEEN) - 1)]
    if T_SPOT and t >= T_SPOT: mood = 'scared'
    elif s or (peek > 0 and in_cone(gx, gy, t)): mood = 'scared'
    elif t >= S.T_END: mood = 'happy'
    else: mood = 'worried'
    sq = 0.04 * math.sin(t * 6) + (0.12 if not moving and peek == 0 else -0.05)
    caught = T_SPOT is not None and t >= T_SPOT
    if not caught: draw_blob(c, t, gx, gy, mood, sq, R=R)
    draw_covers(c, t)
    if caught: draw_blob(c, t, gx, gy, mood, sq, R=R)
    draw_cage(c, t)
    draw_beam(c, t)
    draw_owl(c, t, gx, gy)
    END.draw_claw(c, t)
    for st in seen_starts:
        if st <= t < st + 0.6 and st < S.T_RES + 0.01:
            k = (t - st) / 0.6
            text_at(c, '!', gx, gy - 130 - 30 * k, 110 * (1 + 0.4 * max(0, 1 - k * 4)), rgb('#ff4d4d'))
    PS.draw(c)
    if T_SPOT and t >= T_SPOT and t < END.T_OUTRO:
        c.set_source_rgba(1, 0, 0, 0.16 * (0.5 + 0.5 * math.sin(t * 14))); c.rectangle(0, HEAD, W, H - HEAD); c.fill()
    c.restore()
    END.header(c, t, f)

if __name__ == '__main__':
    if sys.argv[1] == 'sim':
        print(SEED, S.OUTCOME, round(S.T_RES, 2), 'peak', round(S.PEAK), 'final', round(DET[int(S.T_RES * FPS) - 1]), 'dur', S.DUR); sys.exit()
    run(S, render)
