"""2026-11-05 v1 — DAMAGE BAR – LOG %: the ANGRY BEAVER. Gloop is a passive rigid ball (Ball)
bouncing on a raft of tied logs drifting on a forest river at night (two upright stump posts at the raft
ends are the walls). Every landing loosens the lashings in proportion to the real impact speed; a
seeded-random beaver dives and lunges up from below gnawing the logs (some gnaws aimed under where he
is) — each gnaw cuts a notch and throws him up if he's on the logs. LOG 0% = the raft splits apart and
Gloop splashes into the river."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the angry beaver'
SEED = int(os.environ.get('SEED', 15))
rng = random.Random(SEED)

class S: pass
S.HOOK2 = 'THE ANGRY BEAVER?'; S.HOOK2_SIZE = 90; S.FAIL_WORD = 'SPLIT!'; S.FAIL_SIZE = 150
S.T_START = HOOK_T; S.TL = 13.0; S.T_END = S.T_START + S.TL
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
    bx = bar(c, p, f'LOG {int(math.ceil(GL[f]))}%', good_bad_col(p), 0.12 if recent else 0, bw=640, x_off=36)
    c.save(); c.translate(bx - 52, 231)   # little log icon
    c.set_source_rgb(*rgb('#8a5a32')); rrect(c, -32, -15, 64, 30, 15); c.fill()
    c.set_source_rgb(*rgb('#d9b07a')); c.arc(22, 0, 12, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#8a5a32')); c.set_line_width(2.5); c.arc(22, 0, 6, 0, 2 * math.pi); c.stroke(); c.restore()
S.draw_bar = draw_bar

def beaver_pos(t):
    """Beaver swimming at the surface; for a gnaw it dives and lunges up under the raft at r['x']."""
    x = 540 + 430 * math.sin(t * 0.8); y = WATER + 260; d = 1 if math.cos(t * 0.8) >= 0 else -1; ang = 0.0; bite = 0.0
    for r in RAMS:
        if r['t'] - 0.5 <= t < r['t'] + 0.6 and r['t'] < S.T_RES + 0.1:
            if t < r['t']: k = ease((t - (r['t'] - 0.5)) / 0.5); x, y = lerp(x, r['x'], k), lerp(WATER + 280, DECK + 110, k); ang = -1.2 * k; bite = k
            else: k = ease((t - r['t']) / 0.6); x, y = lerp(r['x'], x, k), lerp(DECK + 110, WATER + 280, k); ang = -1.2 * (1 - k); bite = 1 - k
    return x, y, d, ang, bite

def draw_beaver(c, x, y, d, ang, bite, t):
    c.save(); c.translate(x, y); c.rotate(ang * d); c.scale(d, 1)
    c.set_source_rgb(*rgb('#3a2c26'))   # flat paddle tail
    c.save(); c.translate(-170, 6 * math.sin(t * 6)); c.scale(80, 28); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    c.set_source_rgb(*rgb('#2c211c')); c.set_line_width(2)
    for k in range(-2, 3): c.move_to(-230, k * 10); c.line_to(-110, k * 10); c.stroke()
    c.set_source_rgb(*rgb('#6a4a32')); c.save(); c.scale(1.5, 0.85); c.arc(0, 0, 90, 0, 2 * math.pi); c.restore(); c.fill()
    c.set_source_rgb(*rgb('#5a3e2a')); c.arc(95, -25, 62, 0, 2 * math.pi); c.fill()   # head
    c.arc(70, -80, 16, 0, 2 * math.pi); c.fill()   # ear
    c.set_source_rgb(*rgb('#2a1c16')); c.arc(150, -28, 12, 0, 2 * math.pi); c.fill()   # nose
    c.set_source_rgb(0.05, 0.04, 0.04); c.arc(112, -45, 7, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#3a2a20')); c.set_line_width(5); c.move_to(98, -58); c.line_to(126, -50); c.stroke()   # angry brow
    c.set_source_rgb(*rgb('#e8d6a8'))   # big front teeth
    op = 10 * bite
    c.rectangle(128, -10 + op * 0.2, 12, 26 + op); c.fill(); c.rectangle(142, -10 + op * 0.2, 12, 26 + op); c.fill()
    c.set_source_rgb(*rgb('#5a3e2a')); c.save(); c.translate(40, 70); c.scale(26, 14); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()   # paw
    c.restore()

def draw_head_wake(c, x, t):
    """Beaver's head poking out of the water while circling after the split."""
    c.set_source_rgb(*rgb('#5a3e2a')); c.save(); c.translate(x, WATER + 4); c.scale(46, 34); c.arc(0, 0, 1, math.pi, 2 * math.pi); c.restore(); c.fill()
    c.set_source_rgb(0.05, 0.04, 0.04); c.arc(x + 14, WATER - 16, 5, 0, 2 * math.pi); c.fill()

