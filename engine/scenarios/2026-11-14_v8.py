"""2026-11-14 v8 — ITEMS LEFT – WATERMELONS LEFT: the HUNGRY HIPPO. Gloop is a passive rigid ball (Ball) bouncing
on a row of 10 floating watermelons between two reedy riverbanks at night. Every landing pushes the melon under him
deeper (3 dunks = it fills with water and sinks); a hungry hippo lunges out of the river at seeded-random melons
(some aimed near him) and gobbles the melon — a hippo that touches Gloop mid-lunge bounces off him (real momentum
transfer, both get knocked) and misses its melon. If his bounce comes down over a gap wider than him he drops
into the river (= fail). Timer ends with him still on the melons = win."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the hungry hippo'
SEED = int(os.environ.get('SEED', 12))
rng = random.Random(SEED)

class S: pass
S.HOOK2 = 'THE HUNGRY HIPPO?'; S.HOOK2_SIZE = 90; S.FAIL_WORD = 'SPLASH!'; S.FAIL_SIZE = 150
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
PR = 30   # pike body half-thickness (capsule radius)
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
            for u in range(-130, 181, 20):
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
S.AMB = {'drone': 46, 'wind': 0.02}

def draw_bar(c, t, f):
    n = LEFT[f]; recent = any(tb <= t < tb + 0.35 for (tb, _, _) in BREAKS)
    bx = bar(c, n / NB, f'MELONS LEFT: {n}', rgb('#7dff8a') if n > 6 else (rgb('#ffd84a') if n > 2 else rgb('#ff4d4d')), 0.15 if recent else 0, bw=660, x_off=36)
    c.save(); c.translate(bx - 52, 234); draw_duck(c, 0, 0, 0.5, 0); c.restore()
S.draw_bar = draw_bar

def draw_duck(c, x, y, s, wet):   # a floating watermelon (side view); wet = damage 0..1 -> darker, water-logged
    c.save(); c.translate(x, y); c.scale(s, s)
    dk = 1 - 0.3 * wet
    c.set_source_rgb(*[v * dk for v in rgb('#3a8a3e')]); c.save(); c.scale(38, 26); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    c.set_source_rgb(*[v * dk for v in rgb('#245a28')]); c.set_line_width(5)
    for k in (-22, -8, 6, 20):
        c.move_to(k, -24); c.curve_to(k + 6, -8, k + 6, 8, k, 24); c.stroke()
    c.set_source_rgba(1, 1, 1, 0.18 * dk); c.save(); c.translate(-12, -12); c.scale(12, 5); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    c.set_source_rgb(*rgb('#5a4a2a')); c.rectangle(-2, -30, 4, 7); c.fill()
    if wet > 0.2:
        c.set_source_rgba(0.2, 0.3, 0.35, 0.8); c.set_line_width(3); c.move_to(-34, 10); c.line_to(34, 10); c.stroke()   # waterline
    c.restore()

stars = [(rng.uniform(0, W), rng.uniform(HEAD, 820), rng.uniform(1.2, 2.4)) for _ in range(40)]
def draw_bg(c, t):
    c.set_source_rgb(*rgb('#141a24')); c.rectangle(0, HEAD, W, H - HEAD); c.fill()
    c.set_source_rgba(0.85, 0.88, 0.95, 0.45)
    for x, y, r in stars: c.arc(x, y, r, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#e2dcbc')); c.arc(300, 540, 48, 0, 2 * math.pi); c.fill()
    # far savanna bank with acacia trees
    c.set_source_rgb(*rgb('#1e2026')); c.move_to(0, 1219); c.line_to(0, 1110); c.curve_to(300, 1080, 700, 1100, W, 1090); c.line_to(W, 1219); c.close_path(); c.fill()
    for (x, y, sc) in ((180, 1000, 1.0), (820, 980, 0.8)):
        c.set_line_width(14 * sc); c.move_to(x, 1110); c.line_to(x + 10 * sc, y); c.stroke()
        c.save(); c.translate(x + 10 * sc, y - 20 * sc); c.scale(160 * sc, 36 * sc); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    c.set_source_rgb(*rgb('#1a1c22'))   # giraffe silhouette far away
    c.set_line_width(10); c.move_to(560, 1095); c.line_to(560, 1050); c.move_to(600, 1095); c.line_to(600, 1050); c.stroke()
    c.save(); c.translate(580, 1045); c.scale(34, 16); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    c.set_line_width(9); c.move_to(605, 1040); c.line_to(630, 980); c.stroke(); c.save(); c.translate(638, 978); c.scale(14, 7); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    # river
    c.set_source_rgb(*rgb('#16242c')); c.rectangle(0, 1219, W, H - 1219); c.fill()
    c.set_source_rgba(0.9, 0.9, 0.8, 0.10)
    for i in range(6): c.rectangle(300 - 60 + 10 * math.sin(t * 2 + i), 1235 + i * 22, 120 - i * 12, 5); c.fill()
    c.set_source_rgba(1, 1, 1, 0.05); c.set_line_width(3)
    for yy in range(1280, H, 90):
        for x in range(0, W + 1, 30): (c.move_to if x == 0 else c.line_to)(x, yy + 6 * math.sin(x * 0.02 + t * 1.5 + yy))
        c.stroke()

def draw_rocks(c):
    for (xa, xb, top, sgn) in ((0, BERG_L, 1300, 1), (BERG_R, W, 1300, -1)):   # muddy reed banks = walls
        c.set_source_rgb(*rgb('#4a3a2a')); c.rectangle(xa, top, xb - xa, H - top); c.fill()
        c.set_source_rgb(*rgb('#3a2e22'))
        for yy in range(top + 60, H, 120): c.rectangle(xa, yy, xb - xa, 8); c.fill()
        c.set_source_rgb(*rgb('#5a6a34')); rrect(c, xa - 10, top - 18, xb - xa + 20, 30, 12); c.fill()
        c.set_source_rgb(*rgb('#6a7a3a')); c.set_line_width(6)   # reeds
        for k in range(6):
            rx = xa + 12 + k * (xb - xa - 24) / 5
            c.move_to(rx, top); c.line_to(rx + 8 * math.sin(k), top - 120 - (k % 3) * 30); c.stroke()
        c.set_source_rgb(*rgb('#5a3a22'))
        for k in (1, 4):
            rx = xa + 12 + k * (xb - xa - 24) / 5 + 8 * math.sin(k); ry = top - 120 - (k % 3) * 30
            c.save(); c.translate(rx, ry); c.scale(7, 20); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()

def draw_pike_at(c, x, y, ang, t, chomp):   # the hungry hippo (lunging, mouth-first)
    c.save(); c.translate(x, y); c.rotate(ang)
    body, belly, dark = rgb('#6a5a6e'), rgb('#b08a90'), rgb('#4a3e50')
    c.set_source_rgb(*body); c.save(); c.translate(-60, 0); c.scale(130, 64); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()   # body
    c.set_source_rgb(*belly); c.save(); c.translate(-60, 34); c.scale(100, 20); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    fl = 0.4 * math.sin(t * 14)
    for (lx, ph) in ((-120, 0), (0, 1.4)):   # stubby legs
        c.set_source_rgb(*dark); c.save(); c.translate(lx, 46); c.rotate(0.6 + fl * (1 if ph else -1)); rrect(c, -14, 0, 28, 44, 10); c.restore(); c.fill()
    c.set_source_rgb(*dark); c.move_to(-186, -6); c.line_to(-210, 0 + 6 * math.sin(t * 9)); c.line_to(-186, 8); c.close_path(); c.fill()   # tail
    o = 0.08 + 0.55 * chomp
    c.save(); c.translate(50, -4); c.rotate(-o)   # upper head
    c.set_source_rgb(*body); rrect(c, -10, -52, 150, 60, 26); c.fill()
    c.set_source_rgb(*belly); rrect(c, 4, -2, 128, 12, 6); c.fill()
    c.set_source_rgb(*dark)
    for nx in (112, 128): c.arc(nx, -40, 6, 0, 2 * math.pi); c.fill()   # nostrils
    c.set_source_rgb(*body)
    for ex in (10, 34): c.save(); c.translate(ex, -58); c.scale(10, 14); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()   # ears
    c.set_source_rgb(1, 1, 1); c.arc(50, -42, 12, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(0.05, 0.05, 0.05); c.arc(54, -42, 6, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*dark); c.set_line_width(5); c.move_to(36, -60); c.line_to(66, -52); c.stroke()
    c.set_source_rgb(1, 1, 0.9)
    for xx in (30, 116): c.move_to(xx, 6); c.line_to(xx + 8, 26); c.line_to(xx + 16, 6); c.close_path(); c.fill()   # teeth
    c.restore()
    c.save(); c.translate(50, 10); c.rotate(o)   # lower jaw
    c.set_source_rgb(*body); rrect(c, -10, 0, 140, 40, 18); c.fill()
    c.set_source_rgb(*rgb('#a05a6a')); rrect(c, 4, 0, 118, 12, 6); c.fill()
    c.set_source_rgb(1, 1, 0.9)
    for xx in (20, 108): c.move_to(xx, 2); c.line_to(xx + 9, -26); c.line_to(xx + 18, 2); c.close_path(); c.fill()   # tusks
    c.restore()
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
    c.set_source_rgba(0.08, 0.15, 0.16, 0.72); c.move_to(0, H)
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
            c.save(); c.translate(x, y); c.scale(1, 1 - 0.18 * wet); draw_duck(c, 0, 0, 1.15, wet); c.restore()
        else:
            br = [b for b in BREAKS if b[1] == i]
            if br and t - br[0][0] < 0.6:
                k = (t - br[0][0]) / 0.6; c.set_source_rgba(0.8, 0.85, 0.85, 0.5 * (1 - k)); c.set_line_width(4)
                c.save(); c.translate(x, POND); c.scale(1, 0.3); c.arc(0, 0, 20 + 90 * k, 0, 2 * math.pi); c.restore(); c.stroke()
                c.save(); c.translate(x + (40 * k if br[0][2] == 'pike' else 0), y + 30 * k - (120 * k * (1 - k) if br[0][2] == 'pike' else 0))
                c.rotate(2.5 * k if br[0][2] == 'pike' else 0); c.scale(1, max(0.1, 1 - k)); draw_duck(c, 0, 0, 1.15, 1); c.restore()

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
        if abs(t - (r['t'] - QF + 0.12)) < 0.5 / FPS: PS.spawn(sx, POND, 14, (0.6, 0.7, 0.7), 450, 0.5, grav=1500, r=7)
    for (tb, i, why) in BREAKS:
        if abs(t - tb) < 0.5 / FPS and tb <= S.T_RES + 0.01: PS.spawn(bx_(i), TOP + 20, 12, (0.6, 0.42, 0.24) if why == 'pike' else (0.6, 0.7, 0.7), 380, 0.5, grav=1300, r=6)
    for (td, qx, qy) in DEFL:
        if abs(t - td) < 0.5 / FPS: PS.spawn(qx, qy, 10, (0.85, 0.85, 0.75), 300, 0.4, grav=600, r=6)
    if T_FAIL and abs(t - T_FAIL - 0.05) < 0.5 / FPS: PS.spawn(GX[fi], POND, 26, (0.6, 0.7, 0.7), 650, 0.8, grav=2000, r=9)
    PS.draw(c)
    END.draw_claw(c, t)
    c.restore()
    END.header(c, t, fi)

if __name__ == '__main__':
    if sys.argv[1] == 'sim':
        e = int(S.T_RES * FPS) - 1
        print(SEED, S.OUTCOME, round(S.T_RES - S.T_START, 2), 'left', LEFT[e], 'breaks', [(round(b[0] - S.T_START, 1), b[2][0]) for b in BREAKS if b[0] <= S.T_RES], 'defl', len(DEFL), 'dur', S.DUR); sys.exit()
    run(S, render)
