"""2026-11-22 v3 — NOISE – WAKE %: the SLEEPING PANDA. Gloop is a passive rigid ball (Ball) bouncing across a
bamboo-forest clearing at night while a giant panda naps curled up on a bed of leaves. Every landing makes noise
proportional to the real impact speed times the ground under him (soft moss x0.35, packed dirt x1, dry crackly
leaves x2.2, hollow bamboo canes x3); bumps into the rock / bamboo clump add a little. Noise settles slowly.
100% = WOKEN UP -> the panda wakes, grumbles and paw-swats him across the clearing."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the sleeping panda'
SEED = int(os.environ.get('SEED', 1))
rng = random.Random(SEED)

class S: pass
S.HOOK1 = 'WILL GLOOP SNEAK PAST'; S.HOOK2 = 'THE SLEEPING PANDA?'; S.HOOK2_SIZE = 84; S.FAIL_WORD = 'WOKEN UP!'; S.FAIL_SIZE = 140
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
def draw_bear(c, t, awake_k):   # a giant panda curled up asleep on a bed of leaves
    wh, bk, gr = rgb('#e8e6e0'), rgb('#1e1c22'), rgb('#c8c6c0')
    br = (1 - awake_k) * 6 * math.sin(t * 1.5)
    c.set_source_rgb(*rgb('#3e5a2e')); c.save(); c.translate(BEAR_X, BEAR_Y + 10); c.scale(330, 60); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    c.set_source_rgb(*rgb('#4e6e38'))
    for k in range(9): c.save(); c.translate(BEAR_X - 280 + k * 70, BEAR_Y - 4 + (k % 2) * 8); c.rotate(0.4 * (k % 3 - 1)); c.scale(46, 14); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    c.save(); c.translate(BEAR_X, BEAR_Y - 20)
    c.set_source_rgb(*bk)   # back leg
    c.save(); c.translate(200, -40); c.scale(90, 60); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    c.set_source_rgb(*wh); c.save(); c.translate(40, -130); c.scale(250, 140 + br); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()   # body
    c.set_source_rgb(*gr); c.save(); c.translate(60, -60); c.scale(220, 50); c.arc(0, 0, 1, 0, math.pi); c.restore(); c.fill()
    c.set_source_rgb(*bk)   # black shoulder band + tucked arms
    c.save(); c.translate(-90, -150 - br * 0.5); c.rotate(-0.25); c.scale(70, 150); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    for px in (-170, -80): c.save(); c.translate(px, -12); c.scale(56, 30); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    c.save(); c.translate(240, -30); c.scale(40, 26); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()   # foot
    c.set_source_rgb(*rgb('#3a3640'))
    for k in range(3): c.arc(232 + (k - 1) * 18, -42, 7, 0, 2 * math.pi); c.fill()
    # bamboo stalk it was chewing, lying by its paws
    c.set_source_rgb(*rgb('#7aa84a')); c.save(); c.translate(-60, 0); c.rotate(-0.08); c.rectangle(-80, -10, 240, 18); c.restore(); c.fill()
    lift = 150 * awake_k; hx, hy = -190, -110 - lift
    c.set_source_rgb(*bk)
    for sg in (-1, 1): c.arc(hx + sg * 92, hy - 82, 40, 0, 2 * math.pi); c.fill()   # ears
    c.set_source_rgb(*wh); c.save(); c.translate(hx, hy); c.scale(135, 112); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    c.set_source_rgb(*bk)
    for sg in (-1, 1): c.save(); c.translate(hx + sg * 52, hy - 12); c.rotate(sg * 0.5); c.scale(30, 40); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()   # eye patches
    c.save(); c.translate(hx, hy + 30); c.scale(22, 15); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()   # nose
    c.set_line_width(5)
    if awake_k < 0.5:
        c.set_source_rgb(*rgb('#6a6870'))
        for sg in (-1, 1): c.arc(hx + sg * 52, hy - 10, 14, 0.3, math.pi - 0.3); c.stroke()   # closed eyes
        c.set_source_rgb(*bk); c.move_to(hx, hy + 44); c.curve_to(hx - 8, hy + 58, hx - 22, hy + 58, hx - 28, hy + 50); c.stroke()
        c.move_to(hx, hy + 44); c.curve_to(hx + 8, hy + 58, hx + 22, hy + 58, hx + 28, hy + 50); c.stroke()
    else:
        for sg in (-1, 1):
            c.set_source_rgb(1, 1, 1); c.arc(hx + sg * 52, hy - 14, 13, 0, 2 * math.pi); c.fill()
            c.set_source_rgb(*bk); c.arc(hx + sg * 50, hy - 12, 6, 0, 2 * math.pi); c.fill()
        c.set_source_rgb(*rgb('#5a1a2a')); c.save(); c.translate(hx, hy + 70); c.scale(34, 24 * awake_k); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
        c.set_source_rgb(*bk); c.set_line_width(6)   # grumpy brows
        for sg in (-1, 1): c.move_to(hx + sg * 30, hy - 40); c.line_to(hx + sg * 76, hy - 56); c.stroke()
    c.restore()
    if awake_k < 0.5:
        for i in range(3):
            k = (t * 0.45 + i / 3) % 1
            text_at(c, 'Z', BEAR_X - 120 + 50 * k + 20 * math.sin(t * 2 + i), BEAR_Y - 330 - k * 240, 40 + 40 * k, rgb('#7fe0ff'), lw=6)
    elif awake_k > 0.8:
        text_at(c, 'GRRRR!', BEAR_X, BEAR_Y - 580, 104, rgb('#ffd36b'))

BAMB = [(x, rng.uniform(0.7, 1.0), rng.uniform(-0.03, 0.03)) for x in range(20, W, 75)]
def draw_bg(c, t):
    c.set_source_rgb(*rgb('#141a20')); c.rectangle(0, HEAD, W, H - HEAD); c.fill()
    c.set_source_rgb(*rgb('#e6dfc4')); c.arc(780, HEAD + 160, 50, 0, 2 * math.pi); c.fill()   # moon
    c.set_source_rgb(*rgb('#141a20')); c.arc(800, HEAD + 148, 44, 0, 2 * math.pi); c.fill()
    for layer, (col, sc) in enumerate((('#1c2a24', 0.6), ('#22352a', 0.85))):   # two layers of bamboo stalks
        c.set_source_rgb(*rgb(col))
        for i, (x, h, lean) in enumerate(BAMB):
            if (i + layer) % 2: continue
            xx = x + layer * 30; w_ = 16 + 8 * layer; sway = 4 * math.sin(t * 0.8 + i)
            c.save(); c.translate(xx, 1520); c.rotate(lean + sway * 0.002)
            c.rectangle(-w_ / 2, -1300 * h * sc - 200, w_, 1300 * h * sc + 200); c.fill()
            for j in range(1, 8): c.rectangle(-w_ / 2 - 3, -j * 150 * sc, w_ + 6, 6); c.fill()
            for j in range(2, 7, 2):   # leaves
                c.save(); c.translate(0, -j * 150 * sc); c.rotate(-0.6 if j % 4 else 0.6); c.scale(46, 10); c.arc(1, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
            c.restore()
    c.set_source_rgba(0.75, 0.8, 0.95, 0.04); c.move_to(700, HEAD + 200); c.line_to(860, HEAD + 200); c.line_to(980, 1500); c.line_to(300, 1500); c.close_path(); c.fill()

def draw_floor(c, t):
    c.move_to(0, H)
    for x in range(0, W + 1, 6): c.line_to(x, TER.h[x])
    c.line_to(W, H); c.close_path(); c.set_source_rgb(*rgb('#3e3428')); c.fill()   # packed dirt
    c.set_source_rgba(0, 0, 0, 0.15); c.set_line_width(3)
    for y in range(GROUND + 40, H, 50): c.move_to(0, y); c.line_to(W, y); c.stroke()
    for (a, b, m, kind) in ZONES:
        if kind == 'rug':   # soft moss
            c.set_source_rgb(*rgb('#3e6a34')); c.move_to(a, TER.y(a) - 4)
            for x in range(int(a), int(b) + 1, 6): c.line_to(x, TER.y(x) - 4 - 3 * math.sin(x * 0.3))
            c.line_to(b, TER.y(b) + 22); c.line_to(a, TER.y(a) + 22); c.close_path(); c.fill()
        elif kind == 'creak':   # dry crackly leaves
            for j, x in enumerate(range(int(a) + 10, int(b) - 6, 22)):
                c.set_source_rgb(*rgb(('#8a6a3a', '#a07a3e', '#6e5430')[j % 3])); c.save(); c.translate(x, TER.y(x) - 4); c.rotate(0.5 * ((j * 7) % 3 - 1)); c.scale(18, 7); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
        else:   # hollow bamboo canes lying around
            for j, x in enumerate(range(int(a) + 8, int(b) - 30, 44)):
                y = TER.y(x) - 10
                c.set_source_rgb(*rgb('#8ab85a' if j % 2 else '#a8c86a')); c.save(); c.translate(x + 20, y); c.rotate(0.1 * (j % 3 - 1)); rrect(c, -28, -9, 56, 18, 8); c.fill()
                c.set_source_rgb(*rgb('#5a7a3a')); c.rectangle(-2, -9, 4, 18); c.fill(); c.restore()
    c.set_source_rgb(*rgb('#6a5440')); c.set_line_width(4)
    for x in range(0, W + 1, 6): (c.move_to if x == 0 else c.line_to)(x, TER.h[x])
    c.stroke()
    # left wall: a big mossy boulder; right wall: a thick clump of bamboo
    x1 = WALL_L
    c.set_source_rgb(*rgb('#4a4a50')); rrect(c, -40, 1100, x1 + 40, GROUND + 40 - 1100, 40); c.fill()
    c.set_source_rgb(*rgb('#3a3a42')); rrect(c, -20, 1250, x1, 120, 30); c.fill()
    c.set_source_rgb(*rgb('#3e6a34')); c.save(); c.translate(x1 / 2 - 10, 1108); c.scale(x1 / 2 + 20, 22); c.arc(0, 0, 1, math.pi, 2 * math.pi); c.restore(); c.fill()
    x0 = WALL_R
    for k in range(4):
        c.set_source_rgb(*rgb(('#4a7a3a', '#5a8a44')[k % 2])); xx = x0 + 6 + k * 24
        c.rectangle(xx, 700, 20, GROUND + 40 - 700); c.fill()
        c.set_source_rgb(*rgb('#2e4a26'))
        for yy in range(760 + k * 20, GROUND, 140): c.rectangle(xx - 2, yy, 24, 6); c.fill()

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
        c.set_source_rgb(*rgb('#1e1c22')); c.set_line_width(70); c.set_line_cap(cairo.LINE_CAP_ROUND)
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
