"""2026-11-09 v3 — GRIP / TUG – GRIP %: the JET ENGINE. Gloop is a passive rigid ball (Ball) bouncing on the
airport apron at night between a stack of baggage carts (left wall) and luggage containers (right wall). The
jet engine hanging under the wing on the right keeps spooling up: seeded-random throttle bursts (strength +
length vary) really drag him toward the intake (sideways, plus a mild lift) and drain his sticky GRIP —
faster the closer he is. Between bursts GRIP slowly recovers. GRIP 0% = sucked up to the intake, spun
around and sneezed back out by the fan, dizzy."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the jet engine'
SEED = int(os.environ.get('SEED', 14))
rng = random.Random(SEED)

class S: pass
S.HOOK2 = 'THE JET ENGINE?'; S.HOOK2_SIZE = 92; S.FAIL_WORD = 'SUCKED UP!'; S.FAIL_SIZE = 130
S.T_START = HOOK_T; S.TL = float(os.environ.get('TL', 13.0)); S.T_END = S.T_START + S.TL
GROUND = 1600; R = 58; XMIN, XMAX = 230, 800; ROCK_X = XMAX + R
DRAIN, REGEN, PULL, LIFT = float(os.environ.get('DRAIN', 55)), 5.0, 900.0, 520.0
BH = (800, 880)

BURSTS = []; t = -0.2
while t < S.T_END + 1:
    s = rng.uniform(0.45, 1.0); d = rng.uniform(0.7, 1.6)
    BURSTS.append({'t': t, 'd': d, 's': s}); t += d + rng.uniform(0.8, 2.0)
def burst(t):
    for b in BURSTS:
        if b['t'] <= t < b['t'] + b['d']:
            k = min(1, (t - b['t']) / 0.2, (b['t'] + b['d'] - t) / 0.2); return b['s'] * k
    return 0.0

TER = Terrain(GROUND, seed=SEED, bumps=5, amp=12, soft=False)
N0 = int(40 * FPS); GX, GYS, GRIP, SUCK = [], [], [], []
ball = Ball(rng.uniform(300, 560), TER, R=R, seed=SEED, xmin=XMIN, xmax=XMAX, hop=rng.uniform(220, 290))
grip = 100.0; T_FAIL = None; FX = FY = 0
for f in range(N0):
    t = f / FPS; P = burst(t) if T_FAIL is None else 0.0
    prox = clamp(1 - (BH[0] - ball.x) / 760, 0, 1)
    if T_FAIL is None:
        ball.vx += P * PULL * (0.3 + 0.7 * prox) / FPS
        ball.vy -= P * LIFT * (0.3 + 0.7 * prox) / FPS   # steady field toward the hole (never a kick)
    ball.step(t)
    if T_FAIL is None and S.T_START <= t < S.T_END:
        grip = clamp(grip - (DRAIN * P * (0.25 + prox ** 1.5)) / FPS + (REGEN / FPS if P == 0 else 0), 0, 100)
        if grip <= 0: T_FAIL = t; FX, FY = ball.x, ball.y
    GX.append(ball.x); GYS.append(ball.y); GRIP.append(grip); SUCK.append(P)
S.OUTCOME = 'fail' if T_FAIL else 'win'
S.T_RES = T_FAIL if T_FAIL else S.T_END
SPIT = (520, TER.y(520) - R)
S.GRAB = SPIT if T_FAIL else (540, GROUND - R)
END = S.END = Ending(S)
if not T_FAIL: gi = min(int(END.T_GRAB * FPS), N0 - 1); S.GRAB = (GX[gi], GYS[gi])
S.events = [[0.05, 'whoosh']]
for b in BURSTS:
    if b['t'] < S.T_RES: S.events.append([max(0, b['t']), 'whoosh']); S.events.append([max(0, b['t']) + 0.3, 'rumble', min(b['d'], S.T_RES - b['t'] + 0.2)])
for (tl, xl, imp) in ball.landings:
    if tl < S.T_RES: S.events.append([tl, 'hop'])
for tw in ball.walls:
    if tw < S.T_RES: S.events.append([tw, 'thump', 0.4])
if T_FAIL: S.events += [[T_FAIL, 'whoosh'], [T_FAIL + 0.4, 'whoosh'], [T_FAIL + 0.85, 'pop'], [T_FAIL + 1.2, 'thump', 0.9]]
S.AMB = {'drone': 50, 'wind': 0.035, 'rumble': 0.025}

def draw_bar(c, t, f):
    p = GRIP[f] / 100; down = SUCK[f] > 0.05 and t < S.T_RES
    bx = bar(c, p, f'GRIP {int(math.ceil(GRIP[f]))}%', good_bad_col(p), 0.1 if down else 0, bw=640, x_off=36)
    c.save(); c.translate(bx - 52, 231); c.set_source_rgb(*rgb('#ffb347')); c.arc(0, 6, 18, 0, 2 * math.pi); c.fill()
    for dx in (-16, -5, 6, 17): c.arc(dx, -16, 7, 0, 2 * math.pi); c.fill()
    c.restore()
S.draw_bar = draw_bar

stars = [(rng.uniform(0, W), rng.uniform(HEAD, 900), rng.uniform(1.0, 2.2)) for _ in range(40)]
def draw_bg(c, t, P):
    c.set_source_rgb(*rgb('#141a2a')); c.rectangle(0, HEAD, W, H - HEAD); c.fill()
    c.set_source_rgba(0.85, 0.85, 0.9, 0.45)
    for x, y, r in stars: c.arc(x, y, r, 0, 2 * math.pi); c.fill()
    # far terminal building with lit windows + control tower
    c.set_source_rgb(*rgb('#1f2638')); c.rectangle(0, 1240, W, 200); c.fill()
    c.set_source_rgba(0.95, 0.85, 0.55, 0.3)
    for x in range(20, W, 46): c.rectangle(x, 1270, 28, 40); c.fill()
    c.set_source_rgb(*rgb('#1f2638')); c.rectangle(150, 900, 50, 340); c.fill(); rrect(c, 110, 860, 130, 70, 14); c.fill()
    c.set_source_rgba(0.6, 0.85, 0.9, 0.4); c.rectangle(122, 875, 106, 34); c.fill()
    on = (t * 1.2) % 1 < 0.3; c.set_source_rgb(*(rgb('#ff5050') if on else rgb('#5a2a2a'))); c.arc(175, 850, 8, 0, 2 * math.pi); c.fill()
    # runway edge lights
    for i, x in enumerate(range(20, W, 90)):
        c.set_source_rgb(*rgb('#6ab0ff' if i % 2 else '#ffd070')); c.arc(x, 1450, 5, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#22283a')); c.rectangle(0, 1460, W, GROUND - 1460); c.fill()
    # tarmac
    TER.fill(c, TER.h, '#3e424c', '#262a32', '#50555f')
    c.set_source_rgb(*rgb('#c8a02a'))
    for x in range(0, W, 140): c.rectangle(x, GROUND + 90, 80, 10); c.fill()
    # wing from the top right
    c.set_source_rgb(*rgb('#c8ccd4')); c.move_to(W + 20, 600); c.line_to(80, 730); c.line_to(80, 752); c.line_to(W + 20, 680); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#9aa0aa')); c.move_to(W + 20, 680); c.line_to(80, 752); c.line_to(80, 760); c.line_to(W + 20, 700); c.close_path(); c.fill()
    on = (t * 1.5) % 1 < 0.15; c.set_source_rgb(*(rgb('#ff4040') if on else rgb('#6a2a2a'))); c.arc(86, 742, 9, 0, 2 * math.pi); c.fill()

def draw_mast(c, t):   # left wall: stacked baggage carts with suitcases
    bw = XMIN - R
    for k, yy in enumerate((GROUND - 160, GROUND - 330)):
        c.set_source_rgb(*rgb('#4a5060')); c.rectangle(-10, yy + 120, bw + 10, 22); c.fill()
        c.set_source_rgb(*rgb('#2a2e38'))
        for xx in (30, bw - 30): c.arc(xx, yy + 150, 14, 0, 2 * math.pi); c.fill()
        for j, col in enumerate(('#a84a3a', '#3a6a9a', '#c8a03a', '#4a8a5a')):
            c.set_source_rgb(*rgb(col)); rrect(c, 6 + (j % 2) * (bw / 2 - 2), yy + 10 + (j // 2) * 56, bw / 2 - 12, 52, 8); c.fill()
            c.set_source_rgba(0, 0, 0, 0.3); c.rectangle(6 + (j % 2) * (bw / 2 - 2) + bw / 4 - 14, yy + 4 + (j // 2) * 56, 16, 10); c.fill()

def draw_hole(c, t, P):   # the jet engine intake (fan spins faster during bursts)
    x, y = BH; RH = 120
    c.set_source_rgb(*rgb('#8a909a')); c.rectangle(x - 40, 690, 80, y - RH - 690 + 20); c.fill()   # pylon
    c.set_source_rgb(*rgb('#b8bcc4')); c.arc(x, y, RH + 40, 0, 2 * math.pi); c.fill()   # nacelle lip
    c.set_source_rgb(*rgb('#2a2e36')); c.arc(x, y, RH + 8, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#14161c')); c.arc(x, y, RH, 0, 2 * math.pi); c.fill()
    spin = t * (2 + 30 * P)
    c.save(); c.translate(x, y)
    for i in range(14):   # fan blades
        a = spin + i * 2 * math.pi / 14
        c.set_source_rgba(0.55, 0.58, 0.64, 1 - 0.55 * clamp(P * 1.5, 0, 1))
        c.move_to(math.cos(a) * 24, math.sin(a) * 24); c.line_to(math.cos(a + 0.12) * RH * 0.95, math.sin(a + 0.12) * RH * 0.95)
        c.line_to(math.cos(a + 0.34) * RH * 0.95, math.sin(a + 0.34) * RH * 0.95); c.close_path(); c.fill()
    if P > 0.1:
        c.set_source_rgba(0.6, 0.62, 0.68, 0.35 * P); c.arc(0, 0, RH * 0.95, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#c8ccd4')); c.arc(0, 0, 26, 0, 2 * math.pi); c.fill()   # spinner
    c.set_source_rgb(*rgb('#1a1c22')); c.set_line_width(4); c.move_to(0, 0); c.line_to(math.cos(spin * 1.0) * 22, math.sin(spin * 1.0) * 22); c.stroke()
    c.restore()
    # stripes of air rushing in toward the intake
    if P > 0.05:
        c.set_line_width(5)
        for i in range(12):
            k = (t * (1.5 + P) + i / 12) % 1; ang = math.pi * 0.65 + (i * 0.37) % 1.4
            d0 = 520 * (1 - k) + RH + 40
            sx, sy = x + math.cos(ang) * d0, y + math.sin(ang) * d0
            ex, ey = x + math.cos(ang) * (d0 - 70), y + math.sin(ang) * (d0 - 70)
            c.set_source_rgba(0.8, 0.9, 1, 0.45 * P * k); c.move_to(sx, sy); c.line_to(ex, ey); c.stroke()

def draw_rock(c, t):   # right wall: luggage containers
    x0 = ROCK_X
    for (yy, h_, col) in ((GROUND - 190, 190, '#7a808a'), (GROUND - 360, 170, '#6a707a')):
        c.set_source_rgb(*rgb(col)); c.move_to(x0 + 30, yy); c.line_to(W + 10, yy); c.line_to(W + 10, yy + h_); c.line_to(x0, yy + h_); c.line_to(x0, yy + 50); c.close_path(); c.fill()
        c.set_source_rgba(0, 0, 0, 0.25); c.set_line_width(4)
        for xx in range(int(x0) + 40, W, 40): c.move_to(xx, yy + 10); c.line_to(xx, yy + h_ - 10); c.stroke()
        c.set_source_rgb(*rgb('#c8a02a')); c.rectangle(x0 + 20, yy + h_ - 40, W - x0, 12); c.fill()

PS = Particles(9)
def render(f, c):
    t = f / FPS; fi = min(f, len(GX) - 1); P = SUCK[fi] if t < S.T_RES + 0.01 else 0.0
    shake = (rng.uniform(-2, 2) * P, rng.uniform(-2, 2) * P)
    c.save(); c.translate(*shake)
    draw_bg(c, t, P)
    draw_hole(c, t, P)
    sucked = T_FAIL is not None and t >= T_FAIL
    if END.carried(t) or (t >= END.T_GRAB):
        gx, gy = (END.carry_xy(t) if END.carried(t) else S.GRAB)
    elif sucked:
        u = t - T_FAIL
        if u < 0.85:   # spiral in toward the hole
            k = ease(u / 0.85); a = u * 11; rr = 260 * (1 - k) + 140 * k
            cx, cy = lerp(FX, BH[0], k), lerp(FY, BH[1], k)
            gx = cx + math.cos(a) * rr * k * 0.9; gy = cy + math.sin(a) * rr * k * 0.3
        else:          # spat back out on an arc, lands on the ground
            k = clamp((u - 0.85) / 0.35, 0, 1)
            sx, sy = BH[0] - 150, BH[1] + 60
            gx = lerp(sx, SPIT[0], k); gy = lerp(sy, SPIT[1], k) - 260 * 4 * k * (1 - k)
            if u > 1.2: gy = SPIT[1] - 30 * abs(math.sin((u - 1.2) * 8)) * max(0, 1 - (u - 1.2) * 2)
    else:
        gx, gy = GX[fi], GYS[fi]
    if not sucked or t - T_FAIL > 1.1 or END.carried(t):
        if not END.carried(t):
            h = max(0, TER.y(gx) - R - gy); kk = 1 / (1 + h / 220)
            c.set_source_rgba(0, 0, 0, 0.3 * kk); c.save(); c.translate(gx, TER.y(gx) + 3); c.scale(R * (0.5 + 0.4 * kk), 9); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    draw_mast(c, t); draw_rock(c, t)
    p = GRIP[fi] / 100
    mood = 'happy' if (t >= S.T_END and S.OUTCOME == 'win') else ('scared' if sucked or P > 0.3 or p < 0.3 else 'worried')
    sc = R
    if sucked and t - T_FAIL < 1.0: sc = R * (1 - 0.35 * math.sin(math.pi * clamp((t - T_FAIL) / 1.0, 0, 1)))
    draw_blob(c, t, gx, gy, mood, 0, R=sc, dizzy=sucked and t > T_FAIL + 1.0)
    if P > 0.25 and f % 3 == 0 and t < S.T_RES: PS.spawn(rng.uniform(300, 760), GROUND - 10, 1, (0.75, 0.8, 0.9), 160, 0.7, grav=-700, r=4)
    if T_FAIL and abs(t - T_FAIL - 1.2) < 0.5 / FPS: PS.spawn(SPIT[0], GROUND, 16, (0.6, 0.6, 0.65), 400, 0.5, grav=900, r=7)
    PS.draw(c)
    END.draw_claw(c, t)
    c.restore()
    END.header(c, t, fi)

if __name__ == '__main__':
    if sys.argv[1] == 'sim':
        e = int(S.T_RES * FPS) - 1
        print(SEED, S.OUTCOME, round(S.T_RES - S.T_START, 2), 'min', round(min(GRIP[:e + 1])), 'final', round(GRIP[e]), 'bursts', len([b for b in BURSTS if b['t'] < S.T_END]), 'dur', S.DUR); sys.exit()
    run(S, render)
