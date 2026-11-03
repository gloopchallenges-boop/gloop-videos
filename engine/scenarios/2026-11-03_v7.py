"""2026-11-03 v7 — ITEMS LEFT – BALLOONS LEFT: the PORCUPINE. Gloop is a passive rigid ball (Ball)
bouncing on a row of 10 balloons tied between two canyon ledges over a cactus patch. Every landing
squeezes the balloon under him (2 squeezes = pop); a porcupine on the right ledge flicks quills at
seeded-random balloons (some aimed near him) — a quill that reaches its balloon pops it; a quill that
touches Gloop on the way bounces off him (and shoves him). If his bounce comes down over a gap he falls
onto the cactus patch (= fail). Timer ends with him still on the balloons = win."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the porcupine'
SEED = int(os.environ.get('SEED', 16))
rng = random.Random(SEED)

class S: pass
S.HOOK2 = 'THE PORCUPINE?'; S.HOOK2_SIZE = 96; S.FAIL_WORD = 'OUCH!'; S.FAIL_SIZE = 160
S.T_START = HOOK_T; S.TL = 12.0; S.T_END = S.T_START + S.TL
TOP = 1440; WATER = 1800; R = 58; BERG_L, BERG_R = 110, 970; XMIN, XMAX = BERG_L + R, BERG_R - R
NB = 10; BW = (BERG_R - BERG_L) / NB; HP = int(os.environ.get('HP', 3))

class IceRow:
    soft = False
    def __init__(self): self.alive = [True] * NB; self.hp = [HP] * NB; self.over_water = False
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
        return TOP + 12 if gap < 2 * R * 0.95 else WATER - R * 0.5 + 400   # a one-block gap is narrower than Gloop: he lands on its edges
    def slope(self, x, d=30): return 0.0
    def dig(self, *a): pass
ICE = IceRow()
SEA = Terrain(WATER - R * 0.2, seed=SEED, bumps=0, amp=0, soft=False)

PORC = (985, 1010); QF = 0.6   # quill flight time
RAMS = []; t = 0.5
while t < S.T_END + 1:
    RAMS.append({'t': t, 'aim': rng.random() < float(os.environ.get('AIM', 0.25)), 'i': rng.randrange(NB)}); t += rng.uniform(*map(float, os.environ.get('GAP', '1.6,2.8').split(',')))
def bx_(i): return BERG_L + (i + 0.5) * BW
def quill_pos(r, t):
    k = clamp((t - (r['t'] - QF)) / QF, 0, 1); tx, ty = bx_(r['i']), TOP + 10
    return lerp(PORC[0], tx, k), lerp(PORC[1], ty, k) - 260 * 4 * k * (1 - k)
def quill_vel(r, t):
    a = quill_pos(r, t - 0.01); b = quill_pos(r, t + 0.01); return (b[0] - a[0]) / 0.02, (b[1] - a[1]) / 0.02
DEFL = []
N0 = int(40 * FPS); GX, GYS, LEFT, ALIVE, HPS = [], [], [], [], []
ball = Ball(rng.uniform(350, 730), ICE, R=R, seed=SEED, xmin=XMIN, xmax=XMAX, hop=rng.uniform(220, 280))
T_FAIL = None; BREAKS = []; CRACKS = []; nl = 0
for f in range(N0):
    t = f / FPS
    live = T_FAIL is None and S.T_START <= t < S.T_END
    for r in RAMS:
        if abs(t - (r['t'] - QF)) < 0.5 / FPS and r['aim']: r['i'] = ICE.idx(ball.x + rng.uniform(-BW, BW))
        if abs(t - r['t']) < 0.5 / FPS and not r.get('defl'):
            i = r['i']
            if ICE.alive[i] and live: ICE.alive[i] = False; BREAKS.append((t, i, 'quill')); r['did'] = True
    px, py = ball.x, ball.y
    ball.step(t)
    for r in RAMS:   # swept: a quill touching Gloop bounces off him (real momentum transfer)
        if r.get('defl') or not (r['t'] - QF <= t < r['t'] + 1 / FPS): continue
        for k in range(1, 9):
            ts = t - 1 / FPS + k / (8 * FPS)
            if ts < r['t'] - QF or ts > r['t']: continue
            qx, qy = quill_pos(r, ts); bx, by = lerp(px, ball.x, k / 8), lerp(py, ball.y, k / 8)
            d = math.hypot(bx - qx, by - qy)
            if d < R + 14:
                nx, ny = (bx - qx) / (d or 1), (by - qy) / (d or 1); vqx, vqy = quill_vel(r, ts)
                rel = (vqx - ball.vx) * nx + (vqy - ball.vy) * ny
                if rel > 0: j = min(0.5 * rel, 450); ball.vx += j * nx; ball.vy += j * ny
                r['defl'] = ts; r['dpos'] = (qx, qy); DEFL.append((ts, qx, qy)); break
    while nl < len(ball.landings):
        tl, xl, imp = ball.landings[nl]; nl += 1
        if T_FAIL is None and S.T_START <= tl < S.T_END and BERG_L < xl < BERG_R:
            i = ICE.idx(xl)
            if ICE.alive[i]:
                ICE.hp[i] -= 1; CRACKS.append((tl, i, ICE.hp[i]))
                if ICE.hp[i] <= 0: ICE.alive[i] = False; BREAKS.append((tl, i, 'crack'))
    if T_FAIL is None and ball.y > TOP + 10 and live: T_FAIL = t
    if T_FAIL is not None and ball.T is ICE:
        ball.T = SEA; ball.vmin = 0; ball.e = 0.1; ball.base_h = 0
    if ball.T is SEA: ball.vx *= 0.85
    GX.append(ball.x); GYS.append(ball.y); LEFT.append(sum(ICE.alive)); ALIVE.append(list(ICE.alive)); HPS.append(list(ICE.hp))
S.OUTCOME = 'fail' if T_FAIL else 'win'
S.T_RES = T_FAIL if T_FAIL else S.T_END
S.GRAB = (540, TOP - R)
END = S.END = Ending(S)
gi = min(int(END.T_GRAB * FPS), N0 - 1); S.GRAB = (GX[gi], GYS[gi])
S.events = [[0.05, 'rumble', 1.0]]
for r in RAMS:
    if r['t'] - QF < S.T_RES: S.events.append([r['t'] - QF, 'whoosh'])
for (tb, i, why) in BREAKS: S.events.append([tb, 'pop'])
for (td, qx, qy) in DEFL:
    if td < S.T_RES + 0.5: S.events.append([td, 'clink'])
for (tc, i, hp) in CRACKS:
    if hp > 0: S.events.append([tc, 'creak'])
for (tl, xl, imp) in ball.landings:
    if tl < S.T_RES + 1.5: S.events.append([tl, 'hop'])
for tw in ball.walls:
    if tw < S.T_RES: S.events.append([tw, 'thump', 0.3])
TLAND = None
if T_FAIL: S.events += [[T_FAIL + 0.3, 'thump', 1.0], [T_FAIL + 0.35, 'crackle']]
S.AMB = {'drone': 50, 'wind': 0.03}

def draw_bar(c, t, f):
    n = LEFT[f]; recent = any(tb <= t < tb + 0.35 for (tb, _, _) in BREAKS)
    bx = bar(c, n / NB, f'BALLOONS LEFT: {n}', rgb('#7dff8a') if n > 6 else (rgb('#ffd84a') if n > 2 else rgb('#ff4d4d')), 0.15 if recent else 0, bw=660, x_off=36)
    c.save(); c.translate(bx - 52, 226); c.set_source_rgb(*rgb('#e05a6a')); c.save(); c.scale(22, 27); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    c.move_to(-6, 30); c.line_to(6, 30); c.line_to(0, 24); c.close_path(); c.fill(); c.set_source_rgba(1, 1, 1, 0.5); c.arc(-8, -10, 6, 0, 2 * math.pi); c.fill(); c.restore()
S.draw_bar = draw_bar

stars = [(rng.uniform(0, W), rng.uniform(HEAD, 1000), rng.uniform(1.2, 2.6)) for _ in range(60)]
BCOL = ['#c8505e', '#d08a3a', '#5a8ac8', '#7ab05a', '#a066b8']
CACTI = [(rng.uniform(BERG_L + 40, BERG_R - 40), rng.uniform(0.7, 1.1)) for _ in range(7)]
def draw_bg(c, t):
    c.set_source_rgb(*rgb('#1c1626')); c.rectangle(0, HEAD, W, H - HEAD); c.fill()
    c.set_source_rgba(0.9, 0.85, 0.75, 0.5)
    for x, y, r in stars: c.arc(x, y, r, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#e6d6ae')); c.arc(300, 560, 52, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#2a1f2c'))   # far mesas
    c.move_to(0, 1300); c.line_to(0, 1050); c.line_to(220, 1050); c.line_to(260, 1120); c.line_to(560, 1120); c.line_to(600, 980); c.line_to(820, 980); c.line_to(860, 1100); c.line_to(W, 1100); c.line_to(W, 1300); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#3a2a24')); c.rectangle(0, WATER - 10, W, H - WATER + 10); c.fill()   # canyon floor
    c.set_source_rgb(*rgb('#4a3428')); c.rectangle(0, WATER - 10, W, 14); c.fill()
    for (x, s_) in CACTI:   # flat cactus patch
        c.set_source_rgb(*rgb('#3f6b44')); hh = 150 * s_
        rrect(c, x - 18, WATER - hh, 36, hh + 10, 18); c.fill()
        rrect(c, x - 52, WATER - hh * 0.7, 22, hh * 0.35, 11); c.fill(); rrect(c, x - 52, WATER - hh * 0.45, 40, 18, 9); c.fill()
        rrect(c, x + 30, WATER - hh * 0.85, 22, hh * 0.4, 11); c.fill(); rrect(c, x + 12, WATER - hh * 0.5, 40, 18, 9); c.fill()
        c.set_source_rgb(*rgb('#c8d8a0')); c.set_line_width(2)
        for k in range(5):
            yy = WATER - hh + 20 + k * hh / 6; c.move_to(x - 18, yy); c.line_to(x - 28, yy - 6); c.move_to(x + 18, yy); c.line_to(x + 28, yy - 6); c.stroke()

def draw_bergs(c):
    for (xa, xb) in ((0, BERG_L), (BERG_R, W)):   # canyon ledges = walls
        c.set_source_rgb(*rgb('#6b4a35')); c.rectangle(xa, 1000 if xa == 0 else 1060, xb - xa, H); c.fill()
        c.set_source_rgb(*rgb('#5a3d2c'))
        for yy in range(1080, H, 90): c.rectangle(xa, yy, xb - xa, 8); c.fill()
        c.set_source_rgb(*rgb('#7d5940')); c.rectangle(xa, (1000 if xa == 0 else 1060), xb - xa, 14); c.fill()
        c.set_source_rgb(*rgb('#8a8070')); c.arc(BERG_L - 18 if xa == 0 else BERG_R + 18, TOP + 4, 12, 0, 2 * math.pi); c.fill()   # string pegs

def draw_porc(c, t):
    x, y = PORC; fl = any(r['t'] - QF - 0.15 <= t < r['t'] - QF + 0.1 for r in RAMS)
    c.save(); c.translate(x + 40, y + 40); c.scale(1.3, 1.3)
    c.set_source_rgb(*rgb('#3a2e28'))
    for k in range(13):   # quills
        a = math.pi * (0.95 + k / 12 * 0.9) + (0.08 * math.sin(t * 30) if fl else 0); L = 95 + 15 * (k % 2)
        c.set_line_width(7); c.move_to(0, 0); c.line_to(math.cos(a) * L, math.sin(a) * L); c.stroke()
    c.set_source_rgb(*rgb('#6b5544')); c.save(); c.scale(80, 52); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    c.set_source_rgb(*rgb('#a08870')); c.save(); c.translate(-62, 10); c.scale(34, 26); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    c.set_source_rgb(0.08, 0.06, 0.05); c.arc(-90, 6, 8, 0, 2 * math.pi); c.fill(); c.arc(-62, -2, 6, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#3a2e28')); c.set_line_width(5); c.move_to(-74, -14); c.line_to(-52, -10); c.stroke()
    c.restore()

def draw_quills(c, t):
    for r in RAMS:
        if not (r['t'] - QF <= t < r['t']) or r['t'] - QF > S.T_RES: continue
        if r.get('defl') and t >= r['defl']:
            k = t - r['defl']; qx, qy = r['dpos']; qx += 200 * k; qy += -200 * k + 1600 * k * k; ang = k * 14
        else:
            qx, qy = quill_pos(r, t); vx, vy = quill_vel(r, t); ang = math.atan2(vy, vx)
        c.save(); c.translate(qx, qy); c.rotate(ang)
        c.set_source_rgb(*rgb('#e8e0cc')); c.set_line_width(9); c.move_to(-50, 0); c.line_to(22, 0); c.stroke()
        c.set_source_rgb(*rgb('#3a2e28')); c.move_to(-50, 0); c.line_to(-22, 0); c.stroke()
        c.set_source_rgb(*rgb('#e8e0cc')); c.move_to(22, -6); c.line_to(40, 0); c.line_to(22, 6); c.close_path(); c.fill()
        c.restore()
    for r in RAMS:
        if r.get('defl') and r['defl'] <= t < r['defl'] + 0.6:
            k = t - r['defl']; qx, qy = r['dpos']; qx += 200 * k; qy += -200 * k + 1600 * k * k
            c.save(); c.translate(qx, qy); c.rotate(k * 14); c.set_source_rgb(*rgb('#e8e0cc')); c.set_line_width(6); c.move_to(-30, 0); c.line_to(26, 0); c.stroke(); c.restore()

def draw_ice(c, t, f):
    al = ALIVE[f]; hp = HPS[f]
    for i in range(NB):
        x = BERG_L + (i + 0.5) * BW; bob = 3 * math.sin(t * 2 + i * 1.3); sq = 1 - 0.12 * (HP - hp[i])
        c.set_source_rgb(*rgb('#cfc8b8')); c.set_line_width(2); c.move_to(x, TOP + 50 + bob); c.line_to(x + 6 * math.sin(t + i), TOP + 120); c.stroke()
        if al[i]:
            c.set_source_rgb(*rgb(BCOL[i % 5])); c.save(); c.translate(x, TOP + 22 + bob + 6 * (1 - sq)); c.scale(BW * 0.52, 34 * sq); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
            c.move_to(x - 7, TOP + 58 + bob); c.line_to(x + 7, TOP + 58 + bob); c.line_to(x, TOP + 50 + bob); c.close_path(); c.fill()
            c.set_source_rgba(1, 1, 1, 0.35); c.arc(x - 16, TOP + 10 + bob, 7, 0, 2 * math.pi); c.fill()
        else:
            br = [b for b in BREAKS if b[1] == i]
            if br and t - br[0][0] < 0.4:
                k = (t - br[0][0]) / 0.4; c.set_source_rgba(*rgb(BCOL[i % 5]), 1 - k)
                for j in range(6):
                    a = j * 1.05; c.arc(x + math.cos(a) * 60 * k, TOP + 22 + math.sin(a) * 40 * k, 9 * (1 - k) + 2, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#cfc8b8')); c.set_line_width(3); c.move_to(BERG_L - 18, TOP + 4)
    for i in range(NB): c.line_to(BERG_L + (i + 0.5) * BW, TOP + 54)
    c.line_to(BERG_R + 18, TOP + 4); c.stroke()

PS = Particles(9)
def render(f, c):
    t = f / FPS; fi = min(f, len(GX) - 1); shake = (0, 0)
    for (tb, i, why) in BREAKS:
        if tb <= t < tb + 0.15 and why == 'orca': shake = (rng.uniform(-4, 4), rng.uniform(-4, 4))
    c.save(); c.translate(*shake)
    draw_bg(c, t); draw_bergs(c); draw_porc(c, t)
    fell = T_FAIL is not None and t >= T_FAIL
    if END.carried(t) or t >= END.T_GRAB: gx, gy = (END.carry_xy(t) if END.carried(t) else S.GRAB)
    else: gx, gy = GX[fi], GYS[fi]
    p = LEFT[fi] / NB
    danger = any(r['t'] - QF <= t < r['t'] and abs(bx_(r['i']) - GX[fi]) < 220 for r in RAMS)
    mood = 'happy' if (t >= S.T_END and S.OUTCOME == 'win') else ('scared' if fell or danger or p < 0.4 else 'worried')
    draw_ice(c, t, fi)
    prick = fell and gy > WATER - R * 1.6
    draw_blob(c, t, gx, gy, mood, 0, R=R, dizzy=prick and t > T_FAIL + 0.6)
    if prick:
        c.set_source_rgb(*rgb('#c8d8a0')); c.set_line_width(3)
        for j in range(7):
            a = -math.pi * (0.15 + 0.7 * j / 6); c.move_to(gx + math.cos(a) * R * 0.8, gy + math.sin(a) * R * 0.8 + 30); c.line_to(gx + math.cos(a) * (R + 18), gy + math.sin(a) * (R + 18) + 30); c.stroke()
    draw_quills(c, t)
    for (tb, i, why) in BREAKS:
        if abs(t - tb) < 0.5 / FPS: PS.spawn(bx_(i), TOP + 20, 12, rgb(BCOL[i % 5]), 380, 0.5, grav=900, r=6)
    for (td, qx, qy) in DEFL:
        if abs(t - td) < 0.5 / FPS: PS.spawn(qx, qy, 10, (0.85, 0.8, 0.7), 300, 0.4, grav=600, r=6)
    PS.draw(c)
    END.draw_claw(c, t)
    c.restore()
    END.header(c, t, fi)

if __name__ == '__main__':
    if sys.argv[1] == 'sim':
        e = int(S.T_RES * FPS) - 1
        print(SEED, S.OUTCOME, round(S.T_RES - S.T_START, 2), 'left', LEFT[e], 'breaks', [(round(b[0] - S.T_START, 1), b[2][0]) for b in BREAKS], 'defl', len(DEFL), 'dur', S.DUR); sys.exit()
    run(S, render)
