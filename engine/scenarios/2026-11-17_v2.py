"""2026-11-17 v2 — GRIP / TUG – GRIP %: the HUNGRY WHALE. (Adapted from 2026-11-14 v3, wind tunnel.) Gloop is a passive rigid ball (Ball) bouncing on a
wooden pier at night between a stack of lobster crates (left wall) and a mooring post (right wall). A giant whale
rises out of the sea on the right and keeps gulping air: seeded-random surges (strength + length vary)
really drag him toward it (sideways, plus a mild lift) and drain his sticky GRIP — faster the closer he is.
Between surges GRIP slowly recovers. GRIP 0% = sucked into the whale's mouth and spat back out, soggy & dizzy."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the hungry whale'
SEED = int(os.environ.get('SEED', 16))
rng = random.Random(SEED)

class S: pass
S.HOOK2 = 'THE HUNGRY WHALE?'; S.HOOK2_SIZE = 90; S.FAIL_WORD = 'GULP!'; S.FAIL_SIZE = 160
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
if T_FAIL: S.events += [[T_FAIL, 'whoosh'], [T_FAIL + 0.4, 'whoosh'], [T_FAIL + 0.85, 'pop'], [T_FAIL + 0.9, 'splash'], [T_FAIL + 1.2, 'thump', 0.9]]
S.AMB = {'drone': 46, 'wind': 0.03, 'rumble': 0.015}

def draw_bar(c, t, f):
    p = GRIP[f] / 100; down = SUCK[f] > 0.05 and t < S.T_RES
    bx = bar(c, p, f'GRIP {int(math.ceil(GRIP[f]))}%', good_bad_col(p), 0.1 if down else 0, bw=640, x_off=36)
    c.save(); c.translate(bx - 52, 231); c.set_source_rgb(*rgb('#ffb347')); c.arc(0, 6, 18, 0, 2 * math.pi); c.fill()
    for dx in (-16, -5, 6, 17): c.arc(dx, -16, 7, 0, 2 * math.pi); c.fill()
    c.restore()
S.draw_bar = draw_bar

def draw_bg(c, t, P):
    c.set_source_rgb(*rgb('#141a26')); c.rectangle(0, HEAD, W, H - HEAD); c.fill()
    c.set_source_rgba(0.85, 0.9, 1, 0.35)
    for i in range(30): c.arc((i * 263) % W, HEAD + 30 + (i * 151) % 520, 1.6 + (i % 3) * 0.5, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#e6dfc4')); c.arc(250, 560, 44, 0, 2 * math.pi); c.fill()
    # sea with moon path + slow swell
    SEA = 1080
    c.set_source_rgb(*rgb('#1a2a3c')); c.move_to(0, SEA)
    for x in range(0, W + 1, 20): c.line_to(x, SEA + 6 * math.sin(x * 0.02 + t * 1.2))
    c.line_to(W, H); c.line_to(0, H); c.close_path(); c.fill()
    c.set_source_rgba(0.9, 0.88, 0.75, 0.12)
    for k in range(7):
        y = SEA + 20 + k * 40; w_ = 40 + k * 20; c.rectangle(250 - w_ / 2 + 10 * math.sin(t * 1.5 + k), y, w_, 5); c.fill()
    # far lighthouse on a rock
    c.set_source_rgb(*rgb('#22303e')); c.move_to(380, SEA + 4); c.line_to(420, SEA - 40); c.line_to(520, SEA - 30); c.line_to(560, SEA + 4); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#3a4654')); c.move_to(450, SEA - 34); c.line_to(458, SEA - 150); c.line_to(482, SEA - 150); c.line_to(490, SEA - 34); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#e8d890')); c.rectangle(456, SEA - 166, 28, 16); c.fill()
    # pier posts below the deck
    c.set_source_rgb(*rgb('#2a2018'))
    for x in range(60, W, 170): c.rectangle(x, GROUND + 10, 34, H - GROUND); c.fill()
    # wooden pier deck
    TER.fill(c, TER.h, '#6a5038', '#3a2a1e', '#8a6a48')
    c.set_source_rgba(0, 0, 0, 0.22); c.set_line_width(3)
    for j, yy in enumerate(range(GROUND + 50, GROUND + 230, 45)):
        c.move_to(0, yy); c.line_to(W, yy); c.stroke()
        for xx in range((j % 2) * 90, W, 180): c.move_to(xx, yy); c.line_to(xx, yy + 45); c.stroke()
    c.set_source_rgb(*rgb('#1a2a3c')); c.rectangle(0, GROUND + 230, W, H - GROUND - 230); c.fill()
    for x in range(60, W, 170): c.set_source_rgb(*rgb('#2a2018')); c.rectangle(x, GROUND + 230, 34, H); c.fill()
    c.set_source_rgba(0.9, 0.9, 1, 0.08)
    for k in range(5): c.rectangle(40 + k * 220 + 20 * math.sin(t + k), GROUND + 270 + k * 9, 90, 4); c.fill()

def draw_mast(c, t):   # left wall: a stack of lobster crates
    bw = XMIN - R; yy = GROUND
    for k in range(6):
        off = 10 if k % 2 else -4
        c.set_source_rgb(*rgb('#7a5a3a' if k % 2 else '#6a4c30')); c.rectangle(-20 + off, yy - 96, bw + 20 - abs(off), 92); c.fill()
        c.set_source_rgb(*rgb('#3a2818'))
        for xx in range(int(-10 + off), int(bw), 28): c.rectangle(xx, yy - 90, 8, 80); c.fill()
        c.set_source_rgb(*rgb('#8a6a48')); c.rectangle(-20 + off, yy - 96, bw + 20 - abs(off), 10); c.fill()
        yy -= 96
    c.set_source_rgb(*rgb('#c85a3a')); c.arc(bw * 0.5, yy - 10, 14, 0, 2 * math.pi); c.fill()   # a buoy on top

def draw_hole(c, t, P):   # the giant whale rising out of the sea, mouth open at BH, inhaling
    x, y = BH; op = 0.35 + 0.65 * P
    body, dark, belly = rgb('#3a4a66'), rgb('#2a364c'), rgb('#9aa6b8')
    c.save()
    # head mass: big rounded shape off the right edge
    c.set_source_rgb(*body); c.move_to(W + 60, y - 400); c.curve_to(860, y - 420, 700, y - 260, x - 70, y - 60 - 30 * op)
    c.line_to(x + 60, y); c.line_to(x - 70, y + 50 + 40 * op); c.curve_to(700, y + 260, 820, 1090, W + 60, 1090); c.close_path(); c.fill()
    # mouth cavity
    c.set_source_rgb(*rgb('#2a0e18')); c.move_to(x - 70, y - 60 - 30 * op); c.curve_to(x - 10, y - 70 * op, x + 120, y - 50 * op, W + 40, y - 40 * op - 10)
    c.line_to(W + 40, y + 50 * op + 10); c.curve_to(x + 120, y + 60 * op, x - 10, y + 80 * op, x - 70, y + 50 + 40 * op); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#8a3a4a')); c.save(); c.translate(x + 120, y + 30 * op); c.scale(90, 22 * op + 6); c.arc(0, 0, 1, 0, math.pi); c.restore(); c.fill()   # tongue
    # baleen plates on the upper jaw
    c.set_source_rgb(*rgb('#c8c0a8'))
    for k in range(7):
        bx = x - 40 + k * 34; c.rectangle(bx, y - 55 * op - 18 + k * 2, 10, 26 + 6 * op); c.fill()
    # grooved belly on the lower jaw
    c.set_source_rgb(*belly); c.move_to(x - 70, y + 50 + 40 * op); c.curve_to(700, y + 260, 820, 1090, W + 60, 1090); c.line_to(W + 60, y + 60 * op + 30); c.curve_to(x + 100, y + 70 * op + 30, x, y + 80 * op + 20, x - 70, y + 50 + 40 * op); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#7a8698')); c.set_line_width(4)
    for k in range(4): c.move_to(x - 20 + k * 60, y + 80 + 40 * op + k * 14); c.line_to(W + 40, y + 120 + 40 * op + k * 26); c.stroke()
    # eye
    ex, ey = 930, y - 170
    c.set_source_rgb(*rgb('#e8e4d8')); c.arc(ex, ey, 22, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(0.05, 0.05, 0.08); c.arc(ex - 6, ey + 2, 11, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*dark); c.set_line_width(6); c.move_to(ex - 30, ey - 30); c.line_to(ex + 24, ey - 24); c.stroke()
    # barnacles
    c.set_source_rgb(*rgb('#8a92a0'))
    for (bx, by) in ((880, y - 300), (960, y - 330), (1010, y - 250)): c.arc(bx, by, 9, 0, 2 * math.pi); c.fill()
    c.restore()
    # splash ring where it meets the water
    c.set_source_rgba(0.85, 0.9, 1, 0.35); c.set_line_width(5)
    c.move_to(690, 1085); c.curve_to(760, 1060 + 6 * math.sin(t * 3), 900, 1065, W, 1080); c.stroke()
    if P > 0.05:   # air + spray streaks rushing into the mouth
        c.set_line_width(5)
        for i in range(12):
            k = (t * (1.5 + P) + i / 12) % 1; ang = math.pi * 0.72 + (i * 0.37) % 1.1
            d0 = 520 * (1 - k) + 110
            sx, sy = x + math.cos(ang) * d0, y + math.sin(ang) * d0
            ex2, ey2 = x + math.cos(ang) * (d0 - 70), y + math.sin(ang) * (d0 - 70)
            c.set_source_rgba(0.85, 0.9, 1, 0.4 * P * k); c.move_to(sx, sy); c.line_to(ex2, ey2); c.stroke()

def draw_rock(c, t):   # right wall: a thick mooring post with rope coils
    x0 = ROCK_X
    c.set_source_rgb(*rgb('#4a3626')); c.rectangle(x0, 1260, W - x0 + 10, GROUND - 1260 + 30); c.fill()
    c.set_source_rgb(*rgb('#3a2a1c'))
    for xx in range(int(x0) + 20, W, 40): c.rectangle(xx, 1270, 6, GROUND - 1270); c.fill()
    c.set_source_rgb(*rgb('#5a4430')); c.rectangle(x0 - 10, 1244, W - x0 + 20, 26); c.fill()
    c.set_source_rgb(*rgb('#b89a68')); c.set_line_width(12)
    for k in range(4): c.save(); c.translate(x0 + 110, 1330 + k * 22); c.scale(80, 14); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.stroke()

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
    if P > 0.25 and f % 3 == 0 and t < S.T_RES: PS.spawn(rng.uniform(300, 700), GROUND - 10, 1, (0.75, 0.85, 0.95), 160, 0.7, grav=-500, r=4)
    if T_FAIL and abs(t - T_FAIL - 1.2) < 0.5 / FPS: PS.spawn(SPIT[0], GROUND, 16, (0.7, 0.82, 0.95), 400, 0.5, grav=900, r=7)
    PS.draw(c)
    END.draw_claw(c, t)
    c.restore()
    END.header(c, t, fi)

if __name__ == '__main__':
    if sys.argv[1] == 'sim':
        e = int(S.T_RES * FPS) - 1
        print(SEED, S.OUTCOME, round(S.T_RES - S.T_START, 2), 'min', round(min(GRIP[:e + 1])), 'final', round(GRIP[e]), 'bursts', len([b for b in BURSTS if b['t'] < S.T_END]), 'dur', S.DUR); sys.exit()
    run(S, render)
