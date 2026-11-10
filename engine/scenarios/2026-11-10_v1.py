"""2026-11-10 v1 — STEALTH – DETECTED %: the SECURITY DRONE. A warehouse at night; a security drone hovers
under the roof trusses and sweeps its searchlight across the concrete floor. A crate stack on a rack and a
steel crate hanging from a chain hoist cast real shadows (point light: Gloop is hidden when the line
light->Gloop crosses one). Gloop is a passive rigid ball (Ball) bouncing across the floor. Beam moves are
seeded-random; sometimes it 'searches' toward where Gloop is (with lag). In the beam & not shadowed:
DETECTED +40%/s, else -12%/s. 100% = scooped up in a net (fail). Timer ends first = win."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the security drone'
SEED = int(os.environ.get('SEED', 5))
rng = random.Random(SEED)

class S: pass
S.HOOK1 = 'WILL GLOOP STAY'; S.HOOK2 = 'UNSEEN BY THE DRONE?'; S.HOOK2_SIZE = 64; S.FAIL_WORD = 'SPOTTED!'; S.FAIL_SIZE = 150
S.T_START = HOOK_T; S.TL = float(os.environ.get('TL', 12.5)); S.T_END = S.T_START + S.TL
GROUND = 1600; R = 58; XMIN, XMAX = 150, 930
UP, DOWN = 40.0, 12.0; HALF = math.radians(float(os.environ.get('HALF', 10.0)))
LEDGES = [(200, 1060, 440, 1250), (620, 1000, 880, 1140)]   # x0, y0, x1, y1 crate stack on a rack, hanging steel crate
UFO_Y = 500

# --- seeded UFO drift (x) and beam angle keyframes; 'search' segments aim at Gloop's current position
UX = [(0, rng.uniform(380, 700))]; tt = 0
while tt < 40:
    tt += rng.uniform(1.6, 3.2); UX.append((tt, rng.uniform(300, 780)))
def ufo_x(t):
    for (t0, a0), (t1, a1) in zip(UX, UX[1:]):
        if t0 <= t <= t1: return lerp(a0, a1, ease((t - t0) / (t1 - t0)))
    return UX[-1][1]
SEARCH = float(os.environ.get('SEARCH', 0.45))
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
if T_SPOT: S.events += [[T_SPOT, 'siren'], [T_SPOT + 0.1, 'whoosh'], [T_SPOT + 0.35, 'clink']]
S.AMB = {'drone': 50, 'wind': 0.01, 'rumble': 0.02}

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

SKY, WALL, WALL2, FLOOR = '#15161e', '#23242e', '#1c1d26', '#4a4740'
RACKS = [(40 + i * 260, 160) for i in range(4)]
def draw_bg(c, t, th):
    c.set_source_rgb(*rgb(SKY)); c.rectangle(0, HEAD, W, H - HEAD); c.fill()
    # warehouse back wall with high windows (moonlight) and roof trusses
    c.set_source_rgb(*rgb(WALL)); c.rectangle(0, 760, W, GROUND - 760); c.fill()
    c.set_source_rgb(*rgb('#2a2c38')); c.set_line_width(10)
    c.move_to(0, 760); c.line_to(W, 760); c.stroke()
    for x in range(0, W + 1, 180): c.move_to(x, 360); c.line_to(x + 90, 760); c.move_to(x + 180, 360); c.line_to(x + 90, 760); c.stroke()
    c.move_to(0, 360); c.line_to(W, 360); c.stroke()
    for x in (110, 470, 830):
        c.set_source_rgb(*rgb('#2e3a52')); c.rectangle(x, 800, 140, 70); c.fill()
        c.set_source_rgb(*rgb('#1c1d26')); c.rectangle(x + 68, 800, 4, 70); c.fill()
    # shelving racks with boxes (silhouettes)
    for (x0, w_) in RACKS:
        c.set_source_rgb(*rgb(WALL2)); c.rectangle(x0, 930, 10, GROUND - 930); c.fill(); c.rectangle(x0 + w_ + 40, 930, 10, GROUND - 930); c.fill()
        for k, yy in enumerate(range(980, GROUND - 60, 150)):
            c.set_source_rgb(*rgb(WALL2)); c.rectangle(x0, yy, w_ + 50, 10); c.fill()
            c.set_source_rgb(*rgb('#2c2a2a'))
            for j in range(3):
                if (k + j + x0 // 100) % 3: c.rectangle(x0 + 16 + j * 58, yy - 60 + (j % 2) * 14, 50, 60 - (j % 2) * 14); c.fill()
    # concrete floor
    c.move_to(0, H)
    for x in range(0, W + 1, 6): c.line_to(x, th[x])
    c.line_to(W, H); c.close_path(); c.set_source_rgb(*rgb(FLOOR)); c.fill()
    c.set_source_rgb(*rgb('#8a7a2a')); c.rectangle(0, GROUND + 70, W, 10); c.fill()   # yellow floor line
    c.set_source_rgba(0, 0, 0, 0.15)
    for i in range(60):
        x = (i * 137) % W; y = GROUND + 100 + (i * 53) % (H - GROUND - 120)
        c.arc(x, y, 4, 0, 2 * math.pi); c.fill()

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

def draw_walls(c):
    # left: stacked pallets of boxes, right: steel roller door frame
    c.set_source_rgb(*rgb('#5a4630')); c.rectangle(-10, 1180, XMIN - R + 10, GROUND + 40 - 1180); c.fill()
    c.set_source_rgb(*rgb('#46362a'))
    for yy in range(1180, GROUND + 40, 80): c.rectangle(-10, yy, XMIN - R + 10, 6); c.fill()
    c.set_source_rgb(*rgb('#3a3e48')); c.rectangle(XMAX + R, 1040, W - XMAX - R + 10, GROUND + 40 - 1040); c.fill()
    c.set_source_rgb(*rgb('#2c2f38'))
    for yy in range(1060, GROUND + 40, 34): c.rectangle(XMAX + R, yy, W, 5); c.fill()
    c.set_source_rgb(*rgb('#c8a030')); c.rectangle(XMAX + R, 1020, W, 20); c.fill()
    c.set_source_rgb(*rgb('#1a1a1a'))
    for xx in range(int(XMAX + R), W, 40): c.move_to(xx, 1020); c.line_to(xx + 20, 1020); c.line_to(xx, 1040); c.line_to(xx - 20, 1040); c.close_path(); c.fill()
    # big cardboard crate stack on a pallet rack (shadow 1)
    x0, y0, x1, y1 = LEDGES[0]
    c.set_source_rgb(*rgb('#2e3038')); c.set_line_width(12)
    for xx in (x0 + 20, x1 - 20): c.move_to(xx, y1); c.line_to(xx, GROUND + 10); c.stroke()
    c.set_source_rgb(*rgb('#3a3c46')); c.rectangle(x0 - 10, y1 - 12, x1 - x0 + 20, 16); c.fill()
    for (bx, by, bw, bh) in ((x0, y0 + 70, 120, y1 - y0 - 82), (x0 + 124, y0, x1 - x0 - 124, y1 - y0 - 12)):
        c.set_source_rgb(*rgb('#8a6a42')); c.rectangle(bx, by, bw, bh); c.fill()
        c.set_source_rgb(*rgb('#6e5232')); c.rectangle(bx + bw / 2 - 10, by, 20, bh); c.fill()
        c.set_source_rgb(*rgb('#2a2420')); c.rectangle(bx + 14, by + 16, 40, 8); c.fill()
    # hanging steel crate on a chain hoist (shadow 2)
    x0, y0, x1, y1 = LEDGES[1]
    c.set_source_rgb(*rgb('#55585f')); c.set_line_width(5)
    for xx in ((x0 + x1) / 2 - 30, (x0 + x1) / 2 + 30): c.move_to(xx, y0); c.line_to((x0 + x1) / 2, y0 - 70); c.stroke()
    c.move_to((x0 + x1) / 2, y0 - 70); c.line_to((x0 + x1) / 2, 360); c.stroke()
    c.set_source_rgb(*rgb('#4a5a6a')); c.rectangle(x0, y0, x1 - x0, y1 - y0); c.fill()
    c.set_source_rgb(*rgb('#3a4856')); c.set_line_width(6)
    c.rectangle(x0 + 8, y0 + 8, x1 - x0 - 16, y1 - y0 - 16); c.stroke(); c.move_to(x0 + 8, y0 + 8); c.line_to(x1 - 8, y1 - 8); c.move_to(x1 - 8, y0 + 8); c.line_to(x0 + 8, y1 - 8); c.stroke()

def draw_beam(c, t, f, alarm):
    ux = UXS[f]; a = ANG[f]; L = (ux, UFO_Y + 40); Lg = 1500
    if alarm and not END.carried(t):
        bx, by = bubble_xy(min(t, END.T_GRAB)); a = math.atan2(bx - L[0], by - L[1])
    col = (1, 0.5, 0.45) if alarm else (0.95, 0.97, 1.0)
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

def draw_ufo(c, t, f, alarm):   # security drone, searchlight under its belly
    ux = UXS[f]; y = UFO_Y + 8 * math.sin(t * 2.7); a = ANG[f]
    c.save(); c.translate(ux, y)
    c.set_source_rgb(*rgb('#2a2e38')); c.set_line_width(12)
    for sx in (-1, 1): c.move_to(0, -10); c.line_to(sx * 120, -40); c.stroke()
    for sx in (-1, 1):
        c.set_source_rgb(*rgb('#1c1f28')); rrect(c, sx * 120 - 14, -60, 28, 30, 6); c.fill()
        w = 70 * abs(math.cos(t * 30 + sx)); c.set_source_rgba(0.6, 0.65, 0.75, 0.6); c.set_line_width(6)
        c.move_to(sx * 120 - w, -64); c.line_to(sx * 120 + w, -64); c.stroke()
    c.set_source_rgb(*rgb('#3a4050')); rrect(c, -70, -40, 140, 60, 22); c.fill()
    c.set_source_rgb(*rgb('#c8a030')); c.rectangle(-70, -6, 140, 8); c.fill()
    c.set_source_rgb(*rgb('#1a1d26')); c.arc(0, -12, 20, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*(rgb('#ff4040') if (alarm or (t * 2) % 1 < 0.5) else rgb('#602020'))); c.arc(0, -12, 9, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#1a1d26')); c.set_line_width(5)
    for sx in (-1, 1): c.move_to(sx * 40, 20); c.line_to(sx * 55, 44); c.stroke()
    c.restore()
    c.save(); c.translate(ux, UFO_Y + 40); c.rotate(-a)
    c.set_source_rgb(*rgb('#4a4f5b')); rrect(c, -18, -26, 36, 34, 8); c.fill()
    c.set_source_rgb(*rgb('#fff6d0' if not alarm else '#ff8080')); c.save(); c.translate(0, 8); c.scale(20, 7); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    c.restore()

def draw_net(c, x, y):   # a rope net on a cable from the drone
    c.set_source_rgb(*rgb('#c8b890')); c.set_line_width(4); c.move_to(x, y - R - 30); c.line_to(x, HOVER_Y - 640); c.stroke()
    c.set_source_rgba(0.85, 0.78, 0.6, 0.85); c.set_line_width(4)
    for k in range(-3, 4):
        c.move_to(x, y - R - 30); c.curve_to(x + k * 30, y - R, x + k * 34, y + R * 0.7, x + k * 16, y + R + 14); c.stroke()
    for j in range(4):
        yy = y - R * 0.6 + j * 0.45 * R; ww = R + 10 - (j == 3) * 20
        c.save(); c.translate(x, yy); c.scale(ww, 12); c.arc(0, 0, 1, 0, math.pi); c.restore(); c.stroke()

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
    if bubble: draw_net(c, gx, gy)
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
