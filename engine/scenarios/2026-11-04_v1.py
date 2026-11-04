"""2026-11-04 v1 — GRIP / TUG – GRIP %: the TORNADO. Gloop is a passive rigid ball (Ball) bouncing
across a farm yard at night between a red barn (left wall) and a stack of hay bales (right wall).
A tornado funnel sways just behind the hay bales. Seeded-random gust bursts (strength + length vary)
really pull him toward the funnel and drain his sticky GRIP — faster the closer he is and the
stronger the gust. Between gusts GRIP slowly recovers. GRIP 0% = he's whisked up into the funnel."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the tornado'
SEED = int(os.environ.get('SEED', 5))
rng = random.Random(SEED)

class S: pass
S.HOOK2 = 'THE TORNADO?'; S.HOOK2_SIZE = 100; S.FAIL_WORD = 'WHISKED!'; S.FAIL_SIZE = 150
S.T_START = HOOK_T; S.TL = 12.5; S.T_END = S.T_START + S.TL
GROUND = 1600; R = 58; XMIN, XMAX = 230, 800; BALE_X = XMAX + R
DRAIN, REGEN, PULL = float(os.environ.get('DRAIN', 70)), 5.0, 950.0

BURSTS = []; t = -0.2
while t < S.T_END + 1:
    s = rng.uniform(0.45, 1.0); d = rng.uniform(0.7, 1.6)
    BURSTS.append({'t': t, 'd': d, 's': s}); t += d + rng.uniform(0.8, 2.0)
def burst(t):
    for b in BURSTS:
        if b['t'] <= t < b['t'] + b['d']:
            k = min(1, (t - b['t']) / 0.2, (b['t'] + b['d'] - t) / 0.2); return b['s'] * k
    return 0.0
def TX(t): return 960 + 40 * math.sin(t * 0.8) + 15 * math.sin(t * 2.3)

TER = Terrain(GROUND, seed=SEED, bumps=4, amp=10, soft=False)
N0 = int(40 * FPS); GX, GYS, GRIP, SUCK = [], [], [], []
ball = Ball(rng.uniform(300, 560), TER, R=R, seed=SEED, xmin=XMIN, xmax=XMAX, hop=rng.uniform(220, 290))
grip = 100.0; T_FAIL = None; FX = FY = 0
for f in range(N0):
    t = f / FPS; P = burst(t) if T_FAIL is None else 0.0
    prox = clamp(1 - (TX(t) - ball.x) / 760, 0, 1)
    if T_FAIL is None: ball.vx += P * PULL * (0.3 + 0.7 * prox) / FPS
    ball.step(t)
    if T_FAIL is None and S.T_START <= t < S.T_END:
        grip = clamp(grip - (DRAIN * P * (0.25 + prox ** 1.5)) / FPS + (REGEN / FPS if P == 0 else 0), 0, 100)
        if grip <= 0: T_FAIL = t; FX, FY = ball.x, ball.y
    GX.append(ball.x); GYS.append(ball.y); GRIP.append(grip); SUCK.append(P)
S.OUTCOME = 'fail' if T_FAIL else 'win'
S.T_RES = T_FAIL if T_FAIL else S.T_END
HOVER_Y = 1020
S.GRAB = (900, HOVER_Y) if T_FAIL else (540, GROUND - R)
END = S.END = Ending(S)
if not T_FAIL: gi = min(int(END.T_GRAB * FPS), N0 - 1); S.GRAB = (GX[gi], GYS[gi])
S.events = [[0.05, 'whoosh']]
for b in BURSTS:
    if b['t'] < S.T_RES: S.events.append([max(0, b['t']), 'whoosh']); S.events.append([max(0, b['t']) + 0.3, 'rumble', min(b['d'], S.T_RES - b['t'] + 0.2)])
for (tl, xl, imp) in ball.landings:
    if tl < S.T_RES: S.events.append([tl, 'hop'])
for tw in ball.walls:
    if tw < S.T_RES: S.events.append([tw, 'thump', 0.4])
if T_FAIL: S.events += [[T_FAIL, 'whoosh'], [T_FAIL + 0.4, 'whoosh'], [T_FAIL + 0.9, 'pop']]
S.AMB = {'drone': 48, 'wind': 0.05, 'rumble': 0.015}

def draw_bar(c, t, f):
    p = GRIP[f] / 100; down = SUCK[f] > 0.05 and t < S.T_RES
    bx = bar(c, p, f'GRIP {int(math.ceil(GRIP[f]))}%', good_bad_col(p), 0.1 if down else 0, bw=640, x_off=36)
    c.save(); c.translate(bx - 52, 231); c.set_source_rgb(*rgb('#ffb347')); c.arc(0, 6, 18, 0, 2 * math.pi); c.fill()
    for dx in (-16, -5, 6, 17): c.arc(dx, -16, 7, 0, 2 * math.pi); c.fill()
    c.restore()
S.draw_bar = draw_bar

def draw_bg(c, t):
    c.set_source_rgb(*rgb('#1a1d2b')); c.rectangle(0, HEAD, W, H - HEAD); c.fill()
    # low storm clouds
    c.set_source_rgb(*rgb('#262a3b'))
    for i in range(9):
        x = (i * 150 + t * 25 * (1 + i % 3)) % (W + 300) - 150; y = HEAD + 40 + (i % 3) * 45
        c.save(); c.translate(x, y); c.scale(190, 70); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    # far hills + fence
    c.set_source_rgb(*rgb('#1f2a2a')); c.move_to(0, 1380)
    for x in range(0, W + 1, 60): c.line_to(x, 1380 - 50 * math.sin(x / 260) - 20)
    c.line_to(W, GROUND); c.line_to(0, GROUND); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#3a3226')); c.set_line_width(8)
    for x in range(260, 820, 90): c.move_to(x, GROUND - 120); c.line_to(x, GROUND); c.stroke()
    c.set_line_width(6); c.move_to(240, GROUND - 100); c.line_to(820, GROUND - 100); c.stroke(); c.move_to(240, GROUND - 50); c.line_to(820, GROUND - 50); c.stroke()
    # ground
    TER.fill(c, TER.h, '#3d4a2c', '#232a1a', '#4e5c37')
    # barn = left wall
    bw = XMIN - R
    c.set_source_rgb(*rgb('#6e2b26')); c.rectangle(0, 1000, bw, GROUND - 1000); c.fill()
    c.set_source_rgb(*rgb('#5a221e'))
    for x in range(10, bw, 34): c.rectangle(x, 1000, 5, GROUND - 1000); c.fill()
    c.set_source_rgb(*rgb('#4a1b18')); c.move_to(-20, 1010); c.line_to(bw * 0.55, 880); c.line_to(bw + 20, 1010); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#d9cfb8')); c.set_line_width(7); c.rectangle(25, 1300, bw - 50, GROUND - 1300); c.stroke()
    c.move_to(25, 1300); c.line_to(bw - 25, GROUND); c.stroke(); c.move_to(bw - 25, 1300); c.line_to(25, GROUND); c.stroke()
    c.set_source_rgb(*rgb('#e8c46a')); c.rectangle(bw * 0.3, 1080, bw * 0.4, 70); c.fill()   # one warm window

def draw_tornado(c, t, f):
    P = SUCK[min(f, len(SUCK) - 1)]; x0 = TX(t)
    # funnel: stacked ellipses widening upward, gently swaying
    for i in range(26):
        k = i / 25; y = GROUND - 20 - k * (GROUND - HEAD - 140)
        cx = x0 + 50 * math.sin(t * 1.3 + k * 3) * k
        rw = 45 + 330 * k ** 1.6; rh = 18 + 30 * k
        sh = 0.27 + 0.05 * math.sin(i * 1.7 + t * 9)
        c.set_source_rgba(sh, sh + 0.02, sh + 0.08, 0.95)
        c.save(); c.translate(cx, y); c.scale(rw, rh); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    # spin streaks
    c.set_line_width(5); c.set_source_rgba(0.55, 0.58, 0.66, 0.6)
    for i in range(14):
        k = ((i * 0.071 + t * (0.15 + 0.2 * P)) % 1); y = GROUND - 20 - k * (GROUND - HEAD - 140)
        cx = x0 + 50 * math.sin(t * 1.3 + k * 3) * k; rw = 45 + 330 * k ** 1.6
        a0 = (t * (5 + 6 * P) + i) % (2 * math.pi)
        c.save(); c.translate(cx, y); c.scale(rw * 0.9, 12 + 25 * k); c.arc(0, 0, 1, a0, a0 + 1.4); c.restore(); c.stroke()
    # debris orbiting: hay + leaves
    for i in range(9):
        k = 0.1 + 0.8 * ((i * 0.13 + t * 0.05) % 1); y = GROUND - 30 - k * (GROUND - HEAD - 160)
        cx = x0 + 50 * math.sin(t * 1.3 + k * 3) * k; rw = 45 + 330 * k ** 1.6
        a = t * (4 + 4 * P) + i * 2.1; px = cx + math.cos(a) * rw * 1.05; py = y + math.sin(a) * 20
        if math.sin(a) < 0: continue
        c.save(); c.translate(px, py); c.rotate(a * 2); c.set_source_rgb(*rgb('#c9a94e' if i % 2 else '#5e7a3a')); c.rectangle(-14, -4, 28, 8); c.fill(); c.restore()
    # ground dust ring
    c.set_source_rgba(0.4, 0.38, 0.33, 0.5 + 0.3 * P); c.save(); c.translate(x0, GROUND - 5); c.scale(150 + 60 * P, 26); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()

def draw_bales(c, t):
    x0 = BALE_X
    for row in range(3):
        for col in range(2 - (row == 2)):
            x = x0 + col * 120 + (60 if row == 2 else 0); y = GROUND - 110 * (row + 1)
            c.set_source_rgb(*rgb('#b8913f')); rrect(c, x, y, 118, 108, 10); c.fill()
            c.set_source_rgba(0, 0, 0, 0.15); c.set_line_width(3)
            for yy in range(int(y) + 18, int(y) + 108, 18): c.move_to(x + 6, yy); c.line_to(x + 112, yy); c.stroke()
            c.set_source_rgb(*rgb('#7a5a24')); c.rectangle(x + 30, y, 6, 108); c.fill(); c.rectangle(x + 82, y, 6, 108); c.fill()

PS = Particles(9)
def render(f, c):
    t = f / FPS; fi = min(f, len(GX) - 1); P = SUCK[fi]
    shake = (rng.uniform(-2, 2) * P, rng.uniform(-2, 2) * P)
    c.save(); c.translate(*shake)
    draw_bg(c, t)
    draw_tornado(c, t, f)
    whisk = T_FAIL is not None and t >= T_FAIL
    if END.carried(t) or t >= END.T_GRAB:
        gx, gy = (END.carry_xy(t) if END.carried(t) else S.GRAB)
        if whisk and not END.carried(t):
            k = ease((t - T_FAIL - 0.9) / 0.5); gx, gy = S.GRAB[0], S.GRAB[1]
    elif whisk:
        k = ease((t - T_FAIL) / 0.9)
        cx = lerp(FX, TX(t), k); cy = lerp(FY, HOVER_Y, k)
        a = (t - T_FAIL) * 9; rr = 90 * (1 - ease((t - T_FAIL - 0.9) / 0.6))
        gx = lerp(cx, S.GRAB[0], ease((t - T_FAIL - 0.9) / 0.6)) + math.cos(a) * rr * k; gy = cy + math.sin(a) * 25 * k
    else:
        gx, gy = GX[fi], GYS[fi]
        h = max(0, TER.y(gx) - R - gy); kk = 1 / (1 + h / 220)
        c.set_source_rgba(0, 0, 0, 0.25 * kk); c.save(); c.translate(gx, TER.y(gx) + 3); c.scale(R * (0.5 + 0.4 * kk), 9); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    if not whisk: draw_bales(c, t)
    p = GRIP[fi] / 100
    mood = 'happy' if (t >= S.T_END and S.OUTCOME == 'win') else ('scared' if whisk or P > 0.3 or p < 0.3 else 'worried')
    draw_blob(c, t, gx, gy, mood, 0, R=R, dizzy=whisk and t > T_FAIL + 0.7)
    if whisk: draw_bales(c, t)
    if P > 0.25 and f % 3 == 0 and t < S.T_RES: PS.spawn(rng.uniform(300, 760), GROUND - 10, 1, (0.55, 0.6, 0.35), 90, 0.6, grav=-200, r=6)
    PS.draw(c)
    END.draw_claw(c, t)
    c.restore()
    END.header(c, t, fi)

if __name__ == '__main__':
    if sys.argv[1] == 'sim':
        e = int(S.T_RES * FPS) - 1
        print(SEED, S.OUTCOME, round(S.T_RES - S.T_START, 2), 'min', round(min(GRIP[:e + 1])), 'final', round(GRIP[e]), 'bursts', len([b for b in BURSTS if b['t'] < S.T_END]), 'dur', S.DUR); sys.exit()
    run(S, render)
