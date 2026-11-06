"""2026-11-06 v7 — HEIGHT GAUGE – ELEVATOR m: the RUNAWAY ELEVATOR. Gloop is a passive rigid ball (Ball) bouncing
in the pit at the bottom of an old elevator shaft at night. The elevator car above creaks down in seeded-random
jolts (cable slips). Two buffer springs in the pit launch him much higher when he happens to land on one. A ruler
on the shaft wall marks every bounce peak and the car height; header shows `ELEVATOR x.x m` (gap between the pit
floor and the car). If his top ever touches the car during the countdown -> SQUASHED (fail, pancaked then pops
back dizzy). Timer ends -> the brakes catch and the car stops."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the runaway elevator'
SEED = int(os.environ.get('SEED', 3))
rng = random.Random(SEED)

class S: pass
S.HOOK2 = 'THE RUNAWAY ELEVATOR?'; S.HOOK2_SIZE = 68; S.FAIL_WORD = 'SQUASHED!'; S.FAIL_SIZE = 150
S.T_START = HOOK_T; S.TL = float(os.environ.get('TL', 13.0)); S.T_END = S.T_START + S.TL
GROUND = 1640; R = 58; XMIN, XMAX = 190, 890; PPM = 150.0; TIP0 = 520.0; SPK = 40
DROP = (float(os.environ.get('D0', 40)), float(os.environ.get('D1', 80)))

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
if T_FAIL: S.events += [[T_FAIL, 'crash'], [T_FAIL + 0.55, 'thump', 1.0]]
else: S.events.append([S.T_END, 'slam'])
S.AMB = {'drone': 44, 'rumble': 0.02}

def gap_m(f): return (GROUND - TIP[f]) / PPM
def draw_bar(c, t, f):
    g = gap_m(f); p = clamp((g - 2.0) / ((GROUND - TIP0) / PPM - 2.0), 0, 1)
    jolt = any(0 <= t - j['t'] < 0.3 for j in JOLTS) and t < S.T_RES
    bx_ = bar(c, p, f'ELEVATOR {g:.1f} m', good_bad_col(p), 0.12 if jolt else 0, bw=640, x_off=36)
    c.save(); c.translate(bx_ - 52, 231); c.set_source_rgb(*rgb('#9aa0ab'))
    c.rectangle(-2, -30, 4, 14); c.fill(); rrect(c, -20, -16, 40, 40, 5); c.fill()
    c.set_source_rgb(*rgb('#2a2e36')); c.rectangle(-1, -12, 2, 32); c.fill()
    c.restore()
S.draw_bar = draw_bar

def draw_room(c, t, f):
    c.set_source_rgb(*rgb('#1a1a20')); c.rectangle(0, HEAD, W, H - HEAD); c.fill()
    # concrete shaft back wall with block lines
    c.set_source_rgb(*rgb('#24242c')); c.rectangle(XMIN - R, HEAD, XMAX - XMIN + 2 * R, GROUND - HEAD); c.fill()
    c.set_source_rgba(0, 0, 0, 0.22); c.set_line_width(3)
    for j, yy in enumerate(range(HEAD + 40, GROUND, 80)):
        c.move_to(XMIN - R, yy); c.line_to(XMAX + R, yy); c.stroke()
        for xx in range(XMIN - R + (j % 2) * 80, XMAX + R, 160): c.move_to(xx, yy); c.line_to(xx, yy + 80); c.stroke()
    # closed landing door outline higher up the shaft + floor number
    c.set_source_rgb(*rgb('#30303a')); c.rectangle(380, 620, 320, 420); c.fill()
    c.set_source_rgb(*rgb('#1c1c22')); c.set_line_width(5); c.move_to(540, 620); c.line_to(540, 1040); c.stroke()
    c.set_source_rgba(1, 1, 1, 0.08); c.rectangle(380, 1040, 320, 14); c.fill()
    font(c, 40); c.set_source_rgb(*rgb('#55555f')); c.move_to(520, 600); c.show_text('B1')
    # one dim caged work light
    c.set_source_rgb(*rgb('#3a3a44')); rrect(c, 760, 1180, 50, 70, 10); c.fill()
    c.set_source_rgb(*rgb('#d8b45e')); c.arc(785, 1215, 16, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#3a3a44')); c.set_line_width(3)
    for dx in (-10, 0, 10): c.move_to(785 + dx, 1195); c.line_to(785 + dx, 1235); c.stroke()
    # guide rails / shaft side walls (walls), with hazard stripes at the bottom
    for (x0, x1) in ((0, XMIN - R), (XMAX + R, W)):
        c.set_source_rgb(*rgb('#3a3d46')); c.rectangle(x0, HEAD, x1 - x0, GROUND - HEAD); c.fill()
        c.set_source_rgb(*rgb('#6a707c')); c.rectangle(x1 - 18 if x0 == 0 else x0, HEAD, 18, GROUND - HEAD); c.fill()   # steel guide rail
        c.set_source_rgb(*rgb('#2c2f38'))
        for yy in range(HEAD + 60, GROUND, 160): c.rectangle(x0 + 10, yy, x1 - x0 - 30, 10); c.fill()
        c.save(); c.rectangle(x0, GROUND - 90, x1 - x0, 90); c.clip()
        c.set_source_rgb(*rgb('#d9b02a')); c.paint(); c.set_source_rgb(*rgb('#1a1a1a'))
        for k in range(-3, 8):
            xx = x0 + k * 50; c.move_to(xx, GROUND); c.line_to(xx + 25, GROUND); c.line_to(xx + 115, GROUND - 90); c.line_to(xx + 90, GROUND - 90); c.close_path(); c.fill()
        c.restore()
    # pit floor: oily concrete
    c.set_source_rgb(*rgb('#36363e')); c.rectangle(0, GROUND, W, H - GROUND); c.fill()
    c.set_source_rgb(*rgb('#4a4a54')); c.rectangle(0, GROUND - 2, W, 6); c.fill()
    c.set_source_rgba(0, 0, 0, 0.25); c.save(); c.translate(600, GROUND + 120); c.scale(160, 20); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    # ruler on the left wall
    rx = XMIN - R - 66
    c.set_source_rgb(*rgb('#d9c9a0')); c.rectangle(rx, TIP0 - 40, 40, GROUND - 90 - TIP0 + 40); c.fill()
    c.set_source_rgb(0.15, 0.12, 0.1)
    for k in range(1, 9):
        y = GROUND - k * PPM
        if y < TIP0 - 40: break
        c.rectangle(rx, y - 2, 22, 4); c.fill()
        font(c, 22); c.move_to(rx + 24, y + 8); c.show_text(str(k))
        if y - PPM / 2 > TIP0 - 40: c.rectangle(rx, y - PPM / 2 - 1, 12, 2); c.fill()

def draw_ceiling(c, t, f):   # the elevator car (bottom = TIP) hanging on cables
    tip = TIP[f]; x0, x1 = XMIN - R - 4, XMAX + R + 4
    c.set_source_rgb(*rgb('#8a8f99')); c.set_line_width(5)
    for px in (440, 520, 560, 640): c.move_to(px, HEAD); c.line_to(px, tip - 330); c.stroke()
    c.set_source_rgb(*rgb('#4a4e58')); rrect(c, 400, tip - 345, 280, 30, 8); c.fill()   # crosshead
    c.set_source_rgb(*rgb('#6e5a48')); c.rectangle(x0 + 20, tip - 320, x1 - x0 - 40, 240); c.fill()   # car body (wood panels)
    c.set_source_rgb(*rgb('#5e4c3c'))
    for xx in range(int(x0 + 40), int(x1 - 40), 110): c.rectangle(xx, tip - 300, 90, 200); c.fill()
    c.set_source_rgb(*rgb('#8a8f99')); c.rectangle(x0 + 20, tip - 320, x1 - x0 - 40, 14); c.fill()
    c.set_source_rgb(*rgb('#3a3d46')); c.rectangle(x0, tip - 80, x1 - x0, 60); c.fill()   # steel underframe
    c.set_source_rgb(*rgb('#2c2f38'))
    for xx in range(int(x0 + 30), int(x1 - 20), 90): c.rectangle(xx, tip - 70, 50, 40); c.fill()
    c.save(); c.rectangle(x0, tip - 22, x1 - x0, 22); c.clip(); c.set_source_rgb(*rgb('#d9b02a')); c.paint(); c.set_source_rgb(*rgb('#1a1a1a'))
    for k in range(0, 30):
        xx = x0 + k * 44; c.move_to(xx, tip); c.line_to(xx + 22, tip); c.line_to(xx + 44, tip - 22); c.line_to(xx + 22, tip - 22); c.close_path(); c.fill()
    c.restore()
    # floor indicator on the car side
    c.set_source_rgb(*rgb('#1a1a1e')); rrect(c, W / 2 - 60, tip - 260, 120, 60, 10); c.fill()
    font(c, 40); c.set_source_rgb(*rgb('#ff5a4d')); s = 'B2'; e = c.text_extents(s); c.move_to(W / 2 - e.width / 2, tip - 214); c.show_text(s)
    rx = XMIN - R - 66
    c.set_source_rgb(*rgb('#ff5a4d')); c.rectangle(rx - 8, tip - 3, 56, 6); c.fill()

def draw_springs(c, t):
    for sp in SPRINGS:
        x = sp['x']; k = 0.0
        for (ts, xs) in SPR_T:
            if xs == x and 0 <= t - ts < 0.25: k = 1 - (t - ts) / 0.25
        top = GROUND - 52 + 20 * k
        c.set_source_rgb(*rgb('#4a4e58')); rrect(c, x - 50, GROUND - 14, 100, 16, 4); c.fill()
        c.set_source_rgb(*rgb('#a8aeb8')); c.set_line_width(8)
        for j in range(4):
            yy = GROUND - 12 - j * (GROUND - 12 - top) / 4
            c.move_to(x - 36, yy); c.line_to(x + 36, yy - (GROUND - 12 - top) / 8); c.stroke()
        c.set_source_rgb(*rgb('#b84a3a')); rrect(c, x - 56, top - 12, 112, 18, 8); c.fill()

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
