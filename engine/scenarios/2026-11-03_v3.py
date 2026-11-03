"""2026-11-03 v3 — HEIGHT GAUGE – CEILING m: the SPIKE CEILING. Gloop is a passive rigid ball (Ball) bouncing
in a stone trap room. A spiked ceiling grinds down in seeded-random jolts (clank + drop). Two spring pads
on the floor launch him much higher when he happens to land on one. A ruler on the wall marks every bounce
peak and the ceiling height; header shows `CEILING x.x m` (gap between floor and the spike tips).
If his top ever touches the spike tips during the countdown -> POKED (fail). Timer ends -> the trap locks."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the spike ceiling'
SEED = int(os.environ.get('SEED', 13))
rng = random.Random(SEED)

class S: pass
S.HOOK2 = 'THE SPIKE CEILING?'; S.HOOK2_SIZE = 90; S.FAIL_WORD = 'POKED!'; S.FAIL_SIZE = 150
S.T_START = HOOK_T; S.TL = float(os.environ.get('TL', 13.0)); S.T_END = S.T_START + S.TL
GROUND = 1640; R = 58; XMIN, XMAX = 190, 890; PPM = 150.0; TIP0 = 560.0; SPK = 70
DROP = (float(os.environ.get('D0', 30)), float(os.environ.get('D1', 62)))

JOLTS = []; t = 0.15
while t < 40:
    pre = t < S.T_START
    JOLTS.append({'t': t, 'd': rng.uniform(6, 12) if pre else rng.uniform(*DROP)})
    t += rng.uniform(0.45, 0.7) if pre else rng.uniform(0.7, 1.5)
JOLTS = [j for j in JOLTS if j['t'] < S.T_END]
SPRINGS = []
for k in range(2):
    while True:
        x = rng.uniform(XMIN + 70, XMAX - 70)
        if all(abs(x - s['x']) > 260 for s in SPRINGS): break
    SPRINGS.append({'x': x, 'h': rng.uniform(380, 560)})

def tip_sim(t):   # spike tip y from the jolts (each drop eases in over 0.25 s)
    y = TIP0
    for j in JOLTS:
        if t >= j['t']: y += j['d'] * ease((t - j['t']) / 0.25)
    return y

TER = Terrain(GROUND, seed=SEED, bumps=3, amp=6, soft=False)
N0 = int(30 * FPS); GX, GYS, TIP, PEAKS, SPR = [], [], [], [], []
ball = Ball(rng.uniform(320, 760), TER, R=R, seed=SEED, xmin=XMIN, xmax=XMAX, hop=rng.uniform(230, 280))
T_FAIL = None; nl = 0; prev_vy = 0.0; SPR_T = []
for f in range(N0):
    t = f / FPS
    tip = tip_sim(min(t, S.T_END)) if T_FAIL is None else TIP[-1]
    if T_FAIL is None:
        ball.step(t)
        while nl < len(ball.landings):
            tl, xl, imp = ball.landings[nl]; nl += 1
            for sp in SPRINGS:
                if abs(xl - sp['x']) < 62:
                    ball.vy = -math.sqrt(2 * ball.G * sp['h']); SPR_T.append((tl, sp['x']))
        if prev_vy < 0 <= ball.vy: PEAKS.append((t, ball.x, (GROUND - (ball.y - R)) / PPM))   # apex: top-of-Gloop height
        prev_vy = ball.vy
        if ball.y - R <= tip:
            if S.T_START <= t < S.T_END: T_FAIL = t; FX = ball.x; ball.y = tip + R
            else: ball.y = tip + R; ball.vy = abs(ball.vy) * 0.5   # (never happens before the start: ceiling is high)
    GX.append(ball.x); GYS.append(ball.y); TIP.append(tip)
S.OUTCOME = 'fail' if T_FAIL else 'win'
S.T_RES = T_FAIL if T_FAIL else S.T_END
S.GRAB = (540, GROUND - R)
END = S.END = Ending(S)
# after the result the trap resets: ceiling slides back up (so the claw can come in)
fr = int(S.T_RES * FPS)
for i in range(fr, N0):
    k = ease(((i / FPS) - (S.T_RES + 0.5)) / 1.2); TIP[i] = lerp(TIP[fr], TIP0 - 60, k)
if T_FAIL:
    FY0 = GYS[fr]; T_DROP = T_FAIL + 0.55
    S.GRAB = (FX, GROUND - R)
else:
    gi = min(int(END.T_GRAB * FPS), N0 - 1); S.GRAB = (GX[gi], GYS[gi])
S.events = []
for j in JOLTS:
    if j['t'] < S.T_RES: S.events += [[j['t'], 'clang' if j['d'] > 20 else 'creak'], [j['t'], 'rumble', 0.4]]
for (tl, xl, imp) in ball.landings:
    if tl < S.T_RES + 1.3: S.events.append([tl, 'hop'])
for (ts, xs) in SPR_T:
    if ts < S.T_RES + 1.3: S.events.append([ts, 'pop'])
for tw in ball.walls:
    if tw < S.T_RES + 1.3: S.events.append([tw, 'thump', 0.4])
S.events.append([S.T_RES + 0.5, 'rumble', 1.2])
if T_FAIL: S.events += [[T_FAIL, 'crash'], [T_FAIL + 0.55, 'thump', 1.0]]
else: S.events.append([S.T_END, 'slam'])
S.AMB = {'drone': 44, 'rumble': 0.02}

def gap_m(f): return (GROUND - TIP[f]) / PPM
def draw_bar(c, t, f):
    g = gap_m(f); p = clamp((g - 2.0) / ((GROUND - TIP0) / PPM - 2.0), 0, 1)
    jolt = any(0 <= t - j['t'] < 0.3 for j in JOLTS) and t < S.T_RES
    bx_ = bar(c, p, f'CEILING {g:.1f} m', good_bad_col(p), 0.12 if jolt else 0, bw=640, x_off=36)
    c.save(); c.translate(bx_ - 52, 231); c.set_source_rgb(*rgb('#9aa0ab'))
    c.rectangle(-22, -22, 44, 12); c.fill()
    for dx in (-15, 0, 15): c.move_to(dx - 7, -10); c.line_to(dx, 16); c.line_to(dx + 7, -10); c.close_path(); c.fill()
    c.restore()
S.draw_bar = draw_bar

BRICK = [(rng.uniform(0, 1), rng.uniform(0, 1)) for _ in range(40)]
def draw_room(c, t, f):
    c.set_source_rgb(*rgb('#1b1722')); c.rectangle(0, HEAD, W, H - HEAD); c.fill()
    c.set_source_rgb(*rgb('#221d2a'))
    for j in range(12):
        for i in range(-1, 7):
            x = i * 190 + (95 if j % 2 else 0); y = HEAD + 40 + j * 110
            if y < GROUND: c.rectangle(x + 5, y + 5, 180, 100); c.fill()
    # side walls
    for (x0, x1) in ((0, XMIN - R), (XMAX + R, W)):
        c.set_source_rgb(*rgb('#2e2734')); c.rectangle(x0, HEAD, x1 - x0, GROUND - HEAD); c.fill()
        c.set_source_rgb(*rgb('#26202c'))
        for yy in range(HEAD, GROUND, 90): c.rectangle(x0, yy, x1 - x0, 5); c.fill()
    # floor
    c.set_source_rgb(*rgb('#3d3540')); c.rectangle(0, GROUND, W, H - GROUND); c.fill()
    c.set_source_rgb(*rgb('#544a56')); c.rectangle(0, GROUND - 2, W, 6); c.fill()
    c.set_source_rgba(0, 0, 0, 0.15); c.set_line_width(3)
    for yy in range(GROUND + 70, H, 70): c.move_to(0, yy); c.line_to(W, yy); c.stroke()
    # ruler on the left wall
    rx = XMIN - R - 66
    c.set_source_rgb(*rgb('#d9c9a0')); c.rectangle(rx, TIP0 - 40, 40, GROUND - TIP0 + 40); c.fill()
    c.set_source_rgb(0.15, 0.12, 0.1)
    for k in range(0, 9):
        y = GROUND - k * PPM
        if y < TIP0 - 40: break
        c.rectangle(rx, y - 2, 22, 4); c.fill()
        font(c, 22); c.move_to(rx + 24, y + 8); c.show_text(str(k))
        c.rectangle(rx, y - PPM / 2 - 1, 12, 2); c.fill()

def draw_ceiling(c, t, f):
    tip = TIP[f]; base = tip - SPK
    c.set_source_rgb(*rgb('#4b4452')); c.rectangle(XMIN - R - 4, HEAD, XMAX - XMIN + 2 * R + 8, base - HEAD); c.fill()
    c.set_source_rgb(*rgb('#3a3440')); c.rectangle(XMIN - R - 4, base - 26, XMAX - XMIN + 2 * R + 8, 26); c.fill()
    c.set_source_rgb(*rgb('#2c2732'))
    for i, x in enumerate(range(int(XMIN - R + 40), int(XMAX + R - 20), 160)):   # chains/pistons
        c.rectangle(x, HEAD, 18, base - 26 - HEAD); c.fill()
    n = 14; x0, x1 = XMIN - R, XMAX + R; wsp = (x1 - x0) / n
    c.set_source_rgb(*rgb('#a7adb8'))
    for i in range(n):
        xa = x0 + i * wsp; c.move_to(xa, base); c.line_to(xa + wsp / 2, tip); c.line_to(xa + wsp, base); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#7d8390'))
    for i in range(n):
        xa = x0 + i * wsp; c.move_to(xa + wsp / 2, base); c.line_to(xa + wsp / 2, tip); c.line_to(xa + wsp, base); c.close_path(); c.fill()
    # ceiling marker on the ruler
    rx = XMIN - R - 66
    c.set_source_rgb(*rgb('#ff5a4d')); c.rectangle(rx - 8, tip - 3, 56, 6); c.fill()

def draw_springs(c, t):
    for sp in SPRINGS:
        x = sp['x']; k = 0.0
        for (ts, xs) in SPR_T:
            if xs == x and 0 <= t - ts < 0.25: k = 1 - (t - ts) / 0.25
        top = GROUND - 34 + 14 * k
        c.set_source_rgb(*rgb('#8a8f99')); c.set_line_width(7)
        for j in range(4):
            yy = GROUND - 4 - j * (GROUND - 4 - top) / 4
            c.move_to(x - 34, yy); c.line_to(x + 34, yy - (GROUND - 4 - top) / 8); c.stroke()
        c.set_source_rgb(*rgb('#b5544a')); rrect(c, x - 56, top - 12, 112, 16, 6); c.fill()

def draw_peak_marker(c, t):
    pk = [p for p in PEAKS if p[0] <= t and p[0] < S.T_RES + 0.1]
    if not pk: return
    tp, xp, hm = pk[-1]; a = clamp(1 - (t - tp) / 1.4, 0, 1)
    if a <= 0: return
    y = GROUND - hm * PPM; rx = XMIN - R - 66
    c.set_source_rgba(1, 0.65, 0.25, 0.8 * a); c.set_line_width(4); c.set_dash([14, 10])
    c.move_to(rx + 40, y); c.line_to(xp - R - 10, y); c.stroke(); c.set_dash([])
    font(c, 30); s = f'{hm:.1f} m'; e = c.text_extents(s)
    c.move_to(rx + 50, y - 12); c.text_path(s); c.set_source_rgba(0, 0, 0, a); c.set_line_width(6); c.stroke_preserve(); c.set_source_rgba(1, 0.75, 0.35, a); c.fill()

PS = Particles(9)
def render(f, c):
    t = f / FPS; fi = min(f, len(GX) - 1)
    a = 4 if any(0 <= t - j['t'] < 0.18 and j['d'] > 20 and j['t'] < S.T_RES for j in JOLTS) else 0
    shake = (rng.uniform(-a, a), rng.uniform(-a, a))
    c.save(); c.translate(*shake)
    draw_room(c, t, fi); draw_springs(c, t)
    for (ts, xs) in SPR_T:
        if abs(t - ts) < 0.5 / FPS and ts < S.T_RES: PS.spawn(xs, GROUND - 40, 10, (0.6, 0.55, 0.5), 300, 0.4, grav=1200, r=6)
    poked = T_FAIL is not None and t >= T_FAIL
    if END.carried(t) or t >= END.T_GRAB:
        gx, gy = (END.carry_xy(t) if END.carried(t) else S.GRAB)
        draw_blob(c, t, gx, gy, 'worried' if poked else 'happy', 0, R=R, dizzy=poked)
    elif poked:
        if t < T_DROP:
            gx, gy = FX, TIP[int(T_FAIL * FPS)] + R
        else:
            k = clamp((t - T_DROP) / 0.35, 0, 1); gx, gy = FX, lerp(TIP[int(T_FAIL * FPS)] + R, GROUND - R, k * k)
        draw_blob(c, t, gx, gy, 'scared' if t < T_DROP else 'worried', 0, R=R, dizzy=t > T_DROP + 0.3)
        if t >= T_DROP + 0.35:   # little bandage crosses where the spikes poked
            for dx in (-22, 26):
                c.save(); c.translate(gx + dx, gy - R * 0.72); c.rotate(0.5 if dx < 0 else -0.5)
                c.set_source_rgb(*rgb('#f1dcb8')); rrect(c, -18, -6, 36, 12, 4); c.fill(); c.restore()
    else:
        gx, gy = GX[fi], GYS[fi]
        h = max(0, GROUND - R - gy); kk = 1 / (1 + h / 220)
        c.set_source_rgba(0, 0, 0, 0.25 * kk); c.save(); c.translate(gx, GROUND + 3); c.scale(R * (0.5 + 0.4 * kk), 9); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
        close = (gy - R) - TIP[fi] < 250
        mood = 'happy' if (t >= S.T_END and S.OUTCOME == 'win') else ('scared' if close else 'worried')
        draw_blob(c, t, gx, gy, mood, 0, R=R)
    draw_ceiling(c, t, fi); draw_peak_marker(c, t)
    if T_FAIL and abs(t - T_FAIL) < 0.5 / FPS: PS.spawn(FX, TIP[fi] + 10, 16, (0.75, 0.75, 0.8), 380, 0.5, grav=1500, r=6)
    for j in JOLTS:
        if abs(t - j['t']) < 0.5 / FPS and j['t'] < S.T_RES and j['d'] > 20:
            for x in (XMIN, XMAX): PS.spawn(x + rng.uniform(-60, 60), TIP[fi] - SPK - 20, 4, (0.45, 0.4, 0.38), 150, 0.8, grav=1500, r=5)
    PS.draw(c)
    END.draw_claw(c, t)
    c.restore()
    END.header(c, t, fi)

if __name__ == '__main__':
    if sys.argv[1] == 'sim':
        e = int(S.T_RES * FPS) - 1
        margin = min((GYS[i] - R) - TIP[i] for i in range(int(S.T_START * FPS), e + 1))
        print(SEED, S.OUTCOME, round(S.T_RES - S.T_START, 2), 'ceil_end', round(gap_m(e), 2), 'closest_px', round(margin), 'springs', len([s for s in SPR_T if S.T_START <= s[0] < S.T_RES]), 'dur', S.DUR); sys.exit()
    run(S, render)
