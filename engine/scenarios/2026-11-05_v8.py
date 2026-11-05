"""2026-11-05 v8 — GRIP / TUG – GRIP %: the BLACK HOLE. Gloop is a passive rigid ball (Ball) bouncing
across a small asteroid outpost between a metal antenna mast (left wall) and a big boulder (right wall).
A swirling black hole hangs in the sky above the boulder. Seeded-random pull bursts (strength + length
vary) really drag him toward it (sideways, plus a mild lift) and drain his sticky GRIP — faster the
closer he is and the stronger the burst. Between bursts GRIP slowly recovers. GRIP 0% = he's sucked up
into a spin around the black hole and spat back out dizzy."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the black hole'
SEED = int(os.environ.get('SEED', 25))
rng = random.Random(SEED)

class S: pass
S.HOOK2 = 'THE BLACK HOLE?'; S.HOOK2_SIZE = 96; S.FAIL_WORD = 'SUCKED IN!'; S.FAIL_SIZE = 130
S.T_START = HOOK_T; S.TL = 13.5; S.T_END = S.T_START + S.TL
GROUND = 1600; R = 58; XMIN, XMAX = 230, 800; ROCK_X = XMAX + R
DRAIN, REGEN, PULL, LIFT = float(os.environ.get('DRAIN', 55)), 5.0, 900.0, 520.0
BH = (790, 840)

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
S.AMB = {'drone': 42, 'wind': 0.02, 'rumble': 0.02}

def draw_bar(c, t, f):
    p = GRIP[f] / 100; down = SUCK[f] > 0.05 and t < S.T_RES
    bx = bar(c, p, f'GRIP {int(math.ceil(GRIP[f]))}%', good_bad_col(p), 0.1 if down else 0, bw=640, x_off=36)
    c.save(); c.translate(bx - 52, 231); c.set_source_rgb(*rgb('#ffb347')); c.arc(0, 6, 18, 0, 2 * math.pi); c.fill()
    for dx in (-16, -5, 6, 17): c.arc(dx, -16, 7, 0, 2 * math.pi); c.fill()
    c.restore()
S.draw_bar = draw_bar

stars = [(rng.uniform(0, W), rng.uniform(HEAD, 1450), rng.uniform(1.0, 2.6), rng.uniform(0, 6.3)) for _ in range(110)]
CRATERS = [(rng.uniform(250, 800), rng.uniform(0.6, 1.2)) for _ in range(4)]
def draw_bg(c, t, P):
    c.set_source_rgb(*rgb('#0e0f1a')); c.rectangle(0, HEAD, W, H - HEAD); c.fill()
    for (x, y, r, ph) in stars:   # stars near the hole drift around it (gentle lensing feel)
        dx, dy = x - BH[0], y - BH[1]; d = math.hypot(dx, dy)
        a = math.atan2(dy, dx) + (0.6 * (t * 0.05) * 300 / max(d, 150))
        sx, sy = BH[0] + math.cos(a) * d, BH[1] + math.sin(a) * d
        c.set_source_rgba(0.85, 0.87, 0.95, 0.35 + 0.25 * math.sin(t * 2 + ph)); c.arc(sx, sy, r, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#3a4a6a')); c.arc(200, 640, 70, 0, 2 * math.pi); c.fill()   # far planet
    c.set_source_rgb(*rgb('#2e3c58')); c.arc(222, 620, 70, 0, 2 * math.pi); c.fill()
    c.set_source_rgba(0.6, 0.65, 0.75, 0.5); c.set_line_width(4); c.save(); c.translate(200, 640); c.scale(120, 22); c.arc(0, 0, 1, 0.2, math.pi - 0.2); c.restore(); c.stroke()
    # far ridge + ground
    c.set_source_rgb(*rgb('#22232e')); c.move_to(0, GROUND)
    for x in range(0, W + 1, 40): c.line_to(x, 1450 - 40 * math.sin(x / 140) - 25 * math.sin(x / 57))
    c.line_to(W, GROUND); c.close_path(); c.fill()
    TER.fill(c, TER.h, '#55555e', '#2b2b33', '#6a6a74')
    for (x, s_) in CRATERS:
        c.set_source_rgb(*rgb('#3e3e47')); c.save(); c.translate(x, TER.y(x) + 60 * s_ + 30); c.scale(70 * s_, 14 * s_); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()

def draw_mast(c, t):
    bw = XMIN - R; x0 = bw * 0.5
    c.set_source_rgb(*rgb('#7d8494')); c.set_line_width(10)
    c.move_to(x0 - 50, GROUND); c.line_to(x0 - 12, 900); c.stroke(); c.move_to(x0 + 50, GROUND); c.line_to(x0 + 12, 900); c.stroke()
    c.set_line_width(5)
    for k in range(9):
        y1 = GROUND - k * 78; y2 = y1 - 78; w1 = 50 - 38 * (k / 9); w2 = 50 - 38 * ((k + 1) / 9)
        c.move_to(x0 - w1, y1); c.line_to(x0 + w2, y2); c.move_to(x0 + w1, y1); c.line_to(x0 - w2, y2); c.stroke()
    c.set_source_rgb(*rgb('#9aa1b0')); c.save(); c.translate(x0 + 10, 890); c.rotate(-0.5); c.scale(1, 0.45); c.arc(0, 0, 70, 0, math.pi); c.restore(); c.fill()   # dish
    on = (t * 1.5) % 1 < 0.2
    c.set_source_rgb(*(rgb('#ff6060') if on else rgb('#6a2a2a'))); c.arc(x0, 860, 8, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#6a7080')); rrect(c, -10, GROUND - 60, bw + 10, 60, 8); c.fill()   # base block = wall face

def draw_hole(c, t, P):
    x, y = BH; sp = t * (1.2 + 2.5 * P)
    # back half of the accretion ring
    for i in range(3):
        c.set_source_rgba(0.62 - i * 0.1, 0.42 - i * 0.06, 0.55 + i * 0.05, 0.75 - i * 0.18); c.set_line_width(16 - i * 4)
        c.save(); c.translate(x, y); c.rotate(-0.25); c.scale(205 + i * 24, 42 + i * 7); c.arc(0, 0, 1, math.pi, 2 * math.pi); c.restore(); c.stroke()
    # swirl streaks
    c.set_line_width(4)
    for i in range(10):
        a0 = sp * (1 + (i % 3) * 0.3) + i * 0.63; rr = 130 + (i * 23) % 120
        c.set_source_rgba(0.55, 0.45, 0.6, 0.35)
        c.save(); c.translate(x, y); c.rotate(-0.25); c.scale(rr * 1.4, rr * 0.32); c.arc(0, 0, 1, a0, a0 + 0.9); c.restore(); c.stroke()
    for i in range(2):   # lensed far side of the disk: a thin arc bent over the top of the hole
        c.set_source_rgba(0.66 - i * 0.1, 0.48, 0.58, 0.55 - i * 0.2); c.set_line_width(9 - i * 4)
        c.save(); c.translate(x, y); c.rotate(-0.25); c.scale(1, 0.82); c.arc(0, 0, 140 + i * 14, math.pi * 1.04, math.pi * 1.96); c.restore(); c.stroke()
    c.set_source_rgb(0.02, 0.02, 0.04); c.arc(x, y, 112, 0, 2 * math.pi); c.fill()   # the hole
    c.set_source_rgba(0.75, 0.6, 0.62, 0.7); c.set_line_width(3); c.arc(x, y, 114, 0, 2 * math.pi); c.stroke()   # thin photon ring
    # front half of the ring
    for i in range(3):
        c.set_source_rgba(0.72 - i * 0.1, 0.5 - i * 0.06, 0.55 + i * 0.05, 0.85 - i * 0.2); c.set_line_width(16 - i * 4)
        c.save(); c.translate(x, y); c.rotate(-0.25); c.scale(205 + i * 24, 42 + i * 7); c.arc(0, 0, 1, 0, math.pi); c.restore(); c.stroke()
    # pebbles spiralling in
    for i in range(7):
        k = 1 - ((i * 0.143 + t * (0.12 + 0.25 * P)) % 1); rr = 120 + 240 * k; a = t * (2 + 3 * P) / max(0.4, k) * 0.4 + i * 0.9
        px, py = x + math.cos(a) * rr * 1.2, y + math.sin(a) * rr * 0.35
        if math.sin(a) < 0 and rr * 0.35 < 60: continue
        c.set_source_rgb(*rgb('#8a8a94')); c.arc(px, py, 4 + 6 * k, 0, 2 * math.pi); c.fill()

def draw_rock(c, t):
    x0 = ROCK_X
    c.set_source_rgb(*rgb('#5c5560')); c.move_to(x0, GROUND + 10); c.line_to(x0 + 6, GROUND - 230); c.line_to(x0 + 60, GROUND - 330); c.line_to(x0 + 170, GROUND - 350); c.line_to(W + 10, GROUND - 300); c.line_to(W + 10, GROUND + 10); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#4a444e')); c.move_to(x0 + 6, GROUND - 230); c.line_to(x0 + 60, GROUND - 330); c.line_to(x0 + 80, GROUND - 120); c.line_to(x0 + 30, GROUND + 10); c.line_to(x0, GROUND + 10); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#6e6772')); c.move_to(x0 + 60, GROUND - 330); c.line_to(x0 + 170, GROUND - 350); c.line_to(x0 + 150, GROUND - 300); c.close_path(); c.fill()

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
    if P > 0.25 and f % 3 == 0 and t < S.T_RES: PS.spawn(rng.uniform(300, 760), GROUND - 10, 1, (0.55, 0.55, 0.6), 120, 0.7, grav=-500, r=5)
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
