"""2026-11-15 v3 — RACE – GAP m: the GIANT DONUT. Gloop is a passive rigid ball (Ball) bouncing down a steep
city street at night (the slope is what carries him forward — bounces reflect off the real ground slope). A
giant runaway pink-frosted donut rolls after him at a seeded-random, surging speed. Rain puddles kill his speed
when he lands in them; speed bumps deflect his bounces (sometimes backwards).
Header: SURVIVE timer + GAP bar (distance between the donut and Gloop). GAP 0 = run over (cartoony: he pops back
up dizzy)."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the giant donut'
SEED = int(os.environ.get('SEED', 1))
rng = random.Random(SEED)

class S: pass
S.HOOK1 = 'WILL GLOOP OUTRUN'; S.HOOK2 = 'THE GIANT DONUT?'; S.HOOK2_SIZE = 92; S.FAIL_WORD = 'RUN OVER!'; S.FAIL_SIZE = 130
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
    c.set_source_rgb(*rgb('#d86a9a')); c.arc(bx_ - 50, 231, 22, 0, 2 * math.pi); c.fill()   # tiny donut icon
    c.set_source_rgb(*rgb('#0d0b14')); c.arc(bx_ - 50, 231, 9, 0, 2 * math.pi); c.fill()
S.draw_bar = draw_bar

# ---- flat muted steep city street at night ----
POSTS = [x for x in range(300, L, 600)]
def draw_world(c, t, f):
    cx, cy = CAMX[f], CAMY[f]
    c.set_source_rgb(*rgb('#141628')); c.rectangle(0, HEAD, W, H - HEAD); c.fill()
    for i in range(14):
        sx = (i * 263 - cx * 0.05) % W; sy = HEAD + 40 + (i * 157) % 300
        c.set_source_rgba(1, 1, 0.9, 0.35 + 0.25 * math.sin(t * 2 + i)); c.arc(sx, sy, 2.5, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#e6dfc4')); c.arc(860 - (cx * 0.02) % 60, 470, 46, 0, 2 * math.pi); c.fill()
    # far skyline (parallax 0.15)
    c.set_source_rgb(*rgb('#1e2236'))
    for i in range(14):
        sx = (i * 160 - cx * 0.15) % (W + 400) - 200; w = 110 + (i * 53) % 70; hh = 380 + (i * 71) % 300
        c.rectangle(sx, 1350 - hh - cy * 0.2, w, hh + 600); c.fill()
    # nearer row houses on the hill (parallax 0.4) with a few lit windows
    for i in range(16):
        sx = (i * 230 - cx * 0.4) % (W + 460) - 230; hh = 300 + (i * 97) % 200; w = 200
        base = 1500 - cy * 0.45
        c.set_source_rgb(*rgb(('#2c2a3a', '#33303e', '#2a3040')[i % 3])); c.rectangle(sx, base - hh, w, hh + 600); c.fill()
        c.move_to(sx - 10, base - hh); c.line_to(sx + w / 2, base - hh - 60); c.line_to(sx + w + 10, base - hh); c.close_path(); c.fill()
        for r_ in range(3):
            for k in range(2):
                lit = (i * 7 + r_ * 3 + k) % 5 == 0
                c.set_source_rgba(*((1, 0.82, 0.5, 0.55) if lit else (0.08, 0.08, 0.12, 0.8)))
                c.rectangle(sx + 40 + k * 80, base - hh + 40 + r_ * 90, 40, 54); c.fill()
    # streetlamps along the sidewalk
    for tx in POSTS:
        sx = tx - cx
        if -150 < sx < W + 150:
            gy = TER.y(tx) - cy
            c.set_source_rgb(*rgb('#1c1c22')); c.rectangle(sx - 6, gy - 300, 12, 300); c.fill()
            c.move_to(sx, gy - 300); c.curve_to(sx + 10, gy - 330, sx + 40, gy - 330, sx + 50, gy - 310); c.set_line_width(10); c.stroke()
            c.set_source_rgb(*rgb('#e8d8a0')); c.arc(sx + 50, gy - 300, 12, 0, 2 * math.pi); c.fill()
            c.set_source_rgba(1, 0.9, 0.6, 0.035); c.move_to(sx + 40, gy - 300); c.line_to(sx - 30, gy); c.line_to(sx + 130, gy); c.close_path(); c.fill()
    # sidewalk + asphalt street
    x0 = int(max(0, cx - 20)); x1 = int(min(L - 1, cx + W + 20))
    c.move_to(x0 - cx, H + 10)
    for x in range(x0, x1 + 1, 6): c.line_to(x - cx, TER.h[x] - cy)
    c.line_to(x1 - cx, H + 10); c.close_path(); c.set_source_rgb(*rgb('#2e2e36')); c.fill()
    c.set_source_rgb(*rgb('#4a4a54')); c.set_line_width(10)
    for x in range(x0, x1 + 1, 6): (c.move_to if x == x0 else c.line_to)(x - cx, TER.h[x] - cy + 3)
    c.stroke()
    c.set_source_rgba(0.9, 0.85, 0.6, 0.45)   # dashed lane line
    for k in range(int(x0 // 140), int(x1 // 140) + 1):
        wx = k * 140; c.save(); c.translate(wx - cx, 1600 + SLOPE * wx - cy + 70); c.rotate(math.atan(SLOPE)); c.rectangle(0, 0, 70, 8); c.restore(); c.fill()
    c.set_source_rgba(0, 0, 0, 0.18); c.set_line_width(3)
    for x in range(x0, x1 + 1, 30): (c.move_to if x == x0 else c.line_to)(x - cx, TER.h[x] - cy + 160)
    c.stroke()
    # puddles (they kill his speed)
    for a, b in MUD:
        if b - cx > -50 and a - cx < W + 50:
            m = (a + b) / 2; c.set_source_rgb(*rgb('#3a4a66'))
            c.save(); c.translate(m - cx, TER.y(m) - cy + 6); c.rotate(math.atan(SLOPE)); c.scale((b - a) / 2, 14); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
            c.set_source_rgba(0.85, 0.9, 1, 0.35); c.save(); c.translate(m - cx - 30, TER.y(m) - cy + 3); c.rotate(math.atan(SLOPE)); c.scale((b - a) / 5, 4); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    # speed bumps on the bumps (yellow / black stripes)
    for (rx, a, w) in TER.rocks:
        if -80 < rx - cx < W + 80:
            c.save(); c.translate(rx - cx, TER.y(rx) - cy + a * 0.35); c.scale(w * 1.1, a * 0.6); c.arc(0, 0, 1, math.pi, 2 * math.pi); c.restore()
            c.set_source_rgb(*rgb('#3a3a40')); c.fill()
            for k in range(-2, 3):
                c.set_source_rgb(*rgb('#b89a3a' if k % 2 == 0 else '#24242a'))
                c.save(); c.translate(rx - cx + k * w * 0.4, TER.y(rx) - cy + a * 0.15); c.scale(w * 0.18, a * 0.38); c.arc(0, 0, 1, math.pi, 2 * math.pi); c.restore(); c.fill()

SPR = [(random.Random(k).uniform(0, 2 * math.pi), random.Random(k + 99).uniform(0.62, 0.86), ('#f2e6c8', '#5ad0ff', '#ffd36b', '#7ae08a')[k % 4]) for k in range(26)]
def draw_boulder(c, t, f):   # the giant donut rolling down after him
    cx, cy = CAMX[f], CAMY[f]; bx = BX[f]
    if bx + BR - cx < -40: return
    gy = 1600 + SLOPE * bx; rot = bx / BR
    c.save(); c.translate(bx - cx, gy - cy - BR + 4); c.rotate(rot)
    c.set_source_rgb(*rgb('#c8904a')); c.arc(0, 0, BR, 0, 2 * math.pi); c.fill()          # dough
    c.set_source_rgb(*rgb('#d6a05a')); c.arc(0, 0, BR - 10, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#d86a9a'))                                                      # wavy pink frosting
    for k in range(73):
        a = k * 2 * math.pi / 72; rr = BR - 22 + 8 * math.sin(a * 9)
        (c.move_to if k == 0 else c.line_to)(rr * math.cos(a), rr * math.sin(a))
    c.close_path(); c.fill()
    c.set_line_width(7); c.set_line_cap(cairo.LINE_CAP_ROUND)
    for (a, rk, col) in SPR:                                                                # sprinkles
        r_ = BR * rk * 0.95; c.set_source_rgb(*rgb(col))
        c.move_to(r_ * math.cos(a), r_ * math.sin(a)); c.line_to(r_ * math.cos(a) + 14 * math.cos(a * 3), r_ * math.sin(a) + 14 * math.sin(a * 3)); c.stroke()
    c.set_source_rgb(*rgb('#c8904a')); c.arc(0, 0, 66, 0, 2 * math.pi); c.fill()           # hole
    c.set_source_rgb(*rgb('#1c1c26')); c.arc(0, 0, 54, 0, 2 * math.pi); c.fill()
    c.restore()
    for j in range(5):   # crumbs + dust behind it
        k = ((t * 2.5 + j / 5) % 1); c.set_source_rgba(0.75, 0.55, 0.35, 0.35 * (1 - k))
        c.arc(bx - cx - 120 - 120 * k, gy - cy - 20 - 60 * k, 10 + 18 * k, 0, 2 * math.pi); c.fill()

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
