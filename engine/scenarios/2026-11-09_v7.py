"""2026-11-09 v7 — RACE – GAP m: the RUNAWAY MINE CART. Gloop is a passive rigid ball (Ball) bouncing down a
sloping mine tunnel at night (the slope is what carries him forward — bounces reflect off the real ground slope).
A runaway mine cart full of coal rolls after him on the rails at a seeded-random, surging speed. Loose coal piles
kill his speed when he lands in them; rocks between the sleepers deflect his bounces (sometimes backwards).
Header: SURVIVE timer + GAP bar (distance between the cart and Gloop). GAP 0 = run over (cartoony: he pops back
up dizzy)."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the runaway mine cart'
SEED = int(os.environ.get('SEED', 8))
rng = random.Random(SEED)

class S: pass
S.HOOK1 = 'WILL GLOOP OUTRUN'; S.HOOK2 = 'THE RUNAWAY MINE CART?'; S.HOOK2_SIZE = 74; S.FAIL_WORD = 'RUN OVER!'; S.FAIL_SIZE = 130
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
    c.set_source_rgb(*rgb('#8a6a4a')); c.move_to(bx_ - 76, 214); c.line_to(bx_ - 24, 214); c.line_to(bx_ - 32, 244); c.line_to(bx_ - 68, 244); c.close_path(); c.fill()   # tiny cart icon
    c.set_source_rgb(*rgb('#2a2a2e')); c.arc(bx_ - 60, 246, 6, 0, 2 * math.pi); c.fill(); c.arc(bx_ - 40, 246, 6, 0, 2 * math.pi); c.fill()
S.draw_bar = draw_bar

# ---- flat muted mine tunnel ----
BEAMS = [x for x in range(300, L, 520)]
def draw_world(c, t, f):
    cx, cy = CAMX[f], CAMY[f]
    c.set_source_rgb(*rgb('#17130f')); c.rectangle(0, HEAD, W, H - HEAD); c.fill()
    # far rock wall texture (parallax 0.3)
    c.set_source_rgb(*rgb('#211b15'))
    for i in range(40):
        wx = i * 211; sx = (wx - cx * 0.3) % (W + 300) - 150; sy = HEAD + 80 + (i * 137) % 1100 - cy * 0.15 % 200
        c.save(); c.translate(sx, sy); c.scale(110 + (i * 31) % 70, 50 + (i * 17) % 40); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    c.set_source_rgba(0.6, 0.8, 1, 0.25)   # glinting crystals in the wall
    for i in range(14):
        wx = i * 397; sx = (wx - cx * 0.3) % (W + 200) - 100; sy = HEAD + 160 + (i * 211) % 900
        c.move_to(sx, sy - 12); c.line_to(sx + 7, sy); c.line_to(sx, sy + 12); c.line_to(sx - 7, sy); c.close_path(); c.fill()
    # wooden support frames along the tunnel (on the slope)
    for tx in BEAMS:
        sx = tx - cx
        if -150 < sx < W + 150:
            gy = TER.y(tx) - cy; top = gy - 720
            c.set_source_rgb(*rgb('#4a3622')); c.rectangle(sx - 14, top, 28, gy - top); c.fill()
            c.set_source_rgb(*rgb('#3a2a1a')); c.save(); c.translate(sx, top); c.rotate(math.atan(SLOPE)); c.rectangle(-260, -20, 520, 30); c.restore(); c.fill()
            c.set_source_rgb(*rgb('#2a2a2e')); c.set_line_width(3); c.move_to(sx + 60, top + 10); c.line_to(sx + 60, top + 70); c.stroke()
            on = 0.75 + 0.25 * math.sin(t * 7 + tx)
            c.set_source_rgba(1, 0.8, 0.4, 0.9 * on); rrect(c, sx + 46, top + 70, 28, 36, 6); c.fill()   # lantern
    # ground + rails
    x0 = int(max(0, cx - 20)); x1 = int(min(L - 1, cx + W + 20))
    c.move_to(x0 - cx, H + 10)
    for x in range(x0, x1 + 1, 6): c.line_to(x - cx, TER.h[x] - cy)
    c.line_to(x1 - cx, H + 10); c.close_path(); c.set_source_rgb(*rgb('#3a3028')); c.fill()
    c.set_source_rgb(*rgb('#4a3a2a'))   # sleepers
    for k in range(int(x0 // 70), int(x1 // 70) + 1):
        wx = k * 70; y0 = TER.y(wx) - cy
        c.save(); c.translate(wx - cx, y0 + 4); c.rotate(math.atan(SLOPE)); c.rectangle(-16, 0, 32, 14); c.restore(); c.fill()
    c.set_source_rgb(*rgb('#8a8e96')); c.set_line_width(6)
    for x in range(x0, x1 + 1, 6): (c.move_to if x == x0 else c.line_to)(x - cx, 1600 + SLOPE * x - cy + 2)
    c.stroke()
    c.set_source_rgba(0, 0, 0, 0.18); c.set_line_width(3)
    for k in range(1, 6):
        for x in range(x0, x1 + 1, 30): (c.move_to if x == x0 else c.line_to)(x - cx, TER.h[x] - cy + k * 70)
        c.stroke()
    # loose coal piles (sticky)
    for a, b in MUD:
        if b - cx > -50 and a - cx < W + 50:
            m = (a + b) / 2; c.set_source_rgb(*rgb('#1c1c20'))
            c.save(); c.translate(m - cx, TER.y(m) - cy + 4); c.rotate(math.atan(SLOPE)); c.scale((b - a) / 2, 30); c.arc(0, 0, 1, math.pi, 2 * math.pi); c.restore(); c.fill()
            c.set_source_rgb(*rgb('#3a3a42'))
            for j in range(8):
                xx = a + (b - a) * (j + 0.5) / 8; yy = TER.y(xx) - cy - 8 - 8 * math.sin(j * 1.9) ** 2
                c.arc(xx - cx, yy, 9, 0, 2 * math.pi); c.fill()
    # rocks on the bumps
    for (rx, a, w) in TER.rocks:
        if -80 < rx - cx < W + 80:
            c.set_source_rgb(*rgb('#5a524a')); c.save(); c.translate(rx - cx, TER.y(rx) - cy + a * 0.35); c.scale(w * 1.1, a * 0.6); c.arc(0, 0, 1, math.pi, 2 * math.pi); c.restore(); c.fill()
            c.set_source_rgb(*rgb('#6e665c')); c.save(); c.translate(rx - cx - 10, TER.y(rx) - cy + a * 0.1); c.scale(w * 0.5, a * 0.25); c.arc(0, 0, 1, math.pi, 2 * math.pi); c.restore(); c.fill()
    # rock ceiling
    c.set_source_rgb(*rgb('#0f0c09')); c.move_to(0, HEAD)
    for x in range(0, W + 41, 40): c.line_to(x, HEAD + 70 + 30 * math.sin((x + cx) / 130) + 20 * math.sin((x + cx) / 47))
    c.line_to(W, HEAD); c.close_path(); c.fill()

def draw_boulder(c, t, f):   # the runaway mine cart rolling down after him
    cx, cy = CAMX[f], CAMY[f]; bx = BX[f]
    if bx + BR - cx < -40: return
    gy = 1600 + SLOPE * bx; rot = bx / 34
    c.save(); c.translate(bx - cx, gy - cy); c.rotate(math.atan(SLOPE))
    for wx in (-110, 100):   # wheels
        c.set_source_rgb(*rgb('#2a2a2e')); c.arc(wx, -34, 34, 0, 2 * math.pi); c.fill()
        c.set_source_rgb(*rgb('#6a6e76')); c.arc(wx, -34, 12, 0, 2 * math.pi); c.fill()
        c.set_line_width(5); c.move_to(wx, -34); c.line_to(wx + 28 * math.cos(rot), -34 + 28 * math.sin(rot)); c.stroke()
    c.set_source_rgb(*rgb('#1a1a1e'))   # coal heap on top
    for (dx, dy, r) in ((-90, -262, 46), (-30, -280, 56), (40, -272, 50), (100, -258, 40), (0, -300, 40)): c.arc(dx, dy, r, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#7a5a3e')); c.move_to(-170, -250); c.line_to(165, -250); c.line_to(140, -60); c.line_to(-150, -60); c.close_path(); c.fill()   # wooden body
    c.set_source_rgb(*rgb('#5a4028')); c.set_line_width(4)
    for yy in (-190, -125): c.move_to(-165, yy); c.line_to(160, yy); c.stroke()
    c.set_source_rgb(*rgb('#4a4e56'))   # iron bands
    for xx in (-150, 120): c.rectangle(xx, -250, 24, 190); c.fill()
    c.rectangle(-176, -262, 348, 20); c.fill()
    c.restore()
    for j in range(4):   # sparks from the wheels
        k = ((t * 3 + j / 4) % 1); c.set_source_rgba(1, 0.8, 0.3, 0.9 * (1 - k))
        c.arc(bx - cx - 110 - 70 * k, gy - cy - 10 - 70 * k + 130 * k * k, 4, 0, 2 * math.pi); c.fill()

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
        if abs(t - ts) < 0.5 / FPS and t < S.T_RES + 1.3: PS.spawn(xs - cx, TER.y(xs) - cy - 8, 14, (0.2, 0.2, 0.24), 420, 0.6, grav=2200, r=6)
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
