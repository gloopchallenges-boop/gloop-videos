"""2026-11-02 v8 — NOISE – WAKE %: the SLEEPING BEAR. Gloop is a passive rigid ball (Ball) bouncing
on the uneven floorboards of a log cabin while a bear sleeps along the back wall. Every landing makes
noise proportional to the real impact speed times the floor under him (soft rug x0.35, boards x1,
creaky boards x2.2, scattered pans x3); wall bumps add a little. Noise settles slowly when quiet.
100% = WOKEN UP -> the bear swats him across the cabin."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the sleeping bear'
SEED = int(os.environ.get('SEED', 4))
rng = random.Random(SEED)

class S: pass
S.HOOK1 = 'WILL GLOOP SNEAK PAST'; S.HOOK2 = 'THE SLEEPING BEAR?'; S.HOOK2_SIZE = 88; S.FAIL_WORD = 'WOKEN UP!'; S.FAIL_SIZE = 140
S.T_START = HOOK_T; S.TL = 13.0; S.T_END = S.T_START + S.TL
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
S.events = [[0.1, 'snore'], [2.6, 'snore']]
tt = 5.1
while tt < S.T_RES - 0.5: S.events.append([tt, 'snore']); tt += 2.5
for (tn, xn, d, kind, live) in NOISES:
    if tn > S.T_RES + 1.5: continue
    if kind == 'pans': S.events.append([tn, 'clang'])
    elif kind == 'creak': S.events.append([tn, 'creak']); S.events.append([tn, 'hop'])
    elif kind == 'rug': S.events.append([tn, 'hop'])
    elif kind == 'wall': S.events.append([tn, 'thump', 0.4])
    else: S.events.append([tn, 'noise_hit', 0.6])
if T_FAIL: S.events += [[T_FAIL, 'roar'], [T_FAIL + 0.05, 'whoosh']]
S.AMB = {'drone': 44}

def draw_bar(c, t, f):
    p = WAKE[f]; recent = any(n[0] <= t < n[0] + 0.3 and n[4] for n in NOISES)
    bx = bar(c, p / 100, f'WAKE {int(p)}%', bad_col(p / 100), 0.12 if recent else 0, bw=640, x_off=36)
    text_at(c, 'Z', bx - 52, 231, 54, rgb('#9fb6ff'), lw=8)
S.draw_bar = draw_bar

BEAR_X, BEAR_Y = 560, 1330
def draw_bear(c, t, awake_k):
    br, br2, br3 = rgb('#5a3a28'), rgb('#4a2f21'), rgb('#7a5640')
    breath = 1 + 0.03 * math.sin(t * 2.4) * (1 - awake_k)
    c.save(); c.translate(BEAR_X, BEAR_Y - 40 * awake_k)
    c.set_source_rgb(*br2); c.save(); c.scale(1.0, breath); c.save(); c.scale(330, 120); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.restore(); c.fill()
    c.set_source_rgb(*br); c.save(); c.translate(-40, -10); c.scale(1, breath); c.scale(290, 105); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    hx, hy = 300, -30 - 50 * awake_k
    c.set_source_rgb(*br); c.arc(hx, hy, 105, 0, 2 * math.pi); c.fill()
    for ex in (-60, 60):
        c.set_source_rgb(*br); c.arc(hx + ex, hy - 85, 34, 0, 2 * math.pi); c.fill()
        c.set_source_rgb(*br3); c.arc(hx + ex, hy - 85, 18, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*br3); c.save(); c.translate(hx + 10, hy + 35); c.scale(62, 44); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    c.set_source_rgb(0.1, 0.07, 0.06); c.save(); c.translate(hx + 10, hy + 12); c.scale(20, 13); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    c.set_line_cap(cairo.LINE_CAP_ROUND)
    for ex in (-38, 52):
        if awake_k < 0.5:
            c.set_line_width(7); c.set_source_rgb(0.12, 0.08, 0.06); c.arc(hx + ex, hy - 22, 16, 0.2, math.pi - 0.2); c.stroke()
        else:
            c.set_source_rgb(1, 1, 0.9); c.arc(hx + ex, hy - 24, 17, 0, 2 * math.pi); c.fill()
            c.set_source_rgb(0.1, 0.05, 0.05); c.arc(hx + ex, hy - 22, 8, 0, 2 * math.pi); c.fill()
            c.set_line_width(9); c.move_to(hx + ex - 22, hy - 52 + (6 if ex < 0 else 0)); c.line_to(hx + ex + 20, hy - 46 - (6 if ex < 0 else 0)); c.stroke()
    if awake_k > 0.5:
        c.set_source_rgb(0.35, 0.08, 0.1); c.save(); c.translate(hx + 10, hy + 62); c.scale(40, 30 * awake_k); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
        c.set_source_rgb(1, 1, 0.95)
        for dx in (-22, 22): c.move_to(hx + 10 + dx - 8, hy + 40); c.line_to(hx + 10 + dx, hy + 58); c.line_to(hx + 10 + dx + 8, hy + 40); c.close_path(); c.fill()
    c.restore()
    if awake_k < 0.5:
        for i in range(3):
            k = (t * 0.45 + i / 3) % 1
            text_at(c, 'Z', BEAR_X + 380 + 60 * k + 20 * math.sin(t * 2 + i), BEAR_Y - 200 - k * 300, 40 + 40 * k, rgb('#9fb6ff'), lw=6)

def draw_bg(c, t):
    c.set_source_rgb(*rgb('#2a1d18')); c.rectangle(0, HEAD, W, H - HEAD); c.fill()
    c.set_source_rgb(*rgb('#33241d'))
    for yy in range(HEAD + 20, GROUND, 110): rrect(c, -20, yy, W + 40, 86, 40); c.fill()
    c.set_source_rgb(*rgb('#161a2e')); rrect(c, 120, 520, 240, 260, 10); c.fill()   # window
    c.set_source_rgb(*rgb('#d8d0b0')); c.arc(270, 600, 34, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#4a3226')); c.set_line_width(14); rrect(c, 120, 520, 240, 260, 10); c.stroke(); c.move_to(240, 520); c.line_to(240, 780); c.stroke(); c.move_to(120, 650); c.line_to(360, 650); c.stroke()
    c.set_source_rgba(0.85, 0.85, 1, 0.04); c.move_to(120, 780); c.line_to(360, 780); c.line_to(560, GROUND); c.line_to(250, GROUND); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#3b2a22')); c.rectangle(560, 600, 380, 18); c.fill()   # shelf
    for i, col in enumerate(('#6b4b3a', '#5a5f6b', '#7a3d33')): c.set_source_rgb(*rgb(col)); rrect(c, 600 + i * 110, 520, 70, 80, 10); c.fill()
    c.set_source_rgb(*rgb('#3a2219')); c.save(); c.translate(BEAR_X + 40, BEAR_Y + 115); c.scale(420, 40); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()

def draw_floor(c, t):
    c.move_to(0, H)
    for x in range(0, W + 1, 6): c.line_to(x, TER.h[x])
    c.line_to(W, H); c.close_path(); c.set_source_rgb(*rgb('#6b4a32')); c.fill()
    c.set_source_rgba(0, 0, 0, 0.2); c.set_line_width(3)
    for yy in range(GROUND + 60, H, 60): c.move_to(0, yy); c.line_to(W, yy); c.stroke()
    for (a, b, m, kind) in ZONES:
        y0 = TER.y((a + b) / 2)
        if kind == 'rug':
            c.set_source_rgb(*rgb('#7a3a3a')); rrect(c, a, y0 - 6, b - a, 110, 10); c.fill()
            c.set_source_rgb(*rgb('#a35a4a')); rrect(c, a + 14, y0 + 10, b - a - 28, 76, 8); c.fill()
            c.set_source_rgb(*rgb('#7a3a3a')); rrect(c, a + 30, y0 + 26, b - a - 60, 44, 6); c.fill()
        elif kind == 'creak':
            for x in range(int(a), int(b), 38):
                c.set_source_rgb(*rgb('#9a7350')); c.rectangle(x + 2, TER.y(x + 18) - 2, 34, 120); c.fill()
                c.set_source_rgb(*rgb('#5e4430')); c.set_line_width(3); c.move_to(x + 10, TER.y(x + 18) + 20); c.line_to(x + 22, TER.y(x + 18) + 50); c.line_to(x + 14, TER.y(x + 18) + 80); c.stroke()
        else:
            for j, x in enumerate(range(int(a) + 25, int(b) - 10, 52)):
                y = TER.y(x) - 2; c.set_source_rgb(*rgb('#7d8590' if j % 2 else '#5f6670'))
                c.save(); c.translate(x, y); c.rotate(0.15 * (j % 3 - 1)); c.scale(30, 14); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
                c.set_source_rgb(*rgb('#2e2622')); c.save(); c.translate(x, y - 2); c.scale(22, 7); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
                c.set_source_rgb(*rgb('#3b2a22')); c.rectangle(x + 26, y - 5, 28, 7); c.fill()
    c.set_source_rgb(*rgb('#8a6444')); c.set_line_width(4)
    for x in range(0, W + 1, 6): (c.move_to if x == 0 else c.line_to)(x, TER.h[x])
    c.stroke()
    for (x0, x1) in ((0, WALL_L), (WALL_R, W)):
        c.set_source_rgb(*rgb('#4a3226')); c.rectangle(x0, 1000, x1 - x0, GROUND + 20 - 1000); c.fill()
        c.set_source_rgb(*rgb('#3a271d'))
        for yy in range(1000, GROUND, 70): rrect(c, x0 - 10, yy, x1 - x0 + 20, 56, 26); c.fill()

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
        k = (t - T_FAIL) / 0.35; px = lerp(BEAR_X + 200, GX[int(T_FAIL * FPS)], k)
        c.set_source_rgb(*rgb('#5a3a28')); c.arc(px, GROUND - 110, 75, 0, 2 * math.pi); c.fill()
        c.set_source_rgb(*rgb('#7a5640'))
        for dx in (-40, 0, 40): c.arc(px + dx, GROUND - 170, 18, 0, 2 * math.pi); c.fill()
    PS.draw(c)
    END.draw_claw(c, t)
    c.restore()
    END.header(c, t, fi)

if __name__ == '__main__':
    if sys.argv[1] == 'sim':
        e = int(S.T_RES * FPS) - 1
        print(SEED, S.OUTCOME, round(S.T_RES - S.T_START, 2), 'peak', round(max(WAKE[:e + 1])), 'final', round(WAKE[e]), [z[3] for z in ZONES], 'dur', S.DUR); sys.exit()
    run(S, render)
