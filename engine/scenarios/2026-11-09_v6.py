"""2026-11-09 v6 — DAMAGE BAR – DOOR %: the SNAPPING TURTLE. Gloop is a passive rigid ball (Ball) bouncing on an
old wooden door floating in a swamp at night (two mossy cypress stumps at the ends are the walls). Every landing
cracks the soggy wood in proportion to the real impact speed; a seeded-random snapping turtle dives and lunges
up from below to bite chunks out of the door (some bites aimed under where he is) — each bite jolts him up if
he's on the door. DOOR 0% = it splits apart and Gloop splashes into the swamp."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the snapping turtle'
SEED = int(os.environ.get('SEED', 8))
rng = random.Random(SEED)

class S: pass
S.HOOK2 = 'THE SNAPPING TURTLE?'; S.HOOK2_SIZE = 82; S.FAIL_WORD = 'CRACK!'; S.FAIL_SIZE = 150; 
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
    bx = bar(c, p, f'DOOR {int(math.ceil(GL[f]))}%', good_bad_col(p), 0.12 if recent else 0, bw=640, x_off=36)
    c.save(); c.translate(bx - 52, 231)   # little float icon
    c.set_source_rgb(*rgb('#9a6a3a')); rrect(c, -20, -30, 40, 60, 4); c.fill()
    c.set_source_rgb(*rgb('#6a4422')); c.rectangle(-14, -24, 28, 20); c.fill(); c.rectangle(-14, 2, 28, 22); c.fill()
    c.set_source_rgb(*rgb('#e0c060')); c.arc(12, 0, 4, 0, 2 * math.pi); c.fill(); c.restore()
S.draw_bar = draw_bar

def beaver_pos(t):
    """Swordfish cruising under the surface; for a stab it dives and lunges up under the float at r['x']."""
    x = 540 + 430 * math.sin(t * 0.8); y = WATER + 260; d = 1 if math.cos(t * 0.8) >= 0 else -1; ang = 0.0; bite = 0.0
    for r in RAMS:
        if r['t'] - 0.5 <= t < r['t'] + 0.6 and r['t'] < S.T_RES + 0.1:
            if t < r['t']: k = ease((t - (r['t'] - 0.5)) / 0.5); x, y = lerp(x, r['x'], k), lerp(WATER + 280, DECK + 205, k); ang = -1.25 * k; bite = k
            else: k = ease((t - r['t']) / 0.6); x, y = lerp(r['x'], x, k), lerp(DECK + 205, WATER + 280, k); ang = -1.25 * (1 - k); bite = 1 - k
    return x, y, d, ang, bite

def draw_beaver(c, x, y, d, ang, bite, t):   # the snapping turtle (head + beak first when lunging up)
    c.save(); c.translate(x, y); c.rotate(ang * d); c.scale(d, 1)
    shell, shell2, skin = rgb('#56663a'), rgb('#6e7e46'), rgb('#86925c')
    pad = 0.5 * math.sin(t * 7)
    c.set_source_rgb(*skin)
    for (lx, ly, ph) in ((-90, 40, 0), (60, 44, 1.5)):   # paddling legs
        c.save(); c.translate(lx, ly); c.rotate(0.6 + 0.4 * math.sin(t * 7 + ph)); c.scale(46, 16); c.arc(0.5, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    c.move_to(-150, 10); c.line_to(-200, 24 + 10 * pad); c.line_to(-150, 30); c.close_path(); c.fill()   # tail
    c.set_source_rgb(*shell); c.move_to(-160, 20); c.curve_to(-150, -90, 130, -90, 140, 20); c.close_path(); c.fill()   # domed shell
    c.set_source_rgb(*shell2); c.set_line_width(5)
    for (sx, sy) in ((-80, -30), (0, -46), (80, -30)):
        c.save(); c.translate(sx, sy); c.move_to(-28, 0); c.line_to(-14, -18); c.line_to(14, -18); c.line_to(28, 0); c.line_to(14, 18); c.line_to(-14, 18); c.close_path(); c.restore(); c.stroke()
    c.set_source_rgb(*rgb('#8a8a5a')); c.rectangle(-150, 16, 290, 18); c.fill()   # belly plate edge
    # neck + head
    nx = 140 + 50 * bite
    c.set_source_rgb(*skin); c.set_line_width(46); c.set_line_cap(cairo.LINE_CAP_ROUND); c.move_to(110, 10); c.line_to(nx, 0); c.stroke()
    c.save(); c.translate(nx + 30, -4)
    c.set_source_rgb(*skin); c.save(); c.scale(54, 40); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    op = 0.5 * bite
    c.set_source_rgb(*rgb('#3a3020')); c.move_to(20, -8); c.line_to(76, 4 - 10 * op); c.line_to(40, 14); c.close_path(); c.fill()   # hooked beak top
    c.move_to(20, 16); c.line_to(66, 18 + 22 * op); c.line_to(30, 34); c.close_path(); c.fill()   # beak bottom
    c.set_source_rgb(*rgb('#e8d870')); c.arc(6, -18, 10, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(0.05, 0.05, 0.05); c.arc(8, -18, 5, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#2a3018')); c.set_line_width(6); c.move_to(-12, -34); c.line_to(22, -26); c.stroke()   # grumpy brow
    c.restore()
    c.restore()

def draw_head_wake(c, x, t):
    """Shell + head poking out of the swamp after the door splits."""
    c.set_source_rgb(*rgb('#3e4a2a')); c.move_to(x - 110, WATER + 8); c.curve_to(x - 100, WATER - 60, x + 80, WATER - 60, x + 90, WATER + 8); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#6a7448')); c.arc(x + 130, WATER - 10, 28, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#3a3020')); c.move_to(x + 150, WATER - 22); c.line_to(x + 182, WATER - 6); c.line_to(x + 152, WATER + 2); c.close_path(); c.fill()

TREES = [(60, 70), (300, 40), (520, 60), (760, 44), (1000, 66)]
def draw_bg(c, t):
    c.set_source_rgb(*rgb('#121a20')); c.rectangle(0, HEAD, W, H - HEAD); c.fill()
    c.set_source_rgb(*rgb('#e0e0c8')); c.arc(640, 470, 44, 0, 2 * math.pi); c.fill()
    # cypress trunks with hanging moss in the mist
    for k, (x, w_) in enumerate(TREES):
        c.set_source_rgb(*rgb('#1c2620')); c.move_to(x - w_ / 2, 1160); c.line_to(x - w_ / 3, HEAD); c.line_to(x + w_ / 3, HEAD); c.line_to(x + w_ / 2, 1160); c.close_path(); c.fill()
        c.set_source_rgb(*rgb('#26302a'))
        for j in range(4):
            mx = x - 70 + j * 46; my = 520 + (k * 37 + j * 53) % 160
            c.move_to(mx - 14, my - 120); c.curve_to(mx - 10, my - 40, mx + 6 * math.sin(t + j), my, mx, my + 40); c.line_to(mx + 10, my - 120); c.close_path(); c.fill()
    c.set_source_rgba(0.7, 0.8, 0.75, 0.06)
    for i in range(3): c.rectangle(0, 980 + i * 60, W, 40); c.fill()   # mist
    for i in range(8):   # fireflies
        fx = (i * 173 + 40 * math.sin(t * 0.7 + i)) % W; fy = 700 + (i * 97) % 380 + 20 * math.sin(t * 1.3 + i * 2)
        c.set_source_rgba(0.9, 1, 0.5, 0.4 + 0.4 * math.sin(t * 3 + i)); c.arc(fx, fy, 4, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#15241e')); c.rectangle(0, 1155, W, H - 1155); c.fill()   # swamp water
    c.set_source_rgba(0.9, 0.9, 0.8, 0.10)
    for i in range(6): c.rectangle(640 - 60 + 10 * math.sin(t * 2 + i), 1175 + i * 22, 120 - i * 12, 5); c.fill()
    c.set_source_rgba(1, 1, 1, 0.04)
    for i in range(8):
        off = (t * 30 + i * 137) % W
        c.rectangle(off - 200, 1200 + i * 90, 260, 4); c.fill()
    c.set_source_rgb(*rgb('#1a2c22'))   # weeds deep below
    for x in range(40, W, 110):
        c.set_line_width(10); c.move_to(x, H); c.curve_to(x + 20 * math.sin(t + x), H - 80, x - 10, H - 140, x + 10 * math.sin(t * 1.2 + x), H - 200); c.stroke()

def draw_water_front(c, t, f):
    c.set_source_rgba(0.06, 0.15, 0.12, 0.62); c.move_to(0, H)
    for x in range(0, W + 20, 20): c.line_to(x, WATER + 8 * math.sin(x * 0.02 + t * 2.2))
    c.line_to(W, H); c.close_path(); c.fill()
    c.set_source_rgba(1, 1, 1, 0.10); c.set_line_width(4)
    for x in range(0, W + 20, 20): (c.move_to if x == 0 else c.line_to)(x, WATER + 8 * math.sin(x * 0.02 + t * 2.2))
    c.stroke()
    c.set_source_rgb(*rgb('#2e5a32'))   # lily pads on the surface
    for x in (60, 1010):
        c.save(); c.translate(x, WATER + 4 + 3 * math.sin(t * 2 + x)); c.scale(48, 10); c.arc(0, 0, 1, 0.3, 2 * math.pi); c.line_to(0, 0); c.close_path(); c.restore(); c.fill()

NLOG = 5; LOGW = (TANK_R - TANK_L + 80) / NLOG
def draw_raft(c, t, f):
    broke = T_FAIL is not None and t >= T_FAIL
    sp = 0.0 if not broke else ease((t - T_FAIL) / 0.8)
    bob = 3 * math.sin(t * 2); yb = DECK + bob
    x0 = TANK_L - 40
    for i, px in enumerate((TANK_L - 50, TANK_R - 40)):   # mossy cypress stumps (walls)
        c.save(); c.translate(px + 45, yb)
        c.set_source_rgb(*rgb('#3a3028')); c.move_to(-46, 90); c.line_to(-40, -200); c.line_to(40, -200); c.line_to(46, 90); c.close_path(); c.fill()
        c.set_source_rgb(*rgb('#4a3e32')); c.rectangle(-40, -200, 24, 290); c.fill()
        c.set_source_rgb(*rgb('#2c241e')); c.save(); c.translate(0, -200); c.scale(40, 12); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
        c.set_source_rgb(*rgb('#3e6a34')); c.save(); c.translate(-10, -206); c.scale(34, 10); c.arc(0, 0, 1, math.pi, 2 * math.pi); c.restore(); c.fill()   # moss cap
        c.restore()
    sag = 18 * sp
    for i in range(NLOG):   # the old door, side-on: 5 planks that drift apart when it splits
        k = i - (NLOG - 1) / 2; dx = k * 50 * sp; dy = 40 * sp
        lx = x0 + i * LOGW + dx
        c.save(); c.translate(lx + LOGW / 2, yb + 22 + dy + sag); c.rotate(0.12 * k * sp)
        c.set_source_rgb(*rgb('#8a5e36' if i % 2 == 0 else '#7a5230')); c.rectangle(-LOGW / 2, -22, LOGW + (0 if broke else 1), 40); c.fill()
        c.set_source_rgba(0, 0, 0, 0.18); c.set_line_width(3); c.move_to(-LOGW / 2 + 10, -6); c.line_to(LOGW / 2 - 20, -4); c.stroke()
        c.restore()
    if not broke:
        c.set_source_rgb(*rgb('#5a3a1e')); c.rectangle(x0, yb - 2, NLOG * LOGW, 8); c.fill()   # door frame edge
        c.set_source_rgb(*rgb('#d8b850')); c.arc(x0 + NLOG * LOGW - 60, yb + 20, 9, 0, 2 * math.pi); c.fill()   # brass knob
        c.set_source_rgba(0, 0, 0, 0.3); c.set_line_width(4); c.rectangle(x0, yb - 2, NLOG * LOGW, 42); c.stroke()
    for (td, xd, d, kind) in DMG:   # bite notches
        if td > t: break
        if kind == 'ram' and not broke:
            c.set_source_rgb(*rgb('#15241e')); c.save(); c.translate(xd, yb + 40); c.scale(26 if d > 10 else 18, 16 if d > 10 else 11); c.arc(0, 0, 1, math.pi, 2 * math.pi); c.restore(); c.fill()

PS = Particles(9)
CHIP = (0.55, 0.38, 0.22)
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
    if T_FAIL and abs(t - T_FAIL - 0.35) < 0.5 / FPS: PS.spawn(GX[fi], WATER, 30, (0.5, 0.7, 0.6), 700, 0.8, grav=2200, r=9)
    PS.draw(c)
    END.draw_claw(c, t)
    c.restore()
    END.header(c, t, fi)

if __name__ == '__main__':
    if sys.argv[1] == 'sim':
        print(SEED, S.OUTCOME, round(S.T_RES - S.T_START, 2), 'final', round(GL[int(S.T_RES * FPS) - 1]), 'gnaws', len([d for d in DMG if d[3] == 'ram']), 'lands', len([d for d in DMG if d[3] == 'land']), 'dur', S.DUR); sys.exit()
    run(S, render)
