"""2026-11-11 v2 — DAMAGE BAR – BOARD %: the ANGRY STINGRAY. Gloop is a passive rigid ball (Ball) bouncing on a
surfboard floating in a tropical lagoon at night (two lava-rock pillars at the ends are the walls). Every landing
cracks the foam in proportion to the real impact speed; a seeded-random stingray dives and flips up from below to
punch dents into the board (some aimed under where he is) — each punch jolts him up if he's on the board.
BOARD 0% = it snaps apart and Gloop splashes into the lagoon."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the angry stingray'
SEED = int(os.environ.get('SEED', 11))
rng = random.Random(SEED)

class S: pass
S.HOOK2 = 'THE ANGRY STINGRAY?'; S.HOOK2_SIZE = 82; S.FAIL_WORD = 'SNAP!'; S.FAIL_SIZE = 150; 
S.T_START = HOOK_T; S.TL = float(os.environ.get('TL', 13.0)); S.T_END = S.T_START + S.TL
DECK = 1300; R = 58; XMIN, XMAX = 200, 880; TANK_L, TANK_R = XMIN - R, XMAX + R; WATER = DECK + 40
LAND_K = float(os.environ.get('LAND_K', 0.0009)); RAM_D = (float(os.environ.get('BITE_S', 8)), float(os.environ.get('BITE_B', 20)))

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
    if r['t'] < S.T_RES + 0.2: S.events.append([r['t'], 'thump', 1.0 if r['big'] else 0.7]); S.events.append([r['t'] - 0.2, 'splash']); S.events.append([r['t'] + 0.02, 'crackle'])
for (tl, xl, imp) in ball.landings:
    if tl < S.T_RES + 1.5 and (T_FAIL is None or tl <= T_FAIL): S.events.append([tl, 'hop'])
for tw in ball.walls:
    if tw < S.T_RES: S.events.append([tw, 'thump', 0.3])
if T_FAIL: S.events += [[T_FAIL, 'whoosh'], [T_FAIL + 0.1, 'thump', 1.0], [T_FAIL + 0.35, 'splash']]
S.AMB = {'drone': 44, 'wind': 0.02}

def draw_bar(c, t, f):
    p = GL[f] / 100; recent = [d for d in DMG if d[0] <= t and t - d[0] < 0.3]
    bx = bar(c, p, f'BOARD {int(math.ceil(GL[f]))}%', good_bad_col(p), 0.12 if recent else 0, bw=640, x_off=36)
    c.save(); c.translate(bx - 52, 231)   # little float icon
    c.set_source_rgb(*rgb('#e8e0c8')); c.save(); c.scale(14, 32); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    c.set_source_rgb(*rgb('#e0703a')); c.rectangle(-3, -28, 6, 56); c.fill(); c.restore()
S.draw_bar = draw_bar

def beaver_pos(t):
    """Swordfish cruising under the surface; for a stab it dives and lunges up under the float at r['x']."""
    x = 540 + 430 * math.sin(t * 0.8); y = WATER + 260; d = 1 if math.cos(t * 0.8) >= 0 else -1; ang = 0.0; bite = 0.0
    for r in RAMS:
        if r['t'] - 0.5 <= t < r['t'] + 0.6 and r['t'] < S.T_RES + 0.1:
            if t < r['t']: k = ease((t - (r['t'] - 0.5)) / 0.5); x, y = lerp(x, r['x'], k), lerp(WATER + 280, DECK + 205, k); ang = -1.25 * k; bite = k
            else: k = ease((t - r['t']) / 0.6); x, y = lerp(r['x'], x, k), lerp(DECK + 205, WATER + 280, k); ang = -1.25 * (1 - k); bite = 1 - k
    return x, y, d, ang, bite

def draw_beaver(c, x, y, d, ang, bite, t):   # the stingray, seen from above-front: big flapping diamond
    c.save(); c.translate(x, y - 40 * bite); c.rotate(0.15 * d * (1 - bite))
    top, top2 = rgb('#4e5e70'), rgb('#62748a')
    fl = 22 * math.sin(t * 5)
    c.set_source_rgb(*rgb('#3a4654')); c.set_line_width(9); c.set_line_cap(cairo.LINE_CAP_ROUND)   # whip tail trailing down
    c.move_to(0, 90); c.curve_to(14 * math.sin(t * 3), 170, -14 * math.sin(t * 3), 230, 10 * math.sin(t * 3 + 1), 300); c.stroke()
    c.set_source_rgb(*top)
    c.move_to(0, -95); c.curve_to(70, -70, 120, -30, 175, fl); c.curve_to(120, 30, 60, 70, 0, 95)
    c.curve_to(-60, 70, -120, 30, -175, fl); c.curve_to(-120, -30, -70, -70, 0, -95); c.close_path(); c.fill()
    c.set_source_rgb(*top2)
    for (sx, sy) in ((-60, -10), (60, -10), (-30, 30), (30, 30), (0, 0), (-100, 8), (100, 8)): c.arc(sx, sy, 8, 0, 2 * math.pi); c.fill()
    for ex in (-26, 26):
        c.set_source_rgb(*rgb('#e8d870')); c.arc(ex, -52, 11, 0, 2 * math.pi); c.fill()
        c.set_source_rgb(0.05, 0.05, 0.05); c.arc(ex, -50 + 3 * bite, 5, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#2a323c')); c.set_line_width(6)
    c.move_to(-44, -72); c.line_to(-12, -62); c.stroke(); c.move_to(44, -72); c.line_to(12, -62); c.stroke()   # angry brows
    c.restore()

def draw_head_wake(c, x, t):
    """Wing tips flapping at the surface after the board snaps."""
    c.set_source_rgb(*rgb('#4a5a6a'))
    for dx, ph in ((-90, 0), (90, 1.2)):
        h = 30 + 16 * math.sin(t * 6 + ph)
        c.move_to(x + dx - 40, WATER + 8); c.curve_to(x + dx - 20, WATER - h, x + dx + 10, WATER - h, x + dx + 40, WATER + 8); c.close_path(); c.fill()

PALMS = [(70, 1.0), (980, -1.0)]
def draw_bg(c, t):
    c.set_source_rgb(*rgb('#101a2c')); c.rectangle(0, HEAD, W, H - HEAD); c.fill()
    for (sx, sy) in ((90, 420), (220, 520), (420, 400), (610, 480), (980, 430), (860, 380), (330, 470), (500, 560)):
        c.set_source_rgba(1, 1, 0.9, 0.5 + 0.3 * math.sin(t * 2 + sx)); c.arc(sx, sy, 3, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#e6dfc4')); c.arc(560, 520, 52, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#18222e')); c.move_to(0, 1160); c.curve_to(200, 1060, 380, 1080, 520, 1160); c.close_path(); c.fill()   # far island
    for (px, dirn) in PALMS:   # palm trees on little islands at the edges
        c.set_source_rgb(*rgb('#1e2a2a')); c.set_line_width(26); c.move_to(px, 1160); c.curve_to(px + 30 * dirn, 950, px + 60 * dirn, 820, px + 100 * dirn, 700); c.stroke()
        c.set_source_rgb(*rgb('#1a3a2c'))
        for k in range(6):
            a = -math.pi / 2 + (k - 2.5) * 0.55 + 0.05 * math.sin(t * 1.5 + k)
            tx, ty = px + 100 * dirn, 700
            c.move_to(tx, ty); c.curve_to(tx + 90 * math.cos(a), ty + 90 * math.sin(a) - 40, tx + 170 * math.cos(a), ty + 170 * math.sin(a), tx + 190 * math.cos(a), ty + 190 * math.sin(a) + 60)
            c.curve_to(tx + 150 * math.cos(a), ty + 150 * math.sin(a) + 10, tx + 80 * math.cos(a), ty + 80 * math.sin(a) - 10, tx, ty + 8); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#122a3a')); c.rectangle(0, 1155, W, H - 1155); c.fill()   # lagoon water
    c.set_source_rgba(0.9, 0.9, 0.8, 0.10)
    for i in range(6): c.rectangle(560 - 60 + 10 * math.sin(t * 2 + i), 1175 + i * 22, 120 - i * 12, 5); c.fill()
    c.set_source_rgba(1, 1, 1, 0.04)
    for i in range(8):
        off = (t * 30 + i * 137) % W
        c.rectangle(off - 200, 1200 + i * 90, 260, 4); c.fill()
    for i, x in enumerate(range(60, W, 160)):   # coral + sand deep below
        c.set_source_rgb(*rgb(('#3a2c3e', '#2c3a3e', '#3e2c30')[i % 3]))
        c.set_line_width(14); c.set_line_cap(cairo.LINE_CAP_ROUND)
        for b in (-1, 0, 1): c.move_to(x, H - 20); c.line_to(x + b * 40 + 6 * math.sin(t + x), H - 120 - (b == 0) * 40); c.stroke()
    c.set_source_rgb(*rgb('#2a2e30')); c.rectangle(0, H - 30, W, 30); c.fill()

def draw_water_front(c, t, f):
    c.set_source_rgba(0.05, 0.13, 0.2, 0.62); c.move_to(0, H)
    for x in range(0, W + 20, 20): c.line_to(x, WATER + 8 * math.sin(x * 0.02 + t * 2.2))
    c.line_to(W, H); c.close_path(); c.fill()
    c.set_source_rgba(1, 1, 1, 0.10); c.set_line_width(4)
    for x in range(0, W + 20, 20): (c.move_to if x == 0 else c.line_to)(x, WATER + 8 * math.sin(x * 0.02 + t * 2.2))
    c.stroke()

NLOG = 5; LOGW = (TANK_R - TANK_L + 80) / NLOG
def draw_raft(c, t, f):
    broke = T_FAIL is not None and t >= T_FAIL
    sp = 0.0 if not broke else ease((t - T_FAIL) / 0.8)
    bob = 3 * math.sin(t * 2); yb = DECK + bob
    x0 = TANK_L - 40
    for i, px in enumerate((TANK_L - 50, TANK_R - 40)):   # lava-rock pillars (walls)
        c.save(); c.translate(px + 45, yb)
        c.set_source_rgb(*rgb('#2e2a30')); c.move_to(-50, 90); c.line_to(-40, -170); c.curve_to(-30, -215, 30, -215, 40, -170); c.line_to(50, 90); c.close_path(); c.fill()
        c.set_source_rgb(*rgb('#3c3640')); c.move_to(-40, 90); c.line_to(-32, -170); c.curve_to(-26, -200, -10, -205, -8, -190); c.line_to(-14, 90); c.close_path(); c.fill()
        c.set_source_rgb(*rgb('#4a6a5a'))
        for k in range(3): c.arc(-20 + k * 20, -10 + k * 30, 9, 0, 2 * math.pi); c.fill()   # barnacles
        c.restore()
    sag = 18 * sp
    cols = ('#e8e0c8', '#e0d8be')
    for i in range(NLOG):   # the surfboard, side-on: 5 sections that drift apart when it snaps
        k = i - (NLOG - 1) / 2; dx = k * 50 * sp; dy = 40 * sp
        lx = x0 + i * LOGW + dx
        c.save(); c.translate(lx + LOGW / 2, yb + 18 + dy + sag); c.rotate(0.12 * k * sp)
        hw = LOGW / 2 + (0 if broke else 1)
        c.set_source_rgb(*rgb(cols[i % 2]))
        if i == 0: c.move_to(hw, -18); c.line_to(-hw + 40, -18); c.curve_to(-hw - 10, -18, -hw - 10, 18, -hw + 40, 18); c.line_to(hw, 18); c.close_path(); c.fill()
        elif i == NLOG - 1: c.move_to(-hw, -18); c.line_to(hw - 60, -18); c.curve_to(hw + 30, -16, hw + 30, -6, hw + 20, -2); c.curve_to(hw, 18, hw - 30, 18, hw - 60, 18); c.line_to(-hw, 18); c.close_path(); c.fill()
        else: c.rectangle(-hw, -18, 2 * hw, 36); c.fill()
        c.set_source_rgb(*rgb('#e0703a')); c.rectangle(-hw + (30 if i == 0 else 0), -4, 2 * hw - (30 if i == 0 else 0) - (40 if i == NLOG - 1 else 0), 8); c.fill()   # stripe
        c.set_source_rgb(*rgb('#3a8aa0')); c.rectangle(-hw + (30 if i == 0 else 0), 6, 2 * hw - (30 if i == 0 else 0) - (40 if i == NLOG - 1 else 0), 4); c.fill()
        c.restore()
    if not broke:
        c.set_source_rgb(*rgb('#2a2a2a')); c.move_to(x0 + 40, yb + 36); c.line_to(x0 + 70, yb + 66); c.line_to(x0 + 90, yb + 36); c.close_path(); c.fill()   # fin
    for (td, xd, d, kind) in DMG:   # punch dents / cracks
        if td > t: break
        if kind == 'ram' and not broke:
            c.set_source_rgb(*rgb('#122a3a')); c.save(); c.translate(xd, yb + 36); c.scale(26 if d > 10 else 18, 14 if d > 10 else 10); c.arc(0, 0, 1, math.pi, 2 * math.pi); c.restore(); c.fill()
            c.set_source_rgba(0.3, 0.25, 0.2, 0.6); c.set_line_width(3); c.move_to(xd - 10, yb + 24); c.line_to(xd + 4, yb + 8); c.line_to(xd - 4, yb); c.stroke()


PS = Particles(9)
CHIP = (0.9, 0.88, 0.8)
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
    if T_FAIL and abs(t - T_FAIL - 0.35) < 0.5 / FPS: PS.spawn(GX[fi], WATER, 30, (0.5, 0.65, 0.8), 700, 0.8, grav=2200, r=9)
    PS.draw(c)
    END.draw_claw(c, t)
    c.restore()
    END.header(c, t, fi)

if __name__ == '__main__':
    if sys.argv[1] == 'sim':
        print(SEED, S.OUTCOME, round(S.T_RES - S.T_START, 2), 'final', round(GL[int(S.T_RES * FPS) - 1]), 'gnaws', len([d for d in DMG if d[3] == 'ram']), 'lands', len([d for d in DMG if d[3] == 'land']), 'dur', S.DUR); sys.exit()
    run(S, render)
