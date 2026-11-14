"""2026-11-14 v1 — STEALTH – DETECTED %: the PIRATE SHIP. A beach cove at night; a pirate ship drifts offshore
and its lookout sweeps a lantern beam from the crow's nest across the sand. An upturned rowboat on stumps and a
net crate hanging from a pole cast real shadows (point light: Gloop is hidden when the line
light->Gloop crosses one). Gloop is a passive rigid ball (Ball) bouncing across the floor. Beam moves are
seeded-random; sometimes it 'searches' toward where Gloop is (with lag). In the beam & not shadowed:
DETECTED +40%/s, else -12%/s. 100% = scooped up in a net (fail). Timer ends first = win."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the pirate ship'
SEED = int(os.environ.get('SEED', 5))
rng = random.Random(SEED)

class S: pass
S.HOOK1 = 'WILL GLOOP STAY'; S.HOOK2 = 'UNSEEN BY THE PIRATES?'; S.HOOK2_SIZE = 64; S.FAIL_WORD = 'SPOTTED!'; S.FAIL_SIZE = 150
S.T_START = HOOK_T; S.TL = float(os.environ.get('TL', 12.5)); S.T_END = S.T_START + S.TL
GROUND = 1600; R = 58; XMIN, XMAX = 150, 930
UP, DOWN = 40.0, 12.0; HALF = math.radians(float(os.environ.get('HALF', 10.0)))
LEDGES = [(190, 1120, 470, 1260), (600, 1040, 840, 1150)]   # x0, y0, x1, y1 upturned rowboat on stumps, hanging net crate
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
S.AMB = {'drone': 48, 'wind': 0.03, 'rumble': 0.01}

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

SKY, SEA, SAND = '#121726', '#1b2a3c', '#5e5340'
STARS = [((i * 197) % W, HEAD + 20 + (i * 71) % 420) for i in range(40)]
def draw_bg(c, t, th):
    c.set_source_rgb(*rgb(SKY)); c.rectangle(0, HEAD, W, H - HEAD); c.fill()
    c.set_source_rgba(1, 1, 1, 0.35)
    for (x, y) in STARS: c.arc(x, y, 2.5, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#d8d4c0')); c.arc(860, 470, 46, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb(SKY)); c.arc(880, 458, 40, 0, 2 * math.pi); c.fill()
    # sea with gentle swell lines
    c.set_source_rgb(*rgb(SEA)); c.rectangle(0, 930, W, GROUND - 930); c.fill()
    c.set_source_rgba(0.6, 0.7, 0.85, 0.12); c.set_line_width(4)
    for k in range(5):
        y = 960 + k * 48
        c.move_to(0, y)
        for x in range(0, W + 1, 30): c.line_to(x, y + 5 * math.sin(x / 70 + t * 1.6 + k))
        c.stroke()
    # far headland silhouette
    c.set_source_rgb(*rgb('#161e2c')); c.move_to(0, 930); c.curve_to(120, 840, 260, 860, 360, 930); c.close_path(); c.fill()
    # sand beach (terrain) with surf line
    c.set_source_rgba(0.85, 0.9, 1, 0.18); c.set_line_width(8); c.move_to(0, 1225)
    for x in range(0, W + 1, 30): c.line_to(x, 1225 + 8 * math.sin(x / 90 + t * 2))
    c.stroke()
    c.set_source_rgb(*rgb('#4a4436')); c.rectangle(0, 1235, W, GROUND - 1235); c.fill()
    c.move_to(0, H)
    for x in range(0, W + 1, 6): c.line_to(x, th[x])
    c.line_to(W, H); c.close_path(); c.set_source_rgb(*rgb(SAND)); c.fill()
    c.set_source_rgba(0, 0, 0, 0.13)
    for i in range(60):
        x = (i * 137) % W; y = GROUND + 100 + (i * 53) % (H - GROUND - 120)
        c.arc(x, y, 4, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#d8d0c0'))
    for (x, y) in ((180, GROUND + 160), (700, GROUND + 230), (420, GROUND + 300)):
        c.save(); c.translate(x, y); c.scale(14, 8); c.arc(0, 0, 1, math.pi, 2 * math.pi); c.restore(); c.fill()

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
    # left: dark sea rocks; right: palm trunk + rocks
    c.set_source_rgb(*rgb('#2e3238')); c.move_to(-10, GROUND + 40); c.line_to(-10, 1160); c.curve_to(60, 1140, XMIN - R + 20, 1300, XMIN - R, GROUND + 40); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#3a3f46')); c.move_to(-10, 1260); c.curve_to(40, 1250, 70, 1330, XMIN - R - 10, 1420); c.line_to(-10, 1420); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#5a4630')); c.move_to(XMAX + R, GROUND + 40); c.curve_to(XMAX + R + 10, 1300, XMAX + R + 60, 900, W + 10, 760); c.line_to(W + 10, GROUND + 40); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#46362a')); c.set_line_width(5)
    for k in range(12):
        y = 820 + k * 66; c.move_to(XMAX + R + 70 - k * 5, y); c.line_to(W, y - 14); c.stroke()
    c.set_source_rgb(*rgb('#24402c'))
    for a in (-2.6, -2.0, -1.2, -0.7):
        c.save(); c.translate(W - 10, 760); c.rotate(a); c.move_to(0, 0); c.curve_to(120, -40, 240, -10, 300, 60); c.curve_to(220, 10, 120, 10, 0, 18); c.close_path(); c.fill(); c.restore()
    # upturned rowboat on two driftwood stumps (shadow 1)
    x0, y0, x1, y1 = LEDGES[0]
    c.set_source_rgb(*rgb('#4a3a2a')); c.set_line_width(22)
    for xx in (x0 + 40, x1 - 40): c.move_to(xx, y1); c.line_to(xx, GROUND + 10); c.stroke()
    c.set_source_rgb(*rgb('#7a3a2c')); c.move_to(x0, y1); c.curve_to(x0 + 10, y0 - 10, x1 - 10, y0 - 10, x1, y1); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#5e2c22')); c.set_line_width(6)
    for k in (0.35, 0.65): c.move_to(x0 + 20, y1 - (y1 - y0) * k); c.line_to(x1 - 20, y1 - (y1 - y0) * k); c.stroke()
    c.set_source_rgb(*rgb('#c8b890')); c.rectangle(x0 - 6, y1 - 8, x1 - x0 + 12, 10); c.fill()
    # bundle of fishing nets + crate hanging from a rope on a pole (shadow 2)
    x0, y0, x1, y1 = LEDGES[1]; cx = (x0 + x1) / 2
    c.set_source_rgb(*rgb('#4a3a2a')); c.set_line_width(16); c.move_to(x1 + 60, GROUND + 20); c.line_to(x1 + 60, y0 - 120); c.line_to(cx, y0 - 120); c.stroke()
    c.set_source_rgb(*rgb('#c8b890')); c.set_line_width(5)
    for xx in (cx - 30, cx + 30): c.move_to(xx, y0); c.line_to(cx, y0 - 70); c.stroke()
    c.move_to(cx, y0 - 70); c.line_to(cx, y0 - 120); c.stroke()
    c.set_source_rgb(*rgb('#6e5232')); c.rectangle(x0, y0, x1 - x0, y1 - y0); c.fill()
    c.set_source_rgb(*rgb('#55402a')); c.set_line_width(6); c.rectangle(x0 + 8, y0 + 8, x1 - x0 - 16, y1 - y0 - 16); c.stroke()
    c.set_source_rgba(0.75, 0.7, 0.55, 0.6); c.set_line_width(3)
    for k in range(7): c.move_to(x0 + k * 40, y0); c.line_to(x0 + k * 40 + 30, y1); c.move_to(x0 + k * 40 + 30, y0); c.line_to(x0 + k * 40, y1)
    c.stroke()

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

def draw_ufo(c, t, f, alarm):   # pirate ship drifting on the sea, lantern on the crow's nest
    ux = UXS[f]; bob = 6 * math.sin(t * 1.7); a = ANG[f]
    c.save(); c.translate(ux, bob)
    c.set_source_rgb(*rgb('#2a1e18'))
    c.move_to(-230, 930); c.line_to(230, 930); c.line_to(270, 860); c.line_to(-280, 860); c.close_path(); c.fill()   # hull
    c.set_source_rgb(*rgb('#3a2a20')); c.rectangle(-280, 850, 550, 14); c.fill()
    c.set_source_rgb(*rgb('#c8a030'))
    for k in range(5): c.arc(-170 + k * 85, 895, 8, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#2a1e18')); c.set_line_width(12); c.move_to(0, 860); c.line_to(0, UFO_Y - 40); c.stroke()
    c.set_line_width(8); c.move_to(-170, 860); c.line_to(-170, 640); c.stroke()
    c.set_source_rgb(*rgb('#3c3a36'))   # dark tattered sails
    c.move_to(-120, 600); c.line_to(120, 600); c.curve_to(140, 700, 130, 760, 120, 800); c.line_to(-120, 800); c.curve_to(-100, 720, -110, 660, -120, 600); c.close_path(); c.fill()
    c.move_to(-250, 660); c.line_to(-90, 660); c.line_to(-100, 820); c.line_to(-250, 820); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#d8d4c0')); c.arc(0, 700, 26, 0, 2 * math.pi); c.fill()   # skull emblem
    c.set_source_rgb(*rgb('#3c3a36')); c.arc(-9, 696, 6, 0, 2 * math.pi); c.fill(); c.arc(9, 696, 6, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#1c1414')); c.move_to(0, UFO_Y - 40); c.line_to(0, UFO_Y - 120); c.stroke()
    c.move_to(0, UFO_Y - 120); c.line_to(60, UFO_Y - 106 + 6 * math.sin(t * 6)); c.line_to(0, UFO_Y - 92); c.close_path(); c.fill()   # flag
    c.set_source_rgb(*rgb('#3a2a20')); rrect(c, -46, UFO_Y - 30, 92, 50, 8); c.fill()   # crow's nest
    c.restore()
    c.save(); c.translate(ux, UFO_Y + 40); c.rotate(-a)
    c.set_source_rgb(*rgb('#5a4a30')); rrect(c, -18, -26, 36, 34, 8); c.fill()
    c.set_source_rgb(*rgb('#ffd890' if not alarm else '#ff8080')); c.save(); c.translate(0, 8); c.scale(20, 7); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
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
