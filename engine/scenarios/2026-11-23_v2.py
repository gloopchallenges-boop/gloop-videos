"""2026-11-23 v2 — GRIP / TUG – GRIP %: the ANGLERFISH (based on 2026-11-17 v2 whale). Gloop is a passive rigid ball
bouncing on the sandy seabed of the deep sea at night between a rock column (left) and a boulder pile (right). A giant
anglerfish on the right keeps inhaling water: seeded-random surges drag him toward its mouth (sideways + mild lift)
and drain his GRIP, faster the closer he is. GRIP 0% = sucked in and spat back out, soggy & dizzy."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the anglerfish'
SEED = int(os.environ.get('SEED', 23))
rng = random.Random(SEED)

class S: pass
S.HOOK2 = 'THE ANGLERFISH?'; S.HOOK2_SIZE = 90; S.FAIL_WORD = 'GULP!'; S.FAIL_SIZE = 160
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

SNOW = [((i * 263) % W, (i * 397) % 1300 + HEAD, 1.5 + (i % 3)) for i in range(40)]
def draw_bg(c, t, P):   # deep sea at night: dark water, drifting marine snow, faint light shafts
    c.set_source_rgb(*rgb('#0c1a2a')); c.rectangle(0, HEAD, W, H - HEAD); c.fill()
    c.set_source_rgb(*rgb('#0f2234')); c.rectangle(0, HEAD, W, 500); c.fill()
    c.set_source_rgba(0.7, 0.85, 1, 0.04)
    for k in range(3): c.move_to(140 + k * 260, HEAD); c.line_to(220 + k * 260, HEAD); c.line_to(120 + k * 300, 1300); c.line_to(40 + k * 300, 1300); c.close_path(); c.fill()
    c.set_source_rgba(0.8, 0.9, 1, 0.3)
    for x, y, r in SNOW: c.arc((x + 12 * math.sin(t * 0.7 + y)) % W, HEAD + (y - HEAD + t * 22) % (H - HEAD), r, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#13283a'))   # far rocky ridge
    c.move_to(0, 1300); c.line_to(120, 1180); c.line_to(260, 1240); c.line_to(420, 1140); c.line_to(560, 1230); c.line_to(700, 1170); c.line_to(W, 1260); c.line_to(W, 1400); c.line_to(0, 1400); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#1c3040'))   # tube worms / far kelp silhouettes
    c.set_line_width(10)
    for i, x in enumerate(range(80, 700, 110)): c.move_to(x, 1320); c.curve_to(x - 20, 1260, x + 25 * math.sin(t + i), 1220, x + 10 * math.sin(t * 1.2 + i), 1150 - (i % 3) * 40); c.stroke()
    # sandy seabed
    TER.fill(c, TER.h, '#5a5848', '#2e3030', '#74705a')
    c.set_source_rgba(0, 0, 0, 0.18)
    for k in range(10): c.save(); c.translate(80 + k * 100, GROUND + 70 + (k * 67) % 220); c.scale(26, 6); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    c.set_source_rgb(*rgb('#8a7c6a'))
    for k in range(6): c.arc(130 + k * 160, GROUND + 140 + (k * 53) % 140, 7, 0, 2 * math.pi); c.fill()   # little shells

def draw_mast(c, t):   # left wall: tall rock column with sea anemones + kelp
    bw = XMIN - R
    c.set_source_rgb(*rgb('#2a3440')); c.move_to(-10, GROUND + 40); c.line_to(-10, 1000); c.curve_to(40, 960, bw - 20, 990, bw, 1060); c.line_to(bw, GROUND + 40); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#36424e'))
    for (yy, ww) in ((1120, 60), (1260, 90), (1420, 70)): rrect(c, 20, yy, ww, 26, 12); c.fill()
    for k, yy in enumerate((1080, 1330, 1500)):   # anemones on the rock face
        c.set_source_rgb(*rgb('#a85a7a' if k % 2 else '#5a9a8a'))
        for j in range(6): a_ = -math.pi * 0.85 + j * 0.3 + 0.08 * math.sin(t * 2 + j); c.set_line_width(7); c.move_to(bw - 6, yy); c.line_to(bw - 6 + 34 * math.cos(a_ + math.pi / 2), yy + 34 * math.sin(a_)); c.stroke()

def draw_hole(c, t, P):   # giant anglerfish on the right, mouth open at BH, inhaling water
    x, y = BH; op = 0.35 + 0.65 * P
    body, dark = rgb('#3a2e3e'), rgb('#261e2a')
    c.save()
    c.set_source_rgb(*body)
    c.move_to(W + 60, y - 380); c.curve_to(900, y - 420, 760, y - 300, x - 40, y - 60 - 40 * op)
    c.line_to(x + 80, y); c.line_to(x - 60, y + 70 + 50 * op); c.curve_to(760, y + 330, 900, y + 380, W + 60, y + 380); c.close_path(); c.fill()
    # mouth cavity
    c.set_source_rgb(*rgb('#120a12')); c.move_to(x - 40, y - 60 - 40 * op); c.curve_to(x + 40, y - 80 * op, x + 160, y - 60 * op, W + 40, y - 40 * op - 10)
    c.line_to(W + 40, y + 60 * op + 20); c.curve_to(x + 160, y + 80 * op + 20, x + 20, y + 100 * op + 40, x - 60, y + 70 + 50 * op); c.close_path(); c.fill()
    # needle teeth on both jaws
    c.set_source_rgb(*rgb('#e8e2d0'))
    for k in range(7):
        tx = x - 20 + k * 34; ty = y - 60 * op - 30 + k * 3
        c.move_to(tx, ty); c.line_to(tx + 10, ty + 34 + 10 * op); c.line_to(tx + 20, ty); c.close_path(); c.fill()
    for k in range(6):
        tx = x - 30 + k * 36; ty = y + 70 * op + 40 - k * 2
        c.move_to(tx, ty); c.line_to(tx + 10, ty - 36 - 8 * op); c.line_to(tx + 20, ty); c.close_path(); c.fill()
    # lumpy skin spots + fin
    c.set_source_rgb(*dark)
    for (bx, by, br) in ((900, y - 250, 14), (980, y - 300, 10), (1020, y + 240, 16), (860, y + 230, 10)): c.arc(bx, by, br, 0, 2 * math.pi); c.fill()
    c.move_to(1000, y - 340); c.line_to(1060, y - 440); c.line_to(1075, y - 330); c.close_path(); c.fill()
    # eye
    ex, ey = 920, y - 180
    c.set_source_rgb(*rgb('#d8dcc8')); c.arc(ex, ey, 26, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(0.05, 0.05, 0.08); c.arc(ex - 7, ey + 3, 13, 0, 2 * math.pi); c.fill()
    # lure on a stalk (pale, no glow)
    lx, ly = 700 + 14 * math.sin(t * 1.3), y - 360 + 10 * math.sin(t * 2.1)
    c.set_source_rgb(*rgb('#4a3c4e')); c.set_line_width(9); c.move_to(940, y - 360); c.curve_to(880, y - 470, 760, y - 470, lx, ly); c.stroke()
    c.set_source_rgb(*rgb('#e8f0c0')); c.arc(lx, ly + 18, 20, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#c8d8a0')); c.arc(lx - 5, ly + 13, 7, 0, 2 * math.pi); c.fill()
    c.restore()
    if P > 0.05:   # water current streaks + bubbles rushing into the mouth
        c.set_line_width(5)
        for i in range(12):
            k = (t * (1.5 + P) + i / 12) % 1; ang = math.pi * 0.72 + (i * 0.37) % 1.1
            d0 = 520 * (1 - k) + 110
            sx, sy = x + math.cos(ang) * d0, y + math.sin(ang) * d0
            ex2, ey2 = x + math.cos(ang) * (d0 - 70), y + math.sin(ang) * (d0 - 70)
            c.set_source_rgba(0.75, 0.88, 1, 0.4 * P * k); c.move_to(sx, sy); c.line_to(ex2, ey2); c.stroke()
            if i % 3 == 0: c.arc(sx, sy - 20, 6, 0, 2 * math.pi); c.fill()

def draw_rock(c, t):   # right wall: boulder pile under the anglerfish
    x0 = ROCK_X
    c.set_source_rgb(*rgb('#2c3640'))
    for (bx, by, br) in ((x0 + 70, GROUND - 40, 90), (x0 + 150, GROUND - 160, 80), (x0 + 60, GROUND - 230, 60)): c.arc(bx, by, br, 0, 2 * math.pi); c.fill()
    c.rectangle(x0, GROUND - 200, W - x0 + 10, 260); c.fill()
    c.set_source_rgb(*rgb('#38444e'))
    for (bx, by, br) in ((x0 + 50, GROUND - 90, 24), (x0 + 140, GROUND - 190, 20)): c.arc(bx, by, br, 0, 2 * math.pi); c.fill()

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
    if T_FAIL and abs(t - T_FAIL - 1.2) < 0.5 / FPS: PS.spawn(SPIT[0], GROUND, 16, (0.55, 0.52, 0.42), 400, 0.5, grav=900, r=7)
    PS.draw(c)
    END.draw_claw(c, t)
    c.restore()
    END.header(c, t, fi)

if __name__ == '__main__':
    if sys.argv[1] == 'sim':
        e = int(S.T_RES * FPS) - 1
        print(SEED, S.OUTCOME, round(S.T_RES - S.T_START, 2), 'min', round(min(GRIP[:e + 1])), 'final', round(GRIP[e]), 'bursts', len([b for b in BURSTS if b['t'] < S.T_END]), 'dur', S.DUR); sys.exit()
    run(S, render)
