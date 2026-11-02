"""2026-11-02 v6 — GRIP / TUG – GRIP %: the GIANT VACUUM. Gloop is a passive rigid ball (Ball) bouncing
across a living-room floor; a giant vacuum hose lies on the right with its mouth on the floor.
Seeded-random suction bursts (strength + length vary) really pull him toward the mouth, and drain his
sticky GRIP — faster the closer he is and the stronger the burst. Between bursts GRIP slowly
recovers. GRIP 0% = he's slurped into the hose (fail)."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the giant vacuum'
SEED = int(os.environ.get('SEED', 10))
rng = random.Random(SEED)

class S: pass
S.HOOK2 = 'THE GIANT VACUUM?'; S.HOOK2_SIZE = 92; S.FAIL_WORD = 'SLURPED!'; S.FAIL_SIZE = 150
S.T_START = HOOK_T; S.TL = 13.0; S.T_END = S.T_START + S.TL
GROUND = 1600; R = 58; XMIN, XMAX = 170, 840; MOUTH_X = XMAX + R + 10
DRAIN, REGEN, PULL = float(os.environ.get('DRAIN', 55)), 5.0, 900.0

BURSTS = []; t = -0.3
while t < S.T_END + 1:
    s = rng.uniform(0.45, 1.0); d = rng.uniform(0.7, 1.6)
    BURSTS.append({'t': t, 'd': d, 's': s}); t += d + rng.uniform(0.8, 2.0)
def burst(t):
    for b in BURSTS:
        if b['t'] <= t < b['t'] + b['d']:
            k = min(1, (t - b['t']) / 0.2, (b['t'] + b['d'] - t) / 0.2); return b['s'] * k
    return 0.0

TER = Terrain(GROUND, seed=SEED, bumps=4, amp=8, soft=False)
N0 = int(40 * FPS); GX, GYS, GRIP, SUCK = [], [], [], []
ball = Ball(rng.uniform(250, 520), TER, R=R, seed=SEED, xmin=XMIN, xmax=XMAX, hop=rng.uniform(220, 290))
grip = 100.0; T_FAIL = None
for f in range(N0):
    t = f / FPS; P = burst(t) if T_FAIL is None else 0.0
    prox = clamp(1 - (MOUTH_X - ball.x) / 760, 0, 1)
    if T_FAIL is None: ball.vx += P * PULL * (0.3 + 0.7 * prox) / FPS
    ball.step(t)
    if T_FAIL is None and S.T_START <= t < S.T_END:
        grip = clamp(grip - (DRAIN * P * (0.25 + prox ** 1.5)) / FPS + (REGEN / FPS if P == 0 else 0), 0, 100)
        if grip <= 0: T_FAIL = t; FX, FY = ball.x, ball.y
    GX.append(ball.x); GYS.append(ball.y); GRIP.append(grip); SUCK.append(P)
S.OUTCOME = 'fail' if T_FAIL else 'win'
S.T_RES = T_FAIL if T_FAIL else S.T_END
MX, MY = MOUTH_X + 40, GROUND - 95
S.GRAB = (MX - 40, MY) if T_FAIL else (540, GROUND - R)
END = S.END = Ending(S)
if not T_FAIL: gi = min(int(END.T_GRAB * FPS), N0 - 1); S.GRAB = (GX[gi], GYS[gi])
S.events = []
for b in BURSTS:
    if b['t'] < S.T_RES: S.events.append([max(0, b['t']), 'whoosh']); S.events.append([max(0, b['t']) + 0.3, 'rumble', min(b['d'], S.T_RES - b['t'] + 0.2)])
for (tl, xl, imp) in ball.landings:
    if tl < S.T_RES: S.events.append([tl, 'hop'])
for tw in ball.walls:
    if tw < S.T_RES: S.events.append([tw, 'thump', 0.4])
if T_FAIL: S.events += [[T_FAIL, 'whoosh'], [T_FAIL + 0.35, 'pop'], [T_FAIL + 0.4, 'thump', 1.0]]
S.AMB = {'drone': 50, 'rumble': 0.01}

def draw_bar(c, t, f):
    p = GRIP[f] / 100; down = SUCK[f] > 0.05 and t < S.T_RES
    bx = bar(c, p, f'GRIP {int(math.ceil(GRIP[f]))}%', good_bad_col(p), 0.1 if down else 0, bw=640, x_off=36)
    c.save(); c.translate(bx - 52, 231); c.set_source_rgb(*rgb('#ffb347')); c.arc(0, 6, 18, 0, 2 * math.pi); c.fill()
    for dx in (-16, -5, 6, 17): c.arc(dx, -16, 7, 0, 2 * math.pi); c.fill()
    c.restore()
S.draw_bar = draw_bar

def draw_bg(c, t):
    c.set_source_rgb(*rgb('#1f1b2a')); c.rectangle(0, HEAD, W, H - HEAD); c.fill()
    c.set_source_rgb(*rgb('#26213a'))
    for x in range(0, W, 120): c.rectangle(x, HEAD, 60, GROUND - HEAD); c.fill()
    c.set_source_rgb(*rgb('#141c33')); rrect(c, 330, 520, 300, 380, 12); c.fill()
    c.set_source_rgb(*rgb('#d8d0b0')); c.arc(560, 610, 30, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#3a3350')); c.set_line_width(14); rrect(c, 330, 520, 300, 380, 12); c.stroke(); c.move_to(480, 520); c.line_to(480, 900); c.stroke()
    c.set_source_rgb(*rgb('#3b2f48')); rrect(c, -60, 1240, 300, 200, 40); c.fill(); rrect(c, -60, 1160, 260, 120, 40); c.fill()   # sofa arm
    c.set_source_rgb(*rgb('#4a3b2c')); c.rectangle(0, GROUND, W, H - GROUND); c.fill()
    c.set_source_rgba(0, 0, 0, 0.2); c.set_line_width(3)
    for yy in range(GROUND + 60, H, 60): c.move_to(0, yy); c.line_to(W, yy); c.stroke()
    c.set_source_rgb(*rgb('#5e3b44')); c.save(); c.translate(470, GROUND + 90); c.scale(330, 40); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    c.set_source_rgb(*rgb('#3b2f48')); c.rectangle(0, 1000, XMIN - R, GROUND - 1000); c.fill()   # bookshelf = left wall
    c.set_source_rgb(*rgb('#2c2338'))
    for yy in range(1000, GROUND, 120): c.rectangle(0, yy, XMIN - R, 10); c.fill()
    for i, yy in enumerate(range(1020, GROUND - 100, 120)):
        for j in range(3): c.set_source_rgb(*rgb(('#6b4b3a', '#4a5a6b', '#7a3d33')[(i + j) % 3])); c.rectangle(10 + j * 32, yy + 20, 24, 90); c.fill()

def draw_vacuum(c, t, f):
    P = SUCK[min(f, len(SUCK) - 1)]
    if P > 0.05:   # suction streaks flowing into the mouth
        for i in range(12):
            k = (t * (1.5 + P) + i / 12) % 1; y = MY + 60 * math.sin(i * 2.7)
            x = lerp(MOUTH_X - 640, MOUTH_X, k * k)
            c.set_source_rgba(1, 1, 1, 0.5 * P * k); c.set_line_width(5); c.move_to(x - 60, y + (MY - y) * k * 0.5); c.line_to(x, y + (MY - y) * k * 0.6); c.stroke()
    # ribbed hose coming down from the top right into the nozzle head
    P0, P1, P2, P3 = (MOUTH_X + 110, 1040), (MOUTH_X + 60, 760), (760, 560), (1120, 420)
    def bz(a):
        return tuple((1 - a) ** 3 * P0[i] + 3 * (1 - a) ** 2 * a * P1[i] + 3 * (1 - a) * a * a * P2[i] + a ** 3 * P3[i] for i in (0, 1))
    c.set_source_rgb(*rgb('#4f5868')); c.set_line_width(96); c.move_to(*P0); c.curve_to(*P1, *P2, *P3); c.stroke()
    c.set_source_rgb(*rgb('#3c4352')); c.set_line_width(8)
    for k in range(1, 16):
        x0, y0 = bz(k / 16 - 0.01); x1, y1 = bz(k / 16 + 0.01); ang = math.atan2(y1 - y0, x1 - x0) + math.pi / 2
        x, y = bz(k / 16); c.move_to(x - math.cos(ang) * 46, y - math.sin(ang) * 46); c.line_to(x + math.cos(ang) * 46, y + math.sin(ang) * 46); c.stroke()
    # nozzle head (body above the mouth acts as Gloop's right wall)
    sh = 2 * math.sin(t * 60) * P
    c.set_source_rgb(*rgb('#6d7788')); c.move_to(MOUTH_X + sh, 1030); c.line_to(W, 1000); c.line_to(W, GROUND); c.line_to(MOUTH_X + sh, GROUND); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#141218')); c.save(); c.translate(MOUTH_X + 12 + sh, MY); c.scale(34, 92); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    c.set_source_rgb(*rgb('#8a93a3')); c.set_line_width(10); c.save(); c.translate(MOUTH_X + 12 + sh, MY); c.scale(34, 92); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.stroke()
    c.set_source_rgb(*rgb('#ff4040' if P > 0.05 and (t * 6) % 1 < 0.5 else '#7a2020')); c.arc(MOUTH_X + 90, 1110, 14, 0, 2 * math.pi); c.fill()

PS = Particles(9)
def render(f, c):
    t = f / FPS; fi = min(f, len(GX) - 1); P = SUCK[fi]
    shake = (rng.uniform(-2, 2) * P, rng.uniform(-2, 2) * P)
    c.save(); c.translate(*shake)
    draw_bg(c, t)
    slurp = T_FAIL is not None and t >= T_FAIL
    scale = 1.0
    if END.carried(t) or t >= END.T_GRAB: gx, gy = (END.carry_xy(t) if END.carried(t) else S.GRAB)
    elif slurp:
        k = ease((t - T_FAIL) / 0.4); gx, gy = lerp(FX, MX - 40, k), lerp(FY, MY, k)
        scale = 1 - 0.15 * k
    else:
        gx, gy = GX[fi], GYS[fi]
        h = max(0, TER.y(gx) - R - gy); kk = 1 / (1 + h / 220)
        c.set_source_rgba(0, 0, 0, 0.25 * kk); c.save(); c.translate(gx, TER.y(gx) + 3); c.scale(R * (0.5 + 0.4 * kk), 9); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    draw_vacuum(c, t, f)
    p = GRIP[fi] / 100
    mood = 'happy' if (t >= S.T_END and S.OUTCOME == 'win') else ('scared' if slurp or P > 0.3 or p < 0.3 else 'worried')
    stuck = slurp and t >= T_FAIL + 0.4 and not END.carried(t)
    draw_blob(c, t, gx, gy, mood, (-0.12 * P if not slurp else 0.0), R=R * scale, dizzy=slurp and t > T_FAIL + 0.6)
    if stuck:   # he's plugged in the mouth: hose lip drawn over his back half
        c.set_source_rgb(*rgb('#6d7788')); c.rectangle(MOUTH_X + 12, MY - 110, 60, 220); c.fill()
        c.set_source_rgb(*rgb('#8a93a3')); c.set_line_width(10); c.save(); c.translate(MOUTH_X + 12, MY); c.scale(34, 92); c.arc(0, 0, 1, -math.pi / 2, math.pi / 2); c.restore(); c.stroke()
    if P > 0.3 and f % 5 == 0 and t < S.T_RES: PS.spawn(rng.uniform(300, 800), GROUND - 10, 1, (0.6, 0.55, 0.5), 60, 0.5, grav=0, r=6)
    PS.draw(c)
    END.draw_claw(c, t)
    c.restore()
    END.header(c, t, fi)

if __name__ == '__main__':
    if sys.argv[1] == 'sim':
        e = int(S.T_RES * FPS) - 1
        print(SEED, S.OUTCOME, round(S.T_RES - S.T_START, 2), 'min', round(min(GRIP[:e + 1])), 'final', round(GRIP[e]), 'bursts', len([b for b in BURSTS if b['t'] < S.T_END]), 'dur', S.DUR); sys.exit()
    run(S, render)
