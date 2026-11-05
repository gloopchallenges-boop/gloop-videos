"""2026-11-05 v4 — RISING DANGER – WATER GAP m: the SINKING SHIP. Inside a wooden cargo hold at night.
Gloop is a passive rigid ball (Ball) bouncing on a deck platform built on stacked crates, between two
stacks of barrels (walls). Seawater rises from frame 0 at a seeded-random rate: hull planks burst open and
gush (surges) and a bilge pump sometimes gulps it back. WATER GAP = distance from the water surface up to
the platform. If the water touches Gloop he's soaked = fail (floats dizzy). Timer ends first = win."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the sinking ship'
SEED = int(os.environ.get('SEED', 13))
rng = random.Random(SEED)

class S: pass
S.HOOK2 = 'THE SINKING SHIP?'; S.HOOK2_SIZE = 90; S.FAIL_WORD = 'SOAKED!'; S.FAIL_SIZE = 150
S.T_START = HOOK_T; S.TL = 13.0; S.T_END = S.T_START + S.TL
GRATE = 1270; R = 58; XMIN, XMAX = 190, 890; PXM = 100.0
SL0 = 1880; BASE = float(os.environ.get('BASE', 18))

EVS = []; t = rng.uniform(0.0, 0.4)   # pipe surges (+) and drain gulps (-)
while t < S.T_END + 1:
    gulp = rng.random() < 0.3
    EVS.append({'t': t, 'd': rng.uniform(0.8, 1.6), 'a': (-rng.uniform(25, 45) if gulp else rng.uniform(30, 75)), 'pipe': rng.randrange(3)})
    t += rng.uniform(1.0, 2.2)
PIPES = [(300, 820), (790, 760), (560, 980)]   # leaking hull planks (x, y) on the back wall

TER = Terrain(GRATE, seed=SEED, bumps=0, amp=0, soft=False)
N0 = int(40 * FPS); GX, GYS, SL, GAP = [], [], [], []
ball = Ball(rng.uniform(320, 760), TER, R=R, seed=SEED, xmin=XMIN, xmax=XMAX, hop=rng.uniform(230, 300))
sl = SL0; T_FAIL = None
for f in range(N0):
    t = f / FPS
    if T_FAIL is None and t < S.T_END:
        rate = BASE + sum(e['a'] for e in EVS if e['t'] <= t < e['t'] + e['d'])
        sl -= rate / FPS
    elif t >= S.T_END and T_FAIL is None:
        sl -= BASE * max(0, 1 - (t - S.T_END) / 0.6) / FPS
    if T_FAIL is None: ball.step(t)
    if T_FAIL is None and S.T_START <= t < S.T_END and ball.y + R > sl + 4:
        T_FAIL = t; FX, FY = ball.x, ball.y
    GX.append(ball.x); GYS.append(ball.y); SL.append(sl); GAP.append(max(0.0, (sl - GRATE) / PXM))
S.OUTCOME = 'fail' if T_FAIL else 'win'
S.T_RES = T_FAIL if T_FAIL else S.T_END
END = S.END = Ending(S)
if T_FAIL: S.GRAB = (FX, SL[int(T_FAIL * FPS)] - R * 0.45)
else: gi = min(int(END.T_GRAB * FPS), N0 - 1); S.GRAB = (GX[gi], GYS[gi])
S.events = [[0.05, 'rumble', 1.2], [0.3, 'creak']]
for e in EVS:
    if e['t'] < S.T_RES: S.events.append([e['t'], 'splash' if e['a'] > 0 else 'whoosh']); S.events.append([e['t'], 'rumble', min(e['d'], 1.2)])
for (tl, xl, imp) in ball.landings:
    if tl < S.T_RES: S.events.append([tl, 'clink' if tl > S.T_START and (tl * 7) % 1 < 0.3 else 'hop'])
for tw in ball.walls:
    if tw < S.T_RES: S.events.append([tw, 'thump', 0.35])
if T_FAIL: S.events += [[T_FAIL, 'splash'], [T_FAIL + 0.1, 'pop'], [T_FAIL + 0.4, 'splash']]
S.AMB = {'drone': 44, 'rumble': 0.03}
for e in EVS:
    if e['a'] > 0 and e['t'] < S.T_RES: S.events.append([max(0, e['t'] - 0.15), 'creak'])

def draw_bar(c, t, f):
    g = GAP[f]; surge = any(e['t'] <= t < e['t'] + e['d'] and e['a'] > 0 for e in EVS)
    bx = bar(c, g / 6.0, f'WATER GAP {g:.1f} m', good_bad_col(g / 4.0), 0.12 if surge else 0, bw=640, x_off=36)
    c.save(); c.translate(bx - 52, 231); c.set_source_rgb(*rgb('#5fb4e8'))
    c.move_to(0, -28); c.curve_to(10, -10, 24, 2, 24, 12); c.curve_to(24, 26, 12, 32, 0, 32); c.curve_to(-12, 32, -24, 26, -24, 12); c.curve_to(-24, 2, -10, -10, 0, -28); c.fill()
    c.set_source_rgba(1, 1, 1, 0.6); c.arc(-8, 12, 6, 0, 2 * math.pi); c.fill(); c.restore()
S.draw_bar = draw_bar

def lantern_angle(t): return 0.22 * math.sin(t * 1.4) + 0.05 * math.sin(t * 3.1)
def draw_bg(c, t, f):
    c.set_source_rgb(*rgb('#1c1612')); c.rectangle(0, HEAD, W, H - HEAD); c.fill()
    for i, yy in enumerate(range(HEAD, H, 64)):   # hull planks
        c.set_source_rgb(*(rgb('#251d17') if i % 2 else rgb('#2a211a'))); c.rectangle(0, yy, W, 58); c.fill()
        c.set_source_rgb(*rgb('#1a140f'))
        for x in range((i * 173) % 260, W, 260): c.rectangle(x, yy, 5, 58); c.fill()
    for x in (160, 540, 920):   # ribs
        c.set_source_rgb(*rgb('#3a2c20')); c.rectangle(x - 22, HEAD, 44, H - HEAD); c.fill()
    c.set_source_rgb(*rgb('#3a2c20')); c.rectangle(0, HEAD + 40, W, 46); c.fill()   # deck beam
    for (px, py) in ((350, 600), (730, 600)):   # portholes with moonlight
        c.set_source_rgb(*rgb('#6a5a3a')); c.arc(px, py, 62, 0, 2 * math.pi); c.fill()
        c.set_source_rgb(*rgb('#1b2a44')); c.arc(px, py, 46, 0, 2 * math.pi); c.fill()
        c.set_source_rgba(0.9, 0.9, 0.8, 0.8); c.arc(px + 14, py - 12, 12, 0, 2 * math.pi); c.fill()
        c.set_source_rgba(0.75, 0.82, 0.95, 0.05); c.move_to(px - 40, py + 20); c.line_to(px + 40, py + 20); c.line_to(px + 140, 1260); c.line_to(px - 60, 1260); c.close_path(); c.fill()
    # hanging lantern (swings with the ship)
    a = lantern_angle(t); lx, ly0 = 540, HEAD + 86; L = 230
    ex, ey = lx + math.sin(a) * L, ly0 + math.cos(a) * L
    c.set_source_rgba(1, 0.75, 0.35, 0.07); c.arc(ex, ey + 30, 230, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#2a2a2a')); c.set_line_width(4); c.move_to(lx, ly0); c.line_to(ex, ey); c.stroke()
    c.save(); c.translate(ex, ey); c.rotate(-a)
    c.set_source_rgb(*rgb('#3c3a36')); rrect(c, -26, 0, 52, 14, 4); c.fill(); rrect(c, -26, 70, 52, 12, 4); c.fill()
    c.set_source_rgb(*rgb('#f0c060')); rrect(c, -20, 14, 40, 56, 6); c.fill()
    c.set_source_rgb(*rgb('#ffe8a0')); c.arc(0, 44, 9, 0, 2 * math.pi); c.fill()
    c.restore()

def draw_gush(c, t, f):
    for e in EVS:
        if e['a'] > 0 and e['t'] <= t < e['t'] + e['d'] and (e['t'] < S.T_RES or e['t'] < S.T_START):
            px, py = PIPES[e['pipe']]; k = min(1, (t - e['t']) / 0.2, (e['t'] + e['d'] - t) / 0.2)
            ly = SL[min(f, len(SL) - 1)]; dirx = 1 if px < 540 else -1
            c.set_line_cap(cairo.LINE_CAP_ROUND)
            for wdt, col in ((46, (0.35, 0.6, 0.8, 0.85)), (20, (0.7, 0.86, 0.96, 0.9))):
                c.set_source_rgba(*col); c.set_line_width(wdt * k)
                c.move_to(px, py); c.curve_to(px + dirx * 70, py, px + dirx * 100, py + 80, px + dirx * 110, ly + 10); c.stroke()
            for j in range(5):
                q = (t * 2.4 + j / 5) % 1; dx_ = px + dirx * 110 * min(1, q * 3); dy_ = lerp(py, ly, q * q)
                c.set_source_rgba(0.75, 0.9, 1, 0.9 * k); c.arc(dx_ + 10 * math.sin(j * 2.3), dy_, 7, 0, 2 * math.pi); c.fill()
            c.set_source_rgba(0.8, 0.92, 1, 0.7 * k)
            for j in range(4): c.arc(px + dirx * 110 + (j - 1.5) * 26, ly - 8 - 20 * abs(math.sin(t * 9 + j)), 9, 0, 2 * math.pi); c.fill()
        if e['a'] < 0 and e['t'] <= t < e['t'] + e['d'] and e['t'] < S.T_RES:   # bilge pump gulp: swirl around the hose
            ly = SL[min(f, len(SL) - 1)]; c.set_source_rgba(0.75, 0.88, 1, 0.5); c.set_line_width(5)
            for j in range(3): c.save(); c.translate(760, ly + 30); c.scale(1, 0.3); c.arc(0, 0, 50 + j * 45, t * 6 + j, t * 6 + j + 4); c.restore(); c.stroke()

def draw_leaks(c, t):
    for i, (px, py) in enumerate(PIPES):   # cracked planks, dripping
        c.set_source_rgb(*rgb('#120d0a')); c.move_to(px - 40, py - 8); c.line_to(px - 10, py - 4); c.line_to(px, py - 14); c.line_to(px + 34, py - 6); c.line_to(px + 30, py + 8); c.line_to(px - 36, py + 10); c.close_path(); c.fill()
        q = (t * 1.2 + i * 0.37) % 1; c.set_source_rgba(0.7, 0.86, 0.98, 0.8 * (1 - q)); c.arc(px, py + 14 + q * 120, 5, 0, 2 * math.pi); c.fill()

def draw_water(c, t, f):
    ly = SL[min(f, len(SL) - 1)]
    c.move_to(0, H)
    for x in range(0, W + 20, 20): c.line_to(x, ly + 9 * math.sin(x * 0.016 + t * 2.0) + 5 * math.sin(x * 0.05 - t * 2.7))
    c.line_to(W, H); c.close_path(); c.set_source_rgba(0.16, 0.36, 0.5, 0.88); c.fill()
    c.set_source_rgba(0.1, 0.26, 0.38, 0.9); c.rectangle(0, ly + 60, W, H - ly); c.fill()
    c.set_source_rgba(0.85, 0.93, 1, 0.35); c.set_line_width(4)
    for x in range(0, W + 20, 20): (c.move_to if x == 0 else c.line_to)(x, ly + 9 * math.sin(x * 0.016 + t * 2.0) + 5 * math.sin(x * 0.05 - t * 2.7))
    c.stroke()
    # bilge pump hose dipping into the water
    c.set_source_rgb(*rgb('#2b2b2e')); c.set_line_width(22); c.set_line_cap(cairo.LINE_CAP_ROUND); c.move_to(780, HEAD + 86); c.curve_to(800, 700, 700, 900, 760, max(ly + 40, 960)); c.stroke()

def draw_deck(c, t):
    for (x0, x1) in ((0, XMIN - R), (XMAX + R, W)):   # stacked barrels = walls
        for yy in range(860, H, 150):
            c.set_source_rgb(*rgb('#6a4a2c')); rrect(c, x0 + 6, yy, x1 - x0 - 12, 142, 30); c.fill()
            c.set_source_rgb(*rgb('#3c3a38')); c.rectangle(x0 + 6, yy + 26, x1 - x0 - 12, 10); c.fill(); c.rectangle(x0 + 6, yy + 106, x1 - x0 - 12, 10); c.fill()
    c.set_source_rgb(*rgb('#8a6a44')); c.rectangle(XMIN - R, GRATE, XMAX - XMIN + 2 * R, 24); c.fill()
    c.set_source_rgb(*rgb('#5e4630'))
    for x in range(int(XMIN - R), int(XMAX + R), 110): c.rectangle(x, GRATE, 4, 24); c.fill()
    for i, x in enumerate((XMIN - 20, 430, 650, XMAX - 110)):   # crates under the deck
        for j in range(4):
            yy = GRATE + 24 + j * 150
            c.set_source_rgb(*(rgb('#6e5234') if (i + j) % 2 else rgb('#7a5c3a'))); c.rectangle(x, yy, 150, 146); c.fill()
            c.set_source_rgb(*rgb('#4e3a24')); c.set_line_width(10); c.move_to(x + 8, yy + 8); c.line_to(x + 142, yy + 138); c.stroke()
            c.rectangle(x + 4, yy + 4, 142, 138); c.set_line_width(6); c.stroke()

def draw_ruler(c, f):
    ly = SL[min(f, len(SL) - 1)]; x = 1000
    if ly - GRATE < 10: return
    c.set_source_rgba(1, 1, 1, 0.6); c.set_line_width(4); c.set_dash([10, 8]); c.move_to(x, GRATE + 24); c.line_to(x, ly); c.stroke(); c.set_dash([])
    for yy in (GRATE + 24, ly): c.move_to(x - 16, yy); c.line_to(x + 16, yy); c.stroke()

PS = Particles(4)
def render(f, c):
    t = f / FPS; fi = min(f, len(GX) - 1); shake = (0, 0)
    if any(e['t'] <= t < e['t'] + 0.25 and e['a'] > 0 for e in EVS) and t < S.T_RES: shake = (rng.uniform(-3, 3), rng.uniform(-3, 3))
    c.save(); c.translate(*shake)
    draw_bg(c, t, f); draw_leaks(c, t); draw_deck(c, t)
    soaked = T_FAIL is not None and t >= T_FAIL
    if END.carried(t) or t >= END.T_GRAB: gx, gy = (END.carry_xy(t) if END.carried(t) else S.GRAB)
    elif soaked: k = ease((t - T_FAIL) / 0.35); gx = FX; gy = lerp(FY, S.GRAB[1], k) + 6 * math.sin(t * 3) * k
    else:
        gx, gy = GX[fi], GYS[fi]
        h = max(0, GRATE - R - gy); kk = 1 / (1 + h / 220)
        c.set_source_rgba(0, 0, 0, 0.3 * kk); c.save(); c.translate(gx, GRATE + 2); c.scale(R * (0.5 + 0.4 * kk), 8); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    g = GAP[fi]
    mood = 'happy' if (t >= S.T_END and S.OUTCOME == 'win') else ('scared' if soaked or g < 1.5 else 'worried')
    draw_blob(c, t, gx, gy, mood, 0, R=R, dizzy=soaked and t > T_FAIL + 0.5)
    if soaked and t > T_FAIL + 0.2:
        c.set_source_rgba(0.7, 0.88, 1, 0.85)
        for j in range(4): c.arc(gx - 36 + j * 24, gy - R * 0.2 + 30 * ((t * 1.3 + j * 0.27) % 1), 6, 0, 2 * math.pi); c.fill()
    draw_ruler(c, f)
    draw_water(c, t, f); draw_gush(c, t, f)
    if T_FAIL and abs(t - T_FAIL) < 0.5 / FPS: PS.spawn(FX, SL[fi], 24, (0.7, 0.86, 0.98), 650, 0.7, grav=2000, r=9)
    for (tl, xl, imp) in ball.landings:
        if abs(t - tl) < 0.5 / FPS and tl < S.T_RES: PS.spawn(xl, GRATE, 5, (0.55, 0.45, 0.35), 200, 0.35, grav=900, r=5)
    PS.draw(c)
    END.draw_claw(c, t)
    c.restore()
    END.header(c, t, fi)

if __name__ == '__main__':
    if sys.argv[1] == 'sim':
        rs = int(S.T_RES * FPS) - 1
        print(SEED, S.OUTCOME, round(S.T_RES - S.T_START, 2), 'mingap', round(min(GAP[int(S.T_START * FPS):rs + 1]), 2), 'final', round(GAP[rs], 2), 'gulps', len([e for e in EVS if e['a'] < 0 and e['t'] < S.T_RES]), 'dur', S.DUR); sys.exit()
    run(S, render)
