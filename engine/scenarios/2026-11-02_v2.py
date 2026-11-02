"""2026-11-02 v2 — DAMAGE BAR – GLASS %: the PIRANHA TANK. Gloop is a passive rigid ball (Ball)
bouncing on a glass lid over a piranha tank. Every landing damages the glass in proportion to the
real impact speed; seeded-random piranha rams from below (some aimed under where he is) crack it
more and throw him up if he's on the glass. GLASS 0% = the lid shatters and he drops in."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the piranha tank'
SEED = int(os.environ.get('SEED', 17))
rng = random.Random(SEED)

class S: pass
S.HOOK2 = 'THE PIRANHA TANK?'; S.HOOK2_SIZE = 88; S.FAIL_WORD = 'SHATTERED!'; S.FAIL_SIZE = 130
S.T_START = HOOK_T; S.TL = 13.0; S.T_END = S.T_START + S.TL
GLASS = 1240; R = 58; XMIN, XMAX = 175, 905; TANK_L, TANK_R = XMIN - R, XMAX + R; WATER = GLASS + 70
LAND_K = 0.0012; RAM_D = (4, 14)

# --- seeded piranha rams
RAMS = []; t = 0.5
while t < S.T_END + 2:
    big = rng.random() < 0.4
    RAMS.append({'t': t, 'x': rng.uniform(TANK_L + 80, TANK_R - 80), 'big': big, 'aim': rng.random() < 0.3, 'fish': len(RAMS) % 5})
    t += rng.uniform(1.1, 2.7)
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
            if any(k == 'ram' and abs(xd - xl) < 70 for (_, xd, _, k) in DMG): d *= 2.2   # landing on a cracked spot hurts more
            d = round(d, 1); glass -= d; DMG.append((tl, xl, d, 'land'))
            if glass <= 0: glass = 0; T_FAIL = tl
    if T_FAIL is not None and ball.T is TER:
        ball.T = POOL; ball.vmin = 0; ball.e = 0.15; ball.vy = max(ball.vy, 200)
    if ball.T is POOL: ball.vx *= 0.9
    GX.append(ball.x); GYS.append(ball.y); GL.append(glass)
S.OUTCOME = 'fail' if T_FAIL else 'win'
S.T_RES = T_FAIL if T_FAIL else S.T_END
S.GRAB = (540, GLASS - R)
END = S.END = Ending(S)
gi = min(int(END.T_GRAB * FPS), N0 - 1); S.GRAB = (GX[gi], GYS[gi] - (14 if T_FAIL else 0))
S.events = [[0.05, 'rumble', 1.0]]
for r in RAMS:
    if r['t'] < S.T_RES + 0.2: S.events.append([r['t'], 'thump', 1.0 if r['big'] else 0.7]); S.events.append([r['t'], 'clink'])
for (tl, xl, imp) in ball.landings:
    if tl < S.T_RES + 1.5 and (T_FAIL is None or tl <= T_FAIL): S.events.append([tl, 'clink' if tl >= S.T_START else 'hop'])
for tw in ball.walls:
    if tw < S.T_RES: S.events.append([tw, 'thump', 0.3])
if T_FAIL: S.events += [[T_FAIL, 'crash'], [T_FAIL, 'crackle'], [T_FAIL + 0.35, 'splash']]
S.AMB = {'drone': 46}

def draw_bar(c, t, f):
    p = GL[f] / 100; recent = [d for d in DMG if d[0] <= t and t - d[0] < 0.3]
    bx = bar(c, p, f'GLASS {int(math.ceil(GL[f]))}%', good_bad_col(p), 0.12 if recent else 0, bw=640, x_off=36)
    c.save(); c.translate(bx - 52, 231); c.set_source_rgba(0.75, 0.92, 1, 0.9); rrect(c, -26, -26, 52, 52, 8); c.fill()
    c.set_source_rgb(0.2, 0.3, 0.4); c.set_line_width(4); c.move_to(-14, -18); c.line_to(2, 0); c.line_to(-8, 18); c.stroke(); c.move_to(2, 0); c.line_to(18, -6); c.stroke(); c.restore()
S.draw_bar = draw_bar

def fish_pos(i, t):
    F = FISH[i]; x = F['x0'] + 230 * math.sin(t * F['sp'] + F['ph']); y = F['y0'] + 40 * math.sin(t * 1.3 + F['ph'])
    dirx = math.cos(t * F['sp'] + F['ph']); ang = 0.0
    for r in RAMS:
        if r['fish'] == i and r['t'] - 0.45 <= t < r['t'] + 0.55 and r['t'] < S.T_RES + 0.1:
            if t < r['t']: k = ease((t - (r['t'] - 0.45)) / 0.45); x, y = lerp(x, r['x'], k), lerp(y, GLASS + 62, k * k); ang = -1.2 * k
            else: k = ease((t - r['t']) / 0.55); x, y = lerp(r['x'], x, k), lerp(GLASS + 62, y, k); ang = -1.2 * (1 - k)
    return x, y, (1 if dirx >= 0 else -1), ang

def draw_fish(c, x, y, d, ang, s, t):
    c.save(); c.translate(x, y); c.rotate(ang * d); c.scale(d * s, s)
    c.set_source_rgb(*rgb('#3f4752')); c.move_to(-70, 0); c.line_to(-110, -34 + 6 * math.sin(t * 14)); c.line_to(-110, 34 + 6 * math.sin(t * 14)); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#56606d')); c.save(); c.scale(1.25, 0.85); c.arc(0, 0, 60, 0, 2 * math.pi); c.restore(); c.fill()
    c.set_source_rgb(*rgb('#a8443c')); c.save(); c.scale(1.2, 0.5); c.arc(8, 34, 48, 0, math.pi); c.restore(); c.fill()
    c.set_source_rgb(*rgb('#e8e2d4'))
    for k in range(4): c.move_to(44 + k * 9, 6); c.line_to(48 + k * 9, 18); c.line_to(52 + k * 9, 6); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#ffd84a')); c.arc(36, -16, 10, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(0.05, 0.05, 0.05); c.arc(39, -16, 5, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#2c323a')); c.set_line_width(5); c.move_to(26, -30); c.line_to(48, -24); c.stroke()
    c.restore()

def draw_bg(c, t):
    c.set_source_rgb(*rgb('#14121c')); c.rectangle(0, HEAD, W, H - HEAD); c.fill()
    c.set_source_rgb(*rgb('#1b1826'))
    for x in range(0, W, 180): c.rectangle(x, HEAD, 90, GLASS - HEAD); c.fill()
    c.set_source_rgb(*rgb('#2a2433')); c.rectangle(0, 1120, W, 14); c.fill()
    c.set_source_rgba(0.6, 0.85, 0.9, 0.08); c.arc(W / 2, 650, 300, 0, 2 * math.pi); c.fill()   # dim round window
    c.set_source_rgb(*rgb('#2a2433')); c.set_line_width(14); c.arc(W / 2, 650, 300, 0, 2 * math.pi); c.stroke()
    # tank water
    c.set_source_rgb(*rgb('#173a45')); c.rectangle(TANK_L, WATER, TANK_R - TANK_L, H - WATER); c.fill()
    c.set_source_rgb(*rgb('#1d4652'))
    for i in range(6): c.rectangle(TANK_L, WATER + 30 + i * 100, TANK_R - TANK_L, 40); c.fill()
    c.set_source_rgb(*rgb('#2c5f5a'))
    for x in range(TANK_L + 40, TANK_R, 120):
        c.move_to(x, H); c.curve_to(x - 30 + 20 * math.sin(t * 2 + x), H - 140, x + 30, H - 200, x + 10 * math.sin(t * 1.5 + x), H - 260); c.line_to(x + 18, H); c.close_path(); c.fill()
    c.set_source_rgba(0.75, 0.9, 1, 0.25)
    for i in range(10):
        k = (t * 0.35 + i * 0.13) % 1; c.arc(TANK_L + 60 + (i * 97) % (TANK_R - TANK_L - 120), H - k * (H - WATER), 5 + i % 3 * 2, 0, 2 * math.pi); c.fill()

def draw_tank_front(c, t, f):
    # tank frame + pillars Gloop bounces between
    for (x0, x1) in ((0, TANK_L), (TANK_R, W)):
        c.set_source_rgb(*rgb('#3a3346')); c.rectangle(x0, 980, x1 - x0, H - 980); c.fill()
        c.set_source_rgb(*rgb('#2c2636'))
        for yy in range(980, H, 70): c.rectangle(x0, yy, x1 - x0, 5); c.fill()
    broke = T_FAIL is not None and t >= T_FAIL
    if not broke:
        p = GL[min(f, len(GL) - 1)] / 100
        c.set_source_rgba(0.7, 0.9, 1, 0.28 + 0.1 * (1 - p)); c.rectangle(TANK_L, GLASS, TANK_R - TANK_L, 26); c.fill()
        c.set_source_rgba(0.85, 0.97, 1, 0.75); c.set_line_width(4); c.move_to(TANK_L, GLASS + 1); c.line_to(TANK_R, GLASS + 1); c.stroke()
        c.set_source_rgba(1, 1, 1, 0.85); c.set_line_width(3)
        for (td, xd, d, kind) in DMG:
            if td > t: break
            rr = random.Random(int(td * 1000)); L = (28 if kind == 'land' else 60) * (0.6 + 0.4 * d / 6)
            for k in range(3 if kind == 'land' else 5):
                a = rr.uniform(-0.9, 0.9); c.move_to(xd, GLASS + 13); c.line_to(xd + math.cos(a) * L * rr.choice((-1, 1)), GLASS + 13 + math.sin(a) * 12); c.stroke()
    else:
        k = t - T_FAIL
        for i in range(14):
            rr = random.Random(i * 7 + 3); x0 = TANK_L + (i + 0.5) * (TANK_R - TANK_L) / 14
            vx = rr.uniform(-160, 160); y = GLASS + 13 + 900 * k * k + rr.uniform(-10, 10) * k
            if y > H + 40 or (k > 0.25 and y > WATER + 60): continue
            c.save(); c.translate(x0 + vx * k, y); c.rotate(rr.uniform(-1, 1) + k * rr.uniform(-6, 6))
            c.set_source_rgba(0.75, 0.92, 1, 0.6); c.move_to(-26, -6); c.line_to(22, -10); c.line_to(12, 10); c.close_path(); c.fill(); c.restore()
    # tank rim lips
    c.set_source_rgb(*rgb('#4a4258')); c.rectangle(TANK_L - 22, GLASS - 10, 22, 50); c.fill(); c.rectangle(TANK_R, GLASS - 10, 22, 50); c.fill()

PS = Particles(9)
def render(f, c):
    t = f / FPS; shake = (0, 0)
    for r in RAMS:
        if r['t'] <= t < r['t'] + 0.18 and r['t'] < S.T_RES + 0.1: a = 4 if r['big'] else 2; shake = (rng.uniform(-a, a), rng.uniform(-a, a))
    if T_FAIL and T_FAIL <= t < T_FAIL + 0.3: shake = (rng.uniform(-6, 6), rng.uniform(-6, 6))
    c.save(); c.translate(*shake)
    fi = min(f, len(GX) - 1)
    draw_bg(c, t)
    for i in range(5):
        x, y, d, ang = fish_pos(i, t); draw_fish(c, x, y, d, ang, FISH[i]['s'], t)
    fell = T_FAIL is not None and t >= T_FAIL
    if END.carried(t) or t >= END.T_GRAB: gx, gy = (END.carry_xy(t) if END.carried(t) else S.GRAB)
    else:
        gx, gy = GX[fi], GYS[fi]
        if fell and gy > WATER - R: gy = WATER - R * 0.55 + 6 * math.sin(t * 4)
    danger = any(r['t'] - 0.6 <= t < r['t'] + 0.2 and abs(r['x'] - GX[fi]) < 220 for r in RAMS)
    mood = 'happy' if (t >= S.T_END and S.OUTCOME == 'win') else ('scared' if danger or fell or GL[fi] < 30 else 'worried')
    if not fell and not END.carried(t):
        h = max(0, GLASS - R - gy); kk = 1 / (1 + h / 220)
        c.set_source_rgba(0, 0, 0, 0.25 * kk); c.save(); c.translate(gx, GLASS + 2); c.scale(R * (0.5 + 0.4 * kk), 8); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    draw_blob(c, t, gx, gy, mood, 0, R=R, dizzy=fell and t > T_FAIL + 0.6)
    if fell and not END.carried(t):   # water surface line over him + nibbling fish circling
        c.set_source_rgba(0.1, 0.28, 0.34, 0.55); c.rectangle(TANK_L, WATER, TANK_R - TANK_L, 120); c.fill()
        for j in range(3):
            a = t * 2.4 + j * 2.1; draw_fish(c, gx + math.cos(a) * 150, WATER + 70 + math.sin(a) * 30, (1 if math.sin(a) < 0 else -1), 0, 0.55, t)
    draw_tank_front(c, t, f)
    for (td, xd, d, kind) in DMG:
        if td <= t < td + 0.8 and (kind == 'ram' or d >= 2.5):
            k = (t - td) / 0.8; text_at(c, f'-{d:g}%', xd + (70 if xd < 540 else -70), GLASS - 120 - 70 * k, 56 if kind == 'ram' else 44, rgb('#ff6b5a'))
        if abs(t - td) < 0.5 / FPS: PS.spawn(xd, GLASS + 12, 8 if kind == 'land' else 14, (0.8, 0.95, 1), 300, 0.5, grav=900, r=5)
    if T_FAIL and abs(t - T_FAIL - 0.35) < 0.5 / FPS: PS.spawn(GX[fi], WATER, 30, (0.6, 0.85, 0.95), 700, 0.8, grav=2200, r=9)
    PS.draw(c)
    END.draw_claw(c, t)
    c.restore()
    END.header(c, t, fi)

if __name__ == '__main__':
    if sys.argv[1] == 'sim':
        print(SEED, S.OUTCOME, round(S.T_RES - S.T_START, 2), 'final', round(GL[int(S.T_RES * FPS) - 1]), 'rams', len([d for d in DMG if d[3] == 'ram']), 'lands', len([d for d in DMG if d[3] == 'land']), 'avgland', round(sum(d[2] for d in DMG if d[3] == 'land') / max(1, len([d for d in DMG if d[3] == 'land'])), 1), 'dur', S.DUR); sys.exit()
    run(S, render)
