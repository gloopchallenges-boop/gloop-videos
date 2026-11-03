"""2026-11-03 v2 — STEALTH – DETECTED %: the UFO SCANNER. A flying saucer drifts over a desert canyon at
night, sweeping a scan beam across the floor. Two rock ledges jut out of the canyon walls and cast real
shadows (point light: Gloop is hidden when the line UFO->Gloop crosses a ledge). Gloop is a passive rigid
ball (Ball) bouncing across the canyon floor. Beam moves are seeded-random; sometimes it 'searches' toward
where Gloop is (with lag). In the beam & not shadowed: DETECTED +40%/s, else -12%/s. 100% = beamed into a
bubble (fail). Timer ends first = win."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the UFO scanner'
SEED = int(os.environ.get('SEED', 2))
rng = random.Random(SEED)

class S: pass
S.HOOK1 = 'WILL GLOOP STAY'; S.HOOK2 = 'UNSEEN BY THE UFO?'; S.HOOK2_SIZE = 84; S.FAIL_WORD = 'SPOTTED!'; S.FAIL_SIZE = 150
S.T_START = HOOK_T; S.TL = float(os.environ.get('TL', 13.0)); S.T_END = S.T_START + S.TL
GROUND = 1600; R = 58; XMIN, XMAX = 150, 930
UP, DOWN = 40.0, 12.0; HALF = math.radians(float(os.environ.get('HALF', 10.0)))
LEDGES = [(92, 990, 440, 1070), (650, 890, 988, 970)]   # x0, y0, x1, y1 rock ledges (hanging from walls)
UFO_Y = 520

# --- seeded UFO drift (x) and beam angle keyframes; 'search' segments aim at Gloop's current position
UX = [(0, rng.uniform(380, 700))]; tt = 0
while tt < 40:
    tt += rng.uniform(1.6, 3.2); UX.append((tt, rng.uniform(300, 780)))
def ufo_x(t):
    for (t0, a0), (t1, a1) in zip(UX, UX[1:]):
        if t0 <= t <= t1: return lerp(a0, a1, ease((t - t0) / (t1 - t0)))
    return UX[-1][1]
SEARCH = float(os.environ.get('SEARCH', 0.35))
SEGS = []; tt = 0.0
while tt < 40:
    d = rng.uniform(0.6, 1.5); mode = 'search' if (tt > 1.0 and rng.random() < SEARCH) else 'sweep'
    if mode == 'search': d = rng.uniform(1.2, 2.2)
    SEGS.append((tt, tt + d, mode, rng.uniform(-38, 38)))
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
ang = math.radians(rng.uniform(-30, 30)); d = 0.0; T_SPOT = None; si = 0
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
    ang = clamp(ang, math.radians(-50), math.radians(50))
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
HOVER_Y = 1180
if T_SPOT: S.GRAB = (clamp(FX, 260, 820), HOVER_Y)
else: S.GRAB = (540, GROUND - R)
END = S.END = Ending(S)
if not T_SPOT: gi = min(int(END.T_GRAB * FPS), N0 - 1); S.GRAB = (GX[gi], GYS[gi])
seen_starts = [i / FPS for i in range(1, N0) if SEEN[i] and not SEEN[i - 1] and i / FPS < S.T_RES]
S.events = [[s, 'blip'] for s in seen_starts]
for (tl, xl, imp) in ball.landings:
    if tl < S.T_RES: S.events.append([tl, 'hop'])
for tw in ball.walls:
    if tw < S.T_RES: S.events.append([tw, 'thump', 0.4])
if T_SPOT: S.events += [[T_SPOT, 'siren'], [T_SPOT + 0.15, 'pop'], [T_SPOT + 0.2, 'whoosh']]
S.AMB = {'drone': 46, 'wind': 0.02}

def bubble_xy(t):
    k = ease((t - T_SPOT) / 0.7); bx = lerp(FX, S.GRAB[0], k); by = lerp(FY, HOVER_Y, k)
    return bx, by + 10 * math.sin((t - T_SPOT) * 4)

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

stars = [(rng.uniform(0, W), rng.uniform(HEAD, 1100), rng.uniform(1.2, 2.6)) for _ in range(60)]
SKY, MESA, MESA2, SAND, ROCK, ROCK_D = '#15131f', '#221c2b', '#1c1824', '#5e4433', '#4a3a33', '#3a2d28'

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

def draw_bg(c, t, th):
    c.set_source_rgb(*rgb(SKY)); c.rectangle(0, HEAD, W, H - HEAD); c.fill()
    c.set_source_rgba(0.85, 0.82, 0.75, 0.5)
    for x, y, r in stars: c.arc(x, y, r, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb(MESA)); c.move_to(0, 1300); c.line_to(140, 1300); c.line_to(170, 1180); c.line_to(420, 1180); c.line_to(450, 1300)
    c.line_to(700, 1300); c.line_to(730, 1230); c.line_to(900, 1230); c.line_to(930, 1300); c.line_to(W, 1300); c.line_to(W, GROUND); c.line_to(0, GROUND); c.close_path(); c.fill()
    c.set_source_rgb(*rgb(MESA2)); c.rectangle(0, 1420, W, GROUND - 1420); c.fill()
    c.move_to(0, H)
    for x in range(0, W + 1, 6): c.line_to(x, th[x])
    c.line_to(W, H); c.close_path(); c.set_source_rgb(*rgb(SAND)); c.fill()
    c.set_source_rgba(0, 0, 0, 0.12); c.set_line_width(3)
    for yy in range(GROUND + 70, H, 70): c.move_to(0, yy); c.line_to(W, yy); c.stroke()

def draw_walls(c):
    for (x0, x1) in ((0, XMIN - R), (XMAX + R, W)):
        c.set_source_rgb(*rgb(ROCK)); c.rectangle(x0, 820, x1 - x0, GROUND + 40 - 820); c.fill()
        c.set_source_rgb(*rgb(ROCK_D))
        for yy in range(840, GROUND + 40, 70): c.rectangle(x0, yy, x1 - x0, 5); c.fill()
    for (x0, y0, x1, y1) in LEDGES:
        c.set_source_rgb(*rgb(ROCK)); rrect(c, x0 - 20, y0, x1 - x0 + 20, y1 - y0, 14); c.fill()
        c.set_source_rgb(*rgb(ROCK_D)); rrect(c, x0 - 20, y1 - 16, x1 - x0 + 20, 16, 8); c.fill()
        c.set_source_rgb(*rgb('#5a4840')); rrect(c, x0 - 20, y0, x1 - x0 + 20, 12, 6); c.fill()

def draw_beam(c, t, f, alarm):
    ux = UXS[f]; a = ANG[f]; L = (ux, UFO_Y + 40); Lg = 1500
    if alarm and not END.carried(t):
        bx, by = bubble_xy(min(t, END.T_GRAB)); a = math.atan2(bx - L[0], by - L[1])
    col = (0.45, 1, 0.55) if alarm else (0.75, 0.95, 1.0)
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

def draw_ufo(c, t, f, alarm):
    ux = UXS[f]; y = UFO_Y + 6 * math.sin(t * 2.3)
    c.set_source_rgb(*rgb('#8fd8e8')); c.save(); c.translate(ux, y - 30); c.scale(70, 52); c.arc(0, 0, 1, math.pi, 2 * math.pi); c.restore(); c.fill()
    c.set_source_rgb(*rgb('#6b7488')); c.save(); c.translate(ux, y); c.scale(160, 40); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    c.set_source_rgb(*rgb('#4f566a')); c.save(); c.translate(ux, y + 18); c.scale(110, 22); c.arc(0, 0, 1, 0, math.pi); c.restore(); c.fill()
    for i in range(5):
        on = (int(t * 4) + i) % 5 == 0
        c.set_source_rgb(*(rgb('#ff5050') if alarm else (rgb('#ffe37a') if on else rgb('#7a6f4a')))); c.arc(ux - 100 + i * 50, y + 4, 9, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#cfe9ff')); c.save(); c.translate(ux, UFO_Y + 40); c.scale(30, 9); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()

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
    draw_blob(c, t, gx, gy, mood, 0, R=R, dizzy=alarm and t > T_SPOT + 0.8)
    if bubble:
        c.set_source_rgba(0.55, 1, 0.6, 0.22); c.arc(gx, gy, R + 26, 0, 2 * math.pi); c.fill()
        c.set_source_rgba(0.75, 1, 0.8, 0.8); c.set_line_width(5); c.arc(gx, gy, R + 26, 0, 2 * math.pi); c.stroke()
        c.set_source_rgba(1, 1, 1, 0.7); c.arc(gx - 30, gy - 40, 10, 0, 2 * math.pi); c.fill()
    draw_walls(c)
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