stars = [(rng.uniform(0, W), rng.uniform(HEAD, 900), rng.uniform(1.2, 2.6)) for _ in range(55)]
TREES = [(x, rng.uniform(780, 960), rng.uniform(70, 110)) for x in range(-40, W + 80, 85)]
def draw_bg(c, t):
    c.set_source_rgb(*rgb('#121a22')); c.rectangle(0, HEAD, W, H - HEAD); c.fill()
    c.set_source_rgba(0.85, 0.88, 0.95, 0.5)
    for x, y, r in stars: c.arc(x, y, r, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#e6e2cc')); c.arc(780, 560, 54, 0, 2 * math.pi); c.fill()
    for i, (x, top, w) in enumerate(TREES):   # pine forest on the far bank
        c.set_source_rgb(*rgb('#16241f' if i % 2 else '#1a2b24'))
        c.move_to(x, top); c.line_to(x + w * 0.6, 1160); c.line_to(x - w * 0.6, 1160); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#1c2a22')); c.rectangle(0, 1120, W, 40); c.fill()
    c.set_source_rgb(*rgb('#173040')); c.rectangle(0, 1155, W, H - 1155); c.fill()   # river
    c.set_source_rgba(0.9, 0.9, 0.8, 0.12)
    for i in range(7): c.rectangle(780 - 70 + 12 * math.sin(t * 2 + i), 1175 + i * 22, 140 - i * 12, 5); c.fill()
    c.set_source_rgba(1, 1, 1, 0.05)
    for i in range(8):
        off = (t * 60 + i * 137) % W
        c.rectangle(off - 200, 1200 + i * 90, 260, 4); c.fill()   # current streaks drifting by

def draw_water_front(c, t, f):
    c.set_source_rgba(0.07, 0.18, 0.26, 0.62); c.move_to(0, H)
    for x in range(0, W + 20, 20): c.line_to(x, WATER + 8 * math.sin(x * 0.02 + t * 2.2))
    c.line_to(W, H); c.close_path(); c.fill()
    c.set_source_rgba(1, 1, 1, 0.12); c.set_line_width(4)
    for x in range(0, W + 20, 20): (c.move_to if x == 0 else c.line_to)(x, WATER + 8 * math.sin(x * 0.02 + t * 2.2))
    c.stroke()

NLOG = 6; LOGW = (TANK_R - TANK_L + 80) / NLOG
def draw_raft(c, t, f):
    broke = T_FAIL is not None and t >= T_FAIL
    sp = 0.0 if not broke else ease((t - T_FAIL) / 0.8)
    bob = 3 * math.sin(t * 2); yb = DECK + bob
    x0 = TANK_L - 40
    # end posts (walls)
    for i, px in enumerate((TANK_L - 50, TANK_R - 40)):
        dx = (-1 if i == 0 else 1) * 260 * sp
        c.save(); c.translate(px + 45 + dx, yb); c.rotate((-1 if i == 0 else 1) * 0.6 * sp)
        c.set_source_rgb(*rgb('#6a4628')); rrect(c, -40, -200, 80, 250, 18); c.fill()
        c.set_source_rgb(*rgb('#c9a06a')); c.save(); c.translate(0, -200); c.scale(40, 14); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
        c.set_source_rgb(*rgb('#8a6038')); c.set_line_width(3); c.save(); c.translate(0, -200); c.scale(22, 7); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.stroke()
        c.restore()
    for i in range(NLOG):   # logs seen side-on as a long deck, split into sections
        k = i - (NLOG - 1) / 2; dx = k * 70 * sp; dy = 90 * sp * (1 + abs(k) * 0.3)
        lx = x0 + i * LOGW + dx
        c.save(); c.translate(lx + LOGW / 2, yb + 28 + dy); c.rotate(k * 0.12 * sp)
        c.set_source_rgb(*rgb('#7a5030' if i % 2 else '#6e482b')); rrect(c, -LOGW / 2, -26, LOGW - 4, 52, 22); c.fill()
        c.set_source_rgba(0, 0, 0, 0.18); c.set_line_width(3)
        c.move_to(-LOGW / 2 + 20, -6); c.line_to(LOGW / 2 - 30, -8); c.stroke(); c.move_to(-LOGW / 2 + 40, 10); c.line_to(LOGW / 2 - 50, 12); c.stroke()
        if not broke:   # rope lashings
            c.set_source_rgb(*rgb('#c8b07a')); c.rectangle(LOGW / 2 - 14, -28, 10, 56); c.fill()
        c.restore()
    for (td, xd, d, kind) in DMG:   # gnaw notches in the logs
        if td > t: break
        if kind == 'ram' and not broke:
            c.set_source_rgb(*rgb('#d9b07a')); c.move_to(xd - 26, yb + 54); c.line_to(xd, yb + 22); c.line_to(xd + 26, yb + 54); c.close_path(); c.fill()
            c.set_source_rgb(*rgb('#3a2414')); c.set_line_width(3); c.move_to(xd - 26, yb + 54); c.line_to(xd, yb + 22); c.line_to(xd + 26, yb + 54); c.stroke()

PS = Particles(9)
CHIP = (0.85, 0.66, 0.4)
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
