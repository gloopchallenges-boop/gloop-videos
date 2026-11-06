"""2026-11-06 v3 — NOISE – WAKE %: the SLEEPING ROBOT. Gloop is a passive rigid ball (Ball) bouncing on the
floor of a junkyard workshop at night while a big grumpy robot (BOLT-9) sleeps slumped against the wall. Every
landing makes noise proportional to the real impact speed times the floor under him (oily rag pile x0.35,
concrete x1, metal grate x2.2, loose bolts x3); wall bumps add a little. Noise settles slowly when quiet.
100% = WOKEN UP -> the robot powers on and swats him across the workshop."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the sleeping robot'
SEED = int(os.environ.get('SEED', 32))
rng = random.Random(SEED)

class S: pass
S.HOOK1 = 'WILL GLOOP SNEAK PAST'; S.HOOK2 = 'THE SLEEPING ROBOT?'; S.HOOK2_SIZE = 86; S.FAIL_WORD = 'WOKEN UP!'; S.FAIL_SIZE = 140
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
if T_FAIL: S.events += [[T_FAIL, 'roar'], [T_FAIL + 0.05, 'whoosh']]
S.AMB = {'drone': 44}

def draw_bar(c, t, f):
    p = WAKE[f]; recent = any(n[0] <= t < n[0] + 0.3 and n[4] for n in NOISES)
    bx = bar(c, p / 100, f'WAKE {int(p)}%', bad_col(p / 100), 0.12 if recent else 0, bw=640, x_off=36)
    text_at(c, 'Z', bx - 52, 231, 54, rgb('#7fe0ff'), lw=8)
S.draw_bar = draw_bar

BEAR_X, BEAR_Y = 560, 1450
def draw_bear(c, t, awake_k):   # sleeping robot slumped in front of the back wall
    m1, m2, m3 = rgb('#6a7480'), rgb('#525a66'), rgb('#8a94a0')
    sag = (1 - awake_k) * (6 * math.sin(t * 2.6) + 18)
    c.save(); c.translate(BEAR_X + 60, BEAR_Y - 40 * awake_k)
    # legs stretched out
    c.set_source_rgb(*m2)
    for dx in (-120, 120): rrect(c, dx - 45, 60, 90, 80, 14); c.fill()
    c.set_source_rgb(*rgb('#3a404a'))
    for dx in (-120, 120): rrect(c, dx - 60, 120, 120, 40, 12); c.fill()
    # torso
    c.set_source_rgb(*m1); rrect(c, -200, -170 + sag * 0.3, 400, 250, 34); c.fill()
    c.set_source_rgb(*m2); rrect(c, -150, -130 + sag * 0.3, 300, 150, 20); c.fill()
    # chest panel lights
    for i in range(4):
        on = awake_k > 0.5 or (int(t * 1.2) + i) % 4 == 0
        col = rgb('#ff5050') if awake_k > 0.5 else (rgb('#5ad0ff') if on else rgb('#2a3440'))
        c.set_source_rgb(*col); c.arc(-90 + i * 60, -60 + sag * 0.3, 14, 0, 2 * math.pi); c.fill()
    font(c, 34); c.set_source_rgb(*rgb('#c9a85a')); e = c.text_extents('BOLT-9'); c.move_to(-e.width / 2, 58 + sag * 0.3); c.show_text('BOLT-9')
    # arms resting
    c.set_source_rgb(*m2); c.set_line_width(46); c.set_line_cap(cairo.LINE_CAP_ROUND)
    c.move_to(-210, -120); c.line_to(-260, 40); c.stroke(); c.move_to(210, -120); c.line_to(260 + 60 * awake_k, 40 - 140 * awake_k); c.stroke()
    c.set_source_rgb(*m3); c.arc(-260, 60, 38, 0, 2 * math.pi); c.fill(); c.arc(260 + 60 * awake_k, 60 - 140 * awake_k, 38, 0, 2 * math.pi); c.fill()
    # head (drooped to the side while asleep)
    hx, hy = 0, -250 - 60 * awake_k
    c.save(); c.translate(hx, hy + sag); c.rotate(0.28 * (1 - awake_k))
    c.set_source_rgb(*m2); c.rectangle(-30, 40, 60, 50); c.fill()   # neck
    c.set_source_rgb(*m1); rrect(c, -130, -90, 260, 160, 30); c.fill()
    c.set_source_rgb(*rgb('#20262e')); rrect(c, -105, -60, 210, 80, 20); c.fill()   # visor
    c.set_source_rgb(*m3); c.set_line_width(8); c.move_to(0, -90); c.line_to(0, -150); c.stroke()
    c.set_source_rgb(*(rgb('#ff4040') if awake_k > 0.5 else rgb('#7a3030'))); c.arc(0, -160, 14, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*m2); rrect(c, -150, -40, 24, 60, 8); c.fill(); rrect(c, 126, -40, 24, 60, 8); c.fill()   # ear bolts
    for ex in (-50, 50):
        if awake_k < 0.5:
            c.set_source_rgb(*rgb('#3a8ab0')); c.set_line_width(7); c.move_to(ex - 26, -18); c.line_to(ex + 26, -18); c.stroke()
        else:
            c.set_source_rgb(*rgb('#ff4040')); c.arc(ex, -20, 22, 0, 2 * math.pi); c.fill()
            c.set_source_rgb(*rgb('#20262e')); c.set_line_width(10); c.move_to(ex - 30, -54 + (12 if ex < 0 else 0)); c.line_to(ex + 30, -54 + (0 if ex < 0 else 12)); c.stroke()
    if awake_k > 0.5:
        c.set_source_rgb(*rgb('#ff8080')); rrect(c, -50, 36, 100, 14, 5); c.fill()
    c.restore()
    c.restore()
    if awake_k < 0.5:
        for i in range(3):
            k = (t * 0.45 + i / 3) % 1
            text_at(c, 'Z', BEAR_X + 260 + 50 * k + 20 * math.sin(t * 2 + i), BEAR_Y - 380 - k * 260, 40 + 40 * k, rgb('#7fe0ff'), lw=6)
    elif awake_k > 0.8:
        text_at(c, 'BEEP!', BEAR_X + 80, BEAR_Y - 560, 90, rgb('#ffd36b'))

def draw_bg(c, t):
    c.set_source_rgb(*rgb('#17171f')); c.rectangle(0, HEAD, W, H - HEAD); c.fill()
    # corrugated back wall
    c.set_source_rgb(*rgb('#22232c')); c.rectangle(0, 620, W, GROUND - 620); c.fill()
    c.set_source_rgb(*rgb('#1c1d25'))
    for x in range(0, W, 40): c.rectangle(x, 620, 16, GROUND - 620); c.fill()
    # high window with moon
    c.set_source_rgb(*rgb('#141c2c')); c.rectangle(620, 420, 300, 170); c.fill()
    c.set_source_rgb(*rgb('#e6dfc4')); c.arc(840, 480, 34, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#30313c')); c.set_line_width(10); c.rectangle(620, 420, 300, 170); c.stroke(); c.move_to(770, 420); c.line_to(770, 590); c.stroke()
    # shelves with junk
    c.set_source_rgb(*rgb('#3a3540')); c.rectangle(60, 760, 420, 16); c.fill(); c.rectangle(60, 920, 420, 16); c.fill()
    for (x, y, w, h, col) in ((80, 700, 70, 60, '#5a4a3a'), (170, 720, 50, 40, '#6a3030'), (250, 690, 90, 70, '#3a4a5a'), (370, 710, 80, 50, '#4a5a3a'),
                              (90, 870, 100, 50, '#4a4a54'), (220, 850, 60, 70, '#6a5a2a'), (320, 880, 120, 40, '#3a3a44')):
        c.set_source_rgb(*rgb(col)); c.rectangle(x, y, w, h); c.fill()
    # hanging lamp (one quiet light source)
    c.set_source_rgb(*rgb('#3a3a44')); c.set_line_width(4); c.move_to(300, HEAD); c.line_to(300, 520); c.stroke()
    c.move_to(250, 560); c.line_to(350, 560); c.line_to(320, 520); c.line_to(280, 520); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#e8c46a')); c.arc(300, 566, 12, 0, 2 * math.pi); c.fill()
    c.set_source_rgba(1, 0.9, 0.6, 0.05); c.move_to(250, 560); c.line_to(80, GROUND); c.line_to(520, GROUND); c.line_to(350, 560); c.close_path(); c.fill()
    # big tires stacked by the robot
    for (x, y) in ((900, 1480), (900, 1380)):
        c.set_source_rgb(*rgb('#1e1e24')); c.save(); c.translate(x, y); c.scale(110, 48); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
        c.set_source_rgb(*rgb('#2c2c34')); c.save(); c.translate(x, y); c.scale(50, 20); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()

def draw_floor(c, t):
    c.move_to(0, H)
    for x in range(0, W + 1, 6): c.line_to(x, TER.h[x])
    c.line_to(W, H); c.close_path(); c.set_source_rgb(*rgb('#44444c')); c.fill()
    c.set_source_rgba(0, 0, 0, 0.15); c.set_line_width(3)
    for x in range(0, W, 180): c.move_to(x, GROUND + 10); c.line_to(x - 40, H); c.stroke()
    for (a, b, m, kind) in ZONES:
        if kind == 'rug':   # pile of oily rags
            for j, x in enumerate(range(int(a) + 10, int(b) - 10, 24)):
                c.set_source_rgb(*rgb(('#5a4a6a', '#6a5a3a', '#4a5a6a')[j % 3])); c.save(); c.translate(x, TER.y(x) + 8 + (j % 2) * 10); c.rotate(j * 0.7); c.scale(26, 12); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
        elif kind == 'creak':   # rattly metal grate
            c.set_source_rgb(*rgb('#7a8088')); c.rectangle(a, TER.y(a) - 6, b - a, 50); c.fill()
            c.set_source_rgb(*rgb('#2a2e34'))
            for x in range(int(a) + 8, int(b) - 8, 16): c.rectangle(x, TER.y(a) + 6, 8, 26); c.fill()
        else:   # loose bolts and nuts
            for j, x in enumerate(range(int(a) + 20, int(b) - 10, 30)):
                y = TER.y(x) - 6 - (j % 2) * 4
                c.set_source_rgb(*rgb(('#a0a8b0', '#c9a85a')[j % 2]))
                if j % 2 == 0:
                    c.move_to(x + 16, y)
                    for k in range(1, 7): c.line_to(x + 16 * math.cos(k * math.pi / 3), y + 16 * math.sin(k * math.pi / 3))
                    c.close_path(); c.fill(); c.set_source_rgb(*rgb('#44444c')); c.arc(x, y, 5, 0, 2 * math.pi); c.fill()
                else:
                    c.rectangle(x - 14, y - 4, 28, 8); c.fill(); c.rectangle(x - 18, y - 8, 8, 16); c.fill()
    c.set_source_rgb(*rgb('#5a5a64')); c.set_line_width(4)
    for x in range(0, W + 1, 6): (c.move_to if x == 0 else c.line_to)(x, TER.h[x])
    c.stroke()
    for (x0, x1) in ((0, WALL_L), (WALL_R, W)):   # stacked oil drums as walls
        for k, yy in enumerate(range(GROUND - 170, 1000, -170)):
            c.set_source_rgb(*rgb(('#7a3030', '#30507a', '#5a6a30')[(k + (x0 > 0)) % 3])); c.rectangle(x0, yy, x1 - x0, 166); c.fill()
            c.set_source_rgba(0, 0, 0, 0.25); c.rectangle(x0, yy + 40, x1 - x0, 8); c.fill(); c.rectangle(x0, yy + 118, x1 - x0, 8); c.fill()

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
        c.set_source_rgb(*rgb('#8a94a0')); rrect(c, px - 75, GROUND - 190, 150, 150, 30); c.fill()
        c.set_source_rgb(*rgb('#525a66'))
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
