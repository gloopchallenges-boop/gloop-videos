"""2026-11-03 v6 — DAMAGE BAR – RAFT %: the HUNGRY SHARK. Gloop is a passive rigid ball (Ball)
bouncing on an inflatable raft at sea (the raft's side tubes are the walls). Every landing squeezes air
out in proportion to the real impact speed; a seeded-random shark bites the raft from below (some bites
aimed under where he is) — each bite tears it more and throws him up if he's on the floor.
RAFT 0% = the raft deflates and sinks, Gloop ends up bobbing in the sea."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the hungry shark'
SEED = int(os.environ.get('SEED', 17))
rng = random.Random(SEED)

class S: pass
S.HOOK2 = 'THE HUNGRY SHARK?'; S.HOOK2_SIZE = 90; S.FAIL_WORD = 'DEFLATED!'; S.FAIL_SIZE = 140
S.T_START = HOOK_T; S.TL = 14.0; S.T_END = S.T_START + S.TL
GLASS = 1300; R = 58; XMIN, XMAX = 200, 880; TANK_L, TANK_R = XMIN - R, XMAX + R; WATER = GLASS + 40
LAND_K = float(os.environ.get('LAND_K', 0.0008)); RAM_D = (float(os.environ.get('BITE_S', 5)), float(os.environ.get('BITE_B', 18)))

# --- seeded piranha rams
RAMS = []; t = 0.5
while t < S.T_END + 2:
    big = rng.random() < 0.4
    RAMS.append({'t': t, 'x': rng.uniform(TANK_L + 80, TANK_R - 80), 'big': big, 'aim': rng.random() < 0.3, 'fish': 0})
    t += rng.uniform(1.3, 2.9)
FISH = [{'x0': rng.uniform(250, 830), 'y0': rng.uniform(WATER + 160, 1800), 'ph': rng.uniform(0, 6.3), 'sp': rng.uniform(0.5, 0.9), 's': rng.uniform(0.9, 1.15)} for _ in range(5)]

TER = Terrain(GLASS, seed=SEED, bumps=0, amp=0, soft=False)
POOL = Terrain(WATER + 20, seed=SEED, bumps=0, amp=0, soft=False)
N0 = int(40 * FPS); GX, GYS, GL = [], [], []
ball = Ball(rng.uniform(330, 750), TER, R=R, seed=SEED, xmin=XMIN, xmax=XMAX, hop=rng.uniform(250, 310))
glass = 100.0; T_FAIL = None; DMG = []   # (t, x, amount, kind)
nl = 0
for f in range(N0):
    t = f / FPS
    live = T_FAIL is None and S.T_START <= t < S.T_END
    for r in RAMS:
        if abs(t - (r['t'] - 0.45)) < 0.5 / FPS and r['aim']: r['x'] = clamp(ball.x + rng.uniform(-50, 50), TANK_L + 60, TANK_R - 60)
        if abs(t - r['t']) < 0.5 / FPS and T_FAIL is None:
            if abs(ball.x - r['x']) < 150 and ball.height() < 20:   # the thump throws him only if he's on the glass
                ball.push((ball.x - r['x']) * 2.2, -650)
            if live:
                d = RAM_D[1] if r['big'] else RAM_D[0]; glass -= d; DMG.append((t, r['x'], d, 'ram'))
                if glass <= 0: glass = 0; T_FAIL = t
    ball.step(t)
    while nl < len(ball.landings):
        tl, xl, imp = ball.landings[nl]; nl += 1
        if T_FAIL is None and S.T_START <= tl < S.T_END:
            d = LAND_K * imp
            if any(k == 'ram' and abs(xd - xl) < 70 for (_, xd, _, k) in DMG): d *= 1.8   # landing next to a bite hole leaks more
            d = round(d, 1); glass -= d; DMG.append((tl, xl, d, 'land'))
            if glass <= 0: glass = 0; T_FAIL = tl
    if T_FAIL is not None and ball.T is TER:
        ball.T = POOL; ball.vmin = 0; ball.e = 0.15; ball.vy = max(ball.vy, 120)
    if ball.T is POOL: ball.vx *= 0.9
    GX.append(ball.x); GYS.append(ball.y); GL.append(glass)
S.OUTCOME = 'fail' if T_FAIL else 'win'
S.T_RES = T_FAIL if T_FAIL else S.T_END
S.GRAB = (540, GLASS - R)
END = S.END = Ending(S)
gi = min(int(END.T_GRAB * FPS), N0 - 1); S.GRAB = (GX[gi], GYS[gi] - (14 if T_FAIL else 0))
S.events = [[0.05, 'rumble', 1.0]]
for r in RAMS:
    if r['t'] < S.T_RES + 0.2: S.events.append([r['t'], 'thump', 1.0 if r['big'] else 0.7]); S.events.append([r['t'] - 0.2, 'splash'])
for (tl, xl, imp) in ball.landings:
    if tl < S.T_RES + 1.5 and (T_FAIL is None or tl <= T_FAIL): S.events.append([tl, 'hop'])
for tw in ball.walls:
    if tw < S.T_RES: S.events.append([tw, 'thump', 0.3])
if T_FAIL: S.events += [[T_FAIL, 'whoosh'], [T_FAIL + 0.1, 'pop'], [T_FAIL + 0.35, 'splash']]
S.AMB = {'drone': 46, 'wind': 0.03}

def draw_bar(c, t, f):
    p = GL[f] / 100; recent = [d for d in DMG if d[0] <= t and t - d[0] < 0.3]
    bx = bar(c, p, f'RAFT {int(math.ceil(GL[f]))}%', good_bad_col(p), 0.12 if recent else 0, bw=640, x_off=36)
    c.save(); c.translate(bx - 52, 231); c.set_source_rgb(*rgb('#e0603a')); rrect(c, -30, -16, 60, 32, 16); c.fill()
    c.set_source_rgb(*rgb('#f0c040')); c.rectangle(-8, -16, 16, 32); c.fill(); c.restore()
S.draw_bar = draw_bar

def shark_pos(t):
    """Fin cruising on the surface; for a bite it dives and lunges up under the raft at r['x']."""
    x = 540 + 470 * math.sin(t * 0.7); y = WATER + 300; d = 1 if math.cos(t * 0.7) >= 0 else -1; ang = 0.0; bite = 0.0; cruise = True
    for r in RAMS:
        if r['t'] - 0.5 <= t < r['t'] + 0.6 and r['t'] < S.T_RES + 0.1:
            cruise = False
            if t < r['t']: k = ease((t - (r['t'] - 0.5)) / 0.5); x, y = lerp(x, r['x'], k), lerp(WATER + 330, GLASS + 120, k); ang = -1.1 * k; bite = k
            else: k = ease((t - r['t']) / 0.6); x, y = lerp(r['x'], x, k), lerp(GLASS + 120, WATER + 330, k); ang = -1.1 * (1 - k); bite = 1 - k
    return x, y, d, ang, bite, cruise

def draw_shark(c, x, y, d, ang, bite, t):
    c.save(); c.translate(x, y); c.rotate(ang * d); c.scale(d, 1)
    c.set_source_rgb(*rgb('#4a5664')); c.move_to(-150, 0); c.line_to(-230, -50 + 8 * math.sin(t * 10)); c.line_to(-215, 0); c.line_to(-230, 50 + 8 * math.sin(t * 10)); c.close_path(); c.fill()
    c.move_to(-40, -50); c.line_to(-10, -140); c.line_to(40, -50); c.close_path(); c.fill()
    c.save(); c.scale(1.9, 0.75); c.arc(0, 0, 90, 0, 2 * math.pi); c.restore(); c.fill()
    c.set_source_rgb(*rgb('#c8ccd2')); c.save(); c.translate(20, 30); c.scale(140, 30); c.arc(0, 0, 1, 0, math.pi); c.restore(); c.fill()
    c.set_source_rgb(0.05, 0.05, 0.08); c.arc(110, -18, 7, 0, 2 * math.pi); c.fill()
    if bite > 0.2:
        c.set_source_rgb(*rgb('#3a1a22')); c.move_to(170, 0); c.line_to(90, 20 + 30 * bite); c.line_to(170, 30 + 30 * bite); c.close_path(); c.fill()
        c.set_source_rgb(*rgb('#eee8d8'))
        for k in range(4): c.move_to(110 + k * 14, 18); c.line_to(117 + k * 14, 32); c.line_to(124 + k * 14, 18); c.close_path(); c.fill()
    c.restore()

def draw_fin(c, x, t):
    c.set_source_rgb(*rgb('#4a5664')); c.move_to(x - 40, WATER + 6); c.line_to(x + 5 * math.sin(t * 3), WATER - 90); c.line_to(x + 30, WATER + 6); c.close_path(); c.fill()

stars = [(rng.uniform(0, W), rng.uniform(HEAD, 1050), rng.uniform(1.2, 2.6)) for _ in range(60)]
def draw_bg(c, t):
    c.set_source_rgb(*rgb('#121826')); c.rectangle(0, HEAD, W, H - HEAD); c.fill()
    c.set_source_rgba(0.85, 0.88, 0.95, 0.5)
    for x, y, r in stars: c.arc(x, y, r, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#e6e2cc')); c.arc(800, 620, 56, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#1a2233')); c.move_to(0, 1150); c.line_to(120, 1110); c.line_to(260, 1135); c.line_to(330, 1150); c.close_path(); c.fill()   # far island
    c.set_source_rgb(*rgb('#14304a')); c.rectangle(0, 1150, W, H - 1150); c.fill()   # sea
    c.set_source_rgba(0.9, 0.9, 0.8, 0.12)
    for i in range(7): c.rectangle(800 - 70 + 12 * math.sin(t * 2 + i), 1170 + i * 22, 140 - i * 12, 5); c.fill()   # moon path
    c.set_source_rgba(1, 1, 1, 0.05)
    for i in range(8): c.rectangle(0, 1200 + i * 90, W, 5); c.fill()

def draw_water_front(c, t, f):
    c.set_source_rgba(0.08, 0.2, 0.32, 0.6); c.move_to(0, H)
    for x in range(0, W + 20, 20): c.line_to(x, WATER + 8 * math.sin(x * 0.02 + t * 2.2))
    c.line_to(W, H); c.close_path(); c.fill()
    c.set_source_rgba(1, 1, 1, 0.12); c.set_line_width(4)
    for x in range(0, W + 20, 20): (c.move_to if x == 0 else c.line_to)(x, WATER + 8 * math.sin(x * 0.02 + t * 2.2))
    c.stroke()

def draw_raft(c, t, f):
    p = GL[min(f, len(GL) - 1)] / 100
    broke = T_FAIL is not None and t >= T_FAIL
    sag = 0.0 if not broke else ease((t - T_FAIL) / 0.7)
    yb = GLASS + 6 + 160 * sag; bob = 3 * math.sin(t * 2)
    th = 46 * (1 - 0.55 * sag)   # side tubes deflate
    c.set_source_rgb(*rgb('#b2482c')); rrect(c, TANK_L - 40, yb + bob, TANK_R - TANK_L + 80, 30, 14); c.fill()   # floor
    for (x0) in (TANK_L - 50, TANK_R - 40):   # side tubes = walls
        c.set_source_rgb(*rgb('#e0603a')); rrect(c, x0, yb - 170 * (1 - sag) - th + bob, 90, 170 * (1 - sag) + th + 30, 40); c.fill()
        c.set_source_rgb(*rgb('#f0c040')); c.rectangle(x0, yb - 80 * (1 - sag) + bob, 90, 22); c.fill()
    c.set_source_rgb(*rgb('#e0603a')); rrect(c, TANK_L - 50, yb + 10 + bob, TANK_R - TANK_L + 100, th, th / 2); c.fill()   # bottom tube
    c.set_source_rgb(*rgb('#f0c040'))
    for x in range(int(TANK_L), int(TANK_R), 120): c.rectangle(x, yb + 10 + bob, 22, th); c.fill()
    for (td, xd, d, kind) in DMG:   # bite holes / patches
        if td > t: break
        if kind == 'ram':
            c.set_source_rgb(*rgb('#2a1210')); c.save(); c.translate(xd, yb + 10 + th * 0.5 + bob); c.scale(26, th * 0.3); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    if not broke and p < 0.999:   # air leaking
        for (td, xd, d, kind) in DMG:
            if kind == 'ram' and td <= t:
                k = (t * 2 + xd) % 1; c.set_source_rgba(1, 1, 1, 0.35 * (1 - k)); c.arc(xd + 20 * k, yb + 30 - 60 * k + bob, 6 + 8 * k, 0, 2 * math.pi); c.fill()

PS = Particles(9)
def render(f, c):
    t = f / FPS; shake = (0, 0)
    for r in RAMS:
        if r['t'] <= t < r['t'] + 0.18 and r['t'] < S.T_RES + 0.1: a = 4 if r['big'] else 2; shake = (rng.uniform(-a, a), rng.uniform(-a, a))
    if T_FAIL and T_FAIL <= t < T_FAIL + 0.3: shake = (rng.uniform(-6, 6), rng.uniform(-6, 6))
    c.save(); c.translate(*shake)
    fi = min(f, len(GX) - 1)
    draw_bg(c, t)
    sx, sy, sd, sang, sbite, cruise = shark_pos(t)
    draw_shark(c, sx, sy, sd, sang, sbite, t)
    fell = T_FAIL is not None and t >= T_FAIL
    if END.carried(t) or t >= END.T_GRAB: gx, gy = (END.carry_xy(t) if END.carried(t) else S.GRAB)
    else:
        gx, gy = GX[fi], GYS[fi]
        if fell and gy > WATER - R * 0.6: gy = WATER - R * 0.6 + 6 * math.sin(t * 4)
    danger = any(r['t'] - 0.6 <= t < r['t'] + 0.2 and abs(r['x'] - GX[fi]) < 220 for r in RAMS)
    mood = 'happy' if (t >= S.T_END and S.OUTCOME == 'win') else ('scared' if danger or fell or GL[fi] < 30 else 'worried')
    draw_raft(c, t, f)
    if not fell and not END.carried(t):
        h = max(0, GLASS - R - gy); kk = 1 / (1 + h / 220)
        c.set_source_rgba(0, 0, 0, 0.25 * kk); c.save(); c.translate(gx, GLASS + 4); c.scale(R * (0.5 + 0.4 * kk), 8); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    draw_blob(c, t, gx, gy, mood, 0, R=R, dizzy=fell and t > T_FAIL + 0.6)
    draw_water_front(c, t, f)
    if fell and not END.carried(t) and t > T_FAIL + 0.5:
        a_ = t * 1.8; draw_fin(c, gx + 220 * math.cos(a_), t)
    for (td, xd, d, kind) in DMG:
        if td <= t < td + 0.8 and (kind == 'ram' or d >= 2.5):
            k = (t - td) / 0.8; text_at(c, f'-{d:g}%', xd + (70 if xd < 540 else -70), GLASS - 120 - 70 * k, 56 if kind == 'ram' else 44, rgb('#ff6b5a'))
        if abs(t - td) < 0.5 / FPS: PS.spawn(xd, GLASS + 30, 8 if kind == 'land' else 16, (0.7, 0.85, 0.95), 300 if kind == 'land' else 500, 0.5, grav=900, r=5 if kind == 'land' else 8)
    if T_FAIL and abs(t - T_FAIL - 0.35) < 0.5 / FPS: PS.spawn(GX[fi], WATER, 30, (0.6, 0.85, 0.95), 700, 0.8, grav=2200, r=9)
    PS.draw(c)
    END.draw_claw(c, t)
    c.restore()
    END.header(c, t, fi)

if __name__ == '__main__':
    if sys.argv[1] == 'sim':
        print(SEED, S.OUTCOME, round(S.T_RES - S.T_START, 2), 'final', round(GL[int(S.T_RES * FPS) - 1]), 'bites', len([d for d in DMG if d[3] == 'ram']), 'lands', len([d for d in DMG if d[3] == 'land']), 'avgland', round(sum(d[2] for d in DMG if d[3] == 'land') / max(1, len([d for d in DMG if d[3] == 'land'])), 1), 'dur', S.DUR); sys.exit()
    run(S, render)
