"""2026-11-09 v4 — NOISE – WAKE %: the SLEEPING TROLL. Gloop is a passive rigid ball (Ball) bouncing on the
river bank under an old stone bridge at night while a big troll naps against the arch. Every landing makes
noise proportional to the real impact speed times the ground under him (soft moss x0.35, dirt x1, dry leaves
x2.2, old pots & bottles x3); wall bumps add a little. Noise settles slowly when quiet.
100% = WOKEN UP -> the troll wakes, grumbles and swats him across the bank."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the sleeping troll'
SEED = int(os.environ.get('SEED', 10))
rng = random.Random(SEED)

class S: pass
S.HOOK1 = 'WILL GLOOP SNEAK PAST'; S.HOOK2 = 'THE SLEEPING TROLL?'; S.HOOK2_SIZE = 84; S.FAIL_WORD = 'WOKEN UP!'; S.FAIL_SIZE = 140
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

BEAR_X, BEAR_Y = 600, 1450
def draw_bear(c, t, awake_k):   # big mossy troll sitting slumped against the bridge arch
    sk, sk2, sk3 = rgb('#56664a'), rgb('#46553e'), rgb('#68785a')
    br = (1 - awake_k) * 7 * math.sin(t * 1.9)
    c.save(); c.translate(BEAR_X, BEAR_Y + 10 - 30 * awake_k); c.scale(0.95, 0.95)
    # club leaning on the side
    c.set_source_rgb(*rgb('#5a4028')); c.save(); c.translate(260, 40); c.rotate(0.5 - 0.9 * awake_k)
    c.move_to(-14, 120); c.line_to(14, 120); c.line_to(34, -170); c.curve_to(30, -230, -30, -230, -34, -170); c.close_path(); c.fill(); c.restore()
    # body (big belly) + legs
    c.set_source_rgb(*rgb('#4a3a2a')); c.save(); c.translate(0, 90); c.scale(240, 70); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()   # trousers
    c.set_source_rgb(*sk); c.save(); c.translate(0, -10); c.scale(220, 140 + br); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    c.set_source_rgb(*sk3); c.save(); c.translate(0, 20); c.scale(140, 95 + br); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    c.set_source_rgb(*sk2)
    for (fx, fy) in ((-250, 130), (250, 130)): c.save(); c.translate(fx, fy); c.scale(70, 40); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()   # feet
    for side in (-1, 1):   # arms resting on the belly
        c.set_source_rgb(*sk2); c.set_line_width(56); c.set_line_cap(cairo.LINE_CAP_ROUND)
        c.move_to(side * 190, -80); c.curve_to(side * 240, 0, side * 160, 60, side * 70, 50 - 120 * awake_k * (side > 0)); c.stroke()
    # head
    hx, hy = 0, -200 - 70 * awake_k
    c.save(); c.translate(hx, hy); c.rotate(0.18 * (1 - awake_k))
    c.set_source_rgb(*sk); c.save(); c.scale(130, 110); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    for ex in (-1, 1):   # pointy ears
        c.move_to(ex * 110, -20); c.line_to(ex * 200, -70); c.line_to(ex * 112, 30); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#3a4430'))   # shaggy hair tufts
    for k in range(5): c.arc(-60 + k * 30, -100 - (k % 2) * 10, 24, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*sk3); c.save(); c.translate(0, 18); c.scale(42, 52); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()   # big nose
    c.set_source_rgb(*sk2); c.arc(30, 0, 9, 0, 2 * math.pi); c.fill(); c.arc(-60, -30, 7, 0, 2 * math.pi); c.fill()   # warts
    for ex in (-55, 55):
        if awake_k < 0.5:
            c.set_source_rgb(*rgb('#2a3020')); c.set_line_width(7); c.arc(ex, -28, 20, 0.2, math.pi - 0.2); c.stroke()
        else:
            c.set_source_rgb(*rgb('#f0e080')); c.arc(ex, -30, 20, 0, 2 * math.pi); c.fill()
            c.set_source_rgb(*rgb('#1a1008')); c.arc(ex, -30, 8, 0, 2 * math.pi); c.fill()
            c.set_source_rgb(*rgb('#2a3020')); c.set_line_width(9); c.move_to(ex - 28, -64 + (10 if ex < 0 else 0)); c.line_to(ex + 28, -64 + (0 if ex < 0 else 10)); c.stroke()
    if awake_k > 0.5:
        c.set_source_rgb(*rgb('#3a1a1a')); c.save(); c.translate(0, 82); c.scale(60, 22 * awake_k); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
        c.set_source_rgb(*rgb('#f0e8c8'))
        for sx in (-34, 34): c.move_to(sx - 9, 66); c.line_to(sx + 9, 66); c.line_to(sx, 46); c.close_path(); c.fill()   # tusks
    else:
        c.set_source_rgb(*rgb('#2a3020')); c.set_line_width(6); c.move_to(-46, 82); c.curve_to(-20, 92, 20, 92, 46, 82); c.stroke()
        c.set_source_rgb(*rgb('#f0e8c8'))
        for sx in (-34, 34): c.move_to(sx - 8, 84); c.line_to(sx + 8, 84); c.line_to(sx, 64); c.close_path(); c.fill()
    c.restore()
    c.restore()
    if awake_k < 0.5:
        for i in range(3):
            k = (t * 0.45 + i / 3) % 1
            text_at(c, 'Z', BEAR_X + 90 + 50 * k + 20 * math.sin(t * 2 + i), BEAR_Y - 380 - k * 240, 40 + 40 * k, rgb('#7fe0ff'), lw=6)
    elif awake_k > 0.8:
        text_at(c, 'GRRR!', BEAR_X, BEAR_Y - 560, 100, rgb('#ffd36b'))

def draw_bg(c, t):
    c.set_source_rgb(*rgb('#141a2a')); c.rectangle(0, HEAD, W, H - HEAD); c.fill()
    for (sx, sy) in ((90, 420), (220, 520), (420, 400), (610, 480), (980, 430), (860, 380), (330, 470), (70, 600)):
        c.set_source_rgba(1, 1, 0.9, 0.5 + 0.3 * math.sin(t * 2 + sx)); c.arc(sx, sy, 3, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#e6dfc4')); c.arc(800, 470, 60, 0, 2 * math.pi); c.fill()   # moon
    # far river + bank
    c.set_source_rgb(*rgb('#1a2236')); c.rectangle(0, 1180, W, GROUND - 1180); c.fill()
    c.set_source_rgba(1, 1, 1, 0.06)
    for i in range(5): c.rectangle(0, 1220 + i * 70 + 5 * math.sin(t * 1.3 + i), W, 4); c.fill()
    # the stone bridge arch spanning the scene
    c.set_source_rgb(*rgb('#3a3a46'))
    c.move_to(-10, 640); c.line_to(W + 10, 640); c.line_to(W + 10, 1000); c.line_to(XMAX + R, 1000)
    c.curve_to(XMAX + R, 760, XMIN - R, 760, XMIN - R, 1000); c.line_to(-10, 1000); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#2c2c36')); c.set_line_width(5)
    for yy in range(680, 1000, 60): c.move_to(-10, yy); c.line_to(W + 10, yy); c.stroke()
    c.set_source_rgb(*rgb('#141a2a')); c.move_to(XMAX + R - 6, 1000); c.curve_to(XMAX + R - 6, 770, XMIN - R + 6, 770, XMIN - R + 6, 1000); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#24242e')); c.move_to(XMAX + R - 6, 1000); c.curve_to(XMAX + R - 6, 770, XMIN - R + 6, 770, XMIN - R + 6, 1000); c.line_to(XMIN - R + 40, 1000); c.curve_to(XMIN - R + 40, 810, XMAX + R - 40, 810, XMAX + R - 40, 1000); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#4a4a56')); c.rectangle(-10, 610, W + 20, 34); c.fill()   # bridge deck edge
    # a lantern hanging under the arch
    c.set_source_rgb(*rgb('#2a2a30')); c.set_line_width(3); c.move_to(300, 860); c.line_to(300, 940); c.stroke()
    c.set_source_rgb(*rgb('#ffd88a')); rrect(c, 286, 940, 28, 38, 6); c.fill()

def draw_floor(c, t):
    c.move_to(0, H)
    for x in range(0, W + 1, 6): c.line_to(x, TER.h[x])
    c.line_to(W, H); c.close_path(); c.set_source_rgb(*rgb('#3e3a2e')); c.fill()
    c.set_source_rgba(0, 0, 0, 0.12); c.set_line_width(3)
    for x in range(0, W, 140): c.move_to(x, GROUND + 30); c.line_to(x + 60, GROUND + 30); c.stroke()
    for (a, b, m, kind) in ZONES:
        if kind == 'rug':   # soft moss cushions
            for j, x in enumerate(range(int(a) + 20, int(b) - 10, 30)):
                y = TER.y(x) + 2; c.set_source_rgb(*rgb(('#4a6a3a', '#3e5e32')[j % 2]))
                c.save(); c.translate(x, y); c.scale(22, 14); c.arc(0, 0, 1, math.pi, 2 * math.pi); c.restore(); c.fill()
        elif kind == 'creak':   # dry crackly leaves
            for j, x in enumerate(range(int(a) + 12, int(b) - 12, 18)):
                y = TER.y(x) - 3 - (j % 2) * 6; c.set_source_rgb(*rgb(('#a8642a', '#c08a3a', '#8a4a22')[j % 3]))
                c.save(); c.translate(x, y); c.rotate((j * 1.3) % 1.6 - 0.8); c.scale(16, 7); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
        else:   # old clay pots and glass bottles
            for j, x in enumerate(range(int(a) + 22, int(b) - 12, 36)):
                y = TER.y(x) - 2
                if j % 2 == 0:
                    c.set_source_rgb(*rgb('#a0583a')); c.move_to(x - 10, y - 40); c.line_to(x + 10, y - 40); c.curve_to(x + 22, y - 26, x + 18, y, x + 10, y); c.line_to(x - 10, y); c.curve_to(x - 18, y, x - 22, y - 26, x - 10, y - 40); c.close_path(); c.fill()
                else:
                    c.set_source_rgba(0.4, 0.7, 0.5, 0.9); rrect(c, x - 10, y - 30, 20, 30, 5); c.fill(); c.rectangle(x - 4, y - 44, 8, 16); c.fill()
    c.set_source_rgb(*rgb('#5a5444')); c.set_line_width(4)
    for x in range(0, W + 1, 6): (c.move_to if x == 0 else c.line_to)(x, TER.h[x])
    c.stroke()
    for (x0, x1) in ((0, WALL_L), (WALL_R, W)):   # bridge pillars as walls
        c.set_source_rgb(*rgb('#3a3a46')); c.rectangle(x0 - 10, 990, x1 - x0 + 20, GROUND + 40 - 990); c.fill()
        c.set_source_rgb(*rgb('#2c2c36'))
        for k, yy in enumerate(range(1040, GROUND + 40, 60)):
            c.rectangle(x0 - 10, yy, x1 - x0 + 20, 5); c.fill()
            c.rectangle(x0 + (x1 - x0) * (0.3 if k % 2 else 0.65), yy - 55, 5, 55); c.fill()

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
        c.set_source_rgb(*rgb('#6a7a58')); rrect(c, px - 75, GROUND - 190, 150, 150, 60); c.fill()
        c.set_source_rgb(*rgb('#56654a'))
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
