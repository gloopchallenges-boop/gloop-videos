"""2026-11-08 v1 — NOISE – WAKE %: the SLEEPING LION. Gloop is a passive rigid ball (Ball) bouncing on the
dry ground of a savanna at night while a big lion sleeps by a flat rock. Every landing makes noise proportional
to the real impact speed times the ground under him (soft grass x0.35, dirt x1, dry twigs x2.2, tin cans x3);
wall bumps add a little. Noise settles slowly when quiet.
100% = WOKEN UP -> the lion wakes, roars and paws him across the savanna."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the sleeping lion'
SEED = int(os.environ.get('SEED', 32))
rng = random.Random(SEED)

class S: pass
S.HOOK1 = 'WILL GLOOP SNEAK PAST'; S.HOOK2 = 'THE SLEEPING LION?'; S.HOOK2_SIZE = 86; S.FAIL_WORD = 'WOKEN UP!'; S.FAIL_SIZE = 140
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

BEAR_X, BEAR_Y = 600, 1450
def draw_bear(c, t, awake_k):   # sleeping lion lying in front of the rocks
    fur, fur2, mane, mane2 = rgb('#b08a52'), rgb('#94703e'), rgb('#6a4424'), rgb('#56361c')
    br = (1 - awake_k) * 6 * math.sin(t * 2.2)   # breathing
    c.save(); c.translate(BEAR_X, BEAR_Y + 30 - 30 * awake_k); c.scale(0.85, 0.85)
    # tail with tuft
    c.set_source_rgb(*fur2); c.set_line_width(22); c.set_line_cap(cairo.LINE_CAP_ROUND)
    sw = 0.3 * math.sin(t * 1.3) + awake_k * 0.8
    c.move_to(230, 60); c.curve_to(330, 90, 360, 20 - 60 * sw, 330, -40 - 80 * sw); c.stroke()
    c.set_source_rgb(*mane2); c.arc(330, -50 - 80 * sw, 26, 0, 2 * math.pi); c.fill()
    # body
    c.set_source_rgb(*fur); c.save(); c.translate(80, 40); c.scale(250, 105 + br); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    c.set_source_rgb(*fur2); c.save(); c.translate(110, 95); c.scale(200, 40); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    # front paws stretched out
    c.set_source_rgb(*fur)
    for dy in (0, 26):
        rrect(c, -330, 100 + dy, 230, 50, 24); c.fill()
    c.set_source_rgb(*fur2)
    for dy in (0, 26):
        for k in range(3): c.arc(-318 + k * 14, 125 + dy, 5, 0, 2 * math.pi); c.fill()
    # head + mane
    hx, hy = -150, -40 - 110 * awake_k
    c.save(); c.translate(hx, hy); c.rotate(0.22 * (1 - awake_k))
    for i in range(18):
        a = i / 18 * 2 * math.pi; r = 150 + 14 * math.sin(i * 2.3)
        c.set_source_rgb(*(mane if i % 2 else mane2)); c.arc(math.cos(a) * r * 0.75, math.sin(a) * r * 0.75, 52, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*mane); c.arc(0, 0, 135, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*fur); c.arc(0, 10, 95, 0, 2 * math.pi); c.fill()
    for ex in (-70, 70):   # ears
        c.set_source_rgb(*fur); c.arc(ex, -80, 26, 0, 2 * math.pi); c.fill()
        c.set_source_rgb(*fur2); c.arc(ex, -80, 13, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#d8b884')); c.save(); c.translate(0, 50); c.scale(58, 40); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    c.set_source_rgb(*rgb('#3a2414')); c.move_to(-22, 22); c.line_to(22, 22); c.line_to(0, 44); c.close_path(); c.fill()
    for ex in (-42, 42):
        if awake_k < 0.5:
            c.set_source_rgb(*rgb('#3a2414')); c.set_line_width(7); c.arc(ex, -12, 18, 0.2, math.pi - 0.2); c.stroke()
        else:
            c.set_source_rgb(*rgb('#f0c040')); c.arc(ex, -14, 18, 0, 2 * math.pi); c.fill()
            c.set_source_rgb(*rgb('#1a1008')); c.save(); c.translate(ex, -14); c.scale(5, 14); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
            c.set_source_rgb(*rgb('#3a2414')); c.set_line_width(9); c.move_to(ex - 26, -46 + (10 if ex < 0 else 0)); c.line_to(ex + 26, -46 + (0 if ex < 0 else 10)); c.stroke()
    if awake_k > 0.5:   # open roaring mouth
        c.set_source_rgb(*rgb('#5a1a1a')); c.save(); c.translate(0, 72); c.scale(40, 26 * awake_k); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
        c.set_source_rgb(*rgb('#f4ecd8'))
        for sx in (-22, 22): c.move_to(sx - 7, 52); c.line_to(sx + 7, 52); c.line_to(sx, 70); c.close_path(); c.fill()
    else:
        c.set_source_rgb(*rgb('#3a2414')); c.set_line_width(5); c.move_to(0, 44); c.line_to(0, 58); c.stroke()
        c.arc(-14, 58, 14, 0, math.pi); c.stroke(); c.arc(14, 58, 14, 0, math.pi); c.stroke()
    c.restore()
    c.restore()
    if awake_k < 0.5:
        for i in range(3):
            k = (t * 0.45 + i / 3) % 1
            text_at(c, 'Z', BEAR_X - 120 + 50 * k + 20 * math.sin(t * 2 + i), BEAR_Y - 260 - k * 260, 40 + 40 * k, rgb('#7fe0ff'), lw=6)
    elif awake_k > 0.8:
        text_at(c, 'ROAR!', BEAR_X - 60, BEAR_Y - 460, 100, rgb('#ffd36b'))

def draw_bg(c, t):
    c.set_source_rgb(*rgb('#141a2a')); c.rectangle(0, HEAD, W, H - HEAD); c.fill()
    for (sx, sy) in ((90, 420), (220, 520), (420, 400), (610, 480), (980, 430), (860, 600), (330, 640), (70, 700)):
        c.set_source_rgba(1, 1, 0.9, 0.5 + 0.3 * math.sin(t * 2 + sx)); c.arc(sx, sy, 3, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#e6dfc4')); c.arc(800, 520, 70, 0, 2 * math.pi); c.fill()   # moon (one quiet light)
    # far savanna hills
    c.set_source_rgb(*rgb('#1c2232')); c.move_to(0, 1100)
    for x in range(0, W + 1, 60): c.line_to(x, 1080 - 40 * math.sin(x / 170))
    c.line_to(W, GROUND); c.line_to(0, GROUND); c.close_path(); c.fill()
    # acacia tree
    c.set_source_rgb(*rgb('#10141e')); c.set_line_width(26); c.move_to(250, GROUND); c.line_to(270, 900); c.stroke()
    c.set_line_width(14); c.move_to(270, 950); c.line_to(170, 850); c.stroke(); c.move_to(270, 940); c.line_to(380, 860); c.stroke()
    c.save(); c.translate(275, 830); c.scale(230, 50); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    # big flat rock the lion sleeps by
    c.set_source_rgb(*rgb('#2a2a34')); c.move_to(330, GROUND); c.curve_to(360, 1220, 900, 1180, 960, GROUND); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#323240')); c.move_to(420, 1300); c.curve_to(520, 1230, 800, 1230, 880, 1320); c.line_to(860, 1340); c.curve_to(760, 1280, 540, 1280, 440, 1330); c.close_path(); c.fill()

def draw_floor(c, t):
    c.move_to(0, H)
    for x in range(0, W + 1, 6): c.line_to(x, TER.h[x])
    c.line_to(W, H); c.close_path(); c.set_source_rgb(*rgb('#4a3e2c')); c.fill()
    c.set_source_rgba(0, 0, 0, 0.12); c.set_line_width(3)
    for x in range(0, W, 140): c.move_to(x, GROUND + 30); c.line_to(x + 60, GROUND + 30); c.stroke()
    for (a, b, m, kind) in ZONES:
        if kind == 'rug':   # soft tall grass tufts
            for j, x in enumerate(range(int(a) + 10, int(b) - 6, 14)):
                y = TER.y(x) + 4; c.set_source_rgb(*rgb(('#5a6a3a', '#4e5e32')[j % 2])); c.set_line_width(5)
                c.move_to(x, y); c.line_to(x - 6 + (j % 3) * 6, y - 34 - (j % 4) * 8); c.stroke()
        elif kind == 'creak':   # pile of dry crackly twigs
            c.set_source_rgb(*rgb('#8a6a44')); c.set_line_width(7); c.set_line_cap(cairo.LINE_CAP_ROUND)
            for j, x in enumerate(range(int(a) + 12, int(b) - 12, 20)):
                y = TER.y(x) - 4; ang = (j * 1.7) % 1.2 - 0.6
                c.move_to(x - 26 * math.cos(ang), y - 26 * math.sin(ang) - (j % 2) * 8); c.line_to(x + 26 * math.cos(ang), y + 26 * math.sin(ang) - (j % 2) * 8); c.stroke()
        else:   # rattly tin cans left by tourists
            for j, x in enumerate(range(int(a) + 22, int(b) - 12, 36)):
                y = TER.y(x) - 2
                c.set_source_rgb(*rgb(('#a0a8b0', '#b04a3a', '#8a9aa8')[j % 3]))
                if j % 2 == 0: c.rectangle(x - 13, y - 34, 26, 34); c.fill(); c.set_source_rgba(0, 0, 0, 0.25); c.rectangle(x - 13, y - 26, 26, 6); c.fill()
                else: c.rectangle(x - 17, y - 24, 34, 24); c.fill(); c.set_source_rgb(*rgb('#6a747c')); c.save(); c.translate(x + 17, y - 12); c.scale(5, 12); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    c.set_source_rgb(*rgb('#6a5a40')); c.set_line_width(4)
    for x in range(0, W + 1, 6): (c.move_to if x == 0 else c.line_to)(x, TER.h[x])
    c.stroke()
    for (x0, x1) in ((0, WALL_L), (WALL_R, W)):   # stacked boulders as walls
        for k, yy in enumerate(range(GROUND - 150, 1000, -150)):
            c.set_source_rgb(*rgb(('#3a3a46', '#44444f', '#34343e')[(k + (x0 > 0)) % 3])); rrect(c, x0 - 10, yy, x1 - x0 + 20, 146, 40); c.fill()

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
        c.set_source_rgb(*rgb('#b08a52')); rrect(c, px - 75, GROUND - 190, 150, 150, 60); c.fill()
        c.set_source_rgb(*rgb('#94703e'))
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
