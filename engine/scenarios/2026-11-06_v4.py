"""2026-11-06 v4 — RACE – GAP m: the LAVA FLOW. Gloop is a passive rigid ball (Ball) bouncing down the black
basalt slope of a volcano at night (the slope is what carries him forward — bounces reflect off the real ground
slope). A molten lava flow chases him at a seeded-random, surging speed. Sticky ash piles kill his speed when he
lands in them; basalt rocks deflect his bounces (sometimes backwards). Header: SURVIVE timer + GAP bar (distance
between the lava front and Gloop). GAP 0 = engulfed (cartoony: he pops back out sooty and dizzy)."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the lava flow'
SEED = int(os.environ.get('SEED', 15))
rng = random.Random(SEED)

class S: pass
S.HOOK1 = 'WILL GLOOP OUTRUN'; S.HOOK2 = 'THE LAVA FLOW?'; S.HOOK2_SIZE = 96; S.FAIL_WORD = 'SCORCHED!'; S.FAIL_SIZE = 130
S.T_START = HOOK_T; S.TL = 13.0; S.T_END = S.T_START + S.TL
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
    if 0 < t0 < S.T_RES + 1: S.events.append([t0, 'rumble', 1.0])
for (tl, xl, imp) in ball.landings:
    if tl < S.T_RES + 1.3: S.events.append([tl, 'hop'])
for (ts, xs) in SPL:
    if ts < S.T_RES + 1.3: S.events.append([ts, 'thump', 0.5])
if T_FAIL: S.events += [[T_FAIL, 'crash'], [T_FAIL + 0.05, 'thump', 1.0], [T_FAIL + POP, 'pop']]
S.AMB = {'drone': 46, 'rumble': 0.06, 'wind': 0.02}

def draw_bar(c, t, f):
    g = GAP[f]; p = clamp(g / (GAP0 / PPM), 0, 1)
    bx_ = bar(c, p, f'GAP {g:.1f} m', good_bad_col(p), 0, bw=620, x_off=40)
    c.set_source_rgb(*rgb('#5a4a48')); c.move_to(bx_ - 80, 252); c.line_to(bx_ - 60, 208); c.line_to(bx_ - 40, 208); c.line_to(bx_ - 20, 252); c.close_path(); c.fill()   # tiny volcano icon
    c.set_source_rgb(*rgb('#ff7a2a')); c.move_to(bx_ - 60, 208); c.line_to(bx_ - 40, 208); c.line_to(bx_ - 46, 226); c.line_to(bx_ - 54, 222); c.close_path(); c.fill()
S.draw_bar = draw_bar

# ---- flat muted volcano slope ----
TREES = [x for x in range(300, L, 520)]
def draw_world(c, t, f):
    cx, cy = CAMX[f], CAMY[f]
    c.set_source_rgb(*rgb('#1a1218')); c.rectangle(0, HEAD, W, H - HEAD); c.fill()
    c.set_source_rgba(1, 0.9, 0.85, 0.35)
    for i in range(24): c.arc((i * 263 - cx * 0.05) % W, HEAD + 30 + (i * 151) % 420, 2, 0, 2 * math.pi); c.fill()
    # ash cloud bands
    c.set_source_rgba(0.35, 0.25, 0.28, 0.35)
    for i in range(3): c.save(); c.translate((300 + i * 380 - cx * 0.04) % (W + 400) - 200, HEAD + 120 + i * 70); c.scale(260, 40); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    # far volcano peaks (parallax 0.2), mid ridge (0.5)
    for par, col, base, amp, per in ((0.2, '#2a1e26', 1000, 320, 760), (0.5, '#33242c', 1190, 170, 440)):
        c.set_source_rgb(*rgb(col)); c.move_to(0, H)
        for x in range(0, W + 41, 40):
            wx = x + cx * par; k = (wx % per) / per
            c.line_to(x, base - cy * par * 0.5 - amp * (1 - abs(2 * k - 1)) + 30 * math.sin(wx / 97))
        c.line_to(W, H); c.close_path(); c.fill()
    # dead charred trees (parallax 0.8)
    for tx in TREES:
        sx = tx - cx * 0.8
        if -150 < sx < W + 150:
            gy = 1500 - cy * 0.8 + SLOPE * tx * 0.2 - 40
            c.set_source_rgb(*rgb('#120c10')); c.set_line_width(14); c.set_line_cap(cairo.LINE_CAP_ROUND)
            c.move_to(sx, gy + 60); c.line_to(sx, gy - 180); c.stroke(); c.set_line_width(8)
            c.move_to(sx, gy - 80); c.line_to(sx - 60, gy - 150); c.stroke(); c.move_to(sx, gy - 120); c.line_to(sx + 50, gy - 190); c.stroke()
    # basalt slope
    x0 = int(max(0, cx - 20)); x1 = int(min(L - 1, cx + W + 20))
    c.move_to(x0 - cx, H + 10)
    for x in range(x0, x1 + 1, 6): c.line_to(x - cx, TER.h[x] - cy)
    c.line_to(x1 - cx, H + 10); c.close_path(); c.set_source_rgb(*rgb('#3a3036')); c.fill()
    c.set_source_rgb(*rgb('#55474c')); c.set_line_width(6)
    for x in range(x0, x1 + 1, 6): (c.move_to if x == x0 else c.line_to)(x - cx, TER.h[x] - cy)
    c.stroke()
    c.set_source_rgba(0, 0, 0, 0.18); c.set_line_width(3)
    for k in range(1, 6):
        for x in range(x0, x1 + 1, 30): (c.move_to if x == x0 else c.line_to)(x - cx, TER.h[x] - cy + k * 70)
        c.stroke()
    c.set_source_rgba(0.9, 0.4, 0.15, 0.35); c.set_line_width(3)   # faint warm cracks in the rock
    for k in range(int(x0 // 260), int(x1 // 260) + 1):
        wx = k * 260 + 80; y0 = TER.y(wx) - cy + 60 + (k * 37) % 120
        c.move_to(wx - cx, y0); c.line_to(wx - cx + 40, y0 + 30); c.line_to(wx - cx + 20, y0 + 70); c.stroke()
    # sticky ash piles
    for a, b in MUD:
        if b - cx > -50 and a - cx < W + 50:
            m = (a + b) / 2; c.set_source_rgb(*rgb('#6a6066'))
            c.save(); c.translate(m - cx, TER.y(m) - cy + 4); c.rotate(math.atan(SLOPE)); c.scale((b - a) / 2, 22); c.arc(0, 0, 1, math.pi, 2 * math.pi); c.restore(); c.fill()
            c.set_source_rgba(0.75, 0.7, 0.72, 0.5)
            c.save(); c.translate(m - cx - 20, TER.y(m) - cy - 6); c.rotate(math.atan(SLOPE)); c.scale((b - a) / 4, 6); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    # basalt rocks on the bumps
    for (rx, a, w) in TER.rocks:
        if -80 < rx - cx < W + 80:
            c.set_source_rgb(*rgb('#241c22')); c.save(); c.translate(rx - cx, TER.y(rx) - cy + a * 0.35); c.scale(w * 1.1, a * 0.6); c.arc(0, 0, 1, math.pi, 2 * math.pi); c.restore(); c.fill()
            c.set_source_rgb(*rgb('#4a3e44')); c.save(); c.translate(rx - cx - 10, TER.y(rx) - cy + a * 0.1); c.scale(w * 0.5, a * 0.25); c.arc(0, 0, 1, math.pi, 2 * math.pi); c.restore(); c.fill()

def draw_boulder(c, t, f):   # the lava front: a thick molten tongue hugging the slope, dark crust plates on top
    cx, cy = CAMX[f], CAMY[f]; bx = BX[f]
    nose = bx + BR
    if nose - cx < -40: return
    HG = BR * 1.15
    def top(wx):
        d = nose - wx
        if d >= HG: hh = HG + 14 * math.sin(wx * 0.02 + t * 3)
        else: hh = HG * math.sqrt(max(0, d / HG)) * (1 - 0.15 * (1 - d / HG))
        return TER.y(wx) - cy - hh
    xs = list(range(int(cx - 60), int(nose) + 1, 12)) + [nose]
    c.move_to(xs[0] - cx, TER.y(xs[0]) - cy + 30)
    for wx in xs: c.line_to(wx - cx, top(wx))
    c.line_to(nose - cx, TER.y(nose) - cy + 30); c.close_path()
    c.set_source_rgb(*rgb('#c4481c')); c.fill_preserve(); c.save(); c.clip()
    c.set_source_rgb(*rgb('#e06a26'))
    for j in range(7):   # molten streaks flowing forward
        k = ((t * 0.7 + j / 7) % 1); wx = nose - HG * 0.4 - (1 - k) * (nose - cx + 100)
        c.save(); c.translate(wx - cx, TER.y(wx) - cy - HG * (0.25 + 0.12 * (j % 4))); c.rotate(math.atan(SLOPE)); c.scale(70, 9); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    c.set_source_rgb(*rgb('#3a2228'))
    for j in range(10):   # crust plates drifting along the surface
        k = ((t * 0.5 + j * 0.37) % 1); wx = nose - 30 - (1 - k) * (nose - cx + 200)
        yy = top(wx) + 16 + 22 * (j % 3)
        c.save(); c.translate(wx - cx, yy); c.rotate(math.atan(SLOPE) + 0.3 * math.sin(j)); c.scale(34 + (j % 3) * 10, 12); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    c.restore()
    c.set_source_rgba(0.6, 0.55, 0.55, 0.3)
    for j in range(6):   # steam puffs
        k = ((t * 1.0 + j / 6) % 1); wx = nose - 40 - j * 110
        c.arc(wx - cx, top(wx) - 20 - k * 200, 18 + 26 * k, 0, 2 * math.pi); c.fill()

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
        if abs(t - ts) < 0.5 / FPS and t < S.T_RES + 1.3: PS.spawn(xs - cx, TER.y(xs) - cy - 8, 14, (0.5, 0.46, 0.48), 420, 0.6, grav=2200, r=8)
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
