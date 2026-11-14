"""2026-11-14 v3 — GRIP / TUG – GRIP %: the WIND TUNNEL. Gloop is a passive rigid ball (Ball) bouncing on the
steel floor of a wind-tunnel test lab at night between a stack of sandbags (left wall) and a steel bulkhead
(right wall). A giant intake fan on the right keeps spinning up: seeded-random surges (strength + length vary)
really drag him toward it (sideways, plus a mild lift) and drain his sticky GRIP — faster the closer he is.
Between surges GRIP slowly recovers. GRIP 0% = sucked onto the fan grille, spun around and blown back out, dizzy."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the wind tunnel'
SEED = int(os.environ.get('SEED', 14))
rng = random.Random(SEED)

class S: pass
S.HOOK2 = 'THE WIND TUNNEL?'; S.HOOK2_SIZE = 90; S.FAIL_WORD = 'SUCKED IN!'; S.FAIL_SIZE = 130
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
SPIN = [0.0]
for f in range(1, N0): SPIN.append(SPIN[-1] + 22 * SUCK[f] / FPS)
def sum_spin(t): return SPIN[min(int(t * FPS), N0 - 1)]
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
S.AMB = {'drone': 58, 'wind': 0.04, 'rumble': 0.02}

def draw_bar(c, t, f):
    p = GRIP[f] / 100; down = SUCK[f] > 0.05 and t < S.T_RES
    bx = bar(c, p, f'GRIP {int(math.ceil(GRIP[f]))}%', good_bad_col(p), 0.1 if down else 0, bw=640, x_off=36)
    c.save(); c.translate(bx - 52, 231); c.set_source_rgb(*rgb('#ffb347')); c.arc(0, 6, 18, 0, 2 * math.pi); c.fill()
    for dx in (-16, -5, 6, 17): c.arc(dx, -16, 7, 0, 2 * math.pi); c.fill()
    c.restore()
S.draw_bar = draw_bar

def draw_bg(c, t, P):
    c.set_source_rgb(*rgb('#1a1c22')); c.rectangle(0, HEAD, W, H - HEAD); c.fill()
    # riveted steel wall panels
    c.set_source_rgb(*rgb('#24272e')); c.rectangle(0, HEAD, W, GROUND - HEAD); c.fill()
    c.set_source_rgb(*rgb('#1c1e24'))
    for yy in range(HEAD, GROUND, 160): c.rectangle(0, yy, W, 6); c.fill()
    for xx in range(0, W, 220): c.rectangle(xx, HEAD, 6, GROUND - HEAD); c.fill()
    c.set_source_rgb(*rgb('#30333c'))
    for yy in range(HEAD + 20, GROUND, 160):
        for xx in range(20, W, 220): c.arc(xx, yy, 4, 0, 2 * math.pi); c.fill(); c.arc(xx + 180, yy, 4, 0, 2 * math.pi); c.fill()
    # control-room window with a dim monitor glow
    c.set_source_rgb(*rgb('#3a3e48')); rrect(c, 150, 560, 420, 240, 14); c.fill()
    c.set_source_rgb(*rgb('#141822')); rrect(c, 166, 576, 388, 208, 8); c.fill()
    c.set_source_rgb(*rgb('#2c3a34')); c.rectangle(200, 700, 90, 60); c.fill(); c.rectangle(310, 700, 90, 60); c.fill()
    c.set_source_rgba(0.5, 0.85, 0.6, 0.6); c.set_line_width(3); c.move_to(206, 740)
    for k in range(14): c.line_to(206 + k * 6, 740 - 14 * abs(math.sin(t * 3 + k)))
    c.stroke()
    # warning stripes + sign
    c.set_source_rgb(*rgb('#c8a030')); c.rectangle(0, 1020, W, 26); c.fill()
    c.set_source_rgb(*rgb('#1a1a1a'))
    for xx in range(-40, W + 40, 52): c.move_to(xx, 1020); c.line_to(xx + 26, 1020); c.line_to(xx, 1046); c.line_to(xx - 26, 1046); c.close_path(); c.fill()
    # streamer ribbons on a rod, fluttering toward the fan
    c.set_source_rgb(*rgb('#4a4e58')); c.set_line_width(6); c.move_to(300, 1120); c.line_to(560, 1120); c.stroke()
    for k in range(5):
        x = 320 + k * 55; c.set_source_rgba(0.85, 0.85, 0.9, 0.5); c.set_line_width(4); c.move_to(x, 1120)
        lean = 20 + 70 * P
        c.curve_to(x + lean * 0.3, 1150, x + lean * 0.7 + 6 * math.sin(t * 20 + k), 1180, x + lean, 1210); c.stroke()
    # steel floor plates
    TER.fill(c, TER.h, '#4a4e56', '#2a2d34', '#5a5e68')
    c.set_source_rgba(0, 0, 0, 0.2); c.set_line_width(3)
    for j, yy in enumerate(range(GROUND + 60, H, 100)):
        c.move_to(0, yy); c.line_to(W, yy); c.stroke()
        for xx in range((j % 2) * 120, W, 240): c.move_to(xx, yy); c.line_to(xx, yy + 100); c.stroke()

def draw_mast(c, t):   # left wall: a stack of sandbags
    bw = XMIN - R; yy = GROUND
    for k in range(9):
        off = 12 if k % 2 else -6
        c.set_source_rgb(*rgb('#8a7a58' if k % 2 else '#7a6c4c')); rrect(c, -30 + off, yy - 64, bw + 30 - abs(off), 62, 22); c.fill()
        c.set_source_rgb(*rgb('#5e5238')); c.set_line_width(4); c.move_to(bw * 0.5 + off, yy - 60); c.line_to(bw * 0.5 + off, yy - 6); c.stroke()
        yy -= 62

FAN_A = [0.0]
def draw_hole(c, t, P):   # giant intake fan in a round housing
    x, y = BH; RH = 150
    c.set_source_rgb(*rgb('#3a3e48')); c.arc(x, y, RH + 40, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#c8a030')); c.set_line_width(10); c.arc(x, y, RH + 30, 0, 2 * math.pi); c.stroke()
    c.set_source_rgb(*rgb('#101216')); c.arc(x, y, RH, 0, 2 * math.pi); c.fill()
    a0 = t * (2.0 + 22 * P) if P > 0 else t * 2.0
    a0 = t * 2.0 + sum_spin(t)
    c.set_source_rgb(*rgb('#5a5e68'))
    for k in range(5):
        a = a0 + k * 2 * math.pi / 5
        c.save(); c.translate(x, y); c.rotate(a); c.move_to(0, 0); c.curve_to(40, -40, RH - 10, -50, RH - 8, 0); c.curve_to(RH - 30, 20, 40, 20, 0, 0); c.close_path(); c.fill(); c.restore()
    c.set_source_rgb(*rgb('#2a2d34')); c.arc(x, y, 26, 0, 2 * math.pi); c.fill()
    c.set_source_rgba(0.6, 0.62, 0.68, 0.6); c.set_line_width(3)   # grille
    for r_ in range(40, RH, 28): c.arc(x, y, r_, 0, 2 * math.pi); c.stroke()
    if P > 0.05:   # air streaks rushing into the fan
        c.set_line_width(5)
        for i in range(12):
            k = (t * (1.5 + P) + i / 12) % 1; ang = math.pi * 0.65 + (i * 0.37) % 1.4
            d0 = 520 * (1 - k) + RH + 40
            sx, sy = x + math.cos(ang) * d0, y + math.sin(ang) * d0
            ex, ey = x + math.cos(ang) * (d0 - 70), y + math.sin(ang) * (d0 - 70)
            c.set_source_rgba(0.85, 0.9, 1, 0.4 * P * k); c.move_to(sx, sy); c.line_to(ex, ey); c.stroke()

def draw_rock(c, t):   # right wall: steel bulkhead
    x0 = ROCK_X
    c.set_source_rgb(*rgb('#3e424c')); c.rectangle(x0, 1120, W - x0 + 10, GROUND - 1120 + 30); c.fill()
    c.set_source_rgb(*rgb('#2e3138'))
    for yy in range(1160, GROUND, 70): c.rectangle(x0, yy, W - x0, 5); c.fill()
    c.set_source_rgb(*rgb('#c8a030')); c.rectangle(x0 - 10, 1100, W - x0 + 20, 24); c.fill()

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
    if P > 0.25 and f % 3 == 0 and t < S.T_RES: PS.spawn(rng.uniform(300, 700), GROUND - 10, 1, (0.6, 0.6, 0.62), 160, 0.7, grav=-500, r=4)
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
