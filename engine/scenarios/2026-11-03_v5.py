"""2026-11-03 v5 — RISING DANGER – SLIME GAP m: the RISING SLIME in a sewer. Gloop is a passive rigid
ball (Ball) bouncing on a rusty grate walkway between two brick pillars. Toxic slime rises up the shaft
from frame 0 at a seeded-random rate: pipes gush (surges) and the drain sometimes gulps (it drops
back). SLIME GAP = distance from the slime surface up to the grate. If the slime touches Gloop
(at a landing or anywhere) he's slimed = fail. Timer ends before it reaches him = win."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the rising slime'
SEED = int(os.environ.get('SEED', 16))
rng = random.Random(SEED)

class S: pass
S.HOOK2 = 'THE RISING SLIME?'; S.HOOK2_SIZE = 90; S.FAIL_WORD = 'SLIMED!'; S.FAIL_SIZE = 150
S.T_START = HOOK_T; S.TL = 13.0; S.T_END = S.T_START + S.TL
GRATE = 1270; R = 58; XMIN, XMAX = 190, 890; PXM = 100.0
SL0 = 1880; BASE = float(os.environ.get('BASE', 16))

EVS = []; t = rng.uniform(0.0, 0.4)   # pipe surges (+) and drain gulps (-)
while t < S.T_END + 1:
    gulp = rng.random() < 0.3
    EVS.append({'t': t, 'd': rng.uniform(0.8, 1.6), 'a': (-rng.uniform(25, 45) if gulp else rng.uniform(30, 75)), 'pipe': rng.randrange(3)})
    t += rng.uniform(1.0, 2.2)
PIPES = [(66, 820), (1014, 860), (66, 1010)]   # outlet positions (x, y) on the back wall

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
S.events = [[0.05, 'rumble', 1.2]]
for e in EVS:
    if e['t'] < S.T_RES: S.events.append([e['t'], 'splash' if e['a'] > 0 else 'whoosh']); S.events.append([e['t'], 'rumble', min(e['d'], 1.2)])
for (tl, xl, imp) in ball.landings:
    if tl < S.T_RES: S.events.append([tl, 'clink' if tl > S.T_START and (tl * 7) % 1 < 0.3 else 'hop'])
for tw in ball.walls:
    if tw < S.T_RES: S.events.append([tw, 'thump', 0.35])
if T_FAIL: S.events += [[T_FAIL, 'splash'], [T_FAIL + 0.1, 'pop'], [T_FAIL + 0.5, 'sizzle']]
S.AMB = {'drone': 42, 'rumble': 0.03}

def draw_bar(c, t, f):
    g = GAP[f]; surge = any(e['t'] <= t < e['t'] + e['d'] and e['a'] > 0 for e in EVS)
    bx = bar(c, g / 6.0, f'SLIME GAP {g:.1f} m', good_bad_col(g / 4.0), 0.12 if surge else 0, bw=640, x_off=36)
    c.save(); c.translate(bx - 52, 231); c.set_source_rgb(*rgb('#8fd14f'))
    c.move_to(-24, 22); c.curve_to(-28, -4, -6, -6, 0, -28); c.curve_to(6, -6, 28, -4, 24, 22); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#5a8f2a')); c.arc(-6, 8, 6, 0, 2 * math.pi); c.fill(); c.restore()
S.draw_bar = draw_bar

def draw_bg(c, t):
    c.set_source_rgb(*rgb('#171a1c')); c.rectangle(0, HEAD, W, H - HEAD); c.fill()
    c.set_source_rgb(*rgb('#1e2224'))
    for row, yy in enumerate(range(HEAD, H, 70)):   # flat brick courses
        off = 0 if row % 2 else 70
        for x in range(-off, W, 140): rrect(c, x + 4, yy + 4, 132, 62, 6); c.fill()
    c.set_source_rgb(*rgb('#111314')); c.move_to(240, 1270); c.line_to(240, 820); c.curve_to(240, 560, 840, 560, 840, 820); c.line_to(840, 1270); c.close_path(); c.fill()   # tunnel arch
    c.set_source_rgba(0.75, 0.85, 0.6, 0.08); c.arc(540, 450, 160, 0, 2 * math.pi); c.fill()   # light from a manhole above
    c.set_source_rgb(*rgb('#2a2f31')); c.rectangle(460, HEAD, 160, 30); c.fill()

def draw_gush(c, t, f):
    for e in EVS:
        if e['a'] > 0 and e['t'] <= t < e['t'] + e['d'] and (e['t'] < S.T_RES or e['t'] < S.T_START):
            px, py = PIPES[e['pipe']]; k = min(1, (t - e['t']) / 0.2, (e['t'] + e['d'] - t) / 0.2)
            ly = SL[min(f, len(SL) - 1)]; dirx = 1 if px < 540 else -1
            c.set_line_cap(cairo.LINE_CAP_ROUND)
            for wdt, col in ((58, (0.45, 0.72, 0.22, 0.9)), (28, (0.65, 0.9, 0.4, 0.9))):
                c.set_source_rgba(*col); c.set_line_width(wdt * k)
                c.move_to(px, py); c.curve_to(px + dirx * 40, py, px + dirx * 50, py + 60, px + dirx * 50, ly + 10); c.stroke()
            for j in range(5):   # drips riding the stream
                q = (t * 2.2 + j / 5) % 1; dx_ = px + dirx * 50 * min(1, q * 4); dy_ = lerp(py, ly, q * q)
                c.set_source_rgba(0.7, 0.92, 0.45, 0.9 * k); c.arc(dx_ + 10 * math.sin(j * 2.3), dy_, 9, 0, 2 * math.pi); c.fill()
            c.set_source_rgba(0.65, 0.9, 0.4, 0.7 * k)
            for j in range(4): c.arc(px + dirx * 50 + (j - 1.5) * 26, ly - 10 - 20 * abs(math.sin(t * 9 + j)), 10, 0, 2 * math.pi); c.fill()
        if e['a'] < 0 and e['t'] <= t < e['t'] + e['d'] and e['t'] < S.T_RES:   # drain gulp: swirl on the surface
            ly = SL[min(f, len(SL) - 1)]; c.set_source_rgba(0.2, 0.35, 0.1, 0.8); c.set_line_width(6)
            for j in range(3): c.save(); c.translate(540, ly + 30); c.scale(1, 0.3); c.arc(0, 0, 60 + j * 50, t * 6 + j, t * 6 + j + 4); c.restore(); c.stroke()

def draw_slime(c, t, f):
    ly = SL[min(f, len(SL) - 1)]
    c.move_to(0, H)
    for x in range(0, W + 20, 20): c.line_to(x, ly + 9 * math.sin(x * 0.018 + t * 2.0) + 5 * math.sin(x * 0.05 - t * 2.7))
    c.line_to(W, H); c.close_path(); c.set_source_rgb(*rgb('#5f9a2c')); c.fill()
    c.set_source_rgb(*rgb('#4c7f22')); c.rectangle(0, ly + 40, W, H - ly); c.fill()
    for i in range(6):   # popping bubbles
        k = (t * 0.9 + i * 0.29) % 1; bx = (i * 191 + 70) % W
        c.set_source_rgba(0.7, 0.92, 0.45, 0.9 * (1 - k)); c.set_line_width(4); c.arc(bx, ly + 20 - k * 16, 8 + 14 * k, math.pi, 2 * math.pi); c.stroke()

def draw_grate(c, t):
    for (x0, x1) in ((0, XMIN - R), (XMAX + R, W)):   # brick pillars = walls
        c.set_source_rgb(*rgb('#3a3230')); c.rectangle(x0, 900, x1 - x0, H - 900); c.fill()
        c.set_source_rgb(*rgb('#2c2523'))
        for yy in range(900, H, 60): c.rectangle(x0, yy, x1 - x0, 6); c.fill()
    c.set_source_rgb(*rgb('#5a4a3e')); c.rectangle(XMIN - R, GRATE, XMAX - XMIN + 2 * R, 22); c.fill()
    c.set_source_rgb(*rgb('#2a221e'))
    for x in range(int(XMIN - R) + 14, int(XMAX + R) - 10, 34): c.rectangle(x, GRATE + 5, 16, 12); c.fill()
    c.set_source_rgb(*rgb('#4a3d33'))
    for x in (XMIN + 60, 540, XMAX - 60): c.rectangle(x - 10, GRATE + 22, 20, 120); c.fill()   # supports
    for (px, py) in PIPES:
        c.set_source_rgb(*rgb('#3b4246')); c.arc(px, py, 52, 0, 2 * math.pi); c.fill()
        c.set_source_rgb(*rgb('#0c0e0f')); c.arc(px, py, 36, 0, 2 * math.pi); c.fill()

def draw_ruler(c, f):
    ly = SL[min(f, len(SL) - 1)]; x = 970
    if ly - GRATE < 10: return
    c.set_source_rgba(1, 1, 1, 0.6); c.set_line_width(4); c.set_dash([10, 8]); c.move_to(x, GRATE + 22); c.line_to(x, ly); c.stroke(); c.set_dash([])
    for yy in (GRATE + 22, ly): c.move_to(x - 16, yy); c.line_to(x + 16, yy); c.stroke()

PS = Particles(4)
def render(f, c):
    t = f / FPS; fi = min(f, len(GX) - 1); shake = (0, 0)
    if any(e['t'] <= t < e['t'] + 0.25 and e['a'] > 0 for e in EVS) and t < S.T_RES: shake = (rng.uniform(-3, 3), rng.uniform(-3, 3))
    c.save(); c.translate(*shake)
    draw_bg(c, t); draw_grate(c, t)
    slimed = T_FAIL is not None and t >= T_FAIL
    if END.carried(t) or t >= END.T_GRAB: gx, gy = (END.carry_xy(t) if END.carried(t) else S.GRAB)
    elif slimed: k = ease((t - T_FAIL) / 0.35); gx = FX; gy = lerp(FY, S.GRAB[1], k) + 5 * math.sin(t * 3) * k
    else:
        gx, gy = GX[fi], GYS[fi]
        h = max(0, GRATE - R - gy); kk = 1 / (1 + h / 220)
        c.set_source_rgba(0, 0, 0, 0.3 * kk); c.save(); c.translate(gx, GRATE + 2); c.scale(R * (0.5 + 0.4 * kk), 8); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    g = GAP[fi]
    mood = 'happy' if (t >= S.T_END and S.OUTCOME == 'win') else ('scared' if slimed or g < 1.5 else 'worried')
    skin = ('#d8f07a', '#8fc43c', '#4a7a1f') if slimed and t > T_FAIL + 0.2 else ('#ffd36b', '#ff8a1f', '#c45a00')
    draw_blob(c, t, gx, gy, mood, 0, R=R, skin=skin, dizzy=slimed and t > T_FAIL + 0.5)
    if slimed and t > T_FAIL + 0.2:
        c.set_source_rgba(0.55, 0.82, 0.3, 0.85)
        for j in range(4): c.arc(gx - 36 + j * 24, gy + R * 0.6 + 14 * ((t * 1.3 + j * 0.27) % 1), 7, 0, 2 * math.pi); c.fill()
    draw_ruler(c, f)
    draw_slime(c, t, f); draw_gush(c, t, f)
    if T_FAIL and abs(t - T_FAIL) < 0.5 / FPS: PS.spawn(FX, SL[fi], 22, (0.55, 0.82, 0.3), 600, 0.7, grav=2000, r=9)
    for (tl, xl, imp) in ball.landings:
        if abs(t - tl) < 0.5 / FPS and tl < S.T_RES: PS.spawn(xl, GRATE, 5, (0.45, 0.4, 0.35), 200, 0.35, grav=900, r=5)
    PS.draw(c)
    END.draw_claw(c, t)
    c.restore()
    END.header(c, t, fi)

if __name__ == '__main__':
    if sys.argv[1] == 'sim':
        rs = int(S.T_RES * FPS) - 1
        print(SEED, S.OUTCOME, round(S.T_RES - S.T_START, 2), 'mingap', round(min(GAP[int(S.T_START * FPS):rs + 1]), 2), 'final', round(GAP[rs], 2), 'gulps', len([e for e in EVS if e['a'] < 0 and e['t'] < S.T_RES]), 'dur', S.DUR); sys.exit()
    run(S, render)
