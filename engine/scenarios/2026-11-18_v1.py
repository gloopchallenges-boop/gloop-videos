"""2026-11-18 v1 — ITEMS LEFT – BEACH BALLS LEFT: the GIANT PUFFERFISH (STYLE-TEST video: bright sunny lagoon,
rule+question card, streak badge, subscribe outro). Gloop is a passive rigid ball (Ball) bouncing on a row of 10
floating beach balls between two sandy banks. Every landing squeezes air out of the ball under him (3 landings =
it goes flat and sinks); a spiky pufferfish leaps out of the lagoon at seeded-random balls (some aimed near him)
and pops the ball with its spikes — a pufferfish that touches Gloop mid-leap bounces off him (real momentum
transfer) and misses. If his bounce comes down over a gap wider than him he drops into the lagoon (= fail).
Timer ends with him still on the balls = win."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the giant pufferfish'
SEED = int(os.environ.get('SEED', 1))
rng = random.Random(SEED)

class S: pass
S.HOOK2 = 'THE GIANT PUFFERFISH?'; S.HOOK2_SIZE = 84; S.FAIL_WORD = 'SPLASH!'
S.CARD = ['Spikes and bounces *POP* the balls', 'Will Gloop *STAY DRY*?']; S.STREAK = int(os.environ.get('STREAK', 2)); S.CTA = True; S.FAIL_SIZE = 150
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
PR = 74   # pufferfish visible radius incl. spikes (drawn at 0.72 scale)
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
            for u in (0,):
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
S.AMB = {'drone': 52, 'wind': 0.015}

def draw_bar(c, t, f):
    n = LEFT[f]; recent = any(tb <= t < tb + 0.35 for (tb, _, _) in BREAKS)
    bx = bar(c, n / NB, f'BALLS LEFT: {n}', rgb('#7dff8a') if n > 6 else (rgb('#ffd84a') if n > 2 else rgb('#ff4d4d')), 0.15 if recent else 0, bw=660, x_off=36)
    c.save(); c.translate(bx - 52, 234); draw_duck(c, 0, 0, 0.5, 0); c.restore()
S.draw_bar = draw_bar


BALLC = [('#e84a5f', '#ffffff', '#3a7bd5', '#ffd84a'), ('#3a7bd5', '#ffffff', '#4ac07a', '#ffffff'), ('#e070a0', '#ffffff', '#6be0ff', '#ffffff')]
def draw_duck(c, x, y, s, wet, i=0):   # a floating beach ball; wet = air lost 0..1 -> squashed & duller
    c.save(); c.translate(x, y); c.scale(s, s * (1 - 0.32 * wet))
    dk = 1 - 0.18 * wet; cols = BALLC[i % 3]; r = 32
    for k in range(6):
        c.move_to(0, 0); c.arc(0, 0, r, -math.pi / 2 + k * math.pi / 3, -math.pi / 2 + (k + 1) * math.pi / 3); c.close_path()
        c.set_source_rgb(*[v * dk for v in rgb(cols[k % 4])]); c.fill()
    c.set_source_rgb(*[v * dk for v in rgb('#ffffff')]); c.arc(0, 0, 7, 0, 2 * math.pi); c.fill()
    c.set_source_rgba(0, 0, 0, 0.25); c.set_line_width(2.5); c.arc(0, 0, r, 0, 2 * math.pi); c.stroke()
    c.set_source_rgba(1, 1, 1, 0.45); c.save(); c.translate(-12, -14); c.scale(8, 5); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    c.restore()

clouds = [(rng.uniform(0, W), rng.uniform(640, 900), rng.uniform(0.7, 1.2), rng.uniform(8, 16)) for _ in range(4)]
def draw_bg(c, t):
    c.set_source_rgb(*rgb('#7ec8f0')); c.rectangle(0, HEAD, W, H - HEAD); c.fill()   # flat sunny sky
    c.set_source_rgb(*rgb('#a8dcf6')); c.rectangle(0, 900, W, 320); c.fill()
    c.set_source_rgb(*rgb('#fff6c8')); c.arc(860, 700, 56, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(1, 1, 1)
    for (x, y, s, v) in clouds:
        xx = (x + v * t) % (W + 300) - 150
        for (dx, dy, rr) in ((0, 0, 40), (40, -16, 48), (86, 0, 38)):
            c.arc(xx + dx * s, y + dy * s, rr * s, 0, 2 * math.pi); c.fill()
    # far island with palms
    c.set_source_rgb(*rgb('#7fc88a')); c.move_to(250, 1219); c.curve_to(330, 1130, 560, 1120, 680, 1219); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#8a6a4a')); c.set_line_width(9); c.move_to(470, 1150); c.curve_to(480, 1100, 470, 1070, 490, 1040); c.stroke()
    c.set_source_rgb(*rgb('#3f9a5a'))
    for a in (-2.6, -2.0, -1.2, -0.6):
        c.save(); c.translate(490, 1040); c.rotate(a); c.scale(60, 13); c.arc(1, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    # lagoon
    c.set_source_rgb(*rgb('#3fb8c8')); c.rectangle(0, 1219, W, H - 1219); c.fill()
    c.set_source_rgba(1, 1, 1, 0.35)
    for i in range(5): c.rectangle(860 - 60 + 10 * math.sin(t * 2 + i), 1235 + i * 22, 120 - i * 12, 5); c.fill()
    c.set_source_rgba(1, 1, 1, 0.16); c.set_line_width(3)
    for yy in range(1280, H, 90):
        for x in range(0, W + 1, 30): (c.move_to if x == 0 else c.line_to)(x, yy + 6 * math.sin(x * 0.02 + t * 1.5 + yy))
        c.stroke()

def draw_rocks(c):
    for (xa, xb, top, sgn) in ((0, BERG_L, 1300, 1), (BERG_R, W, 1300, -1)):   # sandy banks = walls
        c.set_source_rgb(*rgb('#e8d4a0')); c.rectangle(xa, top, xb - xa, H - top); c.fill()
        c.set_source_rgb(*rgb('#d8c08a'))
        for yy in range(top + 60, H, 120): c.rectangle(xa, yy, xb - xa, 8); c.fill()
        c.set_source_rgb(*rgb('#f2e2b4')); rrect(c, xa - 10, top - 18, xb - xa + 20, 30, 12); c.fill()
        px = (xa + xb) / 2   # palm trunk + leaves
        c.set_source_rgb(*rgb('#9a7650')); c.set_line_width(14); c.move_to(px, top - 10); c.curve_to(px + 10 * sgn, top - 160, px + 30 * sgn, top - 260, px + 46 * sgn, top - 330); c.stroke()
        c.set_source_rgb(*rgb('#3f9a5a'))
        for a in (-2.8, -2.2, -1.6, -1.0, -0.4):
            c.save(); c.translate(px + 46 * sgn, top - 330); c.rotate(a); c.scale(80, 16); c.arc(1, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
        c.set_source_rgb(*rgb('#e070a0'))   # small pink shell
        c.save(); c.translate(px - 20 * sgn, top - 20); c.scale(14, 9); c.arc(0, 0, 1, math.pi, 2 * math.pi); c.restore(); c.fill()

def draw_pike_at(c, x, y, ang, t, chomp):   # the giant pufferfish (leaping, spikes out)
    c.save(); c.translate(x, y); c.rotate(ang); c.scale(0.72, 0.72)
    body, belly, dark = rgb('#a8c86a'), rgb('#f4f0d0'), rgb('#5a7a3a')
    puff = 1 + 0.12 * chomp
    c.save(); c.scale(puff, puff)
    c.set_source_rgb(*dark)
    for k in range(18):   # spikes
        a = k * 2 * math.pi / 18
        c.move_to(78 * math.cos(a - 0.12), 78 * math.sin(a - 0.12)); c.line_to(104 * math.cos(a), 104 * math.sin(a)); c.line_to(78 * math.cos(a + 0.12), 78 * math.sin(a + 0.12)); c.close_path(); c.fill()
    c.set_source_rgb(*body); c.arc(0, 0, 82, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*belly); c.save(); c.translate(0, 30); c.scale(66, 44); c.arc(0, 0, 1, 0, math.pi); c.restore(); c.fill()
    c.set_source_rgb(*dark)
    for (sx, sy) in ((-30, -40), (-50, -6), (-10, -56), (-36, 20)): c.arc(sx, sy, 7, 0, 2 * math.pi); c.fill()
    c.move_to(-80, 0); c.line_to(-128, -30 + 8 * math.sin(t * 12)); c.line_to(-128, 30 + 8 * math.sin(t * 12)); c.close_path(); c.fill()   # tail
    c.set_source_rgb(1, 1, 1); c.arc(36, -26, 18, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(0.05, 0.05, 0.05); c.arc(42, -26, 9, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*dark); c.set_line_width(6); c.move_to(18, -50); c.line_to(54, -42); c.stroke()
    c.set_source_rgb(*rgb('#c85a6a')); c.save(); c.translate(80, 12); c.scale(10, 8 + 6 * chomp); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()   # pouty mouth
    c.restore(); c.restore()

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
            c.save(); c.translate(x, y); c.scale(1, 1 - 0.18 * wet); draw_duck(c, 0, 0, 1.15, wet, i); c.restore()
        else:
            br = [b for b in BREAKS if b[1] == i]
            if br and t - br[0][0] < 0.6:
                k = (t - br[0][0]) / 0.6; c.set_source_rgba(0.8, 0.85, 0.85, 0.5 * (1 - k)); c.set_line_width(4)
                c.save(); c.translate(x, POND); c.scale(1, 0.3); c.arc(0, 0, 20 + 90 * k, 0, 2 * math.pi); c.restore(); c.stroke()
                if br[0][2] == 'pike':   # popped by the spikes: shrivels in a flash
                    kk = min(1, (t - br[0][0]) / 0.22)
                    if kk < 1: c.save(); c.translate(x, y); c.rotate(1.5 * kk); c.scale(1 - 0.85 * kk, 1 - 0.85 * kk); draw_duck(c, 0, 0, 1.15, 1, i); c.restore()
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
        if abs(t - tb) < 0.5 / FPS and tb <= S.T_RES + 0.01: PS.spawn(bx_(i), TOP + 20, 12, (1.0, 1.0, 1.0) if why == 'pike' else (0.85, 0.95, 1.0), 380, 0.5, grav=1300, r=6)
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
