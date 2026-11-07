"""2026-11-07 v5 — RISING DANGER – CHOCOLATE GAP m: the CHOCOLATE FLOOD. Inside a candy factory at night a
broken mixing vat floods the floor with melted chocolate. Gloop is a passive rigid ball (Ball) bouncing on
a steel catwalk on support legs, between two stacks of cocoa sacks (walls). Chocolate rises from frame 0
at a seeded-random rate: wall pipes burst and gush (surges) and a drain pump sometimes gulps it back.
CHOCOLATE GAP = distance from the surface up to the catwalk. If the chocolate touches Gloop he's dunked =
fail (floats dizzy, coated). Timer ends first = win."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the chocolate flood'
SEED = int(os.environ.get('SEED', 13))
rng = random.Random(SEED)

class S: pass
S.HOOK2 = 'THE CHOCOLATE FLOOD?'; S.HOOK2_SIZE = 84; S.FAIL_WORD = 'DUNKED!'; S.FAIL_SIZE = 150
S.T_START = HOOK_T; S.TL = 13.5; S.T_END = S.T_START + S.TL
GRATE = 1270; R = 58; XMIN, XMAX = 190, 890; PXM = 100.0
SL0 = 1880; BASE = float(os.environ.get('BASE', 18))

EVS = []; t = rng.uniform(0.0, 0.4)   # pipe surges (+) and drain gulps (-)
while t < S.T_END + 1:
    gulp = rng.random() < 0.3
    EVS.append({'t': t, 'd': rng.uniform(0.8, 1.6), 'a': (-rng.uniform(25, 45) if gulp else rng.uniform(30, 75)), 'pipe': rng.randrange(3)})
    t += rng.uniform(1.0, 2.2)
PIPES = [(300, 820), (790, 760), (560, 980)]   # burst pipe joints (x, y) on the back wall

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
S.events = [[0.05, 'rumble', 1.2], [0.3, 'clank' if False else 'creak']]
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
    bx = bar(c, g / 6.0, f'CHOCOLATE GAP {g:.1f} m', good_bad_col(g / 4.0), 0.12 if surge else 0, bw=640, x_off=36)
    c.save(); c.translate(bx - 52, 231); c.set_source_rgb(*rgb('#8a5230'))
    c.move_to(0, -28); c.curve_to(10, -10, 24, 2, 24, 12); c.curve_to(24, 26, 12, 32, 0, 32); c.curve_to(-12, 32, -24, 26, -24, 12); c.curve_to(-24, 2, -10, -10, 0, -28); c.fill()
    c.set_source_rgba(1, 1, 1, 0.6); c.arc(-8, 12, 6, 0, 2 * math.pi); c.fill(); c.restore()
S.draw_bar = draw_bar

def draw_bg(c, t, f):
    c.set_source_rgb(*rgb('#1e1a1e')); c.rectangle(0, HEAD, W, H - HEAD); c.fill()
    c.set_source_rgb(*rgb('#262028'))   # wall panels
    for x in range(0, W, 200): c.rectangle(x + 10, HEAD + 120, 180, H - HEAD); c.fill()
    # big factory window with moon
    c.set_source_rgb(*rgb('#3a3440')); c.rectangle(250, 430, 580, 300); c.fill()
    c.set_source_rgb(*rgb('#16203a')); c.rectangle(266, 446, 548, 268); c.fill()
    c.set_source_rgba(0.9, 0.9, 0.8, 0.8); c.arc(700, 520, 28, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#3a3440')); c.set_line_width(10)
    for x in (400, 540, 680): c.move_to(x, 446); c.line_to(x, 714); c.stroke()
    c.move_to(266, 580); c.line_to(814, 580); c.stroke()
    # wall pipes running across
    c.set_source_rgb(*rgb('#5a5560')); c.rectangle(0, 790, W, 30); c.rectangle(0, 965, W, 30); c.fill()
    c.rectangle(285, 740, 30, 100); c.rectangle(775, 700, 30, 80); c.fill()
    # sign
    c.set_source_rgb(*rgb('#6a3a2a')); rrect(c, 380, HEAD + 40, 320, 70, 12); c.fill()
    font(c, 40); c.set_source_rgb(*rgb('#f0d0a0')); e = c.text_extents('CANDY CO.'); c.move_to(540 - e.width / 2 - e.x_bearing, HEAD + 90); c.show_text('CANDY CO.')

def draw_gush(c, t, f):
    for e in EVS:
        if e['a'] > 0 and e['t'] <= t < e['t'] + e['d'] and (e['t'] < S.T_RES or e['t'] < S.T_START):
            px, py = PIPES[e['pipe']]; k = min(1, (t - e['t']) / 0.2, (e['t'] + e['d'] - t) / 0.2)
            ly = SL[min(f, len(SL) - 1)]; dirx = 1 if px < 540 else -1
            c.set_line_cap(cairo.LINE_CAP_ROUND)
            for wdt, col in ((46, (0.36, 0.2, 0.12, 0.95)), (20, (0.52, 0.32, 0.2, 0.95))):
                c.set_source_rgba(*col); c.set_line_width(wdt * k)
                c.move_to(px, py); c.curve_to(px + dirx * 70, py, px + dirx * 100, py + 80, px + dirx * 110, ly + 10); c.stroke()
            for j in range(5):
                q = (t * 2.4 + j / 5) % 1; dx_ = px + dirx * 110 * min(1, q * 3); dy_ = lerp(py, ly, q * q)
                c.set_source_rgba(0.45, 0.27, 0.16, 0.9 * k); c.arc(dx_ + 10 * math.sin(j * 2.3), dy_, 7, 0, 2 * math.pi); c.fill()
            c.set_source_rgba(0.5, 0.3, 0.18, 0.9 * k)
            for j in range(4): c.arc(px + dirx * 110 + (j - 1.5) * 26, ly - 8 - 20 * abs(math.sin(t * 9 + j)), 9, 0, 2 * math.pi); c.fill()
        if e['a'] < 0 and e['t'] <= t < e['t'] + e['d'] and e['t'] < S.T_RES:   # bilge pump gulp: swirl around the hose
            ly = SL[min(f, len(SL) - 1)]; c.set_source_rgba(0.62, 0.42, 0.28, 0.6); c.set_line_width(5)
            for j in range(3): c.save(); c.translate(760, ly + 30); c.scale(1, 0.3); c.arc(0, 0, 50 + j * 45, t * 6 + j, t * 6 + j + 4); c.restore(); c.stroke()

def draw_leaks(c, t):
    for i, (px, py) in enumerate(PIPES):   # cracked pipe joints, dripping chocolate
        c.set_source_rgb(*rgb('#6a6570')); rrect(c, px - 34, py - 30, 68, 60, 10); c.fill()
        c.set_source_rgb(*rgb('#2a1a14')); c.move_to(px - 20, py - 6); c.line_to(px - 4, py + 2); c.line_to(px + 6, py - 10); c.line_to(px + 22, py + 4); c.stroke()
        c.set_source_rgb(*rgb('#c83a3a')); c.arc(px + 20, py - 26, 8, 0, 2 * math.pi); c.fill()   # valve
        q = (t * 1.2 + i * 0.37) % 1; c.set_source_rgba(0.42, 0.25, 0.15, 0.9 * (1 - q)); c.arc(px, py + 34 + q * 120, 6, 0, 2 * math.pi); c.fill()

def choc_surf(x, t, ly): return ly + 7 * math.sin(x * 0.012 + t * 1.2) + 4 * math.sin(x * 0.04 - t * 1.7)
def draw_water(c, t, f):
    ly = SL[min(f, len(SL) - 1)]
    c.move_to(0, H)
    for x in range(0, W + 20, 20): c.line_to(x, choc_surf(x, t, ly))
    c.line_to(W, H); c.close_path(); c.set_source_rgba(0.36, 0.21, 0.13, 0.97); c.fill()
    c.set_source_rgba(0.28, 0.16, 0.1, 1); c.rectangle(0, ly + 60, W, H - ly); c.fill()
    c.set_source_rgba(0.62, 0.42, 0.28, 0.6); c.set_line_width(5)
    for x in range(0, W + 20, 20): (c.move_to if x == 0 else c.line_to)(x, choc_surf(x, t, ly))
    c.stroke()
    c.set_source_rgba(0.7, 0.5, 0.35, 0.35); c.set_line_width(4)   # slow swirls
    for j in range(4):
        c.save(); c.translate(150 + j * 260, ly + 50); c.scale(1, 0.25); c.arc(0, 0, 50, t * 0.8 + j, t * 0.8 + j + 3.5); c.restore(); c.stroke()
    # drain pump hose dipping into the chocolate
    c.set_source_rgb(*rgb('#2b2b2e')); c.set_line_width(22); c.set_line_cap(cairo.LINE_CAP_ROUND); c.move_to(780, HEAD + 86); c.curve_to(800, 700, 700, 900, 760, max(ly + 40, 960)); c.stroke()

def draw_deck(c, t):
    for (x0, x1) in ((0, XMIN - R), (XMAX + R, W)):   # stacked cocoa sacks = walls
        for j, yy in enumerate(range(860, H, 120)):
            c.set_source_rgb(*(rgb('#8a7458') if j % 2 else rgb('#7a6448'))); rrect(c, x0 + 4, yy, x1 - x0 - 8, 116, 40); c.fill()
            c.set_source_rgb(*rgb('#5a3a24')); font(c, 26); e = c.text_extents('COCOA'); c.move_to((x0 + x1) / 2 - e.width / 2 - e.x_bearing, yy + 70); c.show_text('COCOA')
    c.set_source_rgb(*rgb('#7a808c')); c.rectangle(XMIN - R, GRATE, XMAX - XMIN + 2 * R, 24); c.fill()   # steel catwalk
    c.set_source_rgb(*rgb('#5a606c'))
    for x in range(int(XMIN - R), int(XMAX + R), 40): c.rectangle(x, GRATE + 4, 20, 16); c.fill()
    c.set_source_rgb(*rgb('#8a909c')); c.set_line_width(5)
    c.move_to(XMIN - R, GRATE - 70); c.line_to(XMAX + R, GRATE - 70); c.stroke()   # railing (behind)
    for x in range(int(XMIN - R) + 20, int(XMAX + R), 140): c.move_to(x, GRATE - 70); c.line_to(x, GRATE); c.stroke()
    c.set_source_rgb(*rgb('#4a4e58'))
    for x in (XMIN + 20, 450, 680, XMAX - 60): c.rectangle(x, GRATE + 24, 26, H - GRATE); c.fill()   # legs
    c.set_line_width(8)
    for x in (XMIN + 20, 450, 680):
        c.move_to(x + 13, GRATE + 40); c.line_to(x + 13 + (230 if x != 680 else XMAX - 60 - 680), GRATE + 300); c.stroke()

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
        c.set_source_rgba(0.4, 0.23, 0.14, 0.95)
        for j in range(4): c.arc(gx - 36 + j * 24, gy - R * 0.2 + 30 * ((t * 1.3 + j * 0.27) % 1), 6, 0, 2 * math.pi); c.fill()
    draw_ruler(c, f)
    draw_water(c, t, f); draw_gush(c, t, f)
    if T_FAIL and abs(t - T_FAIL) < 0.5 / FPS: PS.spawn(FX, SL[fi], 24, (0.42, 0.25, 0.15), 650, 0.7, grav=2000, r=9)
    for (tl, xl, imp) in ball.landings:
        if abs(t - tl) < 0.5 / FPS and tl < S.T_RES: PS.spawn(xl, GRATE, 5, (0.6, 0.62, 0.66), 200, 0.35, grav=900, r=4)
    PS.draw(c)
    END.draw_claw(c, t)
    c.restore()
    END.header(c, t, fi)

if __name__ == '__main__':
    if sys.argv[1] == 'sim':
        rs = int(S.T_RES * FPS) - 1
        print(SEED, S.OUTCOME, round(S.T_RES - S.T_START, 2), 'mingap', round(min(GAP[int(S.T_START * FPS):rs + 1]), 2), 'final', round(GAP[rs], 2), 'gulps', len([e for e in EVS if e['a'] < 0 and e['t'] < S.T_RES]), 'dur', S.DUR); sys.exit()
    run(S, render)
