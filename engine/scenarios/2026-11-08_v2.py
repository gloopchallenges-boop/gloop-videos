"""2026-11-08 v2 — ITEMS LEFT – ICE BLOCKS LEFT: the ANGRY SEAL. Gloop is a passive rigid ball (Ball) bouncing on
a row of 10 ice blocks floating between two ice-shelf edges of an arctic bay at night. Every landing cracks the
block under him (3 cracks = it splits and sinks); a grumpy seal leaps out of the water at seeded-random blocks
(some aimed near him) and head-butts the block away — a seal that touches Gloop mid-leap bounces off him (real
momentum transfer, both get knocked) and misses its block. If his bounce comes down over a gap wider than him he
drops into the sea (= fail). Timer ends with him still on the blocks = win."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the angry seal'
SEED = int(os.environ.get('SEED', 12))
rng = random.Random(SEED)

class S: pass
S.HOOK2 = 'THE ANGRY SEAL?'; S.HOOK2_SIZE = 92; S.FAIL_WORD = 'SPLASH!'; S.FAIL_SIZE = 150
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
    bx = bar(c, n / NB, f'ICE BLOCKS LEFT: {n}', rgb('#7dff8a') if n > 6 else (rgb('#ffd84a') if n > 2 else rgb('#ff4d4d')), 0.15 if recent else 0, bw=660, x_off=36)
    c.save(); c.translate(bx - 52, 236); draw_duck(c, 0, 0, 0.5, 0); c.restore()
S.draw_bar = draw_bar

def draw_duck(c, x, y, s, wet):   # a floating ice block; wet = damage 0..1 -> cracks + darker
    c.save(); c.translate(x, y); c.scale(s, s)
    c.set_source_rgb(*[v * (1 - 0.25 * wet) for v in rgb('#cfe6f0')]); rrect(c, -40, -34, 80, 56, 8); c.fill()
    c.set_source_rgb(*[v * (1 - 0.25 * wet) for v in rgb('#e8f4fa')]); rrect(c, -40, -34, 80, 16, 8); c.fill()
    c.set_source_rgba(0.35, 0.55, 0.7, 0.6); c.set_line_width(3); rrect(c, -40, -34, 80, 56, 8); c.stroke()
    if wet > 0.2:
        c.set_source_rgba(0.25, 0.4, 0.55, 0.9); c.set_line_width(3)
        c.move_to(-8, -34); c.line_to(2, -14); c.line_to(-10, 0); c.line_to(0, 22); c.stroke()
    if wet > 0.5:
        c.move_to(22, -34); c.line_to(14, -16); c.line_to(30, -2); c.stroke()
    c.restore()

stars = [(rng.uniform(0, W), rng.uniform(HEAD, 820), rng.uniform(1.2, 2.6)) for _ in range(50)]
def draw_bg(c, t):
    c.set_source_rgb(*rgb('#111a28')); c.rectangle(0, HEAD, W, H - HEAD); c.fill()
    c.set_source_rgba(0.85, 0.88, 0.95, 0.5)
    for x, y, r in stars: c.arc(x, y, r, 0, 2 * math.pi); c.fill()
    c.set_source_rgba(0.4, 0.8, 0.6, 0.07); c.set_line_width(60)   # faint aurora band
    for x in range(0, W + 1, 30): (c.move_to if x == 0 else c.line_to)(x, 560 + 60 * math.sin(x / 210 + t * 0.3))
    c.stroke()
    c.set_source_rgb(*rgb('#e2dcbc')); c.arc(860, 520, 46, 0, 2 * math.pi); c.fill()
    # far snowy mountains + iceberg
    c.set_source_rgb(*rgb('#2a3446')); c.move_to(0, 1219); c.line_to(0, 960); c.line_to(170, 820); c.line_to(330, 980); c.line_to(480, 860); c.line_to(700, 1050); c.line_to(700, 1219); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#3a4658')); c.move_to(170, 820); c.line_to(220, 866); c.line_to(140, 846); c.close_path(); c.fill(); c.move_to(480, 860); c.line_to(530, 905); c.line_to(440, 895); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#34405a')); c.move_to(700, 1219); c.line_to(760, 1000); c.line_to(860, 940); c.line_to(980, 1030); c.line_to(1040, 1219); c.close_path(); c.fill()
    # sea
    c.set_source_rgb(*rgb('#0f2a38')); c.rectangle(0, 1219, W, H - 1219); c.fill()
    c.set_source_rgba(1, 1, 1, 0.05); c.set_line_width(3)
    for yy in range(1260, H, 90):
        for x in range(0, W + 1, 30): (c.move_to if x == 0 else c.line_to)(x, yy + 6 * math.sin(x * 0.02 + t * 1.5 + yy))
        c.stroke()

def draw_rocks(c):
    for (xa, xb, top, sgn) in ((0, BERG_L, 1300, 1), (BERG_R, W, 1300, -1)):   # ice-shelf edges = walls
        c.set_source_rgb(*rgb('#a8c0cc')); c.rectangle(xa, top, xb - xa, H - top); c.fill()
        c.set_source_rgb(*rgb('#8aa4b2'))
        for yy in range(top + 60, H, 140): c.rectangle(xa, yy, xb - xa, 10); c.fill()
        c.set_source_rgb(*rgb('#e6f0f4')); rrect(c, xa - 10, top - 24, xb - xa + 20, 36, 16); c.fill()

def draw_pike_at(c, x, y, ang, t, chomp):   # the angry seal (leaping, nose-first)
    c.save(); c.translate(x, y); c.rotate(ang)
    body, belly = rgb('#6a6a72'), rgb('#9a9aa2')
    c.set_source_rgb(*body)
    c.move_to(150, 0); c.curve_to(150, -48, 40, -60, -60, -40); c.curve_to(-120, -28, -160, -12, -175, 0)
    c.curve_to(-160, 12, -120, 28, -60, 40); c.curve_to(40, 60, 150, 48, 150, 0); c.close_path(); c.fill()
    c.set_source_rgb(*belly); c.save(); c.translate(20, 22); c.scale(110, 20); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    c.set_source_rgb(*rgb('#55555c'))   # tail flippers + front flipper
    c.move_to(-170, 0); c.line_to(-215, -32); c.line_to(-200, 0); c.line_to(-215, 32); c.close_path(); c.fill()
    fl = 0.3 * math.sin(t * 18)
    c.save(); c.translate(40, 34); c.rotate(0.6 + fl); c.save(); c.scale(46, 16); c.arc(1, 0, 1, 0, 2 * math.pi); c.restore(); c.fill(); c.restore()
    c.set_source_rgb(*rgb('#2a2a30')); c.arc(170, -2, 11, 0, 2 * math.pi); c.fill()   # nose
    c.set_source_rgb(*rgb('#141418')); c.arc(118, -22, 9, 0, 2 * math.pi); c.fill()   # eye
    c.set_source_rgb(1, 1, 1); c.arc(121, -25, 3, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#2a2a30')); c.set_line_width(5); c.move_to(100, -38); c.line_to(132, -32); c.stroke()   # grumpy brow
    c.set_source_rgba(0.85, 0.85, 0.85, 0.8); c.set_line_width(2)
    for dy in (-6, 2, 10): c.move_to(160, 6); c.line_to(198, 6 + dy * 1.6); c.stroke()   # whiskers
    o = 2 + 12 * chomp
    c.set_source_rgb(*rgb('#3a1a1e')); c.move_to(140, 14); c.line_to(162, 14 - o * 0.3); c.line_to(162, 14 + o * 0.6); c.close_path(); c.fill()
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
        if abs(t - tb) < 0.5 / FPS and tb <= S.T_RES + 0.01: PS.spawn(bx_(i), TOP + 20, 12, (0.85, 0.95, 1.0) if why == 'pike' else (0.7, 0.85, 0.95), 380, 0.5, grav=1300, r=6)
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
