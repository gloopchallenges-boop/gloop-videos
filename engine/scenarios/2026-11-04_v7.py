"""2026-11-04 v7 — STEALTH – DETECTED %: the PRISON SEARCHLIGHT. A guard tower on the right of a prison
yard at night sweeps a searchlight across the yard. Two bedsheets hanging on a clothesline cast real
shadows (point light: Gloop is hidden when the line light->Gloop crosses a sheet). Gloop is a passive
rigid ball (Ball) bouncing across the yard. Beam moves are seeded-random; sometimes it 'searches' toward
where Gloop is (with lag). In the beam & not shadowed: DETECTED +40%/s, else -12%/s. 100% = a cage
drops on him (fail). Timer ends first = win."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the prison searchlight'
SEED = int(os.environ.get('SEED', 14))
rng = random.Random(SEED)

class S: pass
S.HOOK1 = 'WILL GLOOP STAY'; S.HOOK2 = 'UNSEEN BY THE SEARCHLIGHT?'; S.HOOK2_SIZE = 70; S.FAIL_WORD = 'SPOTTED!'; S.FAIL_SIZE = 150
S.T_START = HOOK_T; S.TL = float(os.environ.get('TL', 13.0)); S.T_END = S.T_START + S.TL
GROUND = 1600; R = 58; XMIN, XMAX = 150, 850
UP, DOWN = 40.0, 12.0; HALF = math.radians(float(os.environ.get('HALF', 10.0)))
LEDGES = [(200, 1020, 400, 1215), (560, 1050, 730, 1225)]   # x0, y0, x1, y1 hanging bedsheets
UFO_Y = 600; LIGHT_X = 965

# --- seeded UFO drift (x) and beam angle keyframes; 'search' segments aim at Gloop's current position
def ufo_x(t): return LIGHT_X
SEARCH = float(os.environ.get('SEARCH', 0.35))
SEGS = []; tt = 0.0
while tt < 40:
    d = rng.uniform(0.6, 1.5); mode = 'search' if (tt > 1.0 and rng.random() < SEARCH) else 'sweep'
    if mode == 'search': d = rng.uniform(1.2, 2.2)
    SEGS.append((tt, tt + d, mode, rng.uniform(-52, -4)))
    if rng.random() < 0.25: tt += d; SEGS.append((tt, tt + rng.uniform(0.3, 0.8), 'hold', 0)); tt = SEGS[-1][1]
    else: tt += d

TER = Terrain(GROUND, seed=SEED, bumps=4, amp=10)
def cross(o, a, b): return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
def seg_hits_rect(p, q, r):
    x0, y0, x1, y1 = r
    # Liang-Barsky
    dx, dy = q[0] - p[0], q[1] - p[1]; t0, t1 = 0.0, 1.0
    for pp, qq in ((-dx, p[0] - x0), (dx, x1 - p[0]), (-dy, p[1] - y0), (dy, y1 - p[1])):
        if pp == 0:
            if qq < 0: return False
        else:
            u = qq / pp
            if pp < 0: t0 = max(t0, u)
            else: t1 = min(t1, u)
            if t0 > t1: return False
    return True

N0 = int(40 * FPS)
ball = Ball(rng.uniform(300, 780), TER, R=R, seed=SEED, xmin=XMIN, xmax=XMAX)
GX, GYS, ANG, UXS, DET, SEEN, SH = [], [], [], [], [], [], []
ang = math.radians(rng.uniform(-45, -15)); d = 0.0; T_SPOT = None; si = 0
for f in range(N0):
    t = f / FPS
    ball.step(t)
    ux = ufo_x(t); L = (ux, UFO_Y + 40)
    while si < len(SEGS) - 1 and t >= SEGS[si][1]: si += 1
    s0, s1, mode, tgt = SEGS[si]
    if mode == 'search': goal = math.atan2(ball.x - L[0], ball.y - L[1]); rate = 2.2
    elif mode == 'hold': goal = ang; rate = 0
    else: goal = math.radians(tgt); rate = 3.2
    ang += (goal - ang) * min(1, rate / FPS * 1.0) if mode == 'search' else (goal - ang) * min(1, rate / FPS)
    ang = clamp(ang, math.radians(-60), math.radians(8))
    # angle measured from straight down (positive = to the right)
    a_g = math.atan2(ball.x - L[0], ball.y - L[1]); dist = math.hypot(ball.x - L[0], ball.y - L[1])
    inc = abs(a_g - ang) < HALF + math.atan2(R * 0.5, dist)
    shadow = any(seg_hits_rect(L, (ball.x, ball.y), r) for r in LEDGES)
    s = inc and not shadow and T_SPOT is None
    if T_SPOT is None and S.T_START <= t < S.T_END:
        d = clamp(d + (UP if s else -DOWN) / FPS, 0, 100)
        if d >= 100: T_SPOT = t; FX, FY = ball.x, ball.y
    if T_SPOT is not None: ball.frozen = True
    GX.append(ball.x); GYS.append(ball.y); ANG.append(ang); UXS.append(ux); DET.append(d)
    SEEN.append(s and S.T_START <= t < S.T_END); SH.append(TER.snapshot() if f % 1 == 0 else None)
S.OUTCOME = 'fail' if T_SPOT else 'win'
S.T_RES = T_SPOT if T_SPOT else S.T_END
S.PEAK = max(DET[:int(S.T_RES * FPS)])
HOVER_Y = GROUND - R
if T_SPOT: S.GRAB = (FX, GROUND - R)
else: S.GRAB = (540, GROUND - R)
END = S.END = Ending(S)
if not T_SPOT: gi = min(int(END.T_GRAB * FPS), N0 - 1); S.GRAB = (GX[gi], GYS[gi])
seen_starts = [i / FPS for i in range(1, N0) if SEEN[i] and not SEEN[i - 1] and i / FPS < S.T_RES]
S.events = [[s, 'blip'] for s in seen_starts]
for (tl, xl, imp) in ball.landings:
    if tl < S.T_RES: S.events.append([tl, 'hop'])
for tw in ball.walls:
    if tw < S.T_RES: S.events.append([tw, 'thump', 0.4])
if T_SPOT: S.events += [[T_SPOT, 'siren'], [T_SPOT + 0.05, 'whoosh'], [T_SPOT + 0.4, 'clang']]
S.AMB = {'drone': 46, 'wind': 0.02}

def bubble_xy(t):
    k = clamp((t - T_SPOT) / 0.35, 0, 1); return FX, lerp(FY, GROUND - R, k * k)
def cage_y(t): k = clamp((t - T_SPOT) / 0.4, 0, 1); return lerp(-400, 0, k * k)   # offset of the cage drop
def draw_cage(c, x, y, dy):
    top = y - R - 40 + dy; bot = y + R + 4 + dy
    c.set_source_rgb(*rgb('#8a909c')); c.set_line_width(9)
    for k in range(7): xx = x - R - 22 + k * (2 * R + 44) / 6; c.move_to(xx, top); c.line_to(xx, bot); c.stroke()
    c.set_source_rgb(*rgb('#6b717d')); rrect(c, x - R - 34, top - 16, 2 * R + 68, 22, 8); c.fill(); rrect(c, x - R - 34, bot - 10, 2 * R + 68, 18, 6); c.fill()
    c.set_source_rgb(*rgb('#9aa0ac')); c.arc(x, top - 22, 12, 0, 2 * math.pi); c.fill()

def eye_icon(c, x, y, open_):
    c.save(); c.translate(x, y); col = rgb('#ff4d4d') if open_ else (0.55, 0.55, 0.6)
    c.set_line_width(6); c.set_source_rgb(*col)
    c.move_to(-34, 0); c.curve_to(-14, -26 if open_ else -4, 14, -26 if open_ else -4, 34, 0)
    if open_:
        c.curve_to(14, 26, -14, 26, -34, 0); c.close_path(); c.stroke(); c.arc(0, 0, 11, 0, 2 * math.pi); c.fill()
    else:
        c.stroke()
        for dx in (-18, 0, 18): c.move_to(dx, 2); c.line_to(dx * 1.2, 14); c.stroke()
    c.restore()
def draw_bar(c, t, f):
    dd = DET[f]; s = SEEN[f]
    bx = bar(c, dd / 100, f'DETECTED {int(dd)}%', bad_col(dd / 100), 0.15 if s else 0, bw=620, x_off=40)
    eye_icon(c, bx - 60, 231, s)
S.draw_bar = draw_bar

stars = [(rng.uniform(0, W), rng.uniform(HEAD, 900), rng.uniform(1.2, 2.4)) for _ in range(40)]
def draw_bg(c, t, th):
    c.set_source_rgb(*rgb('#14141e')); c.rectangle(0, HEAD, W, H - HEAD); c.fill()
    c.set_source_rgba(0.85, 0.85, 0.8, 0.45)
    for x, y, r in stars: c.arc(x, y, r, 0, 2 * math.pi); c.fill()
    # prison wall with barbed wire + cell block windows
    c.set_source_rgb(*rgb('#2a2a34')); c.rectangle(0, 900, W, GROUND - 900); c.fill()
    c.set_source_rgb(*rgb('#24242d'))
    for j2, yy in enumerate(range(900, GROUND, 60)):
        for xx in range(-60 * (j2 % 2), W, 120): c.rectangle(xx + 3, yy + 3, 114, 54); c.fill()
    c.set_source_rgb(*rgb('#3a3a46')); c.rectangle(0, 890, W, 20); c.fill()
    c.set_source_rgb(*rgb('#55555f')); c.set_line_width(3)
    for xx in range(0, W, 46):
        c.move_to(xx, 880); c.curve_to(xx + 12, 860, xx + 34, 860, xx + 46, 880); c.stroke()
        c.move_to(xx + 20, 868); c.line_to(xx + 28, 860); c.stroke()
    c.set_source_rgb(*rgb('#2e2e3a')); c.rectangle(80, 520, 520, 370); c.fill()   # cell block behind the wall
    for k2 in range(4):
        for r2 in range(2):
            on = (k2 + r2) % 3 == 1
            c.set_source_rgb(*(rgb('#c9a85a') if on else rgb('#1c1c26'))); c.rectangle(120 + k2 * 120, 570 + r2 * 150, 60, 80); c.fill()
            c.set_source_rgb(*rgb('#2e2e3a')); c.set_line_width(5)
            for b in range(1, 4): c.move_to(120 + k2 * 120 + b * 15, 570 + r2 * 150); c.line_to(120 + k2 * 120 + b * 15, 650 + r2 * 150); c.stroke()
    # yard ground
    c.move_to(0, H)
    for x in range(0, W + 1, 6): c.line_to(x, th[x])
    c.line_to(W, H); c.close_path(); c.set_source_rgb(*rgb('#4a4640')); c.fill()
    c.set_source_rgba(1, 1, 1, 0.12); c.set_line_width(6)
    c.move_to(80, GROUND + 140); c.line_to(860, GROUND + 140); c.stroke()
    c.set_source_rgba(0, 0, 0, 0.12); c.set_line_width(3)
    for yy in range(GROUND + 70, H, 70): c.move_to(0, yy); c.line_to(W, yy); c.stroke()

def draw_walls(c):
    # left: a stack of crates as the left wall
    c.set_source_rgb(*rgb('#5e4a36')); c.rectangle(0, 1180, XMIN - R, GROUND + 40 - 1180); c.fill()
    c.set_source_rgb(*rgb('#4a3a2a'))
    for yy in range(1180, GROUND, 105):
        c.rectangle(0, yy, XMIN - R, 8); c.fill()
        c.set_line_width(6); c.move_to(4, yy + 8); c.line_to(XMIN - R - 4, yy + 100); c.stroke()
    # clothesline posts + line + sheets
    c.set_source_rgb(*rgb('#55504a')); c.set_line_width(14)
    for x in (170, 760): c.move_to(x, 1000); c.line_to(x, GROUND + 10); c.stroke()
    c.set_source_rgb(*rgb('#9a958c')); c.set_line_width(3); c.move_to(170, 1010); c.curve_to(400, 1050, 560, 1050, 760, 1010); c.stroke()
    for n, (x0, y0, x1, y1) in enumerate(LEDGES):
        c.set_source_rgb(*rgb(('#c9c3b4', '#b4c0c9')[n])); c.move_to(x0, y0)
        for k in range(9): c.line_to(lerp(x0, x1, k / 8), y0 + (0 if k % 2 == 0 else 4))
        c.line_to(x1, y1)
        for k in range(8, -1, -1): c.line_to(lerp(x0, x1, k / 8), y1 + 8 * math.sin(k * 1.3))
        c.close_path(); c.fill()
        c.set_source_rgba(0, 0, 0, 0.08)
        for k in range(1, 4): c.rectangle(lerp(x0, x1, k / 4) - 3, y0, 6, y1 - y0); c.fill()
        c.set_source_rgb(*rgb('#d8d0a0'))
        for k in (0.15, 0.85): c.rectangle(lerp(x0, x1, k) - 5, y0 - 8, 10, 18); c.fill()
    # guard tower on the right = right wall
    tx0 = XMAX + R
    c.set_source_rgb(*rgb('#3a3a46')); c.rectangle(tx0, 700, W - tx0, GROUND + 40 - 700); c.fill()
    c.set_source_rgb(*rgb('#30303b'))
    for yy in range(720, GROUND, 80): c.rectangle(tx0, yy, W - tx0, 6); c.fill()
    c.set_source_rgb(*rgb('#2a2a34')); c.rectangle(tx0 - 40, 640, W - tx0 + 60, 60); c.fill()
    c.set_source_rgb(*rgb('#45454f')); c.move_to(tx0 - 60, 520); c.line_to(W + 20, 470); c.line_to(W + 20, 520); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#30303b')); c.rectangle(tx0 - 40, 520, 14, 120); c.fill()

def hull(pts):
    pts = sorted(set(pts))
    lo, up = [], []
    for p in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0: lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(up) >= 2 and cross(up[-2], up[-1], p) <= 0: up.pop()
        up.append(p)
    return lo[:-1] + up[:-1]

def draw_beam(c, t, f, alarm):
    ux = UXS[f]; a = ANG[f]; L = (ux, UFO_Y + 40); Lg = 1500
    if alarm and not END.carried(t):
        bx, by = bubble_xy(min(t, END.T_GRAB)); a = math.atan2(bx - L[0], by - L[1])
    col = (1, 0.5, 0.45) if alarm else (1.0, 0.96, 0.8)
    c.push_group()
    c.move_to(*L)
    c.line_to(L[0] + math.sin(a - HALF) * Lg, L[1] + math.cos(a - HALF) * Lg)
    c.line_to(L[0] + math.sin(a + HALF) * Lg, L[1] + math.cos(a + HALF) * Lg); c.close_path()
    c.set_source_rgba(*col, 0.26); c.fill()
    c.set_operator(cairo.OPERATOR_CLEAR)
    for (x0, y0, x1, y1) in LEDGES:
        pts = []
        for (px, py) in ((x0, y0), (x1, y0), (x0, y1), (x1, y1)):
            pts.append((px, py)); dx, dy = px - L[0], py - L[1]; pts.append((L[0] + dx * 8, L[1] + dy * 8))
        hp = hull(pts); c.move_to(*hp[0])
        for p in hp[1:]: c.line_to(*p)
        c.close_path(); c.fill()
    c.rectangle(0, GROUND + 30, W, H); c.fill()
    c.set_operator(cairo.OPERATOR_OVER)
    c.pop_group_to_source(); c.paint()

def draw_ufo(c, t, f, alarm):   # the searchlight lamp on the tower, pointing along the beam
    a = ANG[f]; L = (UXS[f], UFO_Y + 40)
    c.save(); c.translate(*L); c.rotate(-a)
    c.set_source_rgb(*rgb('#5a5f6b')); rrect(c, -34, -70, 68, 80, 12); c.fill()
    c.set_source_rgb(*rgb('#fff6d0' if not alarm else '#ff8080')); c.save(); c.translate(0, 8); c.scale(30, 9); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    c.restore()
    if alarm and (t * 4) % 1 < 0.5:
        c.set_source_rgb(*rgb('#ff4040')); c.arc(UXS[f] - 60, 500, 14, 0, 2 * math.pi); c.fill()

PS = Particles(9)
def render(f, c):
    t = f / FPS; fi = min(f, len(GX) - 1)
    alarm = T_SPOT is not None and t >= T_SPOT
    shake = (rng.uniform(-6, 6), rng.uniform(-6, 6)) if (alarm and t < T_SPOT + 0.3) else (0, 0)
    c.save(); c.translate(*shake)
    draw_bg(c, t, SH[fi])
    if t < END.T_OUTRO or not alarm: draw_beam(c, t, fi, alarm)
    bubble = False
    if END.carried(t) or t >= END.T_GRAB:
        gx, gy = (END.carry_xy(t) if END.carried(t) else S.GRAB); bubble = alarm
    elif alarm:
        gx, gy = bubble_xy(t); bubble = True
    else:
        gx, gy = GX[fi], GYS[fi]
        h = max(0, TER.y(gx) - R - gy); kk = 1 / (1 + h / 220)
        c.set_source_rgba(0, 0, 0, 0.25 * kk); c.save(); c.translate(gx, TER.y(gx) + 3); c.scale(R * (0.5 + 0.4 * kk), 9); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    s = SEEN[fi]
    mood = 'happy' if (t >= S.T_END and S.OUTCOME == 'win') else ('scared' if s or alarm or DET[fi] > 60 else 'worried')
    draw_walls(c)
    draw_blob(c, t, gx, gy, mood, 0, R=R, dizzy=alarm and t > T_SPOT + 0.8)
    if bubble: draw_cage(c, gx, gy, 0 if END.carried(t) else cage_y(t))
    draw_ufo(c, t, fi, alarm)
    for st in seen_starts:
        if st <= t < st + 0.6:
            k = (t - st) / 0.6
            text_at(c, '!', gx, gy - 120 - 30 * k, 100 * (1 + 0.4 * max(0, 1 - k * 4)), rgb('#ff4d4d'))
    PS.draw(c)
    END.draw_claw(c, t)
    c.restore()
    END.header(c, t, fi)

if __name__ == '__main__':
    if sys.argv[1] == 'sim':
        e = int(S.T_RES * FPS) - 1
        print(SEED, S.OUTCOME, round(S.T_RES - S.T_START, 2), 'peak', round(S.PEAK), 'final', round(DET[e]), 'dur', S.DUR); sys.exit()
    run(S, render)
