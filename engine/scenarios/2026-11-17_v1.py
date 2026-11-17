"""2026-11-17 v1 — NOISE – WAKE %: the SLEEPING GIANT CAT. Gloop is a passive rigid ball (Ball) bouncing across a
living room at night while a giant tabby cat naps curled up on a floor cushion. Every landing makes noise
proportional to the real impact speed times the floor under him (fluffy rug x0.35, wooden floor x1, creaky loose
floorboards x2.2, squeaky cat toys x3); bumps into the bookcase / armchair add a little. Noise settles slowly.
100% = WOKEN UP -> the cat wakes, hisses and paw-swats him across the room."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the sleeping giant cat'
SEED = int(os.environ.get('SEED', 18))
rng = random.Random(SEED)

class S: pass
S.HOOK1 = 'WILL GLOOP SNEAK PAST'; S.HOOK2 = 'THE SLEEPING GIANT CAT?'; S.HOOK2_SIZE = 74; S.FAIL_WORD = 'WOKEN UP!'; S.FAIL_SIZE = 140
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
def draw_bear(c, t, awake_k):   # a giant grey tabby cat curled up asleep on a big cushion
    fur, fur2, stripe, pink = rgb('#7a7480'), rgb('#625c68'), rgb('#4e4854'), rgb('#d89aa8')
    br = (1 - awake_k) * 6 * math.sin(t * 1.7)
    # big round floor cushion
    c.set_source_rgb(*rgb('#5a3a5e')); c.save(); c.translate(BEAR_X, BEAR_Y + 10); c.scale(330, 70); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    c.set_source_rgb(*rgb('#6e4a72')); c.save(); c.translate(BEAR_X, BEAR_Y - 6); c.scale(300, 46); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    c.save(); c.translate(BEAR_X, BEAR_Y - 20)
    # body (curled loaf)
    c.set_source_rgb(*fur); c.save(); c.translate(30, -120); c.scale(250, 140 + br); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    c.set_source_rgb(*stripe)   # tabby stripes on the back
    for k in range(5):
        c.save(); c.translate(-60 + k * 55, -240 - br + abs(k - 2) * 12); c.rotate(0.15 * (k - 2)); c.scale(14, 40); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    # tail wrapped around the front, tip twitching
    tw = 14 * math.sin(t * 1.3)
    c.set_source_rgb(*fur2); c.set_line_width(46); c.set_line_cap(cairo.LINE_CAP_ROUND)
    c.move_to(260, -60); c.curve_to(250, 20, 40, 30, -150, 10 + tw); c.stroke()
    c.set_source_rgb(*stripe); c.set_line_width(46)
    for k in range(3): c.move_to(140 - k * 90, 18 - k * 2); c.line_to(150 - k * 90, 18 - k * 2); c.stroke()
    c.set_line_cap(cairo.LINE_CAP_BUTT)
    # front paws tucked
    c.set_source_rgb(*rgb('#d8d0d8'))
    for px in (-170, -90): c.save(); c.translate(px, -8); c.scale(46, 26); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    # head: resting on the paws while asleep, lifts when awake
    lift = 150 * awake_k
    hx, hy = -190, -110 - lift
    c.set_source_rgb(*fur)
    for s in (-1, 1):   # ears
        c.move_to(hx + s * 40, hy - 70); c.line_to(hx + s * 105, hy - 150 - 10 * awake_k); c.line_to(hx + s * 112, hy - 40); c.close_path(); c.fill()
    c.set_source_rgb(*pink)
    for s in (-1, 1): c.move_to(hx + s * 60, hy - 75); c.line_to(hx + s * 100, hy - 128 - 10 * awake_k); c.line_to(hx + s * 102, hy - 60); c.close_path(); c.fill()
    c.set_source_rgb(*fur); c.save(); c.translate(hx, hy); c.scale(135, 110); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    c.set_source_rgb(*stripe)
    for k in (-1, 0, 1): c.save(); c.translate(hx + k * 28, hy - 88); c.scale(9, 22); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    c.set_source_rgb(*rgb('#d8d0d8')); c.save(); c.translate(hx, hy + 40); c.scale(70, 45); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()   # muzzle
    c.set_source_rgb(*pink); c.move_to(hx - 14, hy + 10); c.line_to(hx + 14, hy + 10); c.line_to(hx, hy + 26); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#2a2430')); c.set_line_width(5)
    if awake_k < 0.5:
        for s in (-1, 1): c.arc(hx + s * 55, hy - 20, 22, 0.3, math.pi - 0.3); c.stroke()   # closed eyes
        c.move_to(hx, hy + 26); c.curve_to(hx - 10, hy + 44, hx - 26, hy + 44, hx - 32, hy + 34); c.stroke()
        c.move_to(hx, hy + 26); c.curve_to(hx + 10, hy + 44, hx + 26, hy + 44, hx + 32, hy + 34); c.stroke()
    else:
        for s in (-1, 1):
            c.set_source_rgb(*rgb('#e8d040')); c.save(); c.translate(hx + s * 55, hy - 20); c.scale(30, 26); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
            c.set_source_rgb(*rgb('#1a1408')); c.save(); c.translate(hx + s * 55, hy - 20); c.scale(7, 22); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
        c.set_source_rgb(*rgb('#5a1a2a')); c.save(); c.translate(hx, hy + 52); c.scale(34, 26 * awake_k); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
        c.set_source_rgb(*rgb('#f0f0e8'))
        for s in (-1, 1): c.move_to(hx + s * 26, hy + 34); c.line_to(hx + s * 18, hy + 54); c.line_to(hx + s * 12, hy + 34); c.close_path(); c.fill()
    c.set_source_rgba(0.9, 0.9, 0.9, 0.6); c.set_line_width(2.5)   # whiskers
    for s in (-1, 1):
        for k in range(3): c.move_to(hx + s * 50, hy + 30 + k * 10); c.line_to(hx + s * 140, hy + 18 + k * 18); c.stroke()
    c.restore()
    if awake_k < 0.5:
        for i in range(3):
            k = (t * 0.45 + i / 3) % 1
            text_at(c, 'Z', BEAR_X - 120 + 50 * k + 20 * math.sin(t * 2 + i), BEAR_Y - 330 - k * 240, 40 + 40 * k, rgb('#7fe0ff'), lw=6)
    elif awake_k > 0.8:
        text_at(c, 'HISSSS!', BEAR_X, BEAR_Y - 580, 104, rgb('#ffd36b'))

def draw_bg(c, t):
    c.set_source_rgb(*rgb('#1c1a24')); c.rectangle(0, HEAD, W, H - HEAD); c.fill()
    # wallpaper with faint vertical stripes
    c.set_source_rgb(*rgb('#26222e')); c.rectangle(0, HEAD, W, 1500 - HEAD); c.fill()
    c.set_source_rgba(1, 1, 1, 0.025)
    for x in range(0, W, 60): c.rectangle(x, HEAD, 22, 1500 - HEAD); c.fill()
    # window with the moon + curtains
    c.set_source_rgb(*rgb('#3a3040')); c.rectangle(330, HEAD + 60, 420, 300); c.fill()
    c.set_source_rgb(*rgb('#18203a')); c.rectangle(346, HEAD + 76, 388, 268); c.fill()
    c.set_source_rgb(*rgb('#e6dfc4')); c.arc(640, HEAD + 150, 34, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#3a3040')); c.rectangle(536, HEAD + 76, 8, 268); c.fill(); c.rectangle(346, HEAD + 206, 388, 8); c.fill()
    c.set_source_rgb(*rgb('#4a2e3a'))
    for (x0, s) in ((300, 1), (780, -1)):
        c.move_to(x0, HEAD + 40); c.line_to(x0 + s * 90, HEAD + 40); c.curve_to(x0 + s * 60, HEAD + 200, x0 + s * 80, HEAD + 300, x0 + s * 50, HEAD + 420); c.line_to(x0, HEAD + 420); c.close_path(); c.fill()
    c.set_source_rgba(0.75, 0.8, 0.95, 0.05); c.move_to(346, HEAD + 344); c.line_to(734, HEAD + 344); c.line_to(880, 1500); c.line_to(220, 1500); c.close_path(); c.fill()
    # picture frames + wall clock
    c.set_source_rgb(*rgb('#6a5a3a')); c.rectangle(130, 860, 150, 120); c.fill(); c.rectangle(820, 840, 130, 160); c.fill()
    c.set_source_rgb(*rgb('#2e3a40')); c.rectangle(142, 872, 126, 96); c.fill(); c.rectangle(832, 852, 106, 136); c.fill()
    c.set_source_rgb(*rgb('#3a4a3a')); c.move_to(142, 968); c.line_to(190, 910); c.line_to(230, 950); c.line_to(268, 900); c.line_to(268, 968); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#d8c8a0')); c.arc(540, 800, 46, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#2a2430')); c.set_line_width(5); c.move_to(540, 800); c.line_to(540 + 30 * math.sin(t * 0.2), 800 - 30 * math.cos(t * 0.2)); c.stroke()
    c.move_to(540, 800); c.line_to(560, 790); c.stroke()
    # skirting board
    c.set_source_rgb(*rgb('#3a3442')); c.rectangle(0, 1470, W, 40); c.fill()

def draw_floor(c, t):
    c.move_to(0, H)
    for x in range(0, W + 1, 6): c.line_to(x, TER.h[x])
    c.line_to(W, H); c.close_path(); c.set_source_rgb(*rgb('#4a3a2e')); c.fill()   # wooden floor
    c.set_source_rgba(0, 0, 0, 0.15); c.set_line_width(3)
    for y in range(GROUND + 40, H, 50): c.move_to(0, y); c.line_to(W, y); c.stroke()
    for (a, b, m, kind) in ZONES:
        if kind == 'rug':   # soft fluffy rug
            c.set_source_rgb(*rgb('#3a5a6a')); c.move_to(a, TER.y(a) + 2)
            for x in range(int(a), int(b) + 1, 6): c.line_to(x, TER.y(x) + 2)
            c.line_to(b, TER.y(b) + 26); c.line_to(a, TER.y(a) + 26); c.close_path(); c.fill()
            c.set_source_rgb(*rgb('#c8d0c0'))
            for x in range(int(a) + 6, int(b), 14): c.rectangle(x, TER.y(x) + 24, 4, 10); c.fill()
        elif kind == 'creak':   # creaky loose floorboards
            c.set_source_rgb(*rgb('#6a4a30')); c.move_to(a, TER.y(a))
            for x in range(int(a), int(b) + 1, 6): c.line_to(x, TER.y(x))
            c.line_to(b, TER.y(b) + 40); c.line_to(a, TER.y(a) + 40); c.close_path(); c.fill()
            c.set_source_rgb(*rgb('#3a2818')); c.set_line_width(3)
            for x in range(int(a) + 30, int(b), 50): c.move_to(x, TER.y(x)); c.line_to(x, TER.y(x) + 40); c.stroke()
            c.set_source_rgb(*rgb('#a0a0a0'))
            for x in range(int(a) + 15, int(b), 50): c.arc(x, TER.y(x) + 8, 3, 0, 2 * math.pi); c.fill()
        else:   # squeaky cat toys: rubber mice + jingle balls
            for j, x in enumerate(range(int(a) + 22, int(b) - 12, 40)):
                y = TER.y(x) - 2
                if j % 2 == 0:
                    c.set_source_rgb(*rgb('#a8a0b0')); c.save(); c.translate(x, y - 10); c.scale(18, 11); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
                    c.set_source_rgb(*rgb('#e09aa8')); c.arc(x - 8, y - 22, 6, 0, 2 * math.pi); c.fill()
                    c.set_source_rgb(*rgb('#e09aa8')); c.set_line_width(3); c.move_to(x + 18, y - 8); c.curve_to(x + 30, y - 8, x + 30, y - 20, x + 38, y - 18); c.stroke()
                else:
                    c.set_source_rgb(*rgb(('#e05a8a', '#5ab0e0', '#e0c040')[j % 3])); c.arc(x, y - 12, 12, 0, 2 * math.pi); c.fill()
                    c.set_source_rgba(1, 1, 1, 0.5); c.arc(x - 4, y - 16, 3, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#6a5440')); c.set_line_width(4)
    for x in range(0, W + 1, 6): (c.move_to if x == 0 else c.line_to)(x, TER.h[x])
    c.stroke()
    # left wall: a tall bookcase side; right wall: an armchair
    x1 = WALL_L
    c.set_source_rgb(*rgb('#4a3424')); c.rectangle(-10, 860, x1 + 10, GROUND + 40 - 860); c.fill()
    c.set_source_rgb(*rgb('#2e2018'))
    for yy in range(900, GROUND, 150): c.rectangle(0, yy, x1 - 14, 120); c.fill()
    for i, yy in enumerate(range(900, GROUND, 150)):
        for k in range(3):
            c.set_source_rgb(*rgb(('#6a3a3a', '#3a5a6a', '#6a6a3a', '#4a3a6a')[(i + k) % 4])); c.rectangle(4 + k * 22, yy + 30 + (k % 2) * 10, 18, 90 - (k % 2) * 10); c.fill()
    x0 = WALL_R
    c.set_source_rgb(*rgb('#6a3a3a')); rrect(c, x0, 1180, W - x0 + 30, GROUND + 40 - 1180, 30); c.fill()
    c.set_source_rgb(*rgb('#7a4646')); rrect(c, x0 - 14, 1280, 80, GROUND + 40 - 1280, 30); c.fill()
    c.set_source_rgb(*rgb('#5a3030')); c.rectangle(x0 + 20, 1390, W - x0, 20); c.fill()

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
        c.set_source_rgb(*rgb('#7a7480')); c.set_line_width(70); c.set_line_cap(cairo.LINE_CAP_ROUND)
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
