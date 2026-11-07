"""2026-11-07 v2 — GRIP / TUG – GRIP %: the SPACESHIP AIRLOCK. Gloop is a passive rigid ball (Ball)
bouncing across a space-station cargo bay between a control console (left wall) and stacked crates (right
wall). A faulty airlock hatch high on the right wall keeps irising open: seeded-random breach bursts
(strength + length vary) really drag him toward it (sideways, plus a mild lift) and drain his sticky GRIP —
faster the closer he is. Between bursts GRIP slowly recovers. GRIP 0% = sucked up to the hatch, spun
around and bounced back off the closing iris, dizzy."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the spaceship airlock'
SEED = int(os.environ.get('SEED', 25))
rng = random.Random(SEED)

class S: pass
S.HOOK2 = 'THE SPACESHIP AIRLOCK?'; S.HOOK2_SIZE = 78; S.FAIL_WORD = 'SUCKED UP!'; S.FAIL_SIZE = 130
S.T_START = HOOK_T; S.TL = 13.5; S.T_END = S.T_START + S.TL
GROUND = 1600; R = 58; XMIN, XMAX = 230, 800; ROCK_X = XMAX + R
DRAIN, REGEN, PULL, LIFT = float(os.environ.get('DRAIN', 55)), 5.0, 900.0, 520.0
BH = (790, 860)

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

DOTS = [(rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(1, 3)) for _ in range(40)]
def draw_bg(c, t, P):
    c.set_source_rgb(*rgb('#1a1e2a')); c.rectangle(0, HEAD, W, H - HEAD); c.fill()
    # wall panels
    c.set_source_rgb(*rgb('#222838'))
    for x in range(0, W, 180):
        for y in range(HEAD + 40, GROUND - 100, 260): rrect(c, x + 12, y, 156, 236, 14); c.fill()
    c.set_source_rgba(0, 0, 0, 0.25)
    for x in range(0, W, 180):
        for y in range(HEAD + 40, GROUND - 100, 260):
            for k in (0, 1): c.arc(x + 30 + k * 120, y + 18, 5, 0, 2 * math.pi); c.fill()
    # ceiling pipes + warning stripe
    c.set_source_rgb(*rgb('#3a4254')); c.rectangle(0, 400, W, 26); c.fill(); c.rectangle(0, 440, W, 14); c.fill()
    for x in range(0, W, 60):
        c.set_source_rgb(*(rgb('#c89a2a') if (x // 60) % 2 else rgb('#2a2a2a'))); c.move_to(x, GROUND - 260); c.line_to(x + 30, GROUND - 260); c.line_to(x + 60, GROUND - 230); c.line_to(x + 30, GROUND - 230); c.close_path(); c.fill()
    # red alarm lamp blinks during a breach
    on = P > 0.05 and (t * 3) % 1 < 0.5
    c.set_source_rgb(*(rgb('#ff5050') if on else rgb('#5a2a2a'))); c.arc(540, 500, 18, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#3a4254')); c.rectangle(522, 478, 36, 8); c.fill()
    # metal floor
    TER.fill(c, TER.h, '#4a5060', '#2a2e38', '#5e6576')
    c.set_source_rgba(0, 0, 0, 0.18); c.set_line_width(3)
    for x in range(40, W, 120): c.move_to(x, GROUND + 20); c.line_to(x, H); c.stroke()

def draw_mast(c, t):   # left wall: control console
    bw = XMIN - R
    c.set_source_rgb(*rgb('#3c4456')); c.rectangle(-10, GROUND - 520, bw + 10, 520); c.fill()
    c.set_source_rgb(*rgb('#2a3040')); c.rectangle(-10, GROUND - 520, bw + 10, 30); c.fill()
    c.set_source_rgb(*rgb('#10202a')); rrect(c, 20, GROUND - 460, bw - 40, 120, 10); c.fill()
    c.set_source_rgba(0.4, 0.9, 0.7, 0.8); c.set_line_width(3)
    for i in range(3):
        c.move_to(30, GROUND - 430 + i * 32)
        for x in range(30, bw - 20, 8): c.line_to(x, GROUND - 430 + i * 32 + 8 * math.sin(x * 0.1 + t * 4 + i))
        c.stroke()
    for i, col in enumerate(('#ff6060', '#ffd060', '#60ff90', '#60a0ff')):
        on = (t * 1.3 + i * 0.37) % 1 < 0.5
        c.set_source_rgb(*(rgb(col) if on else rgb('#30343e'))); c.arc(36 + i * 28, GROUND - 300, 9, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#2a3040'))
    for i in range(3): rrect(c, 24, GROUND - 250 + i * 70, bw - 48, 46, 8); c.fill()

def draw_hole(c, t, P):   # the airlock hatch (open during bursts)
    x, y = BH; RH = 112
    c.set_source_rgb(*rgb('#4a5264')); c.arc(x, y, RH + 46, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#2c3242')); c.arc(x, y, RH + 18, 0, 2 * math.pi); c.fill()
    for i in range(8):
        a = i * math.pi / 4; c.set_source_rgb(*rgb('#6a7284')); c.arc(x + math.cos(a) * (RH + 32), y + math.sin(a) * (RH + 32), 6, 0, 2 * math.pi); c.fill()
    op = clamp(P * 1.4, 0, 1) if P > 0.02 else 0
    gap = RH * op
    c.set_source_rgb(*rgb('#6a7284')); c.arc(x, y, RH, 0, 2 * math.pi); c.fill()   # closed iris disk
    if gap > 2:
        c.save(); c.arc(x, y, gap, 0, 2 * math.pi); c.clip()
        c.set_source_rgb(0.02, 0.02, 0.06); c.paint()   # space outside
        for (dx, dy, r) in DOTS:
            c.set_source_rgba(0.9, 0.9, 1, 0.8); c.arc(x + dx * RH, y + dy * RH, r, 0, 2 * math.pi); c.fill()
        c.set_source_rgb(*rgb('#3a6aa0')); c.arc(x + 60, y + 90, 70, 0, 2 * math.pi); c.fill()   # planet edge
        c.restore()
    c.set_source_rgba(0, 0, 0, 0.35); c.set_line_width(4)   # iris blade seams
    for i in range(6):
        a0 = i * math.pi / 3 + op * 0.8
        c.move_to(x + math.cos(a0) * gap, y + math.sin(a0) * gap)
        c.curve_to(x + math.cos(a0 + 0.5) * (gap + RH) * 0.5, y + math.sin(a0 + 0.5) * (gap + RH) * 0.5, x + math.cos(a0 + 0.9) * RH, y + math.sin(a0 + 0.9) * RH, x + math.cos(a0 + 0.9) * RH, y + math.sin(a0 + 0.9) * RH)
        c.stroke()
    if gap > 2: c.set_line_width(5); c.set_source_rgb(*rgb('#8a92a4')); c.arc(x, y, gap, 0, 2 * math.pi); c.stroke()
    # stripes of air rushing in toward the hatch
    if P > 0.05:
        c.set_line_width(5)
        for i in range(12):
            k = (t * (1.5 + P) + i / 12) % 1; ang = math.pi * 0.65 + (i * 0.37) % 1.4
            d0 = 520 * (1 - k) + RH
            sx, sy = x + math.cos(ang) * d0, y + math.sin(ang) * d0
            ex, ey = x + math.cos(ang) * (d0 - 70), y + math.sin(ang) * (d0 - 70)
            c.set_source_rgba(0.8, 0.9, 1, 0.45 * P * k); c.move_to(sx, sy); c.line_to(ex, ey); c.stroke()
    # warning label
    c.set_source_rgb(*rgb('#c89a2a')); rrect(c, x - 90, y + RH + 60, 180, 40, 6); c.fill()
    font(c, 26); c.set_source_rgb(0.1, 0.1, 0.1); e = c.text_extents('AIRLOCK'); c.move_to(x - e.width / 2 - e.x_bearing, y + RH + 90); c.show_text('AIRLOCK')

def draw_rock(c, t):   # right wall: cargo crates
    x0 = ROCK_X
    for (yy, h_, col) in ((GROUND - 170, 170, '#6a5a44'), (GROUND - 320, 150, '#5a4c3a')):
        c.set_source_rgb(*rgb(col)); c.rectangle(x0, yy, W - x0 + 10, h_); c.fill()
        c.set_source_rgba(0, 0, 0, 0.3); c.set_line_width(6); c.rectangle(x0 + 8, yy + 8, W - x0 - 10, h_ - 16); c.stroke()
        c.move_to(x0 + 8, yy + 8); c.line_to(W, yy + h_ - 8); c.stroke()

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
