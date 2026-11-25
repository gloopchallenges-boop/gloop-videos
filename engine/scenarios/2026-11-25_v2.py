"""2026-11-25 v2 [STYLE] — RACE – GAP m: the GIANT SNOWBALL (bright style-test scene; based on 2026-11-20 v2 pinecone).
Gloop is a passive rigid ball (Ball) bouncing down a sunny ski slope (the slope carries him forward — bounces reflect off
the real ground slope). A giant snowball rolls after him at a seeded-random, surging speed and slowly grows as it rolls.
Deep powder drifts kill his speed when he lands in them; icy moguls deflect his bounces (sometimes backwards).
Header: SURVIVE timer + GAP bar. GAP 0 = rolled up (cartoony: he pops back out of the snow dizzy)."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the giant snowball'
SEED = int(os.environ.get('SEED', 1))
rng = random.Random(SEED)

class S: pass
S.HOOK1 = 'WILL GLOOP OUTRUN'; S.HOOK2 = 'THE GIANT SNOWBALL?'; S.HOOK2_SIZE = 86; S.FAIL_WORD = 'ROLLED UP!'; S.FAIL_SIZE = 130
S.CARD = ['Deep snow *SLOWS* Gloop down', 'Will the snowball *CATCH* him?']; S.STREAK = int(os.environ.get('STREAK', 0)); S.CTA = True
S.T_START = HOOK_T; S.TL = float(os.environ.get('TL', 12.5)); S.T_END = S.T_START + S.TL
R = 58; BR = 150; SLOPE = 0.07; L = 12000; PPM = 100.0; SX = 650   # Gloop's screen x (camera follows)
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
def brt(t): return BR + 3.5 * t   # it grows as it rolls
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
        gap = (ball.x - R * 0.85) - (bx + brt(t) * 0.92)
        if S.T_START <= t < S.T_END and gap <= 0: T_FAIL = t; FX = ball.x
        if t < S.T_START and gap < 120: bx = ball.x - R * 0.85 - brt(t) * 0.92 - 120   # boulder can't matter before the start
    gap = (ball.x - R * 0.85) - (bx + brt(t) * 0.92)
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
    POP = next((i / FPS - T_FAIL for i in range(fi0, N0) if BX[i] - brt(i / FPS) > FX + R * 1.3), 1.2) + 0.15
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
    c.set_source_rgb(0, 0, 0); c.arc(bx_ - 50, 231, 24, 0, 2 * math.pi); c.fill()   # tiny snowball icon
    c.set_source_rgb(*rgb('#f6f9fd')); c.arc(bx_ - 50, 231, 19, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#c8daf0')); c.arc(bx_ - 46, 235, 12, 0, 2 * math.pi); c.fill()
S.draw_bar = draw_bar

# ---- bright sunny ski slope (style-test scene) ----
TREES = [x for x in range(300, L, 640)]
def pine(c, x, y, h, col, snow=True):
    c.set_source_rgb(*rgb('#7a5236')); c.rectangle(x - h * 0.04, y - h * 0.08, h * 0.08, h * 0.12); c.fill()
    for k in range(3):
        w = h * (0.42 - k * 0.1); yy = y - h * (0.25 + k * 0.25)
        c.set_source_rgb(*rgb(col)); c.move_to(x - w, yy + h * 0.3); c.line_to(x, yy - h * 0.12); c.line_to(x + w, yy + h * 0.3); c.close_path(); c.fill()
        if snow:
            c.set_source_rgb(*rgb('#f4f8fc')); c.move_to(x - w * 0.35, yy + h * 0.02); c.line_to(x, yy - h * 0.12); c.line_to(x + w * 0.35, yy + h * 0.02); c.close_path(); c.fill()
FLAGS = [x for x in range(900, L, 900)]
def draw_world(c, t, f):
    cx, cy = CAMX[f], CAMY[f]
    c.set_source_rgb(*rgb('#6ec3f0')); c.rectangle(0, HEAD, W, H - HEAD); c.fill()
    c.set_source_rgb(*rgb('#fff6d0')); c.arc(860, 520, 54, 0, 2 * math.pi); c.fill()
    for (cx0, cy0, s) in ((180, 520, 1.0), (620, 610, 0.75)):
        x = (cx0 - cx * 0.03) % (W + 300) - 150
        c.set_source_rgb(1, 1, 1)
        for (dx, dy, r) in ((0, 0, 48), (50, -18, 56), (105, 0, 44), (50, 14, 46)): c.arc(x + dx * s, cy0 + dy * s, r * s, 0, 2 * math.pi); c.fill()
    # far snowy mountains (parallax 0.1) with blue-violet rock
    c.set_source_rgb(*rgb('#8a9ad8')); c.move_to(0, H)
    pts = []
    for x in range(0, W + 41, 40):
        wx = x + cx * 0.1; y = 1000 - cy * 0.15 - 220 * abs(math.sin(wx * 0.0028)) - 70 * abs(math.sin(wx * 0.009)); pts.append((x, y)); c.line_to(x, y)
    c.line_to(W, H); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#eef4fb')); c.move_to(pts[0][0], pts[0][1])
    for (x, y) in pts: c.line_to(x, y)
    for (x, y) in reversed(pts): c.line_to(x, y + 34 + 26 * math.sin(x * 0.05))
    c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#e6eef9')); c.rectangle(0, 1250 - cy * 0.35, W, H); c.fill()   # snowy foothills
    # far pines (parallax 0.25) and nearer pines (0.5)
    for (par, step, base, hh, col) in ((0.25, 110, 1320, 280, '#3c9a6a'), (0.5, 190, 1480, 420, '#2f8a5c')):
        for i in range(int((cx * par) // step) - 1, int((cx * par + W) // step) + 2):
            sx = i * step - cx * par + (i * 37) % 50; h_ = hh * (0.8 + 0.4 * ((i * 53) % 10) / 10)
            pine(c, sx, base - cy * (par + 0.1), h_, col)
    for tx in TREES:
        sx = tx - cx
        if -200 < sx < W + 200: pine(c, sx, TER.y(tx) - cy - 120, 520, '#23784c')
    # ski-slope flags (red / blue gates)
    for k, fx in enumerate(FLAGS):
        sx = fx - cx
        if -50 < sx < W + 50:
            gy = TER.y(fx) - cy; c.set_source_rgb(*rgb('#555c70')); c.rectangle(sx - 3, gy - 160, 6, 160); c.fill()
            c.set_source_rgb(*rgb('#e8455a' if k % 2 else '#3a6ee0')); c.move_to(sx + 3, gy - 160); c.line_to(sx + 60, gy - 140); c.line_to(sx + 3, gy - 118); c.fill()
    # snow slope
    x0 = int(max(0, cx - 20)); x1 = int(min(L - 1, cx + W + 20))
    c.move_to(x0 - cx, H + 10)
    for x in range(x0, x1 + 1, 6): c.line_to(x - cx, TER.h[x] - cy)
    c.line_to(x1 - cx, H + 10); c.close_path(); c.set_source_rgb(*rgb('#dfeaf6')); c.fill()
    c.set_source_rgb(*rgb('#f8fbff')); c.set_line_width(12)
    for x in range(x0, x1 + 1, 6): (c.move_to if x == x0 else c.line_to)(x - cx, TER.h[x] - cy + 4)
    c.stroke()
    c.set_source_rgba(0.45, 0.6, 0.85, 0.18)   # ski tracks
    c.set_line_width(4)
    for dy in (60, 74, 160, 174):
        c.move_to(x0 - cx, 1600 + SLOPE * x0 - cy + dy); c.line_to(x1 - cx, 1600 + SLOPE * x1 - cy + dy); c.stroke()
    # deep powder drifts (they kill his speed)
    for a, b in MUD:
        if b - cx > -50 and a - cx < W + 50:
            m = (a + b) / 2
            c.set_source_rgb(*rgb('#ffffff')); c.save(); c.translate(m - cx, TER.y(m) - cy + 4); c.rotate(math.atan(SLOPE)); c.scale((b - a) / 2, 26); c.arc(0, 0, 1, math.pi, 2 * math.pi); c.restore(); c.fill()
            c.set_source_rgba(0.5, 0.65, 0.9, 0.35); c.set_line_width(4)
            for k in (-0.5, 0, 0.5): c.move_to(m - cx + k * (b - a) / 2 - 18, TER.y(m) - cy - 6); c.line_to(m - cx + k * (b - a) / 2 + 18, TER.y(m) - cy - 10); c.stroke()
    # icy moguls over the bumps
    for (rx, a, w) in TER.rocks:
        if -80 < rx - cx < W + 80:
            c.save(); c.translate(rx - cx, TER.y(rx) - cy + a * 0.35); c.scale(w * 1.1, a * 0.6); c.arc(0, 0, 1, math.pi, 2 * math.pi); c.restore()
            c.set_source_rgb(*rgb('#a8d4f0')); c.fill()
            c.set_source_rgba(1, 1, 1, 0.8); c.set_line_width(4); c.move_to(rx - cx - w * 0.4, TER.y(rx) - cy - a * 0.1); c.line_to(rx - cx - w * 0.1, TER.y(rx) - cy - a * 0.2); c.stroke()

def draw_boulder(c, t, f):   # the giant snowball rolling down after him (grows as it rolls)
    cx, cy = CAMX[f], CAMY[f]; bx = BX[f]; br = brt(f / FPS)
    if bx + br - cx < -40: return
    gy = 1600 + SLOPE * bx; rot = bx / br
    c.save(); c.translate(bx - cx, gy - cy - br + 4)
    c.set_source_rgb(*rgb('#f6f9fd')); c.arc(0, 0, br, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#c8daf0')); c.arc(br * 0.12, br * 0.12, br * 0.9, -0.3, math.pi * 0.8); c.arc_negative(0, 0, br, math.pi * 0.8, -0.3); c.close_path(); c.fill()
    c.rotate(rot)
    for k in range(9):   # rolled-in lumps, twigs and a pine cone turn with it
        a = k * 2 * math.pi / 9; rr = br * (0.35 + 0.45 * ((k * 37) % 10) / 10)
        x, y = rr * math.cos(a), rr * math.sin(a)
        if k % 3 == 0:
            c.set_source_rgb(*rgb('#7a5236')); c.set_line_width(7); c.move_to(x - 22, y); c.line_to(x + 22, y + 8); c.stroke()
        elif k % 3 == 1:
            c.set_source_rgba(0.6, 0.72, 0.9, 0.55); c.arc(x, y, 18, 0, 2 * math.pi); c.fill()
        else:
            c.set_source_rgb(*rgb('#2f8a5c')); c.move_to(x - 16, y + 10); c.line_to(x, y - 16); c.line_to(x + 16, y + 10); c.fill()
    c.restore()
    for j in range(6):   # snow spray behind it
        k = ((t * 2.5 + j / 6) % 1); c.set_source_rgba(1, 1, 1, 0.8 * (1 - k))
        c.arc(bx - cx - br * 0.6 - 120 * k, gy - cy - 20 - 70 * k, 10 + 18 * k, 0, 2 * math.pi); c.fill()

PS = Particles(9)
def render(f, c):
    t = f / FPS; fi = min(f, len(GX) - 1); cx, cy = CAMX[fi], CAMY[fi]
    near = clamp(1 - (BX[fi] + brt(t) - cx) / 400, 0, 1) if (BX[fi] + brt(t) - cx) > 0 else 1
    a = 3 * clamp(1 - GAP[fi] / 3, 0, 1) + (5 if T_FAIL and 0 <= t - T_FAIL < 0.3 else 0)
    shake = (rng.uniform(-a, a), rng.uniform(-a, a))
    c.save(); c.translate(*shake)
    draw_world(c, t, fi)
    flat = T_FAIL is not None and t >= T_FAIL
    for (ts, xs) in SPL:
        if abs(t - ts) < 0.5 / FPS and t < S.T_RES + 1.3: PS.spawn(xs - cx, TER.y(xs) - cy - 8, 14, (0.95, 0.97, 1.0), 420, 0.6, grav=2200, r=6)
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
