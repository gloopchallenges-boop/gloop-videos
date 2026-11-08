"""2026-11-08 v6 — DAMAGE BAR – FLOAT %: the ANGRY SWORDFISH. Gloop is a passive rigid ball (Ball) bouncing on
a striped inflatable pool float in a tropical lagoon at night (two channel-marker posts at the ends are the walls).
Every landing squeezes air out in proportion to the real impact speed; a seeded-random swordfish dives and stabs
up from below with its bill (some stabs aimed under where he is) — each stab punches a hissing hole and throws
him up if he's on the float. FLOAT 0% = it bursts flat and Gloop splashes into the lagoon."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the angry swordfish'
SEED = int(os.environ.get('SEED', 5))
rng = random.Random(SEED)

class S: pass
S.HOOK2 = 'THE ANGRY SWORDFISH?'; S.HOOK2_SIZE = 80; S.FAIL_WORD = 'POP!'; S.FAIL_SIZE = 150; 
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
    bx = bar(c, p, f'FLOAT {int(math.ceil(GL[f]))}%', good_bad_col(p), 0.12 if recent else 0, bw=640, x_off=36)
    c.save(); c.translate(bx - 52, 231)   # little float icon
    c.set_source_rgb(*rgb('#d84a3a')); rrect(c, -32, -14, 64, 28, 14); c.fill()
    c.set_source_rgb(*rgb('#f0ece0')); c.rectangle(-8, -14, 16, 28); c.fill(); c.restore()
S.draw_bar = draw_bar

def beaver_pos(t):
    """Swordfish cruising under the surface; for a stab it dives and lunges up under the float at r['x']."""
    x = 540 + 430 * math.sin(t * 0.8); y = WATER + 260; d = 1 if math.cos(t * 0.8) >= 0 else -1; ang = 0.0; bite = 0.0
    for r in RAMS:
        if r['t'] - 0.5 <= t < r['t'] + 0.6 and r['t'] < S.T_RES + 0.1:
            if t < r['t']: k = ease((t - (r['t'] - 0.5)) / 0.5); x, y = lerp(x, r['x'], k), lerp(WATER + 280, DECK + 150, k); ang = -1.25 * k; bite = k
            else: k = ease((t - r['t']) / 0.6); x, y = lerp(r['x'], x, k), lerp(DECK + 150, WATER + 280, k); ang = -1.25 * (1 - k); bite = 1 - k
    return x, y, d, ang, bite

def draw_beaver(c, x, y, d, ang, bite, t):   # the angry swordfish (bill first when stabbing up)
    c.save(); c.translate(x, y); c.rotate(ang * d); c.scale(d, 1)
    back, belly = rgb('#3a5a7a'), rgb('#a8b8c4')
    wag = 0.25 * math.sin(t * 9)
    c.save(); c.translate(-150, 0); c.rotate(wag)   # tail
    c.set_source_rgb(*back); c.move_to(0, 0); c.line_to(-70, -70); c.line_to(-40, 0); c.line_to(-70, 70); c.close_path(); c.fill(); c.restore()
    c.set_source_rgb(*back); c.move_to(-40, -40); c.line_to(0, -120); c.line_to(40, -44); c.close_path(); c.fill()   # tall dorsal fin
    c.move_to(-160, 0); c.curve_to(-100, -60, 60, -70, 140, -16); c.line_to(140, 20); c.curve_to(60, 60, -100, 50, -160, 0); c.close_path(); c.fill()   # body
    c.set_source_rgb(*belly); c.move_to(-120, 12); c.curve_to(-40, 50, 80, 44, 140, 14); c.line_to(140, 20); c.curve_to(60, 56, -80, 46, -120, 12); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#2a3a4a')); c.move_to(136, -8); c.line_to(300, 0); c.line_to(136, 10); c.close_path(); c.fill()   # the sword bill
    c.set_source_rgb(*rgb('#f0e6c8')); c.arc(108, -12, 13, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(0.05, 0.05, 0.08); c.arc(111, -11, 6, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#1a2a3a')); c.set_line_width(6); c.move_to(90, -32); c.line_to(126, -24); c.stroke()   # grumpy brow
    c.set_source_rgb(*back); c.save(); c.translate(40, 26); c.rotate(0.5 + wag * 0.5); c.scale(40, 12); c.arc(0.6, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()   # pectoral fin
    c.restore()

def draw_head_wake(c, x, t):
    """Dorsal fin + bill circling at the surface after the float bursts."""
    c.set_source_rgb(*rgb('#3a5a7a')); c.move_to(x - 40, WATER + 6); c.line_to(x, WATER - 80); c.line_to(x + 30, WATER + 6); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#2a3a4a')); c.move_to(x + 90, WATER + 4); c.line_to(x + 200, WATER - 20); c.line_to(x + 92, WATER + 12); c.close_path(); c.fill()

stars = [(rng.uniform(0, W), rng.uniform(HEAD, 900), rng.uniform(1.2, 2.6)) for _ in range(60)]
def draw_bg(c, t):
    c.set_source_rgb(*rgb('#101a28')); c.rectangle(0, HEAD, W, H - HEAD); c.fill()
    c.set_source_rgba(0.85, 0.9, 1.0, 0.45)
    for x, y, r in stars: c.arc(x, y, r, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#e6e8dc')); c.arc(250, 560, 44, 0, 2 * math.pi); c.fill()
    # far tropical island with a volcano + palms
    c.set_source_rgb(*rgb('#1a2634')); c.move_to(420, 1160); c.line_to(640, 900); c.line_to(700, 900); c.line_to(960, 1160); c.close_path(); c.fill()
    c.move_to(300, 1160); c.curve_to(400, 1110, 900, 1100, 1080, 1160); c.close_path(); c.fill()
    for (px, ph) in ((360, 130), (900, 110)):
        c.set_line_width(8); c.move_to(px, 1140); c.curve_to(px + 10, 1100, px - 10, 1060, px + 6, 1140 - ph); c.stroke()
        for a in (-2.6, -1.9, -1.1, -0.4):
            c.save(); c.translate(px + 6, 1140 - ph); c.rotate(a); c.save(); c.scale(50, 9); c.arc(1, 0.3, 1, 0, 2 * math.pi); c.restore(); c.fill(); c.restore()
    c.set_source_rgb(*rgb('#12283a')); c.rectangle(0, 1155, W, H - 1155); c.fill()   # lagoon
    c.set_source_rgba(0.9, 0.9, 0.8, 0.10)
    for i in range(7): c.rectangle(250 - 70 + 12 * math.sin(t * 2 + i), 1175 + i * 22, 140 - i * 12, 5); c.fill()
    c.set_source_rgba(1, 1, 1, 0.05)
    for i in range(8):
        off = (t * 40 + i * 137) % W
        c.rectangle(off - 200, 1200 + i * 90, 260, 4); c.fill()
    c.set_source_rgb(*rgb('#1a3440'))   # coral silhouettes deep below
    for (x, h_) in ((120, 120), (330, 80), (760, 140), (960, 90)):
        c.save(); c.translate(x, H); c.scale(60, h_); c.arc(0, 0, 1, math.pi, 2 * math.pi); c.restore(); c.fill()

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
    for i, px in enumerate((TANK_L - 50, TANK_R - 40)):   # channel-marker posts (walls)
        c.save(); c.translate(px + 45, yb)
        c.set_source_rgb(*rgb('#5a4430')); c.rectangle(-40, -210, 80, 300); c.fill()
        c.set_source_rgb(*rgb('#6e543a')); c.rectangle(-40, -210, 26, 300); c.fill()
        c.set_source_rgb(*rgb('#b84a3a' if i == 0 else '#3a8a5a')); c.rectangle(-40, -210, 80, 50); c.fill()
        c.set_source_rgb(*rgb('#3a2c20')); c.save(); c.translate(0, -210); c.scale(40, 12); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
        c.restore()
    sag = 18 * sp
    for i in range(NLOG):   # striped inflatable float, side-on: 5 air chambers that drift apart flat when it bursts
        k = i - (NLOG - 1) / 2; dx = k * 50 * sp; dy = 40 * sp
        lx = x0 + i * LOGW + dx
        c.save(); c.translate(lx + LOGW / 2, yb + 22 + dy + sag); c.scale(1, 1 - 0.6 * sp)
        c.set_source_rgb(*rgb('#c84a3c' if i % 2 == 0 else '#e8e2d4')); rrect(c, -LOGW / 2, -24, LOGW + (0 if broke else 1), 52, 18 if broke else 4); c.fill()
        c.set_source_rgba(1, 1, 1, 0.18); c.rectangle(-LOGW / 2 + 6, -18, LOGW - 12, 8); c.fill()
        c.restore()
    if not broke:
        c.set_source_rgba(0, 0, 0, 0.25); c.set_line_width(4)
        rrect(c, x0, yb - 2, NLOG * LOGW, 52, 26); c.stroke()
    for (td, xd, d, kind) in DMG:   # puncture holes with hissing air
        if td > t: break
        if kind == 'ram' and not broke:
            c.set_source_rgb(*rgb('#2a1a18')); c.save(); c.translate(xd, yb + 30); c.scale(10, 6); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
            if t - td < 1.2:
                c.set_source_rgba(0.85, 0.9, 0.95, 0.5 * (1 - (t - td) / 1.2)); c.set_line_width(3)
                for j in range(3):
                    kk = ((t - td) * 3 + j / 3) % 1; c.move_to(xd + 6, yb + 40 + j * 4); c.line_to(xd + 20 + 40 * kk, yb + 46 + 30 * kk); c.stroke()

PS = Particles(9)
CHIP = (0.85, 0.9, 0.95)
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
