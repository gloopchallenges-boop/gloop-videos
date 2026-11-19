"""2026-11-19 v1 — HEIGHT GAUGE – UFO m: the LANDING UFO. (based on 2026-11-14 v5) Gloop is a passive rigid ball (Ball) bouncing on the
stone floor of an ancient jungle temple at night. A huge carved stone slab above grinds down in seeded-random
jolts. Two big bouncy mushrooms launch him much higher when he happens to land on one. A ruler on the side marks
every bounce peak and the slab height; header shows `SLAB x.x m`. If his top ever touches the slab during the
countdown -> SQUASHED (fail, flattened then pops back dizzy). Timer ends -> the trap stops and the slab lifts."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the landing UFO'
SEED = int(os.environ.get('SEED', 16))
rng = random.Random(SEED)

class S: pass
S.HOOK2 = 'THE LANDING UFO?'; S.HOOK2_SIZE = 90; S.FAIL_WORD = 'SQUASHED!'; S.FAIL_SIZE = 150
S.T_START = HOOK_T; S.TL = float(os.environ.get('TL', 13.0)); S.T_END = S.T_START + S.TL
GROUND = 1640; R = 58; XMIN, XMAX = 190, 890; PPM = 150.0; TIP0 = 520.0; SPK = 40
DROP = (float(os.environ.get('D0', 28)), float(os.environ.get('D1', 62)))

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
TIPF = TIP[fr]; SLAM = 0.15
for i in range(fr, N0):
    ti = i / FPS
    if T_FAIL:   # the plate slams all the way down, holds, then lifts back up
        if ti < T_FAIL + SLAM: TIP[i] = lerp(TIPF, GROUND - 26, ((ti - T_FAIL) / SLAM) ** 2)
        elif ti < T_FAIL + 0.55: TIP[i] = GROUND - 26
        else: TIP[i] = lerp(GROUND - 26, TIP0 - 60, ease((ti - T_FAIL - 0.55) / 1.0))
    else:
        k = ease((ti - (S.T_RES + 0.5)) / 1.2); TIP[i] = lerp(TIP[fr], TIP0 - 60, k)
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
if T_FAIL: S.events += [[T_FAIL, 'clang'], [T_FAIL + 0.55, 'thump', 1.0]]
else: S.events.append([S.T_END, 'slam'])
S.AMB = {'drone': 55, 'rumble': 0.03, 'wind': 0.012}

def gap_m(f): return (GROUND - TIP[f]) / PPM
def draw_bar(c, t, f):
    g = gap_m(f); p = clamp((g - 2.0) / ((GROUND - TIP0) / PPM - 2.0), 0, 1)
    jolt = any(0 <= t - j['t'] < 0.3 for j in JOLTS) and t < S.T_RES
    bx_ = bar(c, p, f'UFO {g:.1f} m', good_bad_col(p), 0.12 if jolt else 0, bw=640, x_off=36)
    c.save(); c.translate(bx_ - 52, 231); c.set_source_rgb(*rgb('#8fa8b8')); c.save(); c.scale(1, 0.45); c.arc(0, 0, 30, 0, 2 * math.pi); c.restore(); c.fill()
    c.set_source_rgb(*rgb('#7de0c0')); c.arc(0, -8, 13, math.pi, 2 * math.pi); c.fill()
    c.restore()
S.draw_bar = draw_bar


STARS = [(random.Random(SEED + 99).uniform(0, W), random.Random(SEED + 99 + i).uniform(HEAD, 1250), i) for i in range(60)]
_sr = random.Random(77); STARS = [(_sr.uniform(0, W), _sr.uniform(HEAD + 10, 1250), _sr.uniform(1.5, 3.5)) for i in range(70)]
def draw_room(c, t, f):
    # cornfield farm at night: sky, moon, distant barn + corn, hay-bale walls, dirt yard
    c.set_source_rgb(*rgb('#141a2a')); c.rectangle(0, HEAD, W, H - HEAD); c.fill()
    for (sx, sy, sr) in STARS:
        c.set_source_rgba(0.85, 0.88, 1, 0.35 + 0.25 * math.sin(t * 2 + sx)); c.arc(sx, sy, sr, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#d8d4c0')); c.arc(860, 1150, 46, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#141a2a')); c.arc(878, 1140, 40, 0, 2 * math.pi); c.fill()
    # distant hills + barn + corn rows
    c.set_source_rgb(*rgb('#1c2434')); c.move_to(0, 1420); c.curve_to(300, 1330, 600, 1380, W, 1340); c.line_to(W, GROUND); c.line_to(0, GROUND); c.fill()
    bx = 640; by = 1420
    c.set_source_rgb(*rgb('#4a2420')); c.rectangle(bx, by - 120, 170, 120); c.fill()
    c.move_to(bx - 14, by - 120); c.line_to(bx + 85, by - 190); c.line_to(bx + 184, by - 120); c.fill()
    c.set_source_rgb(*rgb('#2e1614')); c.rectangle(bx + 60, by - 70, 50, 70); c.fill()
    c.set_source_rgb(*rgb('#d8c070')); c.rectangle(bx + 72, by - 160, 26, 22); c.fill()
    c.set_source_rgb(*rgb('#24301e'))
    for xx in range(-20, W + 40, 34):
        hh = 120 + 20 * math.sin(xx * 0.3)
        c.move_to(xx, GROUND); c.line_to(xx + 8, GROUND - hh); c.line_to(xx + 22, GROUND - hh + 10); c.line_to(xx + 30, GROUND); c.fill()
    c.set_source_rgb(*rgb('#2f3d26'))
    for xx in range(0, W + 40, 34):
        c.set_line_width(4); c.move_to(xx + 15, GROUND - 60); c.line_to(xx + 35, GROUND - 90); c.stroke()
    # hay-bale stack walls
    for (x0, x1) in ((0, XMIN - R), (XMAX + R, W)):
        for k, yy in enumerate(range(GROUND - 110, 900, -110)):
            c.set_source_rgb(*rgb('#b89a50' if k % 2 else '#a88a44')); rrect(c, x0 - 10, yy, x1 - x0 + 20, 104, 16); c.fill()
            c.set_source_rgb(*rgb('#8a6e34'))
            for xs in range(int(x0) + 12, int(x1), 26): c.rectangle(xs, yy + 10, 3, 84); c.fill()
            c.set_source_rgb(*rgb('#6a4a26')); c.rectangle(x0, yy + 30, x1 - x0, 6); c.fill(); c.rectangle(x0, yy + 70, x1 - x0, 6); c.fill()
    # dirt yard
    c.set_source_rgb(*rgb('#4a3a2c')); c.rectangle(0, GROUND, W, H - GROUND); c.fill()
    c.set_source_rgb(*rgb('#3c2f24'))
    for k in range(14): c.arc(XMIN + (k * 97) % (XMAX - XMIN), GROUND + 50 + (k * 53) % 200, 8 + k % 3 * 4, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#5a4836')); c.rectangle(0, GROUND - 2, W, 6); c.fill()
    # ruler post on the left
    rx = XMIN - R - 66
    c.set_source_rgb(*rgb('#d9c9a0')); c.rectangle(rx, TIP0 - 40, 40, GROUND - 90 - TIP0 + 40); c.fill()
    c.set_source_rgb(0.15, 0.12, 0.1)
    for k in range(1, 9):
        y = GROUND - k * PPM
        if y < TIP0 - 40: break
        c.rectangle(rx, y - 2, 22, 4); c.fill()
        font(c, 22); c.move_to(rx + 24, y + 8); c.show_text(str(k))
        if y - PPM / 2 > TIP0 - 40: c.rectangle(rx, y - PPM / 2 - 1, 12, 2); c.fill()

def draw_ceiling(c, t, f):   # giant flying saucer, flat underside = TIP
    tip = TIP[f]; x0, x1 = XMIN - R - 30, XMAX + R + 30; cx = W / 2
    # faint landing beam
    c.set_source_rgba(0.5, 1, 0.85, 0.07); c.move_to(cx - 200, tip); c.line_to(cx + 200, tip); c.line_to(XMAX + R, GROUND); c.line_to(XMIN - R, GROUND); c.fill()
    # dome
    c.set_source_rgb(*rgb('#5ac8b0')); c.save(); c.translate(cx, tip - 150); c.scale(190, 130); c.arc(0, 0, 1, math.pi, 2 * math.pi); c.restore(); c.fill()
    c.set_source_rgba(1, 1, 1, 0.18); c.save(); c.translate(cx - 70, tip - 210); c.scale(40, 26); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    # alien silhouette in the dome
    c.set_source_rgb(*rgb('#2e6a5e')); c.save(); c.translate(cx + 30, tip - 200); c.scale(34, 40); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    c.rectangle(cx + 6, tip - 170, 48, 30); c.fill()
    c.set_source_rgb(*rgb('#0e1a18')); 
    for dx in (-12, 12): c.save(); c.translate(cx + 30 + dx, tip - 204); c.rotate(dx * 0.03); c.scale(9, 14); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    # upper hull
    c.set_source_rgb(*rgb('#8a96a8')); c.move_to(x0 + 60, tip - 70); c.curve_to(x0 + 200, tip - 175, x1 - 200, tip - 175, x1 - 60, tip - 70); c.close_path(); c.fill()
    # rim
    c.set_source_rgb(*rgb('#6a7586')); rrect(c, x0, tip - 80, x1 - x0, 50, 25); c.fill()
    for k in range(9):
        lx = x0 + 50 + k * (x1 - x0 - 100) / 8
        on = int(t * 6 + k) % 3 == 0
        c.set_source_rgb(*rgb('#ffe070' if on else '#8a7a40')); c.arc(lx, tip - 55, 11, 0, 2 * math.pi); c.fill()
    # flat underside
    c.set_source_rgb(*rgb('#4a5262')); c.rectangle(x0 + 30, tip - 32, x1 - x0 - 60, 32); c.fill()
    c.set_source_rgb(*rgb('#3a4050'))
    for xx in range(int(x0) + 60, int(x1) - 40, 90): c.rectangle(xx, tip - 32, 5, 32); c.fill()
    c.set_source_rgb(*rgb('#7de0c0')); c.save(); c.translate(cx, tip - 8); c.scale(60, 8); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    rx = XMIN - R - 66
    c.set_source_rgb(*rgb('#ff5a4d')); c.rectangle(rx - 8, tip - 3, 56, 6); c.fill()

def draw_springs(c, t):   # big bouncy green alien-goo domes
    for sp in SPRINGS:
        x = sp['x']; k = 0.0
        for (ts, xs) in SPR_T:
            if xs == x and 0 <= t - ts < 0.25: k = 1 - (t - ts) / 0.25
        h_ = 52 - 20 * k; w_ = 68 + 12 * k
        c.set_source_rgb(*rgb('#3aa060')); c.move_to(x - w_, GROUND + 2); c.curve_to(x - w_, GROUND - h_ - 14, x + w_, GROUND - h_ - 14, x + w_, GROUND + 2); c.close_path(); c.fill()
        c.set_source_rgb(*rgb('#6ad080')); c.save(); c.translate(x - 22, GROUND - h_ * 0.6); c.scale(14, 8); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
        c.set_source_rgb(*rgb('#2a7a48')); c.arc(x + 24, GROUND - h_ * 0.35, 6, 0, 2 * math.pi); c.fill(); c.arc(x - 6, GROUND - h_ * 0.2, 4, 0, 2 * math.pi); c.fill()

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
        if abs(t - ts) < 0.5 / FPS and ts < S.T_RES: PS.spawn(xs, GROUND - 40, 10, (0.9, 0.85, 0.6), 300, 0.4, grav=1200, r=5)
    poked = T_FAIL is not None and t >= T_FAIL
    if END.carried(t) or t >= END.T_GRAB:
        gx, gy = (END.carry_xy(t) if END.carried(t) else S.GRAB)
        draw_blob(c, t, gx, gy, 'worried' if poked else 'happy', 0, R=R, dizzy=poked)
    elif poked:
        if t < T_FAIL + SLAM:   # pushed down under the plate
            gx = FX; gy = min(GROUND - R, TIP[fi] + R); draw_blob(c, t, gx, gy, 'scared', 0, R=R)
        elif t < T_DROP:   # plate slams down and pancakes him on the floor
            gx = FX; c.save(); c.translate(gx, GROUND - 14); c.scale(1.8, 0.22); draw_blob(c, t, 0, -R * 0.0, 'scared', 0, R=R, sweat=False); c.restore()
        else:
            pk = ease((t - T_DROP) / 0.3); gx, gy = FX, GROUND - R
            c.save(); c.translate(gx, gy + R * (1 - pk) * 0.75); c.scale(1.8 - 0.8 * pk, 0.22 + 0.78 * pk); draw_blob(c, t, 0, 0, 'worried', 0, R=R, dizzy=True); c.restore()
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
            for x in (XMIN, XMAX): PS.spawn(x + rng.uniform(-60, 60), TIP[fi] - 10, 4, (0.6, 0.55, 0.5), 150, 0.8, grav=1500, r=5)
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
