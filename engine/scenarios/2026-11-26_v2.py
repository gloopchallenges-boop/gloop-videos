"""2026-11-26 v2 — STEALTH – DETECTED %: the ZOOKEEPER (based on 2026-11-21 v3). A monkey enclosure at the zoo at night;
the zookeeper paces the high visitor walkway and sweeps a flashlight across the enclosure. A monkey hut on stilts and a crate of
bananas hanging from a rope cast real shadows (point light: Gloop is hidden when the line light->Gloop crosses one). Gloop is a
passive rigid ball (Ball) bouncing across the floor. Beam moves are seeded-random; sometimes it 'searches' toward where Gloop is
(with lag). In the beam & not shadowed: DETECTED +40%/s, else -12%/s. 100% = scooped up in a net (fail). Timer ends first = win."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the zookeeper'
SEED = int(os.environ.get('SEED', 8))
rng = random.Random(SEED)

class S: pass
S.HOOK1 = 'WILL GLOOP STAY'; S.HOOK2 = 'UNSEEN BY THE ZOOKEEPER?'; S.HOOK2_SIZE = 64; S.FAIL_WORD = 'SPOTTED!'; S.FAIL_SIZE = 150
S.T_START = HOOK_T; S.TL = float(os.environ.get('TL', 12.5)); S.T_END = S.T_START + S.TL
GROUND = 1600; R = 58; XMIN, XMAX = 150, 930
UP, DOWN = 40.0, 12.0; HALF = math.radians(float(os.environ.get('HALF', 12.0)))
LEDGES = [(190, 1150, 450, 1310), (620, 1020, 800, 1140)]   # x0, y0, x1, y1 monkey hut (on stilts), banana crate on a rope
UFO_Y = 500

# --- seeded UFO drift (x) and beam angle keyframes; 'search' segments aim at Gloop's current position
UX = [(0, rng.uniform(380, 700))]; tt = 0
while tt < 40:
    tt += rng.uniform(1.6, 3.2); UX.append((tt, rng.uniform(260, 820)))
def ufo_x(t):
    for (t0, a0), (t1, a1) in zip(UX, UX[1:]):
        if t0 <= t <= t1: return lerp(a0, a1, ease((t - t0) / (t1 - t0)))
    return UX[-1][1]
SEARCH = float(os.environ.get('SEARCH', 0.55))
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
S.AMB = {'drone': 46, 'wind': 0.035}

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

SKY = '#101a24'
STARS = [((i * 197) % W, HEAD + 20 + (i * 71) % 180) for i in range(30)]
WALL_TOP = 600
def draw_bg(c, t, th):
    c.set_source_rgb(*rgb(SKY)); c.rectangle(0, HEAD, W, H - HEAD); c.fill()
    c.set_source_rgba(1, 1, 1, 0.35)
    for (x, y) in STARS: c.arc(x, y, 2.5, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#d8d4c0')); c.arc(860, 420, 30, 0, 2 * math.pi); c.fill()
    # palm silhouettes behind the walkway
    c.set_source_rgb(*rgb('#16222a'))
    for (px, ph) in ((120, 260), (980, 300)):
        c.rectangle(px - 8, WALL_TOP - ph, 16, ph); c.fill()
        for k in range(5):
            a = -math.pi / 2 + (k - 2) * 0.55
            c.save(); c.translate(px, WALL_TOP - ph); c.rotate(a); c.scale(90, 16); c.arc(1, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    # concrete enclosure wall with a painted jungle mural (flat, muted)
    c.set_source_rgb(*rgb('#3a4038')); c.rectangle(0, WALL_TOP, W, GROUND + 40 - WALL_TOP); c.fill()
    c.set_source_rgb(*rgb('#33402e'))
    for i in range(9):
        x = 60 + i * 120; c.save(); c.translate(x, 900 + (i % 3) * 60); c.scale(110, 70); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    c.set_source_rgb(*rgb('#2c3828'))
    for i in range(8):
        x = 120 + i * 120; c.save(); c.translate(x, 1120 + (i % 2) * 70); c.scale(120, 80); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    c.set_source_rgba(0, 0, 0, 0.16); c.set_line_width(3)
    for yy in range(WALL_TOP + 120, GROUND, 140): c.move_to(0, yy); c.line_to(W, yy); c.stroke()
    # visitor walkway (where the keeper walks) + railing
    c.set_source_rgb(*rgb('#2a2a30')); c.rectangle(0, WALL_TOP, W, 22); c.fill()
    c.set_source_rgb(*rgb('#8a8a90')); c.set_line_width(5)
    for x in range(0, W, 46): c.move_to(x, WALL_TOP); c.line_to(x, WALL_TOP - 60); c.stroke()
    c.set_line_width(7); c.move_to(0, WALL_TOP - 60); c.line_to(W, WALL_TOP - 60); c.stroke()
    # little enclosure sign (no text) with a monkey-face icon
    c.set_source_rgb(*rgb('#5a4a32')); rrect(c, 420, 680, 240, 110, 14); c.fill()
    c.set_source_rgb(*rgb('#c8b890')); c.arc(540, 735, 34, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#5a4a32')); c.arc(510, 712, 13, 0, 2 * math.pi); c.fill(); c.arc(570, 712, 13, 0, 2 * math.pi); c.fill()
    c.arc(528, 730, 5, 0, 2 * math.pi); c.fill(); c.arc(552, 730, 5, 0, 2 * math.pi); c.fill()
    # rope from the walkway beam for the banana crate
    c.set_source_rgb(*rgb('#3a2a1e')); c.rectangle(560, WALL_TOP - 230, 320, 22); c.fill()
    c.set_source_rgb(*rgb('#6a6a70')); c.arc(710, WALL_TOP - 200, 16, 0, 2 * math.pi); c.fill()
    # enclosure floor: dirt + scattered leaves
    TER.fill(c, th, '#4a4030', '#2a241a', '#5a4e38')
    for i in range(50):
        x = (i * 137) % W; y = GROUND + 60 + (i * 53) % (H - GROUND - 80)
        c.set_source_rgba(0.35, 0.5, 0.28, 0.45); c.save(); c.translate(x, y); c.rotate(i); c.scale(14, 6); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()

def draw_walls(c):
    # left: stacked boulders; right: iron bars of the enclosure gate
    for k, (yy, rr) in enumerate(((GROUND - 40, 70), (GROUND - 160, 62), (GROUND - 270, 56), (GROUND - 370, 50))):
        c.set_source_rgb(*rgb('#5a5a60' if k % 2 else '#4e4e56')); c.save(); c.translate(XMIN - R - 40, yy); c.scale(rr + 40, rr); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    c.set_source_rgb(*rgb('#2e3036')); c.rectangle(XMAX + R, 1080, W - XMAX - R + 10, 24); c.fill()
    c.set_line_width(12)
    for xx in range(int(XMAX + R) + 8, W + 10, 34): c.move_to(xx, 1080); c.line_to(xx, GROUND + 30); c.stroke()
    c.rectangle(XMAX + R, 1340, W - XMAX - R + 10, 18); c.fill()
    # monkey hut on stilts (shadow 1)
    x0, y0, x1, y1 = LEDGES[0]
    c.set_source_rgb(*rgb('#4a3622')); c.set_line_width(14)
    for xx in (x0 + 24, x1 - 24): c.move_to(xx, y1); c.line_to(xx, GROUND + 10); c.stroke()
    c.set_source_rgb(*rgb('#6a5032')); c.rectangle(x0, y0 + 40, x1 - x0, y1 - y0 - 40); c.fill()
    c.set_source_rgba(0, 0, 0, 0.2); c.set_line_width(3)
    for yy in range(y0 + 60, y1, 22): c.move_to(x0, yy); c.line_to(x1, yy); c.stroke()
    c.set_source_rgb(*rgb('#5a6a38')); c.move_to(x0 - 24, y0 + 44); c.line_to((x0 + x1) / 2, y0 - 26); c.line_to(x1 + 24, y0 + 44); c.close_path(); c.fill()   # leaf roof
    c.set_source_rgb(*rgb('#1e1410')); rrect(c, (x0 + x1) / 2 - 32, y0 + 64, 64, 76, 28); c.fill()
    mx, my = (x0 + x1) / 2, y0 + 104   # sleepy monkey peeking out
    c.set_source_rgb(*rgb('#6a4a30')); c.arc(mx, my, 20, 0, 2 * math.pi); c.fill(); c.arc(mx - 20, my - 4, 8, 0, 2 * math.pi); c.fill(); c.arc(mx + 20, my - 4, 8, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#c8a888')); c.save(); c.translate(mx, my + 4); c.scale(13, 11); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    c.set_source_rgb(*rgb('#1e1410')); c.set_line_width(3); c.move_to(mx - 9, my - 4); c.line_to(mx - 3, my - 4); c.stroke(); c.move_to(mx + 3, my - 4); c.line_to(mx + 9, my - 4); c.stroke()
    # crate of bananas hanging from the rope (shadow 2)
    x0, y0, x1, y1 = LEDGES[1]; cx = (x0 + x1) / 2
    c.set_source_rgb(*rgb('#b8a888')); c.set_line_width(4); c.move_to(710, WALL_TOP - 200); c.line_to(cx, y0 - 30); c.stroke()
    c.move_to(cx, y0 - 30); c.line_to(x0 + 20, y0); c.stroke(); c.move_to(cx, y0 - 30); c.line_to(x1 - 20, y0); c.stroke()
    c.set_source_rgb(*rgb('#d8c048'))
    for k in range(5):
        bx = x0 + 22 + k * 32; c.save(); c.translate(bx, y0 + 6); c.rotate(-0.4 + k * 0.2); c.scale(12, 26); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    c.set_source_rgb(*rgb('#7a5a36')); rrect(c, x0, y0 + 14, x1 - x0, y1 - y0 - 14, 8); c.fill()
    c.set_source_rgba(0.3, 0.2, 0.1, 0.7); c.set_line_width(4)
    for yy in (y0 + 48, y0 + 84): c.move_to(x0, yy); c.line_to(x1, yy); c.stroke()
    c.move_to(x0 + 8, y0 + 20); c.line_to(x1 - 8, y1 - 8); c.stroke()

def draw_ufo(c, t, f, alarm):   # zookeeper walking the visitor walkway, holding out a flashlight
    ux = UXS[f]; a = ANG[f]; step = math.sin(t * 7) * 6
    c.save(); c.translate(ux, 0)
    c.set_source_rgb(*rgb('#2a3448'))
    c.set_line_width(16); c.move_to(-14, WALL_TOP - 70); c.line_to(-16 + step, WALL_TOP); c.stroke(); c.move_to(14, WALL_TOP - 70); c.line_to(16 - step, WALL_TOP); c.stroke()
    c.set_source_rgb(*rgb('#8a7a4a')); rrect(c, -38, WALL_TOP - 170, 76, 106, 18); c.fill()   # khaki shirt
    c.set_source_rgb(*rgb('#5a4e30')); c.rectangle(-38, WALL_TOP - 92, 76, 10); c.fill()   # belt
    c.set_source_rgb(*rgb('#3a5a3a')); c.rectangle(10, WALL_TOP - 156, 18, 12); c.fill()   # badge
    c.set_source_rgb(*rgb('#d8a888')); c.arc(0, WALL_TOP - 196, 26, 0, 2 * math.pi); c.fill()   # face
    c.set_source_rgb(*rgb('#1e1c24')); c.arc(-9, WALL_TOP - 200, 3.5, 0, 2 * math.pi); c.fill(); c.arc(9, WALL_TOP - 200, 3.5, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#4a5a3a')); c.save(); c.translate(0, WALL_TOP - 214); c.scale(48, 10); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()   # straw hat brim
    rrect(c, -24, WALL_TOP - 244, 48, 32, 10); c.fill()
    c.set_source_rgb(*rgb('#2e3a26')); c.rectangle(-24, WALL_TOP - 222, 48, 7); c.fill()
    c.set_source_rgb(*rgb('#8a7a4a')); c.set_line_width(14); c.move_to(24, WALL_TOP - 150); c.line_to(0, UFO_Y + 10); c.stroke()   # arm to the flashlight
    c.restore()
    c.save(); c.translate(ux, UFO_Y + 40); c.rotate(-a)
    c.set_source_rgb(*rgb('#3a3a40')); rrect(c, -12, -40, 24, 46, 6); c.fill()
    c.set_source_rgb(*rgb('#5a5a62')); rrect(c, -18, 0, 36, 14, 4); c.fill()
    c.set_source_rgb(*rgb('#fff4c8' if not alarm else '#ff8080')); c.save(); c.translate(0, 14); c.scale(16, 5); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    c.restore()

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

def draw_net(c, x, y):   # a rope net on a cable from the drone
    c.set_source_rgb(*rgb('#c8b890')); c.set_line_width(4); c.move_to(x, y - R - 30); c.line_to(UXS[min(int(T_SPOT * FPS), len(UXS) - 1)] if T_SPOT else x, UFO_Y + 20); c.stroke()
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
