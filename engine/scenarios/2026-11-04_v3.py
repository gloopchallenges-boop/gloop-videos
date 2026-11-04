"""2026-11-04 v3 — NOISE – WAKE %: the SLEEPING GUARD DOG. Gloop is a passive rigid ball (Ball) bouncing
on the lawn of a backyard at night while a big guard dog (REX) sleeps in front of its doghouse. Every
landing makes noise proportional to the real impact speed times the ground under him (leaf pile x0.35,
grass x1, gravel x2.2, squeaky toys x3); wall bumps add a little. Noise settles slowly when quiet.
100% = WOKEN UP -> the dog bounds up and paws him across the yard."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the sleeping guard dog'
SEED = int(os.environ.get('SEED', 16))
rng = random.Random(SEED)

class S: pass
S.HOOK1 = 'WILL GLOOP SNEAK PAST'; S.HOOK2 = 'THE GUARD DOG?'; S.HOOK2_SIZE = 96; S.FAIL_WORD = 'WOKEN UP!'; S.FAIL_SIZE = 140
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
    text_at(c, 'Z', bx - 52, 231, 54, rgb('#9fb6ff'), lw=8)
S.draw_bar = draw_bar

BEAR_X, BEAR_Y = 560, 1370
def draw_bear(c, t, awake_k):   # sleeping guard dog curled in front of its doghouse
    fur, fur2, fur3 = rgb('#8a6a4a'), rgb('#6e5238'), rgb('#b8946a')
    breath = 1 + 0.035 * math.sin(t * 2.6) * (1 - awake_k)
    c.save(); c.translate(BEAR_X, BEAR_Y - 30 * awake_k)
    # tail
    c.set_source_rgb(*fur2); c.set_line_width(30); c.set_line_cap(cairo.LINE_CAP_ROUND)
    wag = 0.4 * math.sin(t * 20) * awake_k
    c.move_to(-250, 20); c.curve_to(-330, -10, -340, -80 + 60 * wag, -300, -120 + 80 * wag); c.stroke()
    # body
    c.set_source_rgb(*fur); c.save(); c.scale(1, breath); c.save(); c.scale(270, 100); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.restore(); c.fill()
    c.set_source_rgb(*fur3); c.save(); c.translate(-30, 30); c.scale(170, 50); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    # spiked collar + head
    hx, hy = 250, -20 - 60 * awake_k
    c.set_source_rgb(*rgb('#c0392b')); c.set_line_width(22); c.move_to(hx - 85, hy + 30); c.line_to(hx - 70, hy + 110); c.stroke()
    c.set_source_rgb(*fur); c.arc(hx, hy, 95, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*fur2)   # floppy ears
    for ex in (-1, 1):
        c.save(); c.translate(hx + ex * 70, hy - 50); c.rotate(ex * (0.5 - 0.5 * awake_k)); c.scale(32, 70); c.arc(0, 0.6, 1, 0, 2 * math.pi); c.restore(); c.fill()
    c.set_source_rgb(*fur3); c.save(); c.translate(hx + 40, hy + 35); c.scale(70, 46); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    c.set_source_rgb(0.1, 0.07, 0.06); c.save(); c.translate(hx + 80, hy + 18); c.scale(22, 16); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    c.set_line_cap(cairo.LINE_CAP_ROUND)
    for ex in (-30, 40):
        if awake_k < 0.5:
            c.set_line_width(7); c.set_source_rgb(0.12, 0.08, 0.06); c.arc(hx + ex, hy - 20, 15, 0.2, math.pi - 0.2); c.stroke()
        else:
            c.set_source_rgb(1, 1, 0.9); c.arc(hx + ex, hy - 22, 17, 0, 2 * math.pi); c.fill()
            c.set_source_rgb(0.1, 0.05, 0.05); c.arc(hx + ex + 4, hy - 20, 8, 0, 2 * math.pi); c.fill()
            c.set_line_width(9); c.move_to(hx + ex - 20, hy - 50 + (8 if ex < 0 else 0)); c.line_to(hx + ex + 20, hy - 44 - (8 if ex < 0 else 0)); c.stroke()
    if awake_k > 0.5:
        c.set_source_rgb(0.35, 0.08, 0.1); c.save(); c.translate(hx + 45, hy + 62); c.scale(40, 26 * awake_k); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
        c.set_source_rgb(1, 1, 0.95)
        for dx in (-20, 20): c.move_to(hx + 45 + dx - 7, hy + 44); c.line_to(hx + 45 + dx, hy + 60); c.line_to(hx + 45 + dx + 7, hy + 44); c.close_path(); c.fill()
    # front paws
    c.set_source_rgb(*fur3)
    for dx in (90, 170): c.save(); c.translate(dx, 85); c.scale(45, 22); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    c.restore()
    if awake_k < 0.5:
        for i in range(3):
            k = (t * 0.45 + i / 3) % 1
            text_at(c, 'Z', BEAR_X + 360 + 50 * k + 20 * math.sin(t * 2 + i), BEAR_Y - 200 - k * 280, 40 + 40 * k, rgb('#9fb6ff'), lw=6)
    elif awake_k > 0.8:
        text_at(c, 'WOOF!', BEAR_X + 120, BEAR_Y - 330, 90, rgb('#ffd36b'))

def draw_bg(c, t):
    c.set_source_rgb(*rgb('#161b2c')); c.rectangle(0, HEAD, W, H - HEAD); c.fill()
    c.set_source_rgb(*rgb('#e6dfc4')); c.arc(860, 520, 55, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#161b2c')); c.arc(885, 505, 50, 0, 2 * math.pi); c.fill()
    for i in range(14):
        c.set_source_rgba(1, 1, 1, 0.4); c.arc((i * 271) % W, HEAD + 60 + (i * 137) % 420, 3, 0, 2 * math.pi); c.fill()
    # house wall with lit window, wooden fence
    c.set_source_rgb(*rgb('#2a2638')); c.rectangle(0, 760, 420, GROUND - 760); c.fill()
    c.set_source_rgb(*rgb('#3a2e40')); c.move_to(-20, 770); c.line_to(200, 620); c.line_to(440, 770); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#e8c46a')); rrect(c, 120, 860, 170, 150, 8); c.fill()
    c.set_source_rgb(*rgb('#2a2638')); c.set_line_width(10); c.move_to(205, 860); c.line_to(205, 1010); c.stroke()
    c.set_source_rgb(*rgb('#3b3040'))
    for x in range(420, W, 64):
        c.move_to(x + 4, 1120); c.line_to(x + 30, 1095); c.line_to(x + 56, 1120); c.line_to(x + 56, GROUND); c.line_to(x + 4, GROUND); c.close_path(); c.fill()
    c.rectangle(420, 1170, W, 18); c.fill(); c.rectangle(420, 1330, W, 18); c.fill()
    # doghouse behind the dog
    c.set_source_rgb(*rgb('#7a3d33')); c.rectangle(560, 1060, 340, 260); c.fill()
    c.set_source_rgb(*rgb('#5a2a24')); c.move_to(530, 1070); c.line_to(730, 930); c.line_to(930, 1070); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#120e14')); c.arc(730, 1240, 85, math.pi, 2 * math.pi); c.rectangle(645, 1240, 170, 80); c.fill()
    font(c, 40); c.set_source_rgb(*rgb('#e6dfc4')); e = c.text_extents('REX'); c.move_to(730 - e.width / 2, 1110); c.show_text('REX')
    c.set_source_rgb(*rgb('#8a8f99')); c.save(); c.translate(380, GROUND - 10); c.scale(60, 18); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()   # bowl
    c.set_source_rgb(*rgb('#2e2622')); c.save(); c.translate(380, GROUND - 16); c.scale(44, 8); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()

def draw_floor(c, t):
    c.move_to(0, H)
    for x in range(0, W + 1, 6): c.line_to(x, TER.h[x])
    c.line_to(W, H); c.close_path(); c.set_source_rgb(*rgb('#3e5230')); c.fill()
    c.set_source_rgb(*rgb('#2f4024'))
    for x in range(10, W, 46): c.move_to(x, TER.y(x) + 30 + (x * 13) % 40); c.line_to(x + 8, TER.y(x) + 10 + (x * 13) % 40); c.line_to(x + 16, TER.y(x) + 30 + (x * 13) % 40); c.close_path(); c.fill()
    for (a, b, m, kind) in ZONES:
        y0 = TER.y((a + b) / 2)
        if kind == 'rug':   # soft pile of leaves
            for j, x in enumerate(range(int(a) + 10, int(b) - 10, 22)):
                c.set_source_rgb(*rgb(('#8a5a2a', '#a8742e', '#6e4a26')[j % 3])); c.save(); c.translate(x, TER.y(x) + 8 + (j % 2) * 10); c.rotate(j); c.scale(22, 10); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
        elif kind == 'creak':   # crunchy gravel path
            c.set_source_rgb(*rgb('#6a6670')); c.rectangle(a, TER.y(a) - 2, b - a, 90); c.fill()
            for j, x in enumerate(range(int(a) + 6, int(b) - 6, 18)):
                c.set_source_rgb(*rgb(('#8d8a94', '#55525c', '#a3a0aa')[j % 3])); c.arc(x, TER.y(x) + 8 + (j * 7) % 50, 8, 0, 2 * math.pi); c.fill()
        else:   # squeaky dog toys
            for j, x in enumerate(range(int(a) + 28, int(b) - 10, 56)):
                y = TER.y(x) - 6
                if j % 2 == 0:
                    c.set_source_rgb(*rgb('#e0b030')); c.save(); c.translate(x, y); c.scale(26, 18); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
                    c.arc(x + 22, y - 14, 12, 0, 2 * math.pi); c.fill(); c.set_source_rgb(*rgb('#e07a20')); c.move_to(x + 32, y - 16); c.line_to(x + 46, y - 12); c.line_to(x + 32, y - 9); c.close_path(); c.fill()
                else:
                    c.set_source_rgb(*rgb('#d24a6a')); c.arc(x, y, 18, 0, 2 * math.pi); c.fill()
                    c.set_source_rgb(*rgb('#f0e0e0')); c.set_line_width(4); c.arc(x, y, 18, 0.5, 2.5); c.stroke()
    c.set_source_rgb(*rgb('#55703f')); c.set_line_width(4)
    for x in range(0, W + 1, 6): (c.move_to if x == 0 else c.line_to)(x, TER.h[x])
    c.stroke()
    for (x0, x1) in ((0, WALL_L), (WALL_R, W)):   # stacked garden planters as walls
        c.set_source_rgb(*rgb('#5a4030')); c.rectangle(x0, 1000, x1 - x0, GROUND + 20 - 1000); c.fill()
        c.set_source_rgb(*rgb('#46301f'))
        for yy in range(1000, GROUND, 90): c.rectangle(x0, yy, x1 - x0, 10); c.fill()
        c.set_source_rgb(*rgb('#3e6a3a')); c.arc((x0 + x1) / 2, 990, (x1 - x0) * 0.6, math.pi, 2 * math.pi); c.fill()

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
        c.set_source_rgb(*rgb('#8a6a4a')); c.arc(px, GROUND - 110, 75, 0, 2 * math.pi); c.fill()
        c.set_source_rgb(*rgb('#b8946a'))
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
