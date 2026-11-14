"""2026-11-14 v6 — NOISE – WAKE %: the SLEEPING T-REX. Gloop is a passive rigid ball (Ball) bouncing across a
natural-history museum hall at night while a giant T-Rex naps on its display stand. Every landing makes noise
proportional to the real impact speed times the floor under him (soft carpet x0.35, marble x1, creaky floorboards
x2.2, squeaky toy dinos from the gift shop x3); wall bumps add a little. Noise settles slowly when quiet.
100% = WOKEN UP -> the T-Rex wakes, roars and swats him across the hall with its tail."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the sleeping T-Rex'
SEED = int(os.environ.get('SEED', 7))
rng = random.Random(SEED)

class S: pass
S.HOOK1 = 'WILL GLOOP SNEAK PAST'; S.HOOK2 = 'THE SLEEPING T-REX?'; S.HOOK2_SIZE = 84; S.FAIL_WORD = 'WOKEN UP!'; S.FAIL_SIZE = 140
S.T_START = HOOK_T; S.TL = float(os.environ.get('TL', 12.5)); S.T_END = S.T_START + S.TL
GROUND = 1610; R = 58; XMIN, XMAX = 150, 930; WALL_L, WALL_R = XMIN - R, XMAX + R
K = 0.0058; DECAY = 9.0; WALL_N = 3.0
ZONES = []   # (x0, x1, mult, kind) — layout randomised per seed
xs = sorted(rng.sample(range(0, 5), 3))
cand = [(150, 330), (330, 480), (480, 640), (640, 790), (790, 940)]
for (a, b), (m, kind) in zip([cand[i] for i in xs], rng.sample([(0.35, 'rug'), (2.2, 'creak'), (3.0, 'pans')], 3)):
    ZONES.append((a, b, m, kind))
def zone(x):
    for (a, b, m, kind) in ZONES:
        if a <= x < b: return m, kind
    return 1.0, 'boards'

TER = Terrain(GROUND, seed=SEED, bumps=6, amp=10, soft=False)
N0 = int(40 * FPS); GX, GYS, WAKE = [], [], []
ball = Ball(rng.uniform(300, 780), TER, R=R, seed=SEED, xmin=XMIN, xmax=XMAX, hop=rng.uniform(170, 230))
wake = 0.0; T_FAIL = None; NOISES = []   # (t, x, amount, kind)
nl = nw = 0
for f in range(N0):
    t = f / FPS
    ball.step(t)
    live = T_FAIL is None and S.T_START <= t < S.T_END
    while nl < len(ball.landings):
        tl, xl, imp = ball.landings[nl]; nl += 1
        m, kind = zone(xl); d = round(K * imp * m, 1)
        if live: wake += d
        NOISES.append((tl, xl, d, kind, live))
    while nw < len(ball.walls):
        tw = ball.walls[nw]; nw += 1
        if live: wake += WALL_N
        NOISES.append((tw, ball.x, WALL_N, 'wall', live))
    if live:
        wake = max(0.0, wake - DECAY / FPS)
        if wake >= 100: wake = 100; T_FAIL = t; ball.vx = -1150 if ball.x > 540 else 1150; ball.vy = -1100; ball._pushed = True
    if T_FAIL is not None and t > T_FAIL + 0.05: ball.vmin = 0; ball.e = 0.3; ball.vx *= 0.985
    GX.append(ball.x); GYS.append(ball.y); WAKE.append(wake)
S.OUTCOME = 'fail' if T_FAIL else 'win'
S.T_RES = T_FAIL if T_FAIL else S.T_END
S.GRAB = (540, GROUND - R)
END = S.END = Ending(S)
gi = min(int(END.T_GRAB * FPS), N0 - 1); S.GRAB = (GX[gi], GYS[gi])
S.events = [[0.05, 'rumble', 0.5], [0.1, 'snore'], [2.6, 'snore']]
tt = 5.1
while tt < S.T_RES - 0.5: S.events.append([tt, 'snore']); tt += 2.5
for (tn, xn, d, kind, live) in NOISES:
    if tn > S.T_RES + 1.5: continue
    if kind == 'pans': S.events.append([tn, 'blip']); S.events.append([tn, 'pop'])
    elif kind == 'creak': S.events.append([tn, 'crackle']); S.events.append([tn, 'hop'])
    elif kind == 'rug': S.events.append([tn, 'hop'])
    elif kind == 'wall': S.events.append([tn, 'thump', 0.4])
    else: S.events.append([tn, 'noise_hit', 0.6])
if T_FAIL: S.events += [[T_FAIL, 'roar'], [T_FAIL + 0.05, 'whoosh'], [T_FAIL + 0.3, 'thump', 0.8]]
S.AMB = {'drone': 44}

def draw_bar(c, t, f):
    p = WAKE[f]; recent = any(n[0] <= t < n[0] + 0.3 and n[4] for n in NOISES)
    bx = bar(c, p / 100, f'WAKE {int(p)}%', bad_col(p / 100), 0.12 if recent else 0, bw=640, x_off=36)
    text_at(c, 'Z', bx - 52, 231, 54, rgb('#7fe0ff'), lw=8)
S.draw_bar = draw_bar

BEAR_X, BEAR_Y = 600, 1490
def draw_bear(c, t, awake_k):   # a giant green T-Rex lying asleep on its display stand
    sk, sk2, belly = rgb('#3e6a46'), rgb('#33583a'), rgb('#8aa070')
    br = (1 - awake_k) * 6 * math.sin(t * 1.7)
    c.save(); c.translate(BEAR_X, BEAR_Y - 20)
    # tail curling off to the right
    c.set_source_rgb(*sk2); c.move_to(120, -120); c.curve_to(300, -170, 420, -60, 470, 40); c.curve_to(380, -10, 300, -40, 140, 0); c.close_path(); c.fill()
    # back leg
    c.set_source_rgb(*sk2); c.save(); c.translate(140, -20); c.scale(110, 80); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    c.set_source_rgb(*rgb('#e8e0c8'))
    for k in range(3): c.move_to(60 + k * 30, 50); c.line_to(70 + k * 30, 74); c.line_to(80 + k * 30, 50); c.close_path(); c.fill()
    # body
    c.set_source_rgb(*sk); c.save(); c.translate(0, -90); c.scale(230, 120 + br); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    c.set_source_rgb(*belly); c.save(); c.translate(-30, -40); c.scale(170, 55 + br * 0.5); c.arc(0, 0, 1, 0, math.pi); c.restore(); c.fill()
    c.set_source_rgb(*sk2)   # back stripes
    for k in range(5): c.save(); c.translate(-120 + k * 60, -190 - br); c.scale(16, 28); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    # neck + head (resting on the stand while asleep, lifts when awake)
    lift = 170 * awake_k
    hx, hy = -260, -60 - lift
    c.set_source_rgb(*sk); c.move_to(-150, -170); c.curve_to(-220, -170, hx + 40, hy - 70, hx + 40, hy - 40); c.line_to(hx + 60, hy + 40); c.curve_to(-150, -20, -130, -30, -120, -30); c.close_path(); c.fill()
    c.save(); c.translate(hx, hy); c.scale(1.25, 1.25)
    c.set_source_rgb(*sk); rrect(c, -150, -70, 210, 110, 44); c.fill()   # skull
    mo = 50 * awake_k
    c.set_source_rgb(*sk2); rrect(c, -150, 20 + mo * 0.3, 190, 36, 16); c.fill()   # jaw
    if awake_k > 0.3:
        c.set_source_rgb(*rgb('#5a1a1a')); c.rectangle(-140, 20, 170, mo * 0.3 + 4); c.fill()
    c.set_source_rgb(*rgb('#f0e8c8'))
    for k in range(6): c.move_to(-140 + k * 28, 22); c.line_to(-128 + k * 28, 40 if awake_k > 0.3 else 30); c.line_to(-116 + k * 28, 22); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#1a2a1e')); c.arc(-130, -36, 7, 0, 2 * math.pi); c.fill()   # nostril
    if awake_k < 0.5:
        c.set_source_rgb(*rgb('#1a2a1e')); c.set_line_width(6); c.arc(-10, -30, 16, 0.2, math.pi - 0.2); c.stroke()
    else:
        c.set_source_rgb(*rgb('#f0c040')); c.arc(-10, -30, 16, 0, 2 * math.pi); c.fill()
        c.set_source_rgb(*rgb('#1a1008')); c.rectangle(-14, -44, 8, 28); c.fill()
    c.set_source_rgb(*sk2); c.set_line_width(8); c.move_to(-40, -54); c.line_to(16, -46); c.stroke()   # brow
    c.restore()
    # tiny arm
    c.set_source_rgb(*sk2); c.set_line_width(22); c.set_line_cap(cairo.LINE_CAP_ROUND)
    c.move_to(-170, -80); c.line_to(-200, -40 - 30 * awake_k); c.stroke(); c.set_line_cap(cairo.LINE_CAP_BUTT)
    c.restore()
    if awake_k < 0.5:
        for i in range(3):
            k = (t * 0.45 + i / 3) % 1
            text_at(c, 'Z', BEAR_X - 200 + 50 * k + 20 * math.sin(t * 2 + i), BEAR_Y - 260 - k * 240, 40 + 40 * k, rgb('#7fe0ff'), lw=6)
    elif awake_k > 0.8:
        text_at(c, 'ROAAAR!', BEAR_X, BEAR_Y - 560, 104, rgb('#ffd36b'))

def draw_bg(c, t):
    c.set_source_rgb(*rgb('#1a1a22')); c.rectangle(0, HEAD, W, H - HEAD); c.fill()
    # skylight with the moon
    c.set_source_rgb(*rgb('#1e2840')); c.rectangle(300, HEAD + 40, 480, 200); c.fill()
    c.set_source_rgb(*rgb('#e6dfc4')); c.arc(640, HEAD + 120, 36, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#2c2c36')); c.set_line_width(10)
    for x in range(300, 781, 120): c.move_to(x, HEAD + 40); c.line_to(x, HEAD + 240); c.stroke()
    c.rectangle(300, HEAD + 40, 480, 200); c.stroke()
    c.set_source_rgba(0.75, 0.8, 0.95, 0.05); c.move_to(300, HEAD + 240); c.line_to(780, HEAD + 240); c.line_to(900, 1500); c.line_to(200, 1500); c.close_path(); c.fill()
    # hall walls with framed fossils + exit sign
    c.set_source_rgb(*rgb('#24242e')); c.rectangle(0, 600, W, 900); c.fill()
    c.set_source_rgb(*rgb('#2c2c38')); c.rectangle(0, 600, W, 14); c.fill()
    for (x, y) in ((210, 760), (870, 760)):
        c.set_source_rgb(*rgb('#6a5a3a')); c.rectangle(x - 90, y - 70, 180, 140); c.fill()
        c.set_source_rgb(*rgb('#30303a')); c.rectangle(x - 76, y - 56, 152, 112); c.fill()
        c.set_source_rgb(*rgb('#9a9480')); c.set_line_width(5)
        c.arc(x, y, 34, 0, 2 * math.pi * 0.85); c.stroke(); c.arc(x, y, 18, 0, 2 * math.pi * 0.85); c.stroke()   # ammonite
    c.set_source_rgb(*rgb('#2a6a3a')); rrect(c, 480, 650, 120, 44, 6); c.fill()
    font(c, 28); c.set_source_rgb(*rgb('#c8f0c8')); c.move_to(500, 682); c.show_text('EXIT')
    # display stand + velvet rope posts
    c.set_source_rgb(*rgb('#3a3a46')); rrect(c, 140, 1420, 820, 90, 14); c.fill()
    c.set_source_rgb(*rgb('#c8a030')); rrect(c, 440, 1450, 220, 40, 6); c.fill()
    c.set_source_rgb(*rgb('#2a2a30')); font(c, 26); c.move_to(462, 1480); c.show_text('T-REX  68 MYA')

def draw_floor(c, t):
    c.move_to(0, H)
    for x in range(0, W + 1, 6): c.line_to(x, TER.h[x])
    c.line_to(W, H); c.close_path(); c.set_source_rgb(*rgb('#4a4a52')); c.fill()   # marble
    c.set_source_rgba(1, 1, 1, 0.05); c.set_line_width(3)
    for x in range(0, W, 120): c.move_to(x, GROUND + 20); c.line_to(x - 60, H); c.stroke()
    for (a, b, m, kind) in ZONES:
        if kind == 'rug':   # soft red museum carpet
            c.set_source_rgb(*rgb('#6a2a30')); c.move_to(a, TER.y(a) + 2)
            for x in range(int(a), int(b) + 1, 6): c.line_to(x, TER.y(x) + 2)
            c.line_to(b, TER.y(b) + 26); c.line_to(a, TER.y(a) + 26); c.close_path(); c.fill()
            c.set_source_rgb(*rgb('#c8a030')); c.rectangle(a, TER.y(a) + 20, b - a, 4); c.fill()
        elif kind == 'creak':   # creaky old floorboards
            c.set_source_rgb(*rgb('#6a4a30')); c.move_to(a, TER.y(a))
            for x in range(int(a), int(b) + 1, 6): c.line_to(x, TER.y(x))
            c.line_to(b, TER.y(b) + 40); c.line_to(a, TER.y(a) + 40); c.close_path(); c.fill()
            c.set_source_rgb(*rgb('#4a3220')); c.set_line_width(3)
            for x in range(int(a) + 30, int(b), 50): c.move_to(x, TER.y(x)); c.line_to(x, TER.y(x) + 40); c.stroke()
        else:   # squeaky rubber toy dinos from the gift shop
            for j, x in enumerate(range(int(a) + 22, int(b) - 12, 40)):
                y = TER.y(x) - 2; col = ('#e05a8a', '#5ab0e0', '#e0c040')[j % 3]
                c.set_source_rgb(*rgb(col)); c.save(); c.translate(x, y - 10); c.scale(18, 12); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
                c.arc(x - 16, y - 24, 8, 0, 2 * math.pi); c.fill()
                c.set_source_rgb(0.1, 0.1, 0.1); c.arc(x - 18, y - 26, 2, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#6a6a74')); c.set_line_width(4)
    for x in range(0, W + 1, 6): (c.move_to if x == 0 else c.line_to)(x, TER.h[x])
    c.stroke()
    for (x0, x1) in ((0, WALL_L), (WALL_R, W)):   # marble pillars as walls
        c.set_source_rgb(*rgb('#6a6a72')); c.rectangle(x0 - 10, 900, x1 - x0 + 20, GROUND + 40 - 900); c.fill()
        c.set_source_rgb(*rgb('#56565e'))
        for xx in range(int(x0) + 14, int(x1), 26): c.rectangle(xx, 940, 8, GROUND - 960); c.fill()
        c.set_source_rgb(*rgb('#7a7a82')); c.rectangle(x0 - 20, 880, x1 - x0 + 40, 40); c.fill()

PS = Particles(9)
def render(f, c):
    t = f / FPS; fi = min(f, len(GX) - 1); shake = (0, 0)
    if T_FAIL and T_FAIL <= t < T_FAIL + 0.4: shake = (rng.uniform(-6, 6), rng.uniform(-6, 6))
    c.save(); c.translate(*shake)
    draw_bg(c, t)
    awake = 0 if not T_FAIL or t < T_FAIL else ease((t - T_FAIL) / 0.25)
    draw_bear(c, t, awake)
    draw_floor(c, t)
    hit = T_FAIL is not None and t >= T_FAIL
    if END.carried(t) or t >= END.T_GRAB: gx, gy = (END.carry_xy(t) if END.carried(t) else S.GRAB)
    else:
        gx, gy = GX[fi], GYS[fi]
        h = max(0, TER.y(gx) - R - gy); kk = 1 / (1 + h / 220)
        c.set_source_rgba(0, 0, 0, 0.25 * kk); c.save(); c.translate(gx, TER.y(gx) + 3); c.scale(R * (0.5 + 0.4 * kk), 9); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    p = WAKE[fi] / 100
    mood = 'happy' if (t >= S.T_END and S.OUTCOME == 'win') else ('scared' if hit or p > 0.6 else 'worried')
    draw_blob(c, t, gx, gy, mood, 0, R=R, dizzy=hit and t > T_FAIL + 0.9)
    for (tn, xn, d, kind, live) in NOISES:
        if tn > S.T_RES + 0.05: break
        if tn <= t < tn + 0.5 and kind != 'rug':   # sound rings from the landing spot
            k = (t - tn) / 0.5; rr = (40 + 160 * k) * (0.6 + 0.4 * min(2, d / 6))
            c.set_source_rgba(1, 0.95, 0.8, 0.45 * (1 - k)); c.set_line_width(5)
            c.save(); c.translate(xn, TER.y(xn) - 10); c.scale(1, 0.5); c.arc(0, 0, rr, math.pi, 2 * math.pi); c.restore(); c.stroke()
        if live and tn <= t < tn + 0.8 and d >= 9:
            k = (t - tn) / 0.8; text_at(c, f'+{d:.0f}%', xn, TER.y(xn) - 430 - 60 * k, 58, rgb('#ffb347'))
    if T_FAIL and T_FAIL <= t < T_FAIL + 0.35:   # big paw swipe
        k = (t - T_FAIL) / 0.35; px = lerp(BEAR_X + 250, GX[int(T_FAIL * FPS)], k)
        c.set_source_rgb(*rgb('#33583a')); c.set_line_width(70); c.set_line_cap(cairo.LINE_CAP_ROUND)
        c.move_to(BEAR_X + 300, GROUND - 120); c.curve_to(BEAR_X + 200, GROUND - 40, px + 120, GROUND - 60, px, GROUND - 90); c.stroke(); c.set_line_cap(cairo.LINE_CAP_BUTT)
    PS.draw(c)
    END.draw_claw(c, t)
    c.restore()
    END.header(c, t, fi)

if __name__ == '__main__':
    if sys.argv[1] == 'sim':
        e = int(S.T_RES * FPS) - 1
        print(SEED, S.OUTCOME, round(S.T_RES - S.T_START, 2), 'peak', round(max(WAKE[:e + 1])), 'final', round(WAKE[e]), [z[3] for z in ZONES], 'dur', S.DUR); sys.exit()
    run(S, render)
