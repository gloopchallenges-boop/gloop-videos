"""2026-11-11 v1 — NOISE – WAKE %: the SLEEPING GORILLA. Gloop is a passive rigid ball (Ball) bouncing on the
jungle floor at night while a big silverback naps against a fallen tree. Every landing makes noise
proportional to the real impact speed times the ground under him (big soft leaves x0.35, dirt x1, dry twigs
x2.2, coconut shells x3); wall bumps add a little. Noise settles slowly when quiet.
100% = WOKEN UP -> the gorilla wakes, beats its chest and swats him across the clearing."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the sleeping gorilla'
SEED = int(os.environ.get('SEED', 7))
rng = random.Random(SEED)

class S: pass
S.HOOK1 = 'WILL GLOOP SNEAK PAST'; S.HOOK2 = 'THE SLEEPING GORILLA?'; S.HOOK2_SIZE = 84; S.FAIL_WORD = 'WOKEN UP!'; S.FAIL_SIZE = 140
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
    if kind == 'pans': S.events.append([tn, 'blip']); S.events.append([tn, 'noise_hit', 0.5])
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
def draw_bear(c, t, awake_k):   # big silverback gorilla sitting slumped against a fallen tree
    fur, fur2, skin = rgb('#2e2c34'), rgb('#3c3a44'), rgb('#4a4048')
    br = (1 - awake_k) * 7 * math.sin(t * 1.7)
    c.save(); c.translate(BEAR_X, BEAR_Y + 10 - 30 * awake_k); c.scale(0.95, 0.95)
    # legs + body
    c.set_source_rgb(*fur)
    for (fx, fy) in ((-210, 110), (210, 110)): c.save(); c.translate(fx, fy); c.scale(95, 55); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    c.save(); c.translate(0, -20); c.scale(230, 160 + br); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    c.set_source_rgb(*rgb('#8a8a94')); c.save(); c.translate(0, -60); c.scale(170, 60 + br * 0.5); c.arc(0, 0, 1, math.pi, 2 * math.pi); c.restore(); c.fill()   # silver back stripe
    c.set_source_rgb(*skin); c.save(); c.translate(0, 10); c.scale(130, 100 + br); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()   # chest
    c.set_source_rgb(*rgb('#3a3038')); c.set_line_width(5)
    c.move_to(-60, -20); c.curve_to(-30, 0, -30, 0, -2, -20); c.stroke(); c.move_to(2, -20); c.curve_to(30, 0, 30, 0, 60, -20); c.stroke()
    for side in (-1, 1):   # long arms resting
        c.set_source_rgb(*fur2); c.set_line_width(70); c.set_line_cap(cairo.LINE_CAP_ROUND)
        lift = 160 * awake_k
        c.move_to(side * 200, -110); c.curve_to(side * 280, -20, side * 250, 80 - lift, side * 150, 120 - lift); c.stroke()
        c.set_source_rgb(*skin); c.save(); c.translate(side * 150, 125 - lift); c.scale(46, 32); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    # head
    hx, hy = 0, -210 - 60 * awake_k
    c.save(); c.translate(hx, hy); c.rotate(0.2 * (1 - awake_k))
    c.set_source_rgb(*fur); c.save(); c.translate(0, -10); c.scale(115, 120); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    c.save(); c.translate(0, -90); c.scale(80, 55); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()   # crest
    for ex in (-1, 1): c.arc(ex * 112, -10, 26, 0, 2 * math.pi); c.fill()   # ears
    c.set_source_rgb(*skin); c.save(); c.translate(0, 20); c.scale(88, 78); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()   # face
    c.set_source_rgb(*rgb('#2a242a')); c.save(); c.translate(0, -26); c.scale(80, 16); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()   # brow
    c.set_source_rgb(*rgb('#3a3038')); c.save(); c.translate(0, 34); c.scale(46, 30); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()   # muzzle
    c.set_source_rgb(*rgb('#1a1418'))
    for nx in (-14, 14): c.save(); c.translate(nx, 26); c.scale(9, 6); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    for ex in (-36, 36):
        if awake_k < 0.5:
            c.set_source_rgb(*rgb('#1a1418')); c.set_line_width(6); c.arc(ex, -6, 14, 0.2, math.pi - 0.2); c.stroke()
        else:
            c.set_source_rgb(*rgb('#e8c060')); c.arc(ex, -6, 14, 0, 2 * math.pi); c.fill()
            c.set_source_rgb(*rgb('#1a1008')); c.arc(ex, -6, 6, 0, 2 * math.pi); c.fill()
    if awake_k > 0.5:
        c.set_source_rgb(*rgb('#3a1a1a')); c.save(); c.translate(0, 72); c.scale(42, 20 * awake_k); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
        c.set_source_rgb(*rgb('#f0e8c8'))
        for sx in (-24, 24): c.move_to(sx - 7, 56); c.line_to(sx + 7, 56); c.line_to(sx, 72); c.close_path(); c.fill()
    else:
        c.set_source_rgb(*rgb('#1a1418')); c.set_line_width(5); c.move_to(-26, 58); c.curve_to(-10, 64, 10, 64, 26, 58); c.stroke()
    c.restore()
    c.restore()
    if awake_k < 0.5:
        for i in range(3):
            k = (t * 0.45 + i / 3) % 1
            text_at(c, 'Z', BEAR_X + 90 + 50 * k + 20 * math.sin(t * 2 + i), BEAR_Y - 380 - k * 240, 40 + 40 * k, rgb('#7fe0ff'), lw=6)
    elif awake_k > 0.8:
        text_at(c, 'OOH-OOH!', BEAR_X, BEAR_Y - 560, 96, rgb('#ffd36b'))

def draw_bg(c, t):
    c.set_source_rgb(*rgb('#10201c')); c.rectangle(0, HEAD, W, H - HEAD); c.fill()
    c.set_source_rgb(*rgb('#e6dfc4')); c.arc(230, 500, 56, 0, 2 * math.pi); c.fill()   # moon
    # distant tree trunks + canopy
    for (tx, tw, col) in ((80, 70, '#16302a'), (360, 50, '#16302a'), (700, 80, '#16302a'), (980, 60, '#16302a')):
        c.set_source_rgb(*rgb(col)); c.rectangle(tx - tw / 2, 520, tw, 1100); c.fill()
    for i, (cx, cy, r) in enumerate(((60, 380, 200), (330, 330, 190), (620, 360, 220), (900, 340, 210), (1080, 420, 160))):
        c.set_source_rgb(*rgb(('#1a3a2e', '#173428')[i % 2])); c.arc(cx, cy, r, 0, 2 * math.pi); c.fill()
    # hanging vines
    c.set_source_rgb(*rgb('#244a34')); c.set_line_width(6)
    for vx in (170, 470, 830, 960):
        sw = 10 * math.sin(t * 0.8 + vx)
        c.move_to(vx, 450); c.curve_to(vx + sw, 700, vx - sw, 900, vx + sw * 0.5, 1050); c.stroke()
    # fireflies
    for i in range(9):
        fx = (130 + i * 117 + 40 * math.sin(t * 0.7 + i)) % W; fy = 760 + 220 * math.sin(i * 2.1 + t * 0.5)
        c.set_source_rgba(0.95, 1, 0.5, 0.4 + 0.4 * math.sin(t * 3 + i * 1.7)); c.arc(fx, fy, 4, 0, 2 * math.pi); c.fill()
    # fallen tree behind the gorilla
    c.set_source_rgb(*rgb('#3a2c22')); rrect(c, 120, 1330, 840, 120, 55); c.fill()
    c.set_source_rgb(*rgb('#2c2018')); c.set_line_width(4)
    for x in range(180, 920, 90): c.move_to(x, 1350); c.line_to(x + 40, 1420); c.stroke()
    c.set_source_rgb(*rgb('#4a3a2c')); c.save(); c.translate(960, 1390); c.scale(30, 60); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()

def draw_floor(c, t):
    c.move_to(0, H)
    for x in range(0, W + 1, 6): c.line_to(x, TER.h[x])
    c.line_to(W, H); c.close_path(); c.set_source_rgb(*rgb('#2e2a1e')); c.fill()
    c.set_source_rgba(0, 0, 0, 0.12); c.set_line_width(3)
    for x in range(0, W, 140): c.move_to(x, GROUND + 30); c.line_to(x + 60, GROUND + 30); c.stroke()
    for (a, b, m, kind) in ZONES:
        if kind == 'rug':   # big soft jungle leaves
            for j, x in enumerate(range(int(a) + 22, int(b) - 10, 34)):
                y = TER.y(x) + 2; c.set_source_rgb(*rgb(('#2f6a3a', '#3a7a44')[j % 2]))
                c.save(); c.translate(x, y); c.scale(34, 18); c.arc(0, 0, 1, math.pi, 2 * math.pi); c.restore(); c.fill()
        elif kind == 'creak':   # dry snapping twigs
            c.set_line_width(5); c.set_line_cap(cairo.LINE_CAP_ROUND)
            for j, x in enumerate(range(int(a) + 12, int(b) - 12, 20)):
                y = TER.y(x) - 4; c.set_source_rgb(*rgb(('#8a6a42', '#a07a4a')[j % 2]))
                a2 = (j * 1.1) % 1.2 - 0.6; c.move_to(x - 24 * math.cos(a2), y - 8 - 24 * math.sin(a2)); c.line_to(x + 24 * math.cos(a2), y - 8 + 24 * math.sin(a2)); c.stroke()
        else:   # empty coconut shells
            for j, x in enumerate(range(int(a) + 22, int(b) - 12, 36)):
                y = TER.y(x) - 2
                c.set_source_rgb(*rgb('#6a4a2e')); c.arc(x, y, 20, math.pi, 2 * math.pi); c.fill()
                c.set_source_rgb(*rgb('#e8e0cc')); c.arc(x, y, 14, math.pi, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#4a4430')); c.set_line_width(4)
    for x in range(0, W + 1, 6): (c.move_to if x == 0 else c.line_to)(x, TER.h[x])
    c.stroke()
    for (x0, x1) in ((0, WALL_L), (WALL_R, W)):   # big tree trunks as walls
        c.set_source_rgb(*rgb('#3a2c22')); c.rectangle(x0 - 10, 900, x1 - x0 + 20, GROUND + 40 - 900); c.fill()
        c.set_source_rgb(*rgb('#2c2018')); c.set_line_width(4)
        for k, yy in enumerate(range(940, GROUND, 70)):
            xm = x0 + (x1 - x0) * (0.3 if k % 2 else 0.6); c.move_to(xm, yy); c.line_to(xm + 4, yy + 45); c.stroke()


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
        k = (t - T_FAIL) / 0.35; px = lerp(BEAR_X - 250, GX[int(T_FAIL * FPS)], k)
        c.set_source_rgb(*rgb('#3c3a44')); rrect(c, px - 75, GROUND - 190, 150, 150, 60); c.fill()
        c.set_source_rgb(*rgb('#4a4048'))
        for dx in (-40, 0, 40): rrect(c, px + dx - 16, GROUND - 205, 32, 40, 10); c.fill()
    PS.draw(c)
    END.draw_claw(c, t)
    c.restore()
    END.header(c, t, fi)

if __name__ == '__main__':
    if sys.argv[1] == 'sim':
        e = int(S.T_RES * FPS) - 1
        print(SEED, S.OUTCOME, round(S.T_RES - S.T_START, 2), 'peak', round(max(WAKE[:e + 1])), 'final', round(WAKE[e]), [z[3] for z in ZONES], 'dur', S.DUR); sys.exit()
    run(S, render)
