"""2026-11-24 v2 — DAMAGE BAR – PALLET %: the HUNGRY BARRACUDA (based on 2026-11-18 v3). Gloop is a passive rigid
ball (Ball) bouncing on a floating wooden pallet in a mangrove swamp at night (two mangrove root clumps are the walls). Every
landing loosens the raft in proportion to the real impact speed; a seeded-random sea serpent cruises below and
rams up from underneath to smash dents into the barrels (some aimed under where he is) — each ram jolts him up if
he's on the raft. RAFT 0% = it falls apart and Gloop splashes into the sea."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the hungry barracuda'
SEED = int(os.environ.get('SEED', 11))
rng = random.Random(SEED)

class S: pass
S.HOOK2 = 'THE HUNGRY BARRACUDA?'; S.HOOK2_SIZE = 74; S.FAIL_WORD = 'CRASH!'; S.FAIL_SIZE = 150; 
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
S.AMB = {'drone': 40, 'wind': 0.045}

def draw_bar(c, t, f):
    p = GL[f] / 100; recent = [d for d in DMG if d[0] <= t and t - d[0] < 0.3]
    bx = bar(c, p, f'PALLET {int(math.ceil(GL[f]))}%', good_bad_col(p), 0.12 if recent else 0, bw=640, x_off=36)
    c.save(); c.translate(bx - 52, 231)   # little pallet icon
    c.set_source_rgb(*rgb('#b89060')); c.rectangle(-24, -18, 48, 10); c.fill(); c.rectangle(-24, 10, 48, 8); c.fill()
    c.set_source_rgb(*rgb('#8a6a40')); c.rectangle(-22, -8, 10, 18); c.fill(); c.rectangle(-5, -8, 10, 18); c.fill(); c.rectangle(12, -8, 10, 18); c.fill(); c.restore()
S.draw_bar = draw_bar

def beaver_pos(t):
    """Swordfish cruising under the surface; for a stab it dives and lunges up under the float at r['x']."""
    x = 540 + 330 * math.sin(t * 0.8); y = WATER + 280; d = 1 if math.cos(t * 0.8) >= 0 else -1; ang = 0.0; bite = 0.0
    for r in RAMS:
        if r['t'] - 0.5 <= t < r['t'] + 0.6 and r['t'] < S.T_RES + 0.1:
            if t < r['t']: k = ease((t - (r['t'] - 0.5)) / 0.5); x, y = lerp(x, r['x'], k), lerp(WATER + 280, DECK + 205, k); ang = -1.25 * k; bite = k
            else: k = ease((t - r['t']) / 0.6); x, y = lerp(r['x'], x, k), lerp(DECK + 205, WATER + 280, k); ang = -1.25 * (1 - k); bite = 1 - k
    return x, y, d, ang, bite

def draw_beaver(c, x, y, d, ang, bite, t):   # the barracuda: long silver torpedo body, big underbite, rams head-up
    c.save(); c.translate(x, y - 40 * bite); c.rotate(ang * d if bite > 0 else 0.04 * math.sin(t * 2)); c.scale(d, 1)
    body, belly, dark = rgb('#8a9aa8'), rgb('#d8e0e4'), rgb('#4a5a6a')
    fl = 12 * math.sin(t * 10)
    c.set_source_rgb(*dark); c.move_to(-170, 0); c.line_to(-230, -46 + fl); c.line_to(-210, 0); c.line_to(-230, 46 + fl); c.close_path(); c.fill()   # tail
    c.move_to(-60, -30); c.line_to(-40, -64); c.line_to(-10, -30); c.close_path(); c.fill()   # dorsal fins
    c.move_to(-130, -22); c.line_to(-118, -48); c.line_to(-100, -22); c.close_path(); c.fill()
    c.set_source_rgb(*body); c.save(); c.scale(185, 38); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    c.set_source_rgb(*belly); c.save(); c.translate(0, 14); c.scale(170, 18); c.arc(0, 0, 1, 0, math.pi); c.restore(); c.fill()
    c.set_source_rgb(*dark)
    for k in range(8): c.move_to(-140 + k * 30, -30); c.line_to(-150 + k * 30, 10); c.set_line_width(5); c.stroke()   # dark bars
    c.set_source_rgb(*body); c.move_to(140, -20); c.line_to(230, -4); c.line_to(140, 8); c.close_path(); c.fill()   # upper jaw
    c.set_source_rgb(*belly); c.move_to(130, 8); c.line_to(246, 14 - 14 * bite); c.line_to(236, 26); c.line_to(130, 30); c.close_path(); c.fill()   # big underbite
    c.set_source_rgb(1, 1, 0.95)
    for tx in (160, 182, 204, 224): c.move_to(tx, 10 - 4 * bite); c.line_to(tx + 5, -6 - 4 * bite); c.line_to(tx + 10, 10 - 4 * bite); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#f0e68a')); c.arc(126, -12, 12, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(0.05, 0.05, 0.05); c.arc(129, -12, 6, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*dark); c.set_line_width(5); c.move_to(108, -30); c.line_to(144, -22); c.stroke()   # angry brow
    c.restore()

def draw_head_wake(c, x, t):
    """Barracuda fin circling at the surface after the pallet breaks."""
    c.set_source_rgb(*rgb('#4a5a6a')); c.move_to(x - 30, WATER + 10); c.line_to(x + 6, WATER - 56); c.line_to(x + 34, WATER + 10); c.close_path(); c.fill()

def draw_bg(c, t):
    c.set_source_rgb(*rgb('#0e1820')); c.rectangle(0, HEAD, W, H - HEAD); c.fill()
    for (sx, sy) in ((90, 420), (220, 520), (420, 400), (610, 480), (980, 430), (860, 380), (330, 470), (500, 560)):
        c.set_source_rgba(1, 1, 1, 0.5 + 0.3 * math.sin(t * 2 + sx)); c.arc(sx, sy, 3, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#e6dfc4')); c.arc(800, 560, 44, 0, 2 * math.pi); c.fill()
    # distant mangrove silhouettes
    c.set_source_rgb(*rgb('#16241e'))
    for (cx, cy, rr) in ((80, 1060, 120), (260, 1030, 140), (460, 1080, 110), (650, 1050, 130), (860, 1040, 140), (1040, 1070, 110)):
        c.arc(cx, cy, rr, 0, 2 * math.pi); c.fill()
    c.rectangle(0, 1060, W, 100); c.fill()
    c.set_source_rgb(*rgb('#1c2c24')); c.set_line_width(5)
    for k in range(18):   # arching prop roots
        x0 = 30 + k * 60; c.move_to(x0, 1155); c.curve_to(x0 + 10, 1110, x0 + 40, 1100, x0 + 50, 1155); c.stroke()
    for k in range(7):   # fireflies
        fx = (150 + k * 151 + 40 * math.sin(t * 0.7 + k)) % W; fy = 900 + 60 * math.sin(t * 0.9 + k * 2)
        c.set_source_rgba(0.85, 0.95, 0.5, 0.4 + 0.4 * math.sin(t * 3 + k)); c.arc(fx, fy, 4, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#122a2a')); c.rectangle(0, 1155, W, H - 1155); c.fill()   # swamp water
    c.set_source_rgba(0.9, 0.9, 0.8, 0.10)
    for i in range(6): c.rectangle(800 - 60 + 10 * math.sin(t * 2 + i), 1175 + i * 22, 120 - i * 12, 5); c.fill()
    c.set_source_rgba(1, 1, 1, 0.04)
    for i in range(8):
        off = (t * 30 + i * 137) % W
        c.rectangle(off - 200, 1200 + i * 90, 260, 4); c.fill()
    c.set_source_rgb(*rgb('#1a2a26')); c.rectangle(0, H - 30, W, 30); c.fill()

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
        c.set_source_rgb(*rgb('#4a3a2e')); rrect(c, -40, -230, 80, 330, 20); c.fill()   # mangrove trunk
        c.set_line_width(14)
        for (a0, a1) in ((-40, -110), (40, 110), (-20, -80), (20, 80)): c.move_to(0, -120); c.curve_to(a0, -60, a1, 0, a1, 90); c.stroke()   # prop roots
        c.set_source_rgb(*rgb('#2a5a3a'))
        for (lx, ly, lr) in ((-60, -260, 70), (40, -280, 80), (0, -330, 70)): c.arc(lx, ly, lr, 0, 2 * math.pi); c.fill()
        c.restore()
    sag = 18 * sp
    cols = ('#e8e0c8', '#e0d8be')
    for i in range(NLOG):   # the surfboard, side-on: 5 sections that drift apart when it snaps
        k = i - (NLOG - 1) / 2; dx = k * 50 * sp; dy = 40 * sp
        lx = x0 + i * LOGW + dx
        c.save(); c.translate(lx + LOGW / 2, yb + 18 + dy + sag); c.rotate(0.12 * k * sp)
        hw = LOGW / 2 + (0 if broke else 1)
        c.set_source_rgb(*rgb(('#b89060', '#a8824f')[i % 2])); c.rectangle(-hw + 1, -20, 2 * hw - 2, 18); c.fill()   # top deck board
        c.set_source_rgb(*rgb('#7a5a36')); c.rectangle(-hw + 1, 26, 2 * hw - 2, 14); c.fill()   # bottom board
        c.set_source_rgb(*rgb('#8a6a40')); c.rectangle(-22, -2, 44, 28); c.fill()   # block
        c.set_source_rgba(0.25, 0.17, 0.08, 0.6); c.set_line_width(3); c.move_to(-hw + 8, -11); c.line_to(hw - 8, -11); c.stroke()
        c.set_source_rgb(*rgb('#5a5a60'))
        for nx in (-hw + 10, hw - 12): c.arc(nx, -11, 3, 0, 2 * math.pi); c.fill()   # nails
        c.restore()
    if not broke:
        pass
    for (td, xd, d, kind) in DMG:   # punch dents / cracks
        if td > t: break
        if kind == 'ram' and not broke:
            c.set_source_rgb(*rgb('#3a2814')); c.save(); c.translate(xd, yb + 42); c.scale(26 if d > 10 else 18, 14 if d > 10 else 10); c.arc(0, 0, 1, math.pi, 2 * math.pi); c.restore(); c.fill()
            c.set_source_rgba(0.3, 0.25, 0.2, 0.6); c.set_line_width(3); c.move_to(xd - 10, yb + 24); c.line_to(xd + 4, yb + 8); c.line_to(xd - 4, yb); c.stroke()


PS = Particles(9)
CHIP = (0.62, 0.47, 0.28)
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
