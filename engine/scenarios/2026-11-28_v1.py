"""2026-11-28 v1 — NOISE – WAKE %: the SLEEPING WALRUS. Gloop is a passive rigid ball (Ball) bouncing across an
arctic fishing camp at night while a giant walrus snoozes on the packed snow. Every landing makes noise proportional
to the real impact speed times the ground under him (soft powder x0.35, packed snow x1, crunchy ice crust x2.2,
empty tin buckets x3); bumps into the ice wall / fishing hut add a little. Noise settles slowly.
100% = WOKEN UP -> the walrus wakes, bellows and flipper-slaps him across the camp."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the sleeping walrus'
SEED = int(os.environ.get('SEED', 1))
rng = random.Random(SEED)

class S: pass
S.HOOK1 = 'WILL GLOOP SNEAK PAST'; S.HOOK2 = 'THE SLEEPING WALRUS?'; S.HOOK2_SIZE = 84; S.FAIL_WORD = 'WOKEN UP!'; S.FAIL_SIZE = 140
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
if T_FAIL: S.events += [[T_FAIL, 'sizzle'], [T_FAIL + 0.02, 'roar'], [T_FAIL + 0.05, 'whoosh'], [T_FAIL + 0.3, 'thump', 0.8]]
S.AMB = {'drone': 44}

def draw_bar(c, t, f):
    p = WAKE[f]; recent = any(n[0] <= t < n[0] + 0.3 and n[4] for n in NOISES)
    bx = bar(c, p / 100, f'WAKE {int(p)}%', bad_col(p / 100), 0.12 if recent else 0, bw=640, x_off=36)
    text_at(c, 'Z', bx - 52, 231, 54, rgb('#7fe0ff'), lw=8)
S.draw_bar = draw_bar

BEAR_X, BEAR_Y = 590, 1490
def draw_walrus(c, t, awake_k):   # a giant walrus snoozing on the snow
    body, dark, belly = rgb('#8a6656'), rgb('#6a4e40'), rgb('#a58272')
    br = (1 - awake_k) * 6 * math.sin(t * 1.4)
    c.set_source_rgba(0, 0, 0, 0.22); c.save(); c.translate(BEAR_X + 40, BEAR_Y - 10); c.scale(340, 40); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    c.save(); c.translate(BEAR_X, BEAR_Y - 20)
    c.set_source_rgb(*dark)   # tail flippers
    for sg in (-1, 1): c.save(); c.translate(300, -10 + sg * 18); c.rotate(sg * 0.5); c.scale(70, 22); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    c.set_source_rgb(*body); c.save(); c.translate(60, -120); c.scale(270, 130 + br); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()   # huge body
    c.set_source_rgb(*belly); c.save(); c.translate(60, -40); c.scale(240, 46); c.arc(0, 0, 1, 0, math.pi); c.restore(); c.fill()
    c.set_source_rgba(0.35, 0.25, 0.2, 0.35); c.set_line_width(4)   # skin folds
    for k in range(4): c.arc(120 + k * 50, -120, 90, 2.2, 3.6); c.stroke()
    c.set_source_rgb(*dark); c.save(); c.translate(-60, -18); c.rotate(-0.3); c.scale(70, 22); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()   # front flipper
    lift = 150 * awake_k; hx, hy = -190, -120 - lift
    c.set_source_rgb(*body); c.save(); c.translate(hx + 40, hy + 60); c.scale(110, 110); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()   # neck
    c.save(); c.translate(hx, hy); c.scale(115, 95); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()   # head
    c.set_source_rgb(*rgb('#f0e8d8'))   # tusks
    for sg in (-1, 1):
        c.move_to(hx + sg * 22 - 9, hy + 50); c.line_to(hx + sg * 30 - 4, hy + 175 + 10 * awake_k); c.line_to(hx + sg * 22 + 9, hy + 50); c.close_path(); c.fill()
    c.set_source_rgb(*belly)   # whisker pads
    for sg in (-1, 1): c.save(); c.translate(hx + sg * 34, hy + 36); c.scale(44, 32); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    c.set_source_rgba(0.3, 0.22, 0.18, 0.8)
    for sg in (-1, 1):
        for k in range(3):
            for j in range(3): c.arc(hx + sg * (18 + 14 * j), hy + 26 + 12 * k, 2.5, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#3a2a24')); c.save(); c.translate(hx, hy + 8); c.scale(16, 9); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()   # nose
    c.set_line_width(5)
    if awake_k < 0.5:
        c.set_source_rgb(*rgb('#3a2a24'))
        for sg in (-1, 1): c.arc(hx + sg * 48, hy - 30, 12, 0.3, math.pi - 0.3); c.stroke()   # closed eyes
    else:
        for sg in (-1, 1):
            c.set_source_rgb(1, 1, 1); c.arc(hx + sg * 48, hy - 32, 13, 0, 2 * math.pi); c.fill()
            c.set_source_rgb(0.1, 0.08, 0.08); c.arc(hx + sg * 46, hy - 30, 6, 0, 2 * math.pi); c.fill()
        c.set_source_rgb(*rgb('#3a2a24')); c.set_line_width(6)   # grumpy brows
        for sg in (-1, 1): c.move_to(hx + sg * 26, hy - 52); c.line_to(hx + sg * 72, hy - 66); c.stroke()
    c.restore()
    if awake_k < 0.5:
        for i in range(3):
            k = (t * 0.45 + i / 3) % 1
            text_at(c, 'Z', BEAR_X - 120 + 50 * k + 20 * math.sin(t * 2 + i), BEAR_Y - 330 - k * 240, 40 + 40 * k, rgb('#7fe0ff'), lw=6)
    elif awake_k > 0.8:
        text_at(c, 'HONK!', BEAR_X, BEAR_Y - 580, 110, rgb('#ffd36b'))

STARS = [(rng.uniform(0, W), rng.uniform(HEAD + 20, 1000), rng.uniform(1.5, 3)) for _ in range(40)]
def draw_bg(c, t):
    c.set_source_rgb(*rgb('#121822')); c.rectangle(0, HEAD, W, H - HEAD); c.fill()
    for (x, y, r) in STARS: c.set_source_rgba(0.9, 0.95, 1, 0.5 + 0.3 * math.sin(t * 2 + x)); c.arc(x, y, r, 0, 2 * math.pi); c.fill()
    c.set_source_rgba(0.4, 0.85, 0.7, 0.10); c.set_line_width(60)   # faint aurora band
    c.move_to(-50, 560)
    for x in range(0, W + 60, 60): c.line_to(x, 560 + 60 * math.sin(x * 0.006 + t * 0.4))
    c.stroke()
    c.set_source_rgb(*rgb('#e6dfc4')); c.arc(860, HEAD + 170, 46, 0, 2 * math.pi); c.fill()   # moon
    c.set_source_rgb(*rgb('#121822')); c.arc(880, HEAD + 158, 40, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#2a3444')); c.move_to(0, 1250); c.line_to(140, 1020); c.line_to(260, 1130); c.line_to(420, 960); c.line_to(600, 1150); c.line_to(760, 1000); c.line_to(940, 1140); c.line_to(W, 1060); c.line_to(W, 1520); c.line_to(0, 1520); c.close_path(); c.fill()   # icy mountains
    c.set_source_rgb(*rgb('#3a4658'))
    for (px, py) in ((140, 1020), (420, 960), (760, 1000)): c.move_to(px, py); c.line_to(px - 40, py + 60); c.line_to(px + 40, py + 60); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#1e2836')); c.rectangle(0, 1300, W, 140); c.fill()   # frozen sea
    c.set_source_rgb(*rgb('#5a6678')); c.rectangle(0, 1430, W, 200); c.fill()   # back snow plain
    c.set_source_rgb(*rgb('#6a768a')); c.rectangle(0, 1430, W, 8); c.fill()
    c.set_source_rgba(0.75, 0.85, 1.0, 0.04); c.move_to(780, HEAD + 220); c.line_to(940, HEAD + 220); c.line_to(980, 1500); c.line_to(320, 1500); c.close_path(); c.fill()

def draw_floor(c, t):
    c.move_to(0, H)
    for x in range(0, W + 1, 6): c.line_to(x, TER.h[x])
    c.line_to(W, H); c.close_path(); c.set_source_rgb(*rgb('#8a96a8')); c.fill()   # packed snow (moonlit)
    c.set_source_rgba(0, 0, 0, 0.08); c.set_line_width(3)
    for y in range(GROUND + 40, H, 50): c.move_to(0, y); c.line_to(W, y); c.stroke()
    for (a, b, m, kind) in ZONES:
        if kind == 'rug':   # soft fluffy powder drift
            c.set_source_rgb(*rgb('#e2e8f0')); c.move_to(a, TER.y(a) + 4)
            for x in range(int(a), int(b) + 1, 6): c.line_to(x, TER.y(x) - 10 - 8 * abs(math.sin(x * 0.04)))
            c.line_to(b, TER.y(b) + 22); c.line_to(a, TER.y(a) + 22); c.close_path(); c.fill()
        elif kind == 'creak':   # crunchy cracked ice crust
            c.set_source_rgb(*rgb('#7ab0d8')); c.move_to(a, TER.y(a) - 6)
            for x in range(int(a), int(b) + 1, 6): c.line_to(x, TER.y(x) - 6)
            c.line_to(b, TER.y(b) + 26); c.line_to(a, TER.y(a) + 26); c.close_path(); c.fill()
            c.set_source_rgba(0.95, 0.98, 1, 0.85); c.set_line_width(3)
            for j, x in enumerate(range(int(a) + 12, int(b) - 10, 30)):
                y = TER.y(x); c.move_to(x, y - 2); c.line_to(x + 10, y + 8); c.line_to(x + 4, y + 14); c.stroke(); c.move_to(x + 10, y + 8); c.line_to(x + 22, y + 4); c.stroke()
        else:   # empty tin buckets + a fishing pot lying around
            for j, x in enumerate(range(int(a) + 10, int(b) - 30, 56)):
                y = TER.y(x) - 2
                c.set_source_rgb(*rgb('#8a9aa4' if j % 2 else '#a4b2ba')); c.save(); c.translate(x + 20, y); c.scale(1.3, 1.3)
                c.move_to(-20, 0); c.line_to(-15, -34); c.line_to(15, -34); c.line_to(20, 0); c.close_path(); c.fill()
                c.set_source_rgb(*rgb('#5a6a74')); c.rectangle(-16, -26, 32, 4); c.fill(); c.set_line_width(2); c.arc(0, -34, 14, math.pi, 2 * math.pi); c.stroke(); c.restore()
    c.set_source_rgb(*rgb('#c8d2de')); c.set_line_width(4)
    for x in range(0, W + 1, 6): (c.move_to if x == 0 else c.line_to)(x, TER.h[x])
    c.stroke()
    # left wall: stacked ice blocks; right wall: a wooden ice-fishing hut
    x1 = WALL_L
    for k in range(6):
        yy = 1120 + k * 84
        c.set_source_rgb(*rgb('#7a9ab8' if k % 2 else '#6a8aa8')); rrect(c, -30, yy, x1 + 30, 80, 8); c.fill()
        c.set_source_rgba(1, 1, 1, 0.18); c.rectangle(-30, yy + 6, x1 + 20, 6); c.fill()
    c.set_source_rgb(*rgb('#dfe6ee')); c.save(); c.translate(x1 / 2 - 10, 1118); c.scale(x1 / 2 + 24, 20); c.arc(0, 0, 1, math.pi, 2 * math.pi); c.restore(); c.fill()
    x0 = WALL_R
    c.set_source_rgb(*rgb('#6a4a34')); c.rectangle(x0, 1000, W - x0 + 10, GROUND + 40 - 1000); c.fill()
    c.set_source_rgb(*rgb('#54382a'))
    for yy in range(1010, GROUND, 60): c.rectangle(x0, yy, W - x0 + 10, 5); c.fill()
    c.set_source_rgb(*rgb('#8a3a2e')); c.move_to(x0 - 20, 1010); c.line_to(W + 10, 900); c.line_to(W + 10, 1010); c.close_path(); c.fill()   # roof
    c.set_source_rgb(*rgb('#dfe6ee')); c.move_to(x0 - 24, 1012); c.line_to(W + 10, 902); c.line_to(W + 10, 918); c.line_to(x0 - 10, 1022); c.close_path(); c.fill()   # snow on roof
    c.set_source_rgb(*rgb('#e8c870')); rrect(c, x0 + 22, 1120, 50, 50, 6); c.fill()   # warm window

PS = Particles(9)
def render(f, c):
    t = f / FPS; fi = min(f, len(GX) - 1); shake = (0, 0)
    if T_FAIL and T_FAIL <= t < T_FAIL + 0.4: shake = (rng.uniform(-6, 6), rng.uniform(-6, 6))
    c.save(); c.translate(*shake)
    draw_bg(c, t)
    awake = 0 if not T_FAIL or t < T_FAIL else ease((t - T_FAIL) / 0.25)
    draw_walrus(c, t, awake)
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
        c.set_source_rgb(*rgb('#6a4e40')); c.set_line_width(70); c.set_line_cap(cairo.LINE_CAP_ROUND)
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
