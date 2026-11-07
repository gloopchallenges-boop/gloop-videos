"""2026-11-07 v7 — DAMAGE BAR – PLANKS %: the GIANT OCTOPUS. Gloop is a passive rigid ball (Ball) bouncing on
a floating plank raft in a harbor at night (two mooring posts at the ends are the walls). Every landing
loosens the planks in proportion to the real impact speed; a seeded-random giant octopus dives and slams
up from below with its head (some slams aimed under where he is) — each slam punches a split and throws
him up if he's on the raft. PLANKS 0% = the raft breaks apart and Gloop splashes into the harbor."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the giant octopus'
SEED = int(os.environ.get('SEED', 5))
rng = random.Random(SEED)

class S: pass
S.HOOK2 = 'THE GIANT OCTOPUS?'; S.HOOK2_SIZE = 88; S.FAIL_WORD = 'SPLASH!'; S.FAIL_SIZE = 120; 
S.T_START = HOOK_T; S.TL = 12.5; S.T_END = S.T_START + S.TL
DECK = 1300; R = 58; XMIN, XMAX = 200, 880; TANK_L, TANK_R = XMIN - R, XMAX + R; WATER = DECK + 40
LAND_K = float(os.environ.get('LAND_K', 0.0009)); RAM_D = (float(os.environ.get('BITE_S', 6)), float(os.environ.get('BITE_B', 16)))

# --- seeded beaver gnaws
RAMS = []; t = 0.5
while t < S.T_END + 2:
    big = rng.random() < 0.4
    RAMS.append({'t': t, 'x': rng.uniform(TANK_L + 80, TANK_R - 80), 'big': big, 'aim': rng.random() < 0.3})
    t += rng.uniform(1.3, 2.8)

TER = Terrain(DECK, seed=SEED, bumps=0, amp=0, soft=False)
POOL = Terrain(WATER + 20, seed=SEED, bumps=0, amp=0, soft=False)
N0 = int(40 * FPS); GX, GYS, GL = [], [], []
ball = Ball(rng.uniform(330, 750), TER, R=R, seed=SEED, xmin=XMIN, xmax=XMAX, hop=rng.uniform(250, 310))
logp = 100.0; T_FAIL = None; DMG = []   # (t, x, amount, kind)
nl = 0
for f in range(N0):
    t = f / FPS
    live = T_FAIL is None and S.T_START <= t < S.T_END
    for r in RAMS:
        if abs(t - (r['t'] - 0.45)) < 0.5 / FPS and r['aim']: r['x'] = clamp(ball.x + rng.uniform(-50, 50), TANK_L + 60, TANK_R - 60)
        if abs(t - r['t']) < 0.5 / FPS and T_FAIL is None:
            if abs(ball.x - r['x']) < 150 and ball.height() < 20:   # the jolt throws him only if he's on the logs
                ball.push((ball.x - r['x']) * 2.2, -650)
            if live:
                d = RAM_D[1] if r['big'] else RAM_D[0]; logp -= d; DMG.append((t, r['x'], d, 'ram'))
                if logp <= 0: logp = 0; T_FAIL = t
    ball.step(t)
    while nl < len(ball.landings):
        tl, xl, imp = ball.landings[nl]; nl += 1
        if T_FAIL is None and S.T_START <= tl < S.T_END:
            d = LAND_K * imp
            if any(k == 'ram' and abs(xd - xl) < 70 for (_, xd, _, k) in DMG): d *= 1.8   # landing on a notch cracks it more
            d = round(d, 1); logp -= d; DMG.append((tl, xl, d, 'land'))
            if logp <= 0: logp = 0; T_FAIL = tl
    if T_FAIL is not None and ball.T is TER:
        ball.T = POOL; ball.vmin = 0; ball.e = 0.15; ball.vy = max(ball.vy, 120)
    if ball.T is POOL: ball.vx *= 0.9
    GX.append(ball.x); GYS.append(ball.y); GL.append(logp)
S.OUTCOME = 'fail' if T_FAIL else 'win'
S.T_RES = T_FAIL if T_FAIL else S.T_END
S.GRAB = (540, DECK - R)
END = S.END = Ending(S)
gi = min(int(END.T_GRAB * FPS), N0 - 1); S.GRAB = (GX[gi], GYS[gi] - (14 if T_FAIL else 0))
S.events = [[0.05, 'rumble', 1.0]]
for r in RAMS:
    if r['t'] < S.T_RES + 0.2: S.events.append([r['t'], 'thump', 1.0 if r['big'] else 0.7]); S.events.append([r['t'] - 0.2, 'splash'])
for (tl, xl, imp) in ball.landings:
    if tl < S.T_RES + 1.5 and (T_FAIL is None or tl <= T_FAIL): S.events.append([tl, 'hop'])
for tw in ball.walls:
    if tw < S.T_RES: S.events.append([tw, 'thump', 0.3])
if T_FAIL: S.events += [[T_FAIL, 'whoosh'], [T_FAIL + 0.1, 'thump', 1.0], [T_FAIL + 0.35, 'splash']]
S.AMB = {'drone': 46, 'wind': 0.03}

def draw_bar(c, t, f):
    p = GL[f] / 100; recent = [d for d in DMG if d[0] <= t and t - d[0] < 0.3]
    bx = bar(c, p, f'PLANKS {int(math.ceil(GL[f]))}%', good_bad_col(p), 0.12 if recent else 0, bw=640, x_off=36)
    c.save(); c.translate(bx - 52, 231)   # little ice block icon
    c.set_source_rgb(*rgb('#b08050')); c.rectangle(-30, -16, 60, 12); c.rectangle(-30, 2, 60, 12); c.fill()
    c.set_source_rgb(*rgb('#6a4a2a')); c.rectangle(-22, -18, 6, 34); c.rectangle(16, -18, 6, 34); c.fill(); c.restore()
S.draw_bar = draw_bar

def beaver_pos(t):
    """Beaver swimming at the surface; for a gnaw it dives and lunges up under the raft at r['x']."""
    x = 540 + 430 * math.sin(t * 0.8); y = WATER + 260; d = 1 if math.cos(t * 0.8) >= 0 else -1; ang = 0.0; bite = 0.0
    for r in RAMS:
        if r['t'] - 0.5 <= t < r['t'] + 0.6 and r['t'] < S.T_RES + 0.1:
            if t < r['t']: k = ease((t - (r['t'] - 0.5)) / 0.5); x, y = lerp(x, r['x'], k), lerp(WATER + 280, DECK + 110, k); ang = -1.2 * k; bite = k
            else: k = ease((t - r['t']) / 0.6); x, y = lerp(r['x'], x, k), lerp(DECK + 110, WATER + 280, k); ang = -1.2 * (1 - k); bite = 1 - k
    return x, y, d, ang, bite

def draw_beaver(c, x, y, d, ang, bite, t):   # the giant octopus (head first when slamming up)
    c.save(); c.translate(x, y); c.rotate(ang * d); c.scale(d, 1)
    c.set_source_rgb(*rgb('#7a3a52')); c.set_line_cap(cairo.LINE_CAP_ROUND)
    for i in range(6):   # tentacles trailing behind
        yy = -50 + i * 20; c.set_line_width(26 - i * 1.5)
        c.move_to(-60, yy)
        for k in range(1, 8):
            xx = -60 - k * 38; c.line_to(xx, yy * (1 + k * 0.12) + 18 * math.sin(t * 5 + k * 0.8 + i))
        c.stroke()
    c.set_source_rgb(*rgb('#8e4662')); c.save(); c.scale(1.45, 0.95); c.arc(30, 0, 100, 0, 2 * math.pi); c.restore(); c.fill()   # mantle
    c.set_source_rgb(*rgb('#a85a78')); c.save(); c.scale(1.45, 0.95); c.arc(50, -30, 50, 0, 2 * math.pi); c.restore(); c.fill()
    c.set_source_rgba(0.35, 0.12, 0.22, 0.5)
    for (sx, sy) in ((60, 40), (100, -50), (0, -60), (130, 20), (-20, 30)): c.arc(sx, sy, 9, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#f0e6c8')); c.arc(150, 30, 20, 0, 2 * math.pi); c.fill()   # eye
    c.set_source_rgb(0.05, 0.05, 0.08); c.rectangle(142, 24, 16, 10); c.fill()
    c.set_source_rgb(*rgb('#4a1a2c')); c.set_line_width(6); c.move_to(126, 2); c.line_to(170, 12); c.stroke()   # grumpy brow
    c.restore()

def draw_head_wake(c, x, t):
    """Octopus head + a tentacle tip poking out of the water after the raft breaks."""
    c.set_source_rgb(*rgb('#8e4662')); c.save(); c.translate(x, WATER + 4); c.scale(70, 50); c.arc(0, 0, 1, math.pi, 2 * math.pi); c.restore(); c.fill()
    c.set_source_rgb(*rgb('#f0e6c8')); c.arc(x + 30, WATER - 18, 9, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#7a3a52')); c.set_line_width(18); c.set_line_cap(cairo.LINE_CAP_ROUND)
    c.move_to(x + 110, WATER + 10); c.curve_to(x + 130, WATER - 60, x + 170, WATER - 80 + 10 * math.sin(t * 4), x + 160, WATER - 110); c.stroke()

stars = [(rng.uniform(0, W), rng.uniform(HEAD, 900), rng.uniform(1.2, 2.6)) for _ in range(60)]
BERGS = [(-60, 980, 260), (230, 1040, 200), (520, 1000, 300), (860, 960, 280)]
def draw_bg(c, t):
    c.set_source_rgb(*rgb('#111826')); c.rectangle(0, HEAD, W, H - HEAD); c.fill()
    c.set_source_rgba(0.85, 0.9, 1.0, 0.45)
    for x, y, r in stars: c.arc(x, y, r, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#e6e8dc')); c.arc(820, 560, 44, 0, 2 * math.pi); c.fill()
    # far harbor: warehouses + a crane silhouette
    c.set_source_rgb(*rgb('#1c2434'))
    for (x, w_, h_) in ((0, 220, 140), (240, 180, 200), (440, 260, 120), (720, 360, 170)):
        c.rectangle(x, 1155 - h_, w_, h_); c.fill()
    c.rectangle(560, 860, 20, 180); c.fill(); c.rectangle(500, 860, 220, 16); c.fill()
    c.set_source_rgba(1, 0.82, 0.45, 0.35)
    for (x, y) in ((60, 1060), (300, 1000), (340, 1000), (800, 1030), (900, 1030)): c.rectangle(x, y, 20, 26); c.fill()
    c.set_source_rgb(*rgb('#13263a')); c.rectangle(0, 1155, W, H - 1155); c.fill()   # sea
    c.set_source_rgba(0.9, 0.9, 0.8, 0.10)
    for i in range(7): c.rectangle(820 - 70 + 12 * math.sin(t * 2 + i), 1175 + i * 22, 140 - i * 12, 5); c.fill()
    c.set_source_rgba(1, 1, 1, 0.05)
    for i in range(8):
        off = (t * 40 + i * 137) % W
        c.rectangle(off - 200, 1200 + i * 90, 260, 4); c.fill()

def draw_water_front(c, t, f):
    c.set_source_rgba(0.06, 0.16, 0.26, 0.62); c.move_to(0, H)
    for x in range(0, W + 20, 20): c.line_to(x, WATER + 8 * math.sin(x * 0.02 + t * 2.2))
    c.line_to(W, H); c.close_path(); c.fill()
    c.set_source_rgba(1, 1, 1, 0.12); c.set_line_width(4)
    for x in range(0, W + 20, 20): (c.move_to if x == 0 else c.line_to)(x, WATER + 8 * math.sin(x * 0.02 + t * 2.2))
    c.stroke()

NLOG = 5; LOGW = (TANK_R - TANK_L + 80) / NLOG
def draw_raft(c, t, f):
    broke = T_FAIL is not None and t >= T_FAIL
    sp = 0.0 if not broke else ease((t - T_FAIL) / 0.8)
    bob = 3 * math.sin(t * 2); yb = DECK + bob
    x0 = TANK_L - 40
    for i, px in enumerate((TANK_L - 50, TANK_R - 40)):   # mooring posts (walls)
        dx = (-1 if i == 0 else 1) * 260 * sp
        c.save(); c.translate(px + 45 + dx, yb); c.rotate((-1 if i == 0 else 1) * 0.6 * sp)
        c.set_source_rgb(*rgb('#5a4430')); c.rectangle(-40, -210, 80, 300); c.fill()
        c.set_source_rgb(*rgb('#6e543a')); c.rectangle(-40, -210, 26, 300); c.fill()
        c.set_source_rgb(*rgb('#3a2c20')); c.save(); c.translate(0, -210); c.scale(40, 12); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
        c.set_source_rgb(*rgb('#c8b080')); c.set_line_width(8)
        for yy in (-150, -130): c.move_to(-42, yy); c.line_to(42, yy + 8); c.stroke()   # rope wraps
        c.restore()
    for i in range(NLOG):   # plank raft side-on, splits apart into its planks
        k = i - (NLOG - 1) / 2; dx = k * 70 * sp; dy = 90 * sp * (1 + abs(k) * 0.3)
        lx = x0 + i * LOGW + dx
        c.save(); c.translate(lx + LOGW / 2, yb + 28 + dy); c.rotate(k * 0.12 * sp)
        c.set_source_rgb(*rgb('#8a6440' if i % 2 else '#7c5838')); c.rectangle(-LOGW / 2, -28, LOGW + (0 if broke else 1), 44); c.fill()
        c.set_source_rgb(*rgb('#a07a50')); c.rectangle(-LOGW / 2, -28, LOGW + (0 if broke else 1), 8); c.fill()
        c.set_source_rgb(*rgb('#4a3422')); c.rectangle(-LOGW / 2, 16, LOGW + (0 if broke else 1), 22); c.fill()   # cross beam
        c.set_source_rgb(*rgb('#3a2a1c'))
        for xx in (-LOGW / 2 + 16, LOGW / 2 - 16): c.arc(xx, -10, 4, 0, 2 * math.pi); c.fill()   # nails
        c.restore()
    for (td, xd, d, kind) in DMG:   # splits from the slams
        if td > t: break
        if kind == 'ram' and not broke:
            c.set_source_rgb(*rgb('#2a1a10')); c.set_line_width(4)
            c.move_to(xd, yb + 64); c.line_to(xd - 10, yb + 40); c.line_to(xd + 8, yb + 22); c.line_to(xd - 4, yb + 2); c.stroke()
            c.move_to(xd - 10, yb + 40); c.line_to(xd - 34, yb + 30); c.stroke(); c.move_to(xd + 8, yb + 22); c.line_to(xd + 30, yb + 16); c.stroke()

PS = Particles(9)
CHIP = (0.62, 0.46, 0.3)
def render(f, c):
    t = f / FPS; shake = (0, 0)
    for r in RAMS:
        if r['t'] <= t < r['t'] + 0.18 and r['t'] < S.T_RES + 0.1: a = 4 if r['big'] else 2; shake = (rng.uniform(-a, a), rng.uniform(-a, a))
    if T_FAIL and T_FAIL <= t < T_FAIL + 0.3: shake = (rng.uniform(-6, 6), rng.uniform(-6, 6))
    c.save(); c.translate(*shake)
    fi = min(f, len(GX) - 1)
    draw_bg(c, t)
    bxp, byp, bd, bang, bbite = beaver_pos(t)
    after = T_FAIL is not None and t > T_FAIL + 0.5
    if not after: draw_beaver(c, bxp, byp, bd, bang, bbite, t)
    fell = T_FAIL is not None and t >= T_FAIL
    if END.carried(t) or t >= END.T_GRAB: gx, gy = (END.carry_xy(t) if END.carried(t) else S.GRAB)
    else:
        gx, gy = GX[fi], GYS[fi]
        if fell and gy > WATER - R * 0.6: gy = WATER - R * 0.6 + 6 * math.sin(t * 4)
    danger = any(r['t'] - 0.6 <= t < r['t'] + 0.2 and abs(r['x'] - GX[fi]) < 220 for r in RAMS)
    mood = 'happy' if (t >= S.T_END and S.OUTCOME == 'win') else ('scared' if danger or fell or GL[fi] < 30 else 'worried')
    draw_raft(c, t, f)
    if not fell and not END.carried(t):
        h = max(0, DECK - R - gy); kk = 1 / (1 + h / 220)
        c.set_source_rgba(0, 0, 0, 0.25 * kk); c.save(); c.translate(gx, DECK + 4); c.scale(R * (0.5 + 0.4 * kk), 8); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    draw_blob(c, t, gx, gy, mood, 0, R=R, dizzy=fell and t > T_FAIL + 0.6)
    draw_water_front(c, t, f)
    if after and not END.carried(t):
        draw_head_wake(c, gx + 230 * math.cos(t * 1.8), t)
    for (td, xd, d, kind) in DMG:
        if td <= t < td + 0.8 and (kind == 'ram' or d >= 2.5):
            k = (t - td) / 0.8; text_at(c, f'-{d:g}%', xd + (70 if xd < 540 else -70), DECK - 120 - 70 * k, 56 if kind == 'ram' else 44, rgb('#ff6b5a'))
        if abs(t - td) < 0.5 / FPS: PS.spawn(xd, DECK + 30, 6 if kind == 'land' else 18, CHIP, 300 if kind == 'land' else 550, 0.55, grav=1400, r=5 if kind == 'land' else 8)
    if T_FAIL and abs(t - T_FAIL - 0.35) < 0.5 / FPS: PS.spawn(GX[fi], WATER, 30, (0.6, 0.8, 0.9), 700, 0.8, grav=2200, r=9)
    PS.draw(c)
    END.draw_claw(c, t)
    c.restore()
    END.header(c, t, fi)

if __name__ == '__main__':
    if sys.argv[1] == 'sim':
        print(SEED, S.OUTCOME, round(S.T_RES - S.T_START, 2), 'final', round(GL[int(S.T_RES * FPS) - 1]), 'gnaws', len([d for d in DMG if d[3] == 'ram']), 'lands', len([d for d in DMG if d[3] == 'land']), 'dur', S.DUR); sys.exit()
    run(S, render)
