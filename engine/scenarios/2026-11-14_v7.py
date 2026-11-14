"""2026-11-14 v7 — DAMAGE BAR – CRATE %: the KILLER WHALE. Gloop is a passive rigid ball (Ball) bouncing on a long
wooden cargo crate floating in an icy fjord at night (two ice pillars at the ends are the walls). Every landing
cracks the planks in proportion to the real impact speed; a seeded-random killer whale dives and rams up from below
to smash dents into the crate (some aimed under where he is) — each ram jolts him up if he's on the crate.
CRATE 0% = it breaks apart and Gloop splashes into the icy water."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the killer whale'
SEED = int(os.environ.get('SEED', 11))
rng = random.Random(SEED)

class S: pass
S.HOOK2 = 'THE KILLER WHALE?'; S.HOOK2_SIZE = 86; S.FAIL_WORD = 'CRASH!'; S.FAIL_SIZE = 150; 
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
S.AMB = {'drone': 42, 'wind': 0.035}

def draw_bar(c, t, f):
    p = GL[f] / 100; recent = [d for d in DMG if d[0] <= t and t - d[0] < 0.3]
    bx = bar(c, p, f'CRATE {int(math.ceil(GL[f]))}%', good_bad_col(p), 0.12 if recent else 0, bw=640, x_off=36)
    c.save(); c.translate(bx - 52, 231)   # little float icon
    c.set_source_rgb(*rgb('#a07848')); c.rectangle(-26, -22, 52, 44); c.fill()
    c.set_source_rgb(*rgb('#6a4a2a')); c.set_line_width(5); c.rectangle(-22, -18, 44, 36); c.stroke(); c.move_to(-22, -18); c.line_to(22, 18); c.stroke(); c.restore()
S.draw_bar = draw_bar

def beaver_pos(t):
    """Swordfish cruising under the surface; for a stab it dives and lunges up under the float at r['x']."""
    x = 540 + 430 * math.sin(t * 0.8); y = WATER + 260; d = 1 if math.cos(t * 0.8) >= 0 else -1; ang = 0.0; bite = 0.0
    for r in RAMS:
        if r['t'] - 0.5 <= t < r['t'] + 0.6 and r['t'] < S.T_RES + 0.1:
            if t < r['t']: k = ease((t - (r['t'] - 0.5)) / 0.5); x, y = lerp(x, r['x'], k), lerp(WATER + 280, DECK + 205, k); ang = -1.25 * k; bite = k
            else: k = ease((t - r['t']) / 0.6); x, y = lerp(r['x'], x, k), lerp(DECK + 205, WATER + 280, k); ang = -1.25 * (1 - k); bite = 1 - k
    return x, y, d, ang, bite

def draw_beaver(c, x, y, d, ang, bite, t):   # the killer whale: cruises sideways, rams nose-up
    c.save(); c.translate(x, y - 40 * bite); c.rotate(ang * d if bite > 0 else 0.05 * math.sin(t * 2)); c.scale(d, 1)
    blk, wht = rgb('#16181e'), rgb('#e8ecf0')
    c.set_source_rgb(*blk)   # tail flukes
    c.move_to(-170, 0); c.line_to(-250, -40 + 10 * math.sin(t * 6)); c.line_to(-230, 0); c.line_to(-250, 40 - 10 * math.sin(t * 6)); c.close_path(); c.fill()
    c.save(); c.scale(200, 70); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()   # body
    c.move_to(-10, -60); c.line_to(-40, -150); c.line_to(40, -62); c.close_path(); c.fill()   # dorsal fin
    c.move_to(60, 40); c.line_to(20, 110); c.line_to(100, 50); c.close_path(); c.fill()   # flipper
    c.set_source_rgb(*wht)
    c.save(); c.translate(40, 34); c.scale(150, 30); c.arc(0, 0, 1, 0, math.pi); c.restore(); c.fill()   # white belly
    c.save(); c.translate(120, -22); c.scale(34, 14); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()   # eye patch
    c.set_source_rgb(*rgb('#6a7480')); c.save(); c.translate(-60, -50); c.scale(40, 12); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()   # saddle
    c.set_source_rgb(0.05, 0.05, 0.05); c.arc(130, -8, 6, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#3a3e48')); c.set_line_width(5); c.move_to(110, -36); c.line_to(150, -26); c.stroke()   # angry brow
    c.restore()

def draw_head_wake(c, x, t):
    """Dorsal fin circling at the surface after the crate breaks."""
    c.set_source_rgb(*rgb('#16181e'))
    c.move_to(x - 30, WATER + 8); c.line_to(x - 10, WATER - 90); c.line_to(x + 34, WATER + 8); c.close_path(); c.fill()

def draw_bg(c, t):
    c.set_source_rgb(*rgb('#0f1624')); c.rectangle(0, HEAD, W, H - HEAD); c.fill()
    for (sx, sy) in ((90, 420), (220, 520), (420, 400), (610, 480), (980, 430), (860, 380), (330, 470), (500, 560)):
        c.set_source_rgba(1, 1, 1, 0.5 + 0.3 * math.sin(t * 2 + sx)); c.arc(sx, sy, 3, 0, 2 * math.pi); c.fill()
    c.set_source_rgba(0.4, 0.8, 0.6, 0.06); c.set_line_width(60)   # faint northern lights
    c.move_to(-20, 640); c.curve_to(300, 520, 600, 700, 1100, 560); c.stroke()
    c.set_source_rgb(*rgb('#e6dfc4')); c.arc(820, 520, 44, 0, 2 * math.pi); c.fill()
    # snowy fjord mountains
    c.set_source_rgb(*rgb('#1c2434')); c.move_to(0, 1160); c.line_to(0, 820); c.line_to(180, 700); c.line_to(360, 900); c.line_to(520, 760); c.line_to(760, 1000); c.line_to(940, 780); c.line_to(W, 860); c.line_to(W, 1160); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#8a94a8'))
    for (px, py) in ((180, 700), (520, 760), (940, 780)):
        c.move_to(px, py); c.line_to(px - 50, py + 60); c.line_to(px - 20, py + 48); c.line_to(px, py + 66); c.line_to(px + 22, py + 50); c.line_to(px + 50, py + 64); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#c8d4e0'))   # small floating ice floes far off
    for (x, w_) in ((200, 90), (700, 60)): c.rectangle(x, 1150, w_, 12); c.fill()
    c.set_source_rgb(*rgb('#10243a')); c.rectangle(0, 1155, W, H - 1155); c.fill()   # sea
    c.set_source_rgba(0.9, 0.9, 0.8, 0.10)
    for i in range(6): c.rectangle(820 - 60 + 10 * math.sin(t * 2 + i), 1175 + i * 22, 120 - i * 12, 5); c.fill()
    c.set_source_rgba(1, 1, 1, 0.04)
    for i in range(8):
        off = (t * 30 + i * 137) % W
        c.rectangle(off - 200, 1200 + i * 90, 260, 4); c.fill()
    c.set_source_rgb(*rgb('#1a2a36')); c.rectangle(0, H - 30, W, 30); c.fill()

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
        c.set_source_rgb(*rgb('#8aa4bc')); c.move_to(-55, 90); c.line_to(-45, -150); c.line_to(-10, -210); c.line_to(30, -175); c.line_to(50, 90); c.close_path(); c.fill()
        c.set_source_rgb(*rgb('#b8cadc')); c.move_to(-45, 90); c.line_to(-36, -150); c.line_to(-10, -195); c.line_to(-6, 90); c.close_path(); c.fill()
        c.set_source_rgb(*rgb('#e8f0f8')); c.move_to(-45, -150); c.line_to(-10, -210); c.line_to(30, -175); c.line_to(-10, -185); c.close_path(); c.fill()
        c.restore()
    sag = 18 * sp
    cols = ('#e8e0c8', '#e0d8be')
    for i in range(NLOG):   # the surfboard, side-on: 5 sections that drift apart when it snaps
        k = i - (NLOG - 1) / 2; dx = k * 50 * sp; dy = 40 * sp
        lx = x0 + i * LOGW + dx
        c.save(); c.translate(lx + LOGW / 2, yb + 18 + dy + sag); c.rotate(0.12 * k * sp)
        hw = LOGW / 2 + (0 if broke else 1)
        c.set_source_rgb(*rgb(('#a07848', '#94703f')[i % 2])); c.rectangle(-hw, -18, 2 * hw, 60); c.fill()
        c.set_source_rgb(*rgb('#6a4a2a')); c.set_line_width(5)
        c.move_to(-hw, 4); c.line_to(hw, 4); c.stroke(); c.move_to(-hw, 24); c.line_to(hw, 24); c.stroke()
        c.move_to(-hw + 6, -18); c.line_to(-hw + 6, 42); c.stroke(); c.move_to(-hw + 10, -14); c.line_to(hw - 10, 38); c.stroke()
        c.restore()
    if not broke:
        font(c, 30); c.set_source_rgba(0.2, 0.12, 0.06, 0.8); c.move_to(x0 + LOGW * 2 + 10, yb + 32); c.show_text('FRAGILE')
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
