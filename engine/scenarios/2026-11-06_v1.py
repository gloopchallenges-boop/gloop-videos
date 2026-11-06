"""2026-11-06 v1 — STEALTH – DETECTED %: the MUSEUM GUARD. A night guard on a balcony on the right of a museum
hall sweeps a flashlight across the floor. Two hanging exhibit banners cast real
shadows (point light: Gloop is hidden when the line light->Gloop crosses a sheet). Gloop is a passive
rigid ball (Ball) bouncing across the yard. Beam moves are seeded-random; sometimes it 'searches' toward
where Gloop is (with lag). In the beam & not shadowed: DETECTED +40%/s, else -12%/s. 100% = a cage
drops on him (fail). Timer ends first = win."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the museum guard'
SEED = int(os.environ.get('SEED', 10))
rng = random.Random(SEED)

class S: pass
S.HOOK1 = 'WILL GLOOP STAY'; S.HOOK2 = 'UNSEEN BY THE GUARD?'; S.HOOK2_SIZE = 70; S.FAIL_WORD = 'SPOTTED!'; S.FAIL_SIZE = 150
S.T_START = HOOK_T; S.TL = float(os.environ.get('TL', 13.0)); S.T_END = S.T_START + S.TL
GROUND = 1600; R = 58; XMIN, XMAX = 150, 850
UP, DOWN = 40.0, 12.0; HALF = math.radians(float(os.environ.get('HALF', 10.0)))
LEDGES = [(210, 1000, 400, 1230), (570, 1040, 740, 1250)]   # x0, y0, x1, y1 hanging banners
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

stars = [(rng.uniform(80, 1000), rng.uniform(HEAD + 40, 560), rng.uniform(1.2, 2.2)) for _ in range(26)]
def draw_bg(c, t, th):
    c.set_source_rgb(*rgb('#1a1822')); c.rectangle(0, HEAD, W, H - HEAD); c.fill()
    # skylight with night sky
    c.set_source_rgb(*rgb('#101826')); c.rectangle(140, HEAD + 30, 800, 230); c.fill()
    c.set_source_rgba(0.85, 0.85, 0.8, 0.4)
    for x, y, r in stars:
        if 150 < x < 930 and y < HEAD + 250: c.arc(x, y, r, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#2a2733')); c.set_line_width(10)
    for xx in range(140, 941, 160): c.move_to(xx, HEAD + 30); c.line_to(xx, HEAD + 260); c.stroke()
    c.rectangle(140, HEAD + 30, 800, 230); c.stroke()
    # back wall panels with framed paintings
    c.set_source_rgb(*rgb('#24212c')); c.rectangle(0, 620, W, GROUND - 620); c.fill()
    c.set_source_rgb(*rgb('#2c2935'))
    for xx in range(0, W, 180): c.rectangle(xx + 8, 640, 164, GROUND - 660); c.fill()
    for (px, py, pw, ph, col) in ((90, 700, 200, 150, '#4a5a48'), (420, 680, 150, 200, '#5a4a3c'), (650, 720, 160, 120, '#3c4a5a')):
        c.set_source_rgb(*rgb('#8a7448')); c.rectangle(px - 12, py - 12, pw + 24, ph + 24); c.fill()
        c.set_source_rgb(*rgb(col)); c.rectangle(px, py, pw, ph); c.fill()
        c.set_source_rgba(1, 1, 1, 0.08); c.arc(px + pw * 0.4, py + ph * 0.45, min(pw, ph) * 0.25, 0, 2 * math.pi); c.fill()
    # velvet rope posts along the back
    c.set_source_rgb(*rgb('#8a7448'))
    for xx in (230, 540): c.rectangle(xx - 6, 1380, 12, 150); c.fill(); c.arc(xx, 1376, 12, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#6a2430')); c.set_line_width(8); c.move_to(230, 1395); c.curve_to(330, 1450, 440, 1450, 540, 1395); c.stroke()
    # marble floor
    c.move_to(0, H)
    for x in range(0, W + 1, 6): c.line_to(x, th[x])
    c.line_to(W, H); c.close_path(); c.set_source_rgb(*rgb('#4c4a52')); c.fill()
    c.set_source_rgba(0, 0, 0, 0.14); c.set_line_width(3)
    for yy in range(GROUND + 70, H, 90): c.move_to(0, yy); c.line_to(W, yy); c.stroke()
    for xx in range(-200, W + 200, 150): c.move_to(xx, GROUND + 20); c.line_to(xx + (xx - 540) * 0.6, H); c.stroke()

def draw_walls(c):
    # left: a stone column as the left wall
    c.set_source_rgb(*rgb('#6a6672')); c.rectangle(0, 620, XMIN - R, GROUND + 40 - 620); c.fill()
    c.set_source_rgb(*rgb('#5a5662'))
    for xx in range(14, XMIN - R - 6, 22): c.rectangle(xx, 660, 8, GROUND - 680); c.fill()
    c.set_source_rgb(*rgb('#77737f')); c.rectangle(0, 600, XMIN - R + 20, 40); c.fill(); c.rectangle(0, GROUND - 30, XMIN - R + 20, 40); c.fill()
    # hanging exhibit banners on cables
    for n, (x0, y0, x1, y1) in enumerate(LEDGES):
        c.set_source_rgb(*rgb('#77737f')); c.set_line_width(3)
        for xx in (x0 + 20, x1 - 20): c.move_to(xx, HEAD + 260); c.line_to(xx, y0); c.stroke()
        c.set_source_rgb(*rgb(('#7a2a34', '#2a4a6a')[n])); c.move_to(x0, y0); c.line_to(x1, y0); c.line_to(x1, y1)
        c.line_to((x0 + x1) / 2, y1 - 40); c.line_to(x0, y1); c.close_path(); c.fill()
        c.set_source_rgb(*rgb('#c9a85a')); c.rectangle(x0 - 6, y0 - 8, x1 - x0 + 12, 14); c.fill()
        c.set_source_rgba(0.9, 0.8, 0.5, 0.75); c.set_line_width(5)
        cx, cy = (x0 + x1) / 2, y0 + 70
        if n == 0:   # tiny dinosaur skull icon
            c.arc(cx, cy, 30, math.pi, 2 * math.pi); c.line_to(cx + 30, cy + 18); c.line_to(cx - 30, cy + 18); c.close_path(); c.stroke()
        else:        # vase icon
            c.move_to(cx - 16, cy - 30); c.curve_to(cx - 40, cy, cx - 30, cy + 30, cx, cy + 30); c.curve_to(cx + 30, cy + 30, cx + 40, cy, cx + 16, cy - 30); c.stroke()
    # mezzanine balcony on the right = right wall
    tx0 = XMAX + R
    c.set_source_rgb(*rgb('#3a3644')); c.rectangle(tx0, 700, W - tx0, GROUND + 40 - 700); c.fill()
    c.set_source_rgb(*rgb('#322e3c'))
    for yy in range(720, GROUND, 80): c.rectangle(tx0, yy, W - tx0, 6); c.fill()
    c.set_source_rgb(*rgb('#4a4654')); c.rectangle(tx0 - 50, 680, W - tx0 + 60, 30); c.fill()
    c.set_source_rgb(*rgb('#8a7448')); c.set_line_width(5)
    for xx in range(int(tx0 - 40), W, 22): c.move_to(xx, 680); c.line_to(xx, 610); c.stroke()
    c.rectangle(tx0 - 46, 600, W - tx0 + 60, 12); c.fill()

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

def draw_ufo(c, t, f, alarm):   # the night guard on the balcony holding the flashlight along the beam
    a = ANG[f]; L = (UXS[f], UFO_Y + 40)
    gx0 = L[0] + 48; gy0 = 690
    # body
    c.set_source_rgb(*rgb('#2c3550')); rrect(c, gx0 - 38, gy0 - 170, 76, 120, 18); c.fill()
    c.set_source_rgb(*rgb('#d9a77a')); c.arc(gx0, gy0 - 200, 30, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#1e2640')); rrect(c, gx0 - 36, gy0 - 242, 72, 22, 6); c.fill(); c.rectangle(gx0 - 44, gy0 - 224, 60, 8); c.fill()
    c.set_source_rgb(*rgb('#c9a85a')); c.arc(gx0 - 14, gy0 - 140, 6, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#1a1a22'))
    ex = -1 if not alarm else 0
    c.arc(gx0 - 12 + ex * 3, gy0 - 202, 4, 0, 2 * math.pi); c.fill()
    if alarm: c.set_line_width(4); c.arc(gx0 - 8, gy0 - 182, 9, 0, 2 * math.pi); c.stroke()
    # arm to the flashlight
    c.set_source_rgb(*rgb('#2c3550')); c.set_line_width(18); c.set_line_cap(cairo.LINE_CAP_ROUND)
    c.move_to(gx0 - 20, gy0 - 140); c.line_to(*L); c.stroke()
    c.save(); c.translate(*L); c.rotate(-a)
    c.set_source_rgb(*rgb('#4a4f5b')); rrect(c, -13, -46, 26, 54, 8); c.fill()
    c.set_source_rgb(*rgb('#fff6d0' if not alarm else '#ff8080')); c.save(); c.translate(0, 8); c.scale(17, 6); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    c.restore()
    if alarm and (t * 4) % 1 < 0.5:
        c.set_source_rgb(*rgb('#ff4040')); c.arc(W - 60, HEAD + 60, 16, 0, 2 * math.pi); c.fill()

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
