"""2026-11-10 v8 — GRIP / TUG – GRIP %: the MAGIC PORTAL. Gloop is a passive rigid ball (Ball) bouncing on the
stone floor of a wizard's tower at night between a stack of spell books (left wall) and a stone pillar (right
wall). A swirling magic portal hanging in the air on the right keeps flaring up: seeded-random surges (strength +
length vary) really drag him toward it (sideways, plus a mild lift) and drain his sticky GRIP — faster the closer
he is. Between surges GRIP slowly recovers. GRIP 0% = sucked into the portal, spun around and spat back out,
dizzy."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the magic portal'
SEED = int(os.environ.get('SEED', 14))
rng = random.Random(SEED)

class S: pass
S.HOOK2 = 'THE MAGIC PORTAL?'; S.HOOK2_SIZE = 90; S.FAIL_WORD = 'SUCKED UP!'; S.FAIL_SIZE = 130
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
S.AMB = {'drone': 52, 'wind': 0.03, 'rumble': 0.02}

def draw_bar(c, t, f):
    p = GRIP[f] / 100; down = SUCK[f] > 0.05 and t < S.T_RES
    bx = bar(c, p, f'GRIP {int(math.ceil(GRIP[f]))}%', good_bad_col(p), 0.1 if down else 0, bw=640, x_off=36)
    c.save(); c.translate(bx - 52, 231); c.set_source_rgb(*rgb('#ffb347')); c.arc(0, 6, 18, 0, 2 * math.pi); c.fill()
    for dx in (-16, -5, 6, 17): c.arc(dx, -16, 7, 0, 2 * math.pi); c.fill()
    c.restore()
S.draw_bar = draw_bar

stars = [(rng.uniform(250, 560), rng.uniform(560, 900), rng.uniform(1.0, 2.2)) for _ in range(14)]
def draw_bg(c, t, P):
    c.set_source_rgb(*rgb('#1a1824')); c.rectangle(0, HEAD, W, H - HEAD); c.fill()
    # curved stone tower wall
    c.set_source_rgb(*rgb('#24212e')); c.rectangle(0, HEAD, W, GROUND - HEAD); c.fill()
    c.set_source_rgb(*rgb('#1c1a26'))
    for j, yy in enumerate(range(HEAD, GROUND, 70)):
        c.rectangle(0, yy, W, 5); c.fill()
        for xx in range((j % 2) * 60, W, 120): c.rectangle(xx, yy, 5, 70); c.fill()
    # arched window with the moon
    c.set_source_rgb(*rgb('#141a30')); c.move_to(250, 900); c.line_to(250, 640); c.arc(405, 640, 155, math.pi, 2 * math.pi); c.line_to(560, 900); c.close_path(); c.fill()
    c.set_source_rgba(0.85, 0.85, 0.9, 0.45)
    for x, y, r in stars: c.arc(x, y, r, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#e2e0cc')); c.arc(470, 620, 34, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#3a3446')); c.set_line_width(12); c.move_to(250, 900); c.line_to(250, 640); c.arc(405, 640, 155, math.pi, 2 * math.pi); c.line_to(560, 900); c.close_path(); c.stroke()
    c.move_to(405, 485); c.line_to(405, 900); c.stroke()
    # wall shelf with candles + potion jars
    c.set_source_rgb(*rgb('#3a2a20')); c.rectangle(150, 1120, 360, 16); c.fill()
    for (x, col) in ((190, '#6a3a8a'), (250, '#3a7a6a'), (440, '#8a6a2a')):
        c.set_source_rgb(*rgb(col)); rrect(c, x - 18, 1070, 36, 50, 8); c.fill()
        c.set_source_rgb(*rgb('#2a2026')); c.rectangle(x - 8, 1060, 16, 12); c.fill()
    for x in (330, 380):
        c.set_source_rgb(*rgb('#d8d0b8')); c.rectangle(x - 8, 1070, 16, 50); c.fill()
        fl = 1 + 0.15 * math.sin(t * 13 + x)
        c.set_source_rgb(*rgb('#f0b84a')); c.save(); c.translate(x, 1058); c.scale(7, 13 * fl); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    # stone floor
    TER.fill(c, TER.h, '#3e3a46', '#26232e', '#4e4a58')
    c.set_source_rgba(0, 0, 0, 0.2); c.set_line_width(3)
    for j, yy in enumerate(range(GROUND + 60, H, 80)):
        c.move_to(0, yy); c.line_to(W, yy); c.stroke()
        for xx in range((j % 2) * 90, W, 180): c.move_to(xx, yy); c.line_to(xx, yy + 80); c.stroke()
    # rune circle painted on the floor
    c.set_source_rgba(0.6, 0.45, 0.85, 0.25); c.set_line_width(5); c.save(); c.translate(500, GROUND + 160); c.scale(260, 50); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.stroke()

def draw_mast(c, t):   # left wall: a tall stack of old spell books
    bw = XMIN - R; yy = GROUND
    cols = ('#6a2a2a', '#2a4a6a', '#5a4a2a', '#3a5a3a', '#4a2a5a', '#6a4a2a', '#2a3a5a', '#5a2a3a')
    for k in range(8):
        h_ = 52 + (k * 13) % 30; off = ((k * 37) % 30) - 15
        c.set_source_rgb(*rgb(cols[k])); rrect(c, -20 + off * 0.3, yy - h_, bw + 20 - abs(off) * 0.3, h_, 6); c.fill()
        c.set_source_rgb(*rgb('#c8a860')); c.rectangle(bw - 30 + off * 0.3, yy - h_ + 10, 8, h_ - 20); c.fill()
        c.set_source_rgb(*rgb('#e8e0c8')); c.rectangle(-20, yy - h_ + 6, 12, h_ - 12); c.fill()
        yy -= h_

def draw_hole(c, t, P):   # the swirling magic portal
    x, y = BH; RH = 120
    c.save(); c.translate(x, y); c.scale(0.8, 1.0)
    c.set_source_rgb(*rgb('#2a1a3a')); c.arc(0, 0, RH + 34, 0, 2 * math.pi); c.fill()
    for k in range(5):   # swirling rings
        rr = RH + 26 - k * 26; a0 = t * (1.5 + 6 * P) * (1 if k % 2 else -1) + k
        c.set_source_rgba(0.55 + 0.1 * k, 0.35 + 0.08 * k, 0.9, 0.85); c.set_line_width(12)
        c.arc(0, 0, max(8, rr), a0, a0 + 4.2); c.stroke()
    c.set_source_rgb(*rgb('#0e0816')); c.arc(0, 0, 34 + 10 * P, 0, 2 * math.pi); c.fill()
    c.restore()
    for i in range(6):   # sparkles orbiting
        a = t * (2 + 4 * P) + i * 2 * math.pi / 6; rr = RH + 50 + 10 * math.sin(t * 3 + i)
        c.set_source_rgba(0.85, 0.75, 1, 0.8); c.arc(x + math.cos(a) * rr * 0.8, y + math.sin(a) * rr, 5, 0, 2 * math.pi); c.fill()
    # streaks of magic rushing in toward the portal
    if P > 0.05:
        c.set_line_width(5)
        for i in range(12):
            k = (t * (1.5 + P) + i / 12) % 1; ang = math.pi * 0.65 + (i * 0.37) % 1.4
            d0 = 520 * (1 - k) + RH + 40
            sx, sy = x + math.cos(ang) * d0, y + math.sin(ang) * d0
            ex, ey = x + math.cos(ang) * (d0 - 70), y + math.sin(ang) * (d0 - 70)
            c.set_source_rgba(0.8, 0.7, 1, 0.45 * P * k); c.move_to(sx, sy); c.line_to(ex, ey); c.stroke()

def draw_rock(c, t):   # right wall: stone pillar
    x0 = ROCK_X
    c.set_source_rgb(*rgb('#4a4656')); c.rectangle(x0, 1100, W - x0 + 10, GROUND - 1100 + 30); c.fill()
    c.set_source_rgb(*rgb('#3a3646'))
    for yy in range(1140, GROUND, 80): c.rectangle(x0, yy, W - x0, 6); c.fill()
    c.set_source_rgb(*rgb('#5a5666')); c.rectangle(x0 - 16, 1080, W - x0 + 30, 34); c.fill()
    c.set_source_rgb(*rgb('#8a5aba')); c.arc(x0 + 80, 1260, 10, 0, 2 * math.pi); c.fill()   # glowing rune
    c.set_source_rgba(0.55, 0.35, 0.9, 0.6); c.set_line_width(3); c.arc(x0 + 80, 1260, 20, 0, 2 * math.pi); c.stroke()

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
    if P > 0.25 and f % 3 == 0 and t < S.T_RES: PS.spawn(rng.uniform(300, 760), GROUND - 10, 1, (0.8, 0.7, 1.0), 160, 0.7, grav=-700, r=4)
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
