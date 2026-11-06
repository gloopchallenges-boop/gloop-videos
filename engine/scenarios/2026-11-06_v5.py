"""2026-11-06 v5 — ITEMS LEFT – DUCKS LEFT: the ELECTRIC EEL. Gloop is a passive rigid ball (Ball) bouncing on
a row of 10 rubber ducks floating between the two tiled edges of a backyard pool at night. Every landing squeezes
the duck under him (3 squeezes = it deflates and sinks); an electric eel leaps out of the water at seeded-random
ducks (some aimed near him) and zaps the duck away — an eel that touches Gloop mid-leap bounces off him (real
momentum transfer, both get knocked) and misses its duck. If his bounce comes down over a gap wider than him he
drops into the pool (= fail). Timer ends with him still on the ducks = win."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the electric eel'
SEED = int(os.environ.get('SEED', 12))
rng = random.Random(SEED)

class S: pass
S.HOOK2 = 'THE ELECTRIC EEL?'; S.HOOK2_SIZE = 92; S.FAIL_WORD = 'SPLASH!'; S.FAIL_SIZE = 150
S.T_START = HOOK_T; S.TL = 13.0; S.T_END = S.T_START + S.TL
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
    if tb <= S.T_RES + 0.01: S.events.append([tb, 'crackle' if why == 'pike' else 'splash']); S.events.append([tb, 'blip'])
for (td, qx, qy) in DEFL:
    if td < S.T_RES + 0.5: S.events.append([td, 'thump', 0.8])
for (tc, i, hp) in DUNKS:
    if hp > 0: S.events.append([tc, 'creak'])
for (tl, xl, imp) in ball.landings:
    if tl < S.T_RES + 1.5 and (T_FAIL is None or tl <= T_FAIL): S.events.append([tl, 'hop'])
for tw in ball.walls:
    if tw < S.T_RES: S.events.append([tw, 'thump', 0.3])
if T_FAIL: S.events += [[T_FAIL + 0.05, 'splash'], [T_FAIL + 0.1, 'thump', 0.8]]
S.AMB = {'drone': 48, 'wind': 0.025}

def draw_bar(c, t, f):
    n = LEFT[f]; recent = any(tb <= t < tb + 0.35 for (tb, _, _) in BREAKS)
    bx = bar(c, n / NB, f'DUCKS LEFT: {n}', rgb('#7dff8a') if n > 6 else (rgb('#ffd84a') if n > 2 else rgb('#ff4d4d')), 0.15 if recent else 0, bw=660, x_off=36)
    c.save(); c.translate(bx - 52, 236); draw_duck(c, 0, 0, 0.55, 0); c.restore()
S.draw_bar = draw_bar

def draw_duck(c, x, y, s, wet):
    body = [v * (1 - 0.35 * wet) for v in rgb('#f2c43a')]
    c.save(); c.translate(x, y); c.scale(s, s)
    c.set_source_rgb(*body); c.save(); c.scale(40, 22); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    c.move_to(-40, -4); c.line_to(-52, -18); c.line_to(-30, -14); c.close_path(); c.fill()   # tail tip
    c.arc(22, -24, 17, 0, 2 * math.pi); c.fill()   # head
    c.set_source_rgb(*rgb('#e8862a')); c.move_to(36, -26); c.line_to(52, -22); c.line_to(36, -16); c.close_path(); c.fill()
    c.set_source_rgb(0.1, 0.08, 0.06); c.arc(27, -29, 3.5, 0, 2 * math.pi); c.fill()
    c.set_source_rgba(0, 0, 0, 0.12); c.save(); c.translate(-6, 2); c.scale(18, 8); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()   # wing
    c.restore()

stars = [(rng.uniform(0, W), rng.uniform(HEAD, 820), rng.uniform(1.2, 2.6)) for _ in range(50)]
def draw_bg(c, t):
    c.set_source_rgb(*rgb('#131826')); c.rectangle(0, HEAD, W, H - HEAD); c.fill()
    c.set_source_rgba(0.85, 0.88, 0.95, 0.5)
    for x, y, r in stars: c.arc(x, y, r, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#e2dcbc')); c.arc(220, 560, 50, 0, 2 * math.pi); c.fill()
    # house with a lit window + wooden fence
    c.set_source_rgb(*rgb('#262434')); c.rectangle(560, 760, 520, 420); c.fill()
    c.set_source_rgb(*rgb('#2e2a3c')); c.move_to(530, 770); c.line_to(820, 600); c.line_to(1110, 770); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#d8b45e')); rrect(c, 640, 860, 140, 120, 6); c.fill()
    c.set_source_rgb(*rgb('#262434')); c.set_line_width(8); c.move_to(710, 860); c.line_to(710, 980); c.stroke()
    c.set_source_rgb(*rgb('#1c1a26')); c.rectangle(860, 900, 110, 280); c.fill()
    c.set_source_rgb(*rgb('#33303e'))
    for x in range(0, 560, 56): c.rectangle(x + 4, 980, 48, 200); c.fill(); c.move_to(x + 4, 980); c.line_to(x + 28, 958); c.line_to(x + 52, 980); c.fill()
    c.rectangle(0, 1030, 560, 14); c.fill(); c.rectangle(0, 1120, 560, 14); c.fill()
    # pool deck + water
    c.set_source_rgb(*rgb('#3c3a44')); c.rectangle(0, 1170, W, 50); c.fill()
    c.set_source_rgb(*rgb('#d8d4cc')); c.rectangle(0, 1205, W, 14); c.fill()
    c.set_source_rgb(*rgb('#123440')); c.rectangle(0, 1219, W, H - 1219); c.fill()
    c.set_source_rgba(1, 1, 1, 0.05); c.set_line_width(3)
    for yy in range(1300, H, 90):
        for x in range(0, W + 1, 30): (c.move_to if x == 0 else c.line_to)(x, yy + 6 * math.sin(x * 0.02 + t * 1.5 + yy))
        c.stroke()
    c.set_source_rgba(0.2, 0.45, 0.55, 0.35); c.set_line_width(14)   # lane rope stripe on the pool floor
    c.move_to(0, 1780); c.line_to(W, 1780); c.stroke()

def draw_rocks(c):
    for (xa, xb, top) in ((0, BERG_L, 1300), (BERG_R, W, 1300)):   # tiled pool edges = walls
        c.set_source_rgb(*rgb('#b8c4c8')); c.rectangle(xa, top, xb - xa, H - top); c.fill()
        c.set_source_rgb(*rgb('#8a9aa0')); c.set_line_width(3)
        for yy in range(top, H, 44): c.move_to(xa, yy); c.line_to(xb, yy); c.stroke()
        for xx in range(int(xa), int(xb), 44): c.move_to(xx, top); c.line_to(xx, H); c.stroke()
        c.set_source_rgb(*rgb('#d8d4cc')); c.rectangle(xa, top - 16, xb - xa, 22); c.fill()
    c.set_source_rgb(*rgb('#9aa4aa')); c.set_line_width(10)   # pool ladder on the right edge
    for dx in (0, 50):
        c.move_to(BERG_R + 20 + dx, 1290); c.curve_to(BERG_R + 20 + dx, 1230, BERG_R - 30 + dx, 1230, BERG_R - 30 + dx, 1290); c.stroke()

def draw_pike_at(c, x, y, ang, t, chomp):   # the electric eel (long wavy body, sparks when it strikes)
    c.save(); c.translate(x, y); c.rotate(ang)
    pts = [(u, 16 * math.sin(u * 0.03 - t * 14) * (1 - (u + 170) / 400)) for u in range(-170, 121, 10)]
    c.set_line_cap(cairo.LINE_CAP_ROUND); c.set_line_join(cairo.LINE_JOIN_ROUND)
    c.set_source_rgb(*rgb('#4a7458')); c.set_line_width(58)
    c.move_to(*pts[0])
    for p in pts[1:]: c.line_to(*p)
    c.stroke()
    c.set_source_rgb(*rgb('#c8c070')); c.set_line_width(10)   # pale belly stripe
    c.move_to(pts[0][0], pts[0][1] + 12)
    for p in pts[1:]: c.line_to(p[0], p[1] + 12)
    c.stroke()
    c.set_source_rgba(0.95, 0.9, 0.5, 0.8)
    for k in range(3, len(pts) - 3, 4): c.arc(pts[k][0], pts[k][1] - 10, 4, 0, 2 * math.pi); c.fill()   # glowing dots along the back
    c.set_source_rgb(*rgb('#4a7458')); c.save(); c.translate(132, 0); c.scale(50, 36); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()   # head
    o = 4 + 16 * chomp
    c.set_source_rgb(*rgb('#1a2620')); c.move_to(150, 4); c.line_to(178, 4 - o * 0.5); c.line_to(178, 4 + o * 0.5); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#e8d870')); c.arc(140, -12, 8, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(0.05, 0.05, 0.05); c.arc(142, -12, 4, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#24362c')); c.set_line_width(4); c.move_to(128, -26); c.line_to(152, -20); c.stroke()   # grumpy brow
    if chomp > 0.4:   # zig-zag sparks
        c.set_source_rgb(*rgb('#f4e36a')); c.set_line_width(4)
        for a in (-0.9, 0.0, 0.9):
            c.move_to(180 + 10 * math.cos(a), 10 * math.sin(a))
            r0 = 30
            for j in range(4): r0 += 12; c.line_to(180 + r0 * math.cos(a + (0.25 if j % 2 else -0.25)), r0 * math.sin(a + (0.25 if j % 2 else -0.25)))
            c.stroke()
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
    c.set_source_rgba(0.07, 0.2, 0.25, 0.72); c.move_to(0, H)
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
                k = (t - br[0][0]) / 0.6; c.set_source_rgba(0.85, 0.92, 1, 0.5 * (1 - k)); c.set_line_width(4)
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
        if abs(t - (r['t'] - QF + 0.12)) < 0.5 / FPS: PS.spawn(sx, POND, 14, (0.7, 0.85, 0.95), 450, 0.5, grav=1500, r=7)
    for (tb, i, why) in BREAKS:
        if abs(t - tb) < 0.5 / FPS and tb <= S.T_RES + 0.01: PS.spawn(bx_(i), TOP + 20, 12, (0.95, 0.9, 0.5) if why == 'pike' else (0.7, 0.85, 0.95), 380, 0.5, grav=1300, r=6)
    for (td, qx, qy) in DEFL:
        if abs(t - td) < 0.5 / FPS: PS.spawn(qx, qy, 10, (0.85, 0.85, 0.75), 300, 0.4, grav=600, r=6)
    if T_FAIL and abs(t - T_FAIL - 0.05) < 0.5 / FPS: PS.spawn(GX[fi], POND, 26, (0.7, 0.85, 0.95), 650, 0.8, grav=2000, r=9)
    PS.draw(c)
    END.draw_claw(c, t)
    c.restore()
    END.header(c, t, fi)

if __name__ == '__main__':
    if sys.argv[1] == 'sim':
        e = int(S.T_RES * FPS) - 1
        print(SEED, S.OUTCOME, round(S.T_RES - S.T_START, 2), 'left', LEFT[e], 'breaks', [(round(b[0] - S.T_START, 1), b[2][0]) for b in BREAKS if b[0] <= S.T_RES], 'defl', len(DEFL), 'dur', S.DUR); sys.exit()
    run(S, render)
