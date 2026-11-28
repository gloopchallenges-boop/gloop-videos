"""2026-11-28 v2 — ITEMS LEFT – COCONUTS LEFT: the GIANT SEA TURTLE (STYLE-TEST video: sunny palm beach, rule+question
card, streak badge, subscribe outro; based on 2026-11-26 v3). Gloop is a passive rigid ball (Ball) bouncing on a row of 10
floating coconuts between two sandy rock piles. Every landing pushes the coconut under him lower (3 landings = it sinks);
a giant sea turtle leaps out of the lagoon at seeded-random coconuts (some aimed near him) and bonks the coconut away as it
lands — a turtle that touches Gloop mid-leap bounces off him (real momentum transfer) and misses. If his bounce comes down over a gap
wider than him he drops into the river (= fail). Timer ends with him still on the apples = win."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the giant sea turtle'
SEED = int(os.environ.get('SEED', 1))
rng = random.Random(SEED)

class S: pass
S.HOOK2 = 'THE GIANT SEA TURTLE?'; S.HOOK2_SIZE = 84; S.FAIL_WORD = 'SPLASH!'
S.CARD = ['Leaps and bounces *SINK* coconuts', 'Will *1 COCONUT* be left?']; S.STREAK = int(os.environ.get('STREAK', 2)); S.CTA = True; S.FAIL_SIZE = 150
S.T_START = HOOK_T; S.TL = float(os.environ.get('TL', 13.0)); S.T_END = S.T_START + S.TL
TOP = 1440; POND = TOP + 26; R = 58; BERG_L, BERG_R = 110, 970; XMIN, XMAX = BERG_L + R, BERG_R - R
NB = 10; BW = (BERG_R - BERG_L) / NB; HP = int(os.environ.get('HP', 3))

class PadRow:
    soft = False
    def __init__(self): self.alive = [True] * NB; self.hp = [HP] * NB
    def idx(self, x): return int(clamp((x - BERG_L) // BW, 0, NB - 1))
    def y(self, x):
        if x < BERG_L + 4 or x > BERG_R - 4: return TOP
        i = self.idx(x)
        if self.alive[i]: return TOP
        a = i
        while a > 0 and not self.alive[a - 1]: a -= 1
        b = i
        while b < NB - 1 and not self.alive[b + 1]: b += 1
        gap = (b - a + 1) * BW
        return TOP + 12 if gap < 2 * R * 0.95 else TOP + 600   # a one-pad gap is narrower than Gloop
    def slope(self, x, d=30): return 0.0
    def dig(self, *a): pass
PADS = PadRow()
SINK = Terrain(POND + R * 0.35, seed=SEED, bumps=0, amp=0, soft=False)   # in the pond: floats half under

QF = 0.75   # leap flight time
RAMS = []; t = 0.35
while t < S.T_END + 1:
    RAMS.append({'t': t, 'aim': rng.random() < float(os.environ.get('AIM', 0.3)), 'i': rng.randrange(NB), 'dir': rng.choice((-1, 1))})
    t += rng.uniform(*map(float, os.environ.get('GAP', '1.5,2.6').split(',')))
def bx_(i): return BERG_L + (i + 0.5) * BW
def pike_pos(r, t):
    """Leaps out of the water 230 px to the side of the target pad, arcs up and chomps down on it."""
    k = (t - (r['t'] - QF)) / QF; tx, ty = bx_(r['i']), TOP + 14; sx = tx - r['dir'] * 230
    return lerp(sx, tx, k), lerp(POND + 70, ty, k) - 330 * 4 * k * (1 - k)
def pike_vel(r, t):
    a = pike_pos(r, t - 0.01); b = pike_pos(r, t + 0.01); return (b[0] - a[0]) / 0.02, (b[1] - a[1]) / 0.02
PR = 46   # dolphin body half-thickness; capsule along its axis (u = -70..70)
DEFL = []
N0 = int(40 * FPS); GX, GYS, LEFT, ALIVE, HPS = [], [], [], [], []
ball = Ball(rng.uniform(350, 730), PADS, R=R, seed=SEED, xmin=XMIN, xmax=XMAX, hop=rng.uniform(220, 280))
T_FAIL = None; BREAKS = []; DUNKS = []; nl = 0
for f in range(N0):
    t = f / FPS
    live = T_FAIL is None and S.T_START <= t < S.T_END
    for r in RAMS:
        if abs(t - (r['t'] - QF)) < 0.5 / FPS and r['aim']: r['i'] = PADS.idx(ball.x + rng.uniform(-BW, BW))
        if abs(t - r['t']) < 0.5 / FPS and not r.get('defl'):
            i = r['i']
            if PADS.alive[i] and live: PADS.alive[i] = False; BREAKS.append((t, i, 'pike')); r['did'] = True
    px, py = ball.x, ball.y
    ball.step(t)
    for r in RAMS:   # swept: a leaping pike that touches Gloop bounces off him (real momentum transfer)
        if r.get('defl') or not (r['t'] - QF <= t < r['t'] + 1 / FPS): continue
        for k in range(1, 9):
            ts = t - 1 / FPS + k / (8 * FPS)
            if ts < r['t'] - QF or ts > r['t']: continue
            cx, cy = pike_pos(r, ts); bx, by = lerp(px, ball.x, k / 8), lerp(py, ball.y, k / 8)
            vqx, vqy = pike_vel(r, ts); a_ = math.atan2(vqy, vqx); ca, sa = math.cos(a_), math.sin(a_)
            best = None   # the whole visible body (capsule along the fish axis), not just its centre
            for u in (-70, -35, 0, 35, 70):
                qx, qy = cx + ca * u, cy + sa * u
                if qy > POND + 10: continue   # that part is still under water
                d = math.hypot(bx - qx, by - qy)
                if best is None or d < best[0]: best = (d, qx, qy)
            if best is None: continue
            d, qx, qy = best
            if d < R + PR:
                nx, ny = (bx - qx) / (d or 1), (by - qy) / (d or 1)
                rel = (vqx - ball.vx) * nx + (vqy - ball.vy) * ny
                if rel > 0: j = min(0.6 * rel, 520); ball.vx += j * nx; ball.vy += j * ny; ball._pushed = True
                r['defl'] = ts; r['dpos'] = (qx, qy); r['dvel'] = (-nx * 300, 500); DEFL.append((ts, qx, qy)); break
    while nl < len(ball.landings):
        tl, xl, imp = ball.landings[nl]; nl += 1
        if T_FAIL is None and S.T_START <= tl < S.T_END and BERG_L < xl < BERG_R:
            i = PADS.idx(xl)
            if PADS.alive[i]:
                PADS.hp[i] -= 1; DUNKS.append((tl, i, PADS.hp[i]))
                if PADS.hp[i] <= 0: PADS.alive[i] = False; BREAKS.append((tl, i, 'sink'))
    if T_FAIL is None and ball.y > TOP + 10 and live: T_FAIL = t
    if T_FAIL is not None and ball.T is PADS:
        ball.T = SINK; ball.vmin = 0; ball.e = 0.1; ball.base_h = 0
    if ball.T is SINK: ball.vx *= 0.85; ball.vy *= 0.8
    GX.append(ball.x); GYS.append(ball.y); LEFT.append(sum(PADS.alive)); ALIVE.append(list(PADS.alive)); HPS.append(list(PADS.hp))
S.OUTCOME = 'fail' if T_FAIL else 'win'
S.T_RES = T_FAIL if T_FAIL else S.T_END
S.GRAB = (540, TOP - R)
END = S.END = Ending(S)
gi = min(int(END.T_GRAB * FPS), N0 - 1); S.GRAB = (GX[gi], min(GYS[gi], POND - R * 0.3))
S.events = [[0.05, 'rumble', 1.0]]
for r in RAMS:
    if r['t'] - QF < S.T_RES: S.events.append([r['t'] - QF + 0.08, 'splash']); S.events.append([r['t'] - QF + 0.1, 'whoosh'])
for (tb, i, why) in BREAKS:
    if tb <= S.T_RES + 0.01: S.events.append([tb, 'thump' if why == 'pike' else 'splash', 0.7]); S.events.append([tb, 'blip'])
for (td, qx, qy) in DEFL:
    if td < S.T_RES + 0.5: S.events.append([td, 'thump', 0.8])
for (tc, i, hp) in DUNKS:
    if hp > 0: S.events.append([tc, 'creak'])
for (tl, xl, imp) in ball.landings:
    if tl < S.T_RES + 1.5 and (T_FAIL is None or tl <= T_FAIL): S.events.append([tl, 'hop'])
for tw in ball.walls:
    if tw < S.T_RES: S.events.append([tw, 'thump', 0.3])
if T_FAIL: S.events += [[T_FAIL + 0.05, 'splash'], [T_FAIL + 0.1, 'thump', 0.8]]
S.AMB = {'drone': 52, 'wind': 0.012}

def draw_bar(c, t, f):
    n = LEFT[f]; recent = any(tb <= t < tb + 0.35 for (tb, _, _) in BREAKS)
    bx = bar(c, n / NB, f'COCONUTS LEFT: {n}', rgb('#7dff8a') if n > 6 else (rgb('#ffd84a') if n > 2 else rgb('#ff4d4d')), 0.15 if recent else 0, bw=660, x_off=36)
    c.save(); c.translate(bx - 52, 252); draw_duck(c, 0, 8, 0.62, 0); c.restore()
S.draw_bar = draw_bar


def draw_duck(c, x, y, s, wet, i=0):   # a floating coconut; wet = water on it 0..1 -> lower & darker
    c.save(); c.translate(x, y); c.scale(s, s)
    dk = 1 - 0.25 * wet; col = rgb(('#7a5232', '#86603a', '#6e4a2c')[i % 3])
    c.set_source_rgb(*[v * dk for v in col]); c.save(); c.translate(0, -6); c.scale(38, 32); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    c.set_source_rgba(0.25, 0.15, 0.08, 0.5); c.set_line_width(2)
    for k in range(-2, 3): c.move_to(-30 + k * 4, -24 + abs(k) * 2); c.curve_to(-10 + k * 6, -12, 10 + k * 6, -2, 30 + k * 3, 6 - abs(k) * 2); c.stroke()   # fibres
    c.set_source_rgb(*[v * 0.45 for v in col])
    for (dx, dy) in ((-10, -22), (6, -24), (-2, -12)): c.arc(dx, dy, 4.5, 0, 2 * math.pi); c.fill()   # three eyes
    c.set_source_rgba(1, 1, 1, 0.22 * dk); c.save(); c.translate(-18, -20); c.scale(8, 5); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    if wet > 0: c.set_source_rgba(0.3, 0.75, 0.85, 0.75); c.save(); c.translate(0, 12); c.scale(32 * wet + 6, 6 * wet + 2); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    c.restore()

clouds = [(rng.uniform(0, W), rng.uniform(520, 760), rng.uniform(0.7, 1.2), rng.uniform(8, 16)) for _ in range(4)]
def palm(c, x, y, h, lean, t, k):
    c.set_source_rgb(*rgb('#a8865a')); c.set_line_width(18); c.set_line_cap(cairo.LINE_CAP_ROUND)
    tx, ty = x + lean, y - h
    c.move_to(x, y); c.curve_to(x + lean * 0.2, y - h * 0.5, x + lean * 0.7, y - h * 0.8, tx, ty); c.stroke()
    c.set_source_rgb(*rgb('#3aa060' if k % 2 else '#4ab86a'))
    for j in range(6):
        a = -math.pi / 2 + (j - 2.5) * 0.55 + 0.04 * math.sin(t * 1.2 + j + k)
        c.save(); c.translate(tx, ty); c.rotate(a); c.scale(90, 18); c.arc(1, 0.3, 1, 0, 2 * math.pi); c.restore(); c.fill()
    c.set_line_cap(cairo.LINE_CAP_BUTT)
def draw_bg(c, t):
    c.set_source_rgb(*rgb('#86d0f4')); c.rectangle(0, HEAD, W, H - HEAD); c.fill()   # flat sunny sky
    c.set_source_rgb(*rgb('#b0e2fa')); c.rectangle(0, 900, W, 320); c.fill()
    c.set_source_rgb(*rgb('#fff8dc')); c.arc(860, 560, 54, 0, 2 * math.pi); c.fill()   # sun
    for (x, y, sc, v) in clouds:
        xx = (x + v * t) % (W + 300) - 150; c.set_source_rgba(1, 1, 1, 0.92)
        for (dx, dy, rr) in ((0, 0, 40), (40, -16, 48), (86, 0, 38)):
            c.arc(xx + dx * sc, y + dy * sc, rr * sc, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#5ab8d8')); c.rectangle(0, 1080, W, 140); c.fill()   # far sea
    c.set_source_rgb(*rgb('#7a9ac8')); c.move_to(600, 1082); c.curve_to(680, 1000, 820, 990, 900, 1082); c.close_path(); c.fill()   # far island
    # sandy beach strip with a striped umbrella, sandcastle and palms
    c.set_source_rgb(*rgb('#f4e2b8')); c.move_to(0, 1219); c.curve_to(300, 1130, 700, 1140, W, 1170); c.line_to(W, 1219); c.close_path(); c.fill()
    palm(c, 150, 1200, 330, 60, t, 0); palm(c, 300, 1190, 250, -40, t, 1); palm(c, 960, 1200, 300, -70, t, 2)
    ux, uy = 640, 1170
    c.set_source_rgb(*rgb('#ffffff')); c.set_line_width(5); c.move_to(ux, uy); c.line_to(ux, uy - 120); c.stroke()
    for k in range(5):
        c.set_source_rgb(*rgb('#e86a9a' if k % 2 else '#ffffff')); c.move_to(ux, uy - 150)
        c.arc(ux, uy - 110, 90, math.pi + k * math.pi / 5, math.pi + (k + 1) * math.pi / 5); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#e8d0a0')); c.rectangle(440, 1140, 70, 50); c.fill(); c.rectangle(455, 1115, 40, 26); c.fill()   # sandcastle
    for k in range(4): c.rectangle(440 + k * 20, 1130, 10, 12); c.fill()
    c.set_source_rgb(*rgb('#4a90d0')); c.move_to(475, 1115); c.line_to(475, 1085); c.stroke(); c.move_to(475, 1085); c.line_to(495, 1092); c.line_to(475, 1099); c.close_path(); c.fill()
    # turquoise lagoon
    c.set_source_rgb(*rgb('#3ac0cc')); c.rectangle(0, 1219, W, H - 1219); c.fill()
    c.set_source_rgba(1, 1, 1, 0.16); c.set_line_width(3)
    for yy in range(1280, H, 90):
        for x in range(0, W + 1, 30): (c.move_to if x == 0 else c.line_to)(x, yy + 6 * math.sin(x * 0.02 + t * 1.5 + yy))
        c.stroke()

def draw_rocks(c):
    for (xa, xb, top) in ((0, BERG_L, 1300), (BERG_R, W, 1300)):   # sandy rock piles = walls
        for k in range(7):
            yy = top + k * 90
            c.set_source_rgb(*rgb('#a89e94' if k % 2 else '#b8aea4')); rrect(c, xa - 30 + (k % 2) * 8, yy, xb - xa + 60, 86, 34); c.fill()
            c.set_source_rgba(1, 1, 1, 0.18); c.save(); c.translate((xa + xb) / 2, yy + 20); c.scale((xb - xa) * 0.3, 8); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
        c.set_source_rgb(*rgb('#f4e2b8')); c.move_to(xa - 20, top + 10); c.curve_to(xa + 20, top - 24, xb - 20, top - 24, xb + 20, top + 10); c.line_to(xb + 20, top + 22); c.line_to(xa - 20, top + 22); c.close_path(); c.fill()
        fx = (xa + xb) / 2   # a pink starfish + shell on top
        c.set_source_rgb(*rgb('#f07aa8')); star_path(c, fx - 12, top - 14, 16); c.fill()
        c.set_source_rgb(*rgb('#ffffff')); c.save(); c.translate(fx + 22, top - 10); c.scale(11, 8); c.arc(0, 0, 1, math.pi, 2 * math.pi); c.restore(); c.fill()

def draw_pike_at(c, x, y, ang, t, chomp):   # the giant sea turtle (leaping, body along its jump)
    c.save(); c.translate(x, y); c.rotate(ang)
    if math.cos(ang) < 0: c.scale(1, -1)   # keep the shell up
    skin, dark, shell, shell2 = rgb('#7ab89a'), rgb('#4a8a6a'), rgb('#3a7a5a'), rgb('#6aa070')
    fl = 0.4 * math.sin(t * 12)
    c.set_source_rgb(*skin)   # flippers
    c.save(); c.translate(40, 30); c.rotate(0.7 + fl); c.scale(60, 18); c.arc(1, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    c.save(); c.translate(-60, 26); c.rotate(0.9 - fl); c.scale(36, 14); c.arc(1, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    c.save(); c.translate(-100, 4); c.scale(22, 10); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()   # tail
    c.set_source_rgb(*rgb('#e8e0b0')); c.save(); c.translate(0, 14); c.scale(100, 26); c.arc(0, 0, 1, 0, math.pi); c.restore(); c.fill()   # plastron
    c.set_source_rgb(*shell); c.save(); c.translate(0, 8); c.scale(104, 58); c.arc(0, 0, 1, math.pi, 2 * math.pi); c.restore(); c.fill()   # shell dome
    c.set_source_rgb(*shell2)
    for (px, py, rr) in ((0, -26, 20), (-44, -16, 15), (44, -16, 15), (-22, -2, 12), (22, -2, 12)):
        c.save(); c.translate(px, py); c.scale(rr * 1.2, rr * 0.8); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    c.set_source_rgb(*dark); c.set_line_width(4); c.save(); c.translate(0, 8); c.scale(104, 58); c.arc(0, 0, 1, math.pi, 2 * math.pi); c.restore(); c.stroke()
    c.set_source_rgb(*skin); c.save(); c.translate(98, 4); c.scale(26, 18); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()   # neck
    c.arc(124, -4, 28, 0, 2 * math.pi); c.fill()   # head
    c.set_source_rgb(0.08, 0.08, 0.06); c.arc(128, -14, 6, 0, 2 * math.pi); c.fill()   # eye
    c.set_source_rgb(1, 1, 1); c.arc(130, -16, 2, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#2a4a3a')); c.save(); c.translate(140, 8); c.scale(12, 2 + 7 * chomp); c.arc(0, 0, 1, 0, math.pi); c.restore(); c.fill()   # beak mouth
    c.restore()

def pike_draw_state(r, t):
    """Position/angle while visible: leap arc, then (after a chomp or a bounce-off) a dive back down."""
    if r.get('defl') and t >= r['defl']:
        k = t - r['defl']; qx, qy = r['dpos']; vx, vy = r['dvel']
        x, y = qx + vx * k, qy + vy * k + 1600 * k * k; return x, y, math.atan2(vy + 3200 * k, vx), 0.0
    if t < r['t']:
        qx, qy = pike_pos(r, t); vx, vy = pike_vel(r, t); return qx, qy, math.atan2(vy, vx), 1 - abs(2 * ((t - (r['t'] - QF)) / QF) - 1)
    k = t - r['t']; tx = bx_(r['i']); vx, vy = pike_vel(r, r['t'] - 0.02)
    return tx + vx * 0.3 * k, TOP + 14 + 900 * k, math.atan2(vy, vx), 0.0

def draw_pikes(c, t, front):
    for r in RAMS:
        if not (r['t'] - QF <= t < r['t'] + 0.6) or r['t'] - QF > S.T_RES: continue
        x, y, ang, ch = pike_draw_state(r, t)
        under = y > POND + 20
        if under == front: continue
        draw_pike_at(c, x, y, ang, t, ch)

def draw_water_front(c, t):
    c.set_source_rgba(0.18, 0.62, 0.72, 0.62); c.move_to(0, H)
    for x in range(0, W + 20, 20): c.line_to(x, POND + 5 * math.sin(x * 0.03 + t * 2))
    c.line_to(W, H); c.close_path(); c.fill()
    c.set_source_rgba(1, 1, 1, 0.10); c.set_line_width(3)
    for x in range(0, W + 20, 20): (c.move_to if x == 0 else c.line_to)(x, POND + 5 * math.sin(x * 0.03 + t * 2))
    c.stroke()

def draw_pads(c, t, f):
    al = ALIVE[f]; hp = HPS[f]
    for i in range(NB):
        x = BERG_L + (i + 0.5) * BW; bob = 2 * math.sin(t * 2 + i * 1.3)
        dunk = 0.0
        for (td, j, h) in DUNKS:
            if j == i and td <= t < td + 0.35: dunk = 10 * math.sin(math.pi * (t - td) / 0.35)
        y = TOP + 25 + bob + dunk + 3 * (HP - hp[i])
        if al[i]:
            wet = (HP - hp[i]) / HP
            c.save(); c.translate(x, y + 6 * wet); draw_duck(c, 0, 0, 1.08, wet, i); c.restore()
        else:
            br = [b for b in BREAKS if b[1] == i]
            if br and t - br[0][0] < 0.6:
                k = (t - br[0][0]) / 0.6; c.set_source_rgba(0.8, 0.85, 0.85, 0.5 * (1 - k)); c.set_line_width(4)
                c.save(); c.translate(x, POND); c.scale(1, 0.3); c.arc(0, 0, 20 + 90 * k, 0, 2 * math.pi); c.restore(); c.stroke()
                if br[0][2] == 'pike':   # bonked by the beak: flies off spinning
                    kk = t - br[0][0]; dr = 1 if i < NB / 2 else -1
                    c.save(); c.translate(x - dr * 700 * kk, y - 900 * kk + 1800 * kk * kk); c.rotate(-dr * 6 * kk); draw_duck(c, 0, 0, 1.15, 0, i); c.restore()
                else:
                    c.save(); c.translate(x, y + 30 * k); c.scale(1, max(0.1, 1 - k)); draw_duck(c, 0, 0, 1.15, 1, i); c.restore()

PS = Particles(9)
def render(f, c):
    t = f / FPS; fi = min(f, len(GX) - 1); shake = (0, 0)
    for (tb, i, why) in BREAKS:
        if tb <= t < tb + 0.15 and why == 'pike' and tb <= S.T_RES + 0.01: shake = (rng.uniform(-3, 3), rng.uniform(-3, 3))
    c.save(); c.translate(*shake)
    draw_bg(c, t); draw_pikes(c, t, False); draw_rocks(c)
    fell = T_FAIL is not None and t >= T_FAIL
    if END.carried(t) or t >= END.T_GRAB: gx, gy = (END.carry_xy(t) if END.carried(t) else S.GRAB)
    else:
        gx, gy = GX[fi], GYS[fi]
        if fell: gy = min(gy, POND - R * 0.3 + 5 * math.sin(t * 4)) if t > T_FAIL + 0.4 else gy
    p = LEFT[fi] / NB
    danger = any(r['t'] - QF <= t < r['t'] and abs(bx_(r['i']) - GX[fi]) < 220 for r in RAMS)
    mood = 'happy' if (t >= S.T_END and S.OUTCOME == 'win') else ('scared' if fell or danger or p < 0.4 else 'worried')
    draw_pads(c, t, fi)
    draw_blob(c, t, gx, gy, mood, 0, R=R, dizzy=fell and t > T_FAIL + 0.6)
    draw_water_front(c, t)
    draw_pikes(c, t, True)
    for r in RAMS:
        if r['t'] - QF > S.T_RES: continue
        sx, sy = pike_pos(r, r['t'] - QF + 0.12)
        if abs(t - (r['t'] - QF + 0.12)) < 0.5 / FPS: PS.spawn(sx, POND, 14, (0.85, 0.95, 1.0), 450, 0.5, grav=1500, r=7)
    for (tb, i, why) in BREAKS:
        if abs(t - tb) < 0.5 / FPS and tb <= S.T_RES + 0.01: PS.spawn(bx_(i), TOP + 20, 12, (0.9, 0.95, 1.0) if why == 'pike' else (0.85, 0.95, 1.0), 380, 0.5, grav=1300, r=6)
    for (td, qx, qy) in DEFL:
        if abs(t - td) < 0.5 / FPS: PS.spawn(qx, qy, 10, (0.85, 0.85, 0.75), 300, 0.4, grav=600, r=6)
    if T_FAIL and abs(t - T_FAIL - 0.05) < 0.5 / FPS: PS.spawn(GX[fi], POND, 26, (0.85, 0.95, 1.0), 650, 0.8, grav=2000, r=9)
    PS.draw(c)
    END.draw_claw(c, t)
    c.restore()
    END.header(c, t, fi)

if __name__ == '__main__':
    if sys.argv[1] == 'sim':
        e = int(S.T_RES * FPS) - 1
        print(SEED, S.OUTCOME, round(S.T_RES - S.T_START, 2), 'left', LEFT[e], 'breaks', [(round(b[0] - S.T_START, 1), b[2][0]) for b in BREAKS if b[0] <= S.T_RES], 'defl', len(DEFL), 'dur', S.DUR); sys.exit()
    run(S, render)
