"""2026-11-14 v2 — RISING DANGER – PAINT GAP m: the PAINT FLOOD. In a paint factory at night the mixing tanks
burst. Gloop is a passive rigid ball (Ball) bouncing on a steel catwalk between two stacks of paint cans (walls).
Purple paint rises from frame 0 at a seeded-random rate: nozzles on the back wall gush (surges) and a floor
drain sometimes gulps it back. PAINT GAP = distance from the surface up to the catwalk. If the paint touches
Gloop he's swept off = fail (covered in purple paint & dizzy, claw collects him)."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the paint flood'
SEED = int(os.environ.get('SEED', 11))
rng = random.Random(SEED)

class S: pass
S.HOOK2 = 'THE PAINT FLOOD?'; S.HOOK2_SIZE = 92; S.FAIL_WORD = 'SPLAT!'; S.FAIL_SIZE = 150
S.T_START = HOOK_T; S.TL = float(os.environ.get('TL', 13.0)); S.T_END = S.T_START + S.TL
GRATE = 1270; R = 58; XMIN, XMAX = 190, 890; PXM = 100.0
SL0 = 1880; BASE = float(os.environ.get('BASE', 18))

EVS = []; t = rng.uniform(0.0, 0.4)   # pipe surges (+) and drain gulps (-)
while t < S.T_END + 1:
    gulp = rng.random() < 0.3
    EVS.append({'t': t, 'd': rng.uniform(0.8, 1.6), 'a': (-rng.uniform(25, 45) if gulp else rng.uniform(30, 75)), 'pipe': rng.randrange(3)})
    t += rng.uniform(1.0, 2.2)
PIPES = [(300, 820), (790, 760), (560, 1000)]   # outflow pipes (x, y) on the back wall

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
    if tl < S.T_RES: S.events.append([tl, 'hop'])
for tw in ball.walls:
    if tw < S.T_RES: S.events.append([tw, 'thump', 0.35])
if T_FAIL: S.events += [[T_FAIL, 'splash'], [T_FAIL + 0.1, 'pop'], [T_FAIL + 0.4, 'splash']]
S.AMB = {'drone': 46, 'rumble': 0.03}
for e in EVS:
    if e['a'] > 0 and e['t'] < S.T_RES: S.events.append([max(0, e['t'] - 0.15), 'creak'])

def draw_bar(c, t, f):
    g = GAP[f]; surge = any(e['t'] <= t < e['t'] + e['d'] and e['a'] > 0 for e in EVS)
    bx = bar(c, g / 6.0, f'PAINT GAP {g:.1f} m', good_bad_col(g / 4.0), 0.12 if surge else 0, bw=640, x_off=36)
    c.save(); c.translate(bx - 52, 231); c.set_source_rgb(*rgb('#a070e0'))
    c.move_to(0, -28); c.curve_to(10, -10, 24, 2, 24, 12); c.curve_to(24, 26, 12, 32, 0, 32); c.curve_to(-12, 32, -24, 26, -24, 12); c.curve_to(-24, 2, -10, -10, 0, -28); c.fill()
    c.set_source_rgba(1, 1, 1, 0.6); c.arc(-8, 12, 6, 0, 2 * math.pi); c.fill(); c.restore()
S.draw_bar = draw_bar

CANCOL = ['#b04848', '#4870b0', '#c8a030', '#489070', '#a070e0']
def draw_bg(c, t, f):
    # factory back wall: corrugated panels, big mixing tanks, shelves of paint cans
    c.set_source_rgb(*rgb('#22232a')); c.rectangle(0, HEAD, W, H - HEAD); c.fill()
    c.set_source_rgb(*rgb('#1c1d23'))
    for xx in range(0, W, 36): c.rectangle(xx, HEAD, 6, H - HEAD); c.fill()
    for (cx, w_) in ((300, 300), (790, 260)):   # mixing tanks
        c.set_source_rgb(*rgb('#3a3c46')); c.rectangle(cx - w_ / 2, 520, w_, 600); c.fill()
        c.save(); c.translate(cx, 520); c.scale(w_ / 2, 40); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.set_source_rgb(*rgb('#4a4c58')); c.fill()
        c.set_source_rgb(*rgb('#2c2e36'))
        for yy in (640, 820, 1000): c.rectangle(cx - w_ / 2, yy, w_, 10); c.fill()
        c.set_source_rgb(*rgb('#6a4a90')); c.rectangle(cx - w_ / 2 + 30, 880, w_ - 60, 70); c.fill()
        c.set_source_rgb(*rgb('#22232a')); font(c, 40); c.move_to(cx - 56, 930); c.show_text('PAINT')
    c.set_source_rgba(0.85, 0.85, 1, 0.05); c.move_to(470, HEAD); c.line_to(610, HEAD); c.line_to(700, 1250); c.line_to(400, 1250); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#3a3c46')); c.rectangle(460, HEAD, 160, 20); c.fill()

def draw_gush(c, t, f):
    for e in EVS:
        if e['a'] > 0 and e['t'] <= t < e['t'] + e['d'] and (e['t'] < S.T_RES or e['t'] < S.T_START):
            px, py = PIPES[e['pipe']]; k = min(1, (t - e['t']) / 0.2, (e['t'] + e['d'] - t) / 0.2)
            ly = SL[min(f, len(SL) - 1)]; dirx = 1 if px < 540 else -1
            c.set_line_cap(cairo.LINE_CAP_ROUND)
            for wdt, col in ((46, (0.42, 0.24, 0.62, 0.95)), (20, (0.62, 0.42, 0.85, 0.95))):
                c.set_source_rgba(*col); c.set_line_width(wdt * k)
                c.move_to(px, py); c.curve_to(px + dirx * 70, py, px + dirx * 100, py + 80, px + dirx * 110, ly + 10); c.stroke()
            for j in range(5):
                q = (t * 2.4 + j / 5) % 1; dx_ = px + dirx * 110 * min(1, q * 3); dy_ = lerp(py, ly, q * q)
                c.set_source_rgba(0.62, 0.42, 0.85, 0.9 * k); c.arc(dx_ + 10 * math.sin(j * 2.3), dy_, 7, 0, 2 * math.pi); c.fill()
            c.set_source_rgba(0.7, 0.52, 0.9, 0.9 * k)
            for j in range(4): c.arc(px + dirx * 110 + (j - 1.5) * 26, ly - 8 - 20 * abs(math.sin(t * 9 + j)), 9, 0, 2 * math.pi); c.fill()
        if e['a'] < 0 and e['t'] <= t < e['t'] + e['d'] and e['t'] < S.T_RES:   # bilge pump gulp: swirl around the hose
            ly = SL[min(f, len(SL) - 1)]; c.set_source_rgba(0.8, 0.65, 0.95, 0.6); c.set_line_width(5)
            for j in range(3): c.save(); c.translate(560, ly + 30); c.scale(1, 0.3); c.arc(0, 0, 50 + j * 45, t * 6 + j, t * 6 + j + 4); c.restore(); c.stroke()

def draw_leaks(c, t):
    for i, (px, py) in enumerate(PIPES):   # outflow pipes sticking out of the wall, dripping
        dirx = 1 if px < 540 else -1
        c.set_source_rgb(*rgb('#4a4e56')); c.save(); c.translate(px, py); c.scale(56, 56); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
        c.set_source_rgb(*rgb('#5a5e68')); c.save(); c.translate(px, py); c.scale(46, 46); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
        c.set_source_rgb(*rgb('#14161a')); c.arc(px, py, 34, 0, 2 * math.pi); c.fill()
        c.set_source_rgba(0.55, 0.38, 0.8, 0.8); c.rectangle(px - 10, py + 30, 20, 50); c.fill()
        q = (t * 1.0 + i * 0.37) % 1; c.set_source_rgba(0.62, 0.42, 0.85, 0.9 * (1 - q)); c.arc(px, py + 40 + q * 120, 7, 0, 2 * math.pi); c.fill()

def choc_surf(x, t, ly): return ly + 7 * math.sin(x * 0.012 + t * 1.2) + 4 * math.sin(x * 0.04 - t * 1.7)
def draw_water(c, t, f):
    ly = SL[min(f, len(SL) - 1)]
    c.move_to(0, H)
    for x in range(0, W + 20, 20): c.line_to(x, choc_surf(x, t, ly))
    c.line_to(W, H); c.close_path(); c.set_source_rgba(0.4, 0.22, 0.6, 0.97); c.fill()
    c.set_source_rgba(0.32, 0.17, 0.5, 1); c.rectangle(0, ly + 60, W, H - ly); c.fill()
    c.set_source_rgba(0.78, 0.6, 0.95, 0.75); c.set_line_width(5)
    for x in range(0, W + 20, 20): (c.move_to if x == 0 else c.line_to)(x, choc_surf(x, t, ly))
    c.stroke()
    c.set_source_rgba(0.78, 0.6, 0.95, 0.3); c.set_line_width(4)   # slow swirls
    for j in range(4):
        c.save(); c.translate(150 + j * 260, ly + 50); c.scale(1, 0.25); c.arc(0, 0, 50, t * 0.8 + j, t * 0.8 + j + 3.5); c.restore(); c.stroke()

def draw_deck(c, t):
    for (x0, x1) in ((0, XMIN - R), (XMAX + R, W)):   # stacks of paint cans = walls
        c.set_source_rgb(*rgb('#2a2b32')); c.rectangle(x0, 760, x1 - x0, H - 760); c.fill()
        for k, yy in enumerate(range(760, H, 110)):
            col = CANCOL[(k + (x0 > 0) * 2) % 5]
            c.set_source_rgb(*rgb('#8a8e98')); rrect(c, x0 + 6, yy + 6, x1 - x0 - 12, 100, 8); c.fill()
            c.set_source_rgb(*rgb(col)); c.rectangle(x0 + 6, yy + 36, x1 - x0 - 12, 44); c.fill()
            c.set_source_rgb(*rgb('#6a6e78')); c.rectangle(x0 + 6, yy + 6, x1 - x0 - 12, 10); c.fill()
    c.set_source_rgb(*rgb('#6a7080')); c.rectangle(XMIN - R, GRATE, XMAX - XMIN + 2 * R, 26); c.fill()   # steel catwalk
    c.set_source_rgb(*rgb('#3e424c'))
    for x in range(int(XMIN - R) + 10, int(XMAX + R), 30): c.rectangle(x, GRATE + 6, 16, 14); c.fill()
    c.set_source_rgb(*rgb('#4a4e58')); c.set_line_width(10)
    for x in (XMIN + 20, 450, 680, XMAX - 40):   # steel legs
        c.move_to(x, GRATE + 26); c.line_to(x, H); c.stroke()
    c.set_line_width(6)
    for x in (XMIN + 20, 450, 680): c.move_to(x, GRATE + 60); c.line_to(x + 120, GRATE + 300); c.stroke()

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
        c.set_source_rgba(0.6, 0.4, 0.85, 0.95)
        for j in range(4): c.arc(gx - 36 + j * 24, gy - R * 0.2 + 30 * ((t * 1.3 + j * 0.27) % 1), 6, 0, 2 * math.pi); c.fill()
    draw_ruler(c, f)
    draw_water(c, t, f); draw_gush(c, t, f)
    if T_FAIL and abs(t - T_FAIL) < 0.5 / FPS: PS.spawn(FX, SL[fi], 24, (0.6, 0.4, 0.85), 650, 0.7, grav=2000, r=9)
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
