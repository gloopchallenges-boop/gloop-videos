"""2026-11-11 v3 — RACE – GAP m: the GIANT TRACTOR TIRE. Gloop is a passive rigid ball (Ball) bouncing down a
sloping desert canyon road at night (the slope is what carries him forward — bounces reflect off the real ground
slope). A giant runaway tractor tire rolls after him at a seeded-random, surging speed. Soft sand drifts kill his
speed when he lands in them; rocks deflect his bounces (sometimes backwards).
Header: SURVIVE timer + GAP bar (distance between the tire and Gloop). GAP 0 = run over (cartoony: he pops back
up dizzy)."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the giant tractor tire'
SEED = int(os.environ.get('SEED', 15))
rng = random.Random(SEED)

class S: pass
S.HOOK1 = 'WILL GLOOP OUTRUN'; S.HOOK2 = 'THE GIANT TRACTOR TIRE?'; S.HOOK2_SIZE = 74; S.FAIL_WORD = 'RUN OVER!'; S.FAIL_SIZE = 130
S.T_START = HOOK_T; S.TL = float(os.environ.get('TL', 12.5)); S.T_END = S.T_START + S.TL
R = 58; BR = 175; SLOPE = 0.07; L = 12000; PPM = 100.0; SX = 650   # Gloop's screen x (camera follows)
X0 = 900.0; GAP0 = 760.0
VB = (float(os.environ.get('VB0', 405)), float(os.environ.get('VB1', 530)))

class WTerrain:
    """World-length ground (rock floor, not soft)."""
    def __init__(self):
        self.xs = np.arange(L + 1, dtype=float); self.h = 1600 + SLOPE * self.xs; self.soft = False
        self.rocks = []
        x = X0 + 500
        while x < L - 400:
            x += rng.uniform(450, 1100); a = rng.uniform(12, 20); w = rng.uniform(45, 70)
            self.rocks.append((x, a, w)); self.h -= a * np.exp(-((self.xs - x) / w) ** 2)
        self.base = 1600
    def y(self, x):
        x = clamp(x, 0, L - 1); i = int(x); f = x - i
        return self.h[i] * (1 - f) + self.h[i + 1] * f
    def slope(self, x, d=30): return (self.y(x + d) - self.y(x - d)) / (2 * d)
    def dig(self, *a): pass
TER = WTerrain()
MUD = []; x = X0 + 700
while x < L - 400:
    x += rng.uniform(700, 1400); w = rng.uniform(150, 230)
    if all(abs(x - rx) > w / 2 + 80 for rx, _, _ in TER.rocks): MUD.append((x - w / 2, x + w / 2))
def in_mud(x): return any(a <= x <= b for a, b in MUD)

SEGS = []; t = 0.0
while t < 40: d = rng.uniform(0.7, 1.8); SEGS.append((t, rng.uniform(*VB))); t += d
def vb_target(t):
    v = SEGS[0][1]
    for (t0, vv) in SEGS:
        if t0 <= t: v = vv
    return v

N0 = int(30 * FPS); GX, GYS, BX, GAP, CAMX, CAMY = [], [], [], [], [], []
ball = Ball(X0, TER, R=R, seed=SEED, vx=380, hop=rng.uniform(210, 250), xmin=-1e9, xmax=1e9)
bx = X0 - GAP0; bv = 420.0; T_FAIL = None; SPL = []; nl = 0; MUDHITS = 0
camx = X0 - SX; camy = 0.0; FREEZE = None
for f in range(N0):
    t = f / FPS
    bv += (vb_target(t) - bv) * 2.0 / FPS
    bx += bv / FPS
    if T_FAIL is None:
        ball.step(t)
        while nl < len(ball.landings):
            tl, xl, imp = ball.landings[nl]; nl += 1
            if in_mud(xl):
                ball.vx *= 0.5; SPL.append((tl, xl))
                if S.T_START <= tl < S.T_END: MUDHITS += 1
        gap = (ball.x - R * 0.85) - (bx + BR * 0.92)
        if S.T_START <= t < S.T_END and gap <= 0: T_FAIL = t; FX = ball.x
        if t < S.T_START and gap < 120: bx = ball.x - R * 0.85 - BR * 0.92 - 120   # boulder can't matter before the start
    gap = (ball.x - R * 0.85) - (bx + BR * 0.92)
    GX.append(ball.x); GYS.append(ball.y); BX.append(bx); GAP.append(max(0.0, gap) / PPM if T_FAIL is None or t < T_FAIL else 0.0)
    if T_FAIL is None and (FREEZE is None):
        camx += ((ball.x - SX) - camx) * 0.18; camy += ((TER.y(ball.x) - 1600) - camy) * 0.12
    CAMX.append(camx); CAMY.append(camy)
    if f == int((S.T_END + 1.3) * FPS) or (T_FAIL is not None and FREEZE is None): FREEZE = t
S.OUTCOME = 'fail' if T_FAIL else 'win'
S.T_RES = T_FAIL if T_FAIL else S.T_END
S.GRAB = (540, 1400)
END = S.END = Ending(S)
# camera follows Gloop until the claw grabs him (win) / until the boulder flattens him (fail)
fz = int(END.T_GRAB * FPS) if not T_FAIL else int(T_FAIL * FPS)
for i in range(fz, len(CAMX)): CAMX[i] = CAMX[fz]; CAMY[i] = CAMY[fz]
gi = min(int(END.T_GRAB * FPS), N0 - 1)
if T_FAIL:
    fi0 = int(T_FAIL * FPS); FY = TER.y(FX) - R
    S.GRAB = (FX - CAMX[fi0], FY - CAMY[fi0])
    POP = next((i / FPS - T_FAIL for i in range(fi0, N0) if BX[i] - BR > FX + R * 1.3), 1.2) + 0.15
else:
    S.GRAB = (GX[gi] - CAMX[gi], GYS[gi] - CAMY[gi])
S.events = [[0.0, 'rumble', 1.5]]
for (t0, v) in SEGS:
    if 0 < t0 < S.T_RES + 1: S.events.append([t0, 'rumble', 1.0]); S.events.append([t0 + 0.1, 'creak'])
for (tl, xl, imp) in ball.landings:
    if tl < S.T_RES + 1.3: S.events.append([tl, 'hop'])
for (ts, xs) in SPL:
    if ts < S.T_RES + 1.3: S.events.append([ts, 'thump', 0.5])
if T_FAIL: S.events += [[T_FAIL, 'crash'], [T_FAIL + 0.05, 'thump', 1.0], [T_FAIL + POP, 'pop']]
S.AMB = {'drone': 42, 'rumble': 0.06}

def draw_bar(c, t, f):
    g = GAP[f]; p = clamp(g / (GAP0 / PPM), 0, 1)
    bx_ = bar(c, p, f'GAP {g:.1f} m', good_bad_col(p), 0, bw=620, x_off=40)
    c.set_source_rgb(*rgb('#1e1e22')); c.arc(bx_ - 50, 231, 22, 0, 2 * math.pi); c.fill()   # tiny tire icon
    c.set_source_rgb(*rgb('#b89a3a')); c.arc(bx_ - 50, 231, 10, 0, 2 * math.pi); c.fill()
S.draw_bar = draw_bar

# ---- flat muted desert canyon road ----
POSTS = [x for x in range(300, L, 600)]
def draw_world(c, t, f):
    cx, cy = CAMX[f], CAMY[f]
    c.set_source_rgb(*rgb('#141628')); c.rectangle(0, HEAD, W, H - HEAD); c.fill()
    for i in range(16):
        sx = (i * 263 - cx * 0.05) % W; sy = HEAD + 60 + (i * 157) % 500
        c.set_source_rgba(1, 1, 0.9, 0.4 + 0.3 * math.sin(t * 2 + i)); c.arc(sx, sy, 3, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#e6dfc4')); c.arc(820 - (cx * 0.02) % 60, 520, 54, 0, 2 * math.pi); c.fill()
    # far mesas (parallax 0.15) and nearer canyon wall (parallax 0.35)
    c.set_source_rgb(*rgb('#2a2230'))
    for i in range(12):
        sx = (i * 420 - cx * 0.15) % (W + 600) - 300; w = 220 + (i * 53) % 160; hh = 220 + (i * 71) % 180
        c.move_to(sx - w / 2 - 40, 1300 - cy * 0.2); c.line_to(sx - w / 2, 1300 - hh - cy * 0.2); c.line_to(sx + w / 2, 1300 - hh - cy * 0.2); c.line_to(sx + w / 2 + 40, 1300 - cy * 0.2); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#3a2c2c'))
    for i in range(18):
        sx = (i * 290 - cx * 0.35) % (W + 400) - 200; hh = 160 + (i * 97) % 220
        c.save(); c.translate(sx, 1420 - cy * 0.4); c.scale(170 + (i * 37) % 80, hh); c.arc(0, 0, 1, math.pi, 2 * math.pi); c.restore(); c.fill()
    c.rectangle(0, 1418 - cy * 0.4, W, H); c.fill()
    # cacti + wooden road posts on the slope
    for tx in POSTS:
        sx = tx - cx
        if -150 < sx < W + 150:
            gy = TER.y(tx) - cy
            if (tx // 600) % 2 == 0:
                c.set_source_rgb(*rgb('#2e4a34')); rrect(c, sx - 18, gy - 260, 36, 260, 18); c.fill()
                rrect(c, sx - 70, gy - 190, 26, 90, 13); c.fill(); rrect(c, sx - 70, gy - 124, 60, 24, 12); c.fill()
                rrect(c, sx + 44, gy - 220, 26, 80, 13); c.fill(); rrect(c, sx + 10, gy - 164, 60, 24, 12); c.fill()
            else:
                c.set_source_rgb(*rgb('#5a4430')); c.rectangle(sx - 8, gy - 120, 16, 120); c.fill()
                c.set_source_rgb(*rgb('#c8a040')); c.save(); c.translate(sx, gy - 140); c.rotate(math.pi / 4); c.rectangle(-28, -28, 56, 56); c.restore(); c.fill()
                c.set_source_rgb(*rgb('#2a2018')); c.set_line_width(5); c.move_to(sx - 12, gy - 152); c.line_to(sx + 12, gy - 128); c.stroke()
    # ground + road
    x0 = int(max(0, cx - 20)); x1 = int(min(L - 1, cx + W + 20))
    c.move_to(x0 - cx, H + 10)
    for x in range(x0, x1 + 1, 6): c.line_to(x - cx, TER.h[x] - cy)
    c.line_to(x1 - cx, H + 10); c.close_path(); c.set_source_rgb(*rgb('#4a3a30')); c.fill()
    c.set_source_rgb(*rgb('#5e4c3e')); c.set_line_width(8)
    for x in range(x0, x1 + 1, 6): (c.move_to if x == x0 else c.line_to)(x - cx, TER.h[x] - cy + 2)
    c.stroke()
    c.set_source_rgba(0, 0, 0, 0.16); c.set_line_width(3)
    for k in range(1, 6):
        for x in range(x0, x1 + 1, 30): (c.move_to if x == x0 else c.line_to)(x - cx, TER.h[x] - cy + k * 70)
        c.stroke()
    c.set_source_rgba(0.85, 0.78, 0.5, 0.5)   # dashed road line
    for k in range(int(x0 // 120), int(x1 // 120) + 1):
        wx = k * 120; c.save(); c.translate(wx - cx, 1600 + SLOPE * wx - cy + 40); c.rotate(math.atan(SLOPE)); c.rectangle(0, 0, 60, 7); c.restore(); c.fill()
    # soft sand drifts (sticky)
    for a, b in MUD:
        if b - cx > -50 and a - cx < W + 50:
            m = (a + b) / 2; c.set_source_rgb(*rgb('#8a7050'))
            c.save(); c.translate(m - cx, TER.y(m) - cy + 4); c.rotate(math.atan(SLOPE)); c.scale((b - a) / 2, 30); c.arc(0, 0, 1, math.pi, 2 * math.pi); c.restore(); c.fill()
            c.set_source_rgb(*rgb('#9e8460')); c.save(); c.translate(m - cx - 20, TER.y(m) - cy - 6); c.rotate(math.atan(SLOPE)); c.scale((b - a) / 3, 12); c.arc(0, 0, 1, math.pi, 2 * math.pi); c.restore(); c.fill()
    # rocks on the bumps
    for (rx, a, w) in TER.rocks:
        if -80 < rx - cx < W + 80:
            c.set_source_rgb(*rgb('#6a5248')); c.save(); c.translate(rx - cx, TER.y(rx) - cy + a * 0.35); c.scale(w * 1.1, a * 0.6); c.arc(0, 0, 1, math.pi, 2 * math.pi); c.restore(); c.fill()
            c.set_source_rgb(*rgb('#7e665a')); c.save(); c.translate(rx - cx - 10, TER.y(rx) - cy + a * 0.1); c.scale(w * 0.5, a * 0.25); c.arc(0, 0, 1, math.pi, 2 * math.pi); c.restore(); c.fill()

def draw_boulder(c, t, f):   # the giant runaway tractor tire rolling down after him
    cx, cy = CAMX[f], CAMY[f]; bx = BX[f]
    if bx + BR - cx < -40: return
    gy = 1600 + SLOPE * bx; rot = bx / BR
    c.save(); c.translate(bx - cx, gy - cy - BR + 4); c.rotate(rot)
    c.set_source_rgb(*rgb('#1e1e22')); c.arc(0, 0, BR, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#2c2c32'))   # chunky treads
    for k in range(16):
        a = k * 2 * math.pi / 16; c.save(); c.rotate(a); c.rectangle(BR - 34, -16, 34, 32); c.restore(); c.fill()
    c.set_source_rgb(*rgb('#141418')); c.arc(0, 0, BR - 40, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#b89a3a')); c.arc(0, 0, 88, 0, 2 * math.pi); c.fill()   # yellow rim
    c.set_source_rgb(*rgb('#8a7228')); c.arc(0, 0, 70, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#b89a3a')); c.arc(0, 0, 30, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#5a4a18'))
    for k in range(6): a = k * math.pi / 3; c.arc(50 * math.cos(a), 50 * math.sin(a), 8, 0, 2 * math.pi); c.fill()   # bolts
    c.restore()
    for j in range(5):   # dust kicked up behind the tire
        k = ((t * 2.5 + j / 5) % 1); c.set_source_rgba(0.55, 0.45, 0.35, 0.35 * (1 - k))
        c.arc(bx - cx - 120 - 120 * k, gy - cy - 20 - 60 * k, 16 + 30 * k, 0, 2 * math.pi); c.fill()

PS = Particles(9)
def render(f, c):
    t = f / FPS; fi = min(f, len(GX) - 1); cx, cy = CAMX[fi], CAMY[fi]
    near = clamp(1 - (BX[fi] + BR - cx) / 400, 0, 1) if (BX[fi] + BR - cx) > 0 else 1
    a = 3 * clamp(1 - GAP[fi] / 3, 0, 1) + (5 if T_FAIL and 0 <= t - T_FAIL < 0.3 else 0)
    shake = (rng.uniform(-a, a), rng.uniform(-a, a))
    c.save(); c.translate(*shake)
    draw_world(c, t, fi)
    flat = T_FAIL is not None and t >= T_FAIL
    for (ts, xs) in SPL:
        if abs(t - ts) < 0.5 / FPS and t < S.T_RES + 1.3: PS.spawn(xs - cx, TER.y(xs) - cy - 8, 14, (0.6, 0.5, 0.35), 420, 0.6, grav=2200, r=6)
    if END.carried(t) or t >= END.T_GRAB:
        gx, gy = (END.carry_xy(t) if END.carried(t) else S.GRAB); sq = 0; dz = flat
        draw_blob(c, t, gx, gy, 'happy' if not flat else 'worried', 0, R=R, dizzy=dz)
    elif flat:
        gx, gy = S.GRAB; k = t - T_FAIL
        if k < POP:
            c.save(); c.translate(gx, TER.y(FX) - cy - 12); c.scale(1.7, 0.22); draw_blob(c, t, 0, 0, 'scared', 0, R=R, sweat=False); c.restore()
        else:
            pk = ease((k - POP) / 0.25); c.save(); c.translate(gx, gy + R * (1 - pk) * 0.7); c.scale(1.7 - 0.7 * pk, 0.22 + 0.78 * pk); draw_blob(c, t, 0, 0, 'worried', 0, R=R, dizzy=True); c.restore()
    else:
        gx, gy = GX[fi] - cx, GYS[fi] - cy
        h = max(0, TER.y(GX[fi]) - R - GYS[fi]); kk = 1 / (1 + h / 220)
        c.set_source_rgba(0, 0, 0, 0.25 * kk); c.save(); c.translate(gx, TER.y(GX[fi]) - cy + 3); c.scale(R * (0.5 + 0.4 * kk), 9); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
        mood = 'happy' if (t >= S.T_END and S.OUTCOME == 'win') else ('scared' if GAP[fi] < 2.5 else 'worried')
        draw_blob(c, t, gx, gy, mood, 0, R=R)
    draw_boulder(c, t, fi)
    PS.draw(c)
    END.draw_claw(c, t)
    c.restore()
    END.header(c, t, fi)

if __name__ == '__main__':
    if sys.argv[1] == 'sim':
        e = int(S.T_RES * FPS) - 1; g = GAP[int(S.T_START * FPS):e + 1]
        post = min(GAP[e:int(END.T_LIFT * FPS)]) if not T_FAIL else 0
        print(SEED, S.OUTCOME, round(S.T_RES - S.T_START, 2), 'mingap', round(min(g), 2), 'final', round(GAP[e], 2), 'mud', MUDHITS, 'postmin', round(post, 2), 'dur', S.DUR); sys.exit()
    run(S, render)
