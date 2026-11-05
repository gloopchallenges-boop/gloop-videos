"""2026-11-05 v2 — WHO FIRST: the GIANT FLYTRAP. Gloop (orange) and two rival blobs (teal, lilac) are
passive rigid balls (Ball) bouncing on a tiled greenhouse floor between two stacks of flower pots; they
collide with each other (equal-mass elastic). A giant venus flytrap in a big pot at the back lunges on
its stalk at seeded-random times at where a random remaining blob WAS a moment ago — the open jaws
catch whoever they touch. Gloop caught = fail (swallowed, spat out sticky & dizzy). Timer ends uneaten = win."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the giant flytrap'
SEED = int(os.environ.get('SEED', 8))
rng = random.Random(SEED)

class S: pass
S.HOOK2 = 'THE GIANT FLYTRAP?'; S.HOOK2_SIZE = 88; S.FAIL_WORD = 'SNAP!'; S.FAIL_SIZE = 160
S.T_START = HOOK_T; S.TL = 13.0; S.T_END = S.T_START + S.TL
GROUND = 1610; R = 56; XMIN, XMAX = 160, 920
MOUTH = (540, 1060); TIP_R = 46; T_OUT, T_HOLD, T_BACK = 0.22, 0.08, 0.35
NAMES = ['GLOOP', 'MINTY', 'LILAC']
SKINS = [('#ffd36b', '#ff8a1f', '#c45a00'), ('#9ff0e0', '#2fb8a0', '#1a6a5c'), ('#e6d0ff', '#b08ae6', '#5e3e8a')]

TER = Terrain(GROUND, seed=SEED, bumps=4, amp=10, soft=False)
xs0 = rng.sample([250, 420, 600, 780], 3)
balls = [Ball(xs0[i], TER, R=R, seed=SEED * 3 + i, xmin=XMIN, xmax=XMAX, hop=rng.uniform(220, 300)) for i in range(3)]
STR = []; t = 0.45
while t < S.T_END + 1:
    STR.append({'t': t}); t += rng.uniform(1.2, 2.2)
N0 = int(40 * FPS); POS = [], ; POS = []; EATEN_AT = [None, None, None]; T_FAIL = None; HIST = []
caught = {}   # blob -> strike index
def tongue_tip(s, t):
    k = t - s['t']
    if k < 0 or k > T_OUT + T_HOLD + T_BACK: return None
    tx, ty = s['tx'], s['ty']
    if k < T_OUT: a = ease(k / T_OUT)
    elif k < T_OUT + T_HOLD: a = 1
    else: a = 1 - ease((k - T_OUT - T_HOLD) / T_BACK)
    return lerp(MOUTH[0], tx, a), lerp(MOUTH[1], ty, a), k < T_OUT + T_HOLD
for f in range(N0):
    t = f / FPS
    HIST.append([(b.x, b.y) for b in balls])
    for si, s in enumerate(STR):
        if 'tx' not in s and t >= s['t'] - 0.001:
            alive = [i for i in range(3) if EATEN_AT[i] is None and i not in caught.values()]
            if s['t'] < S.T_START or not alive or T_FAIL is not None:
                s['tx'], s['ty'], s['who'] = rng.choice((XMIN + 20, XMAX - 20)), GROUND - 40, None
            else:
                w = rng.choice(alive); lag = int(rng.uniform(0.3, 0.55) * FPS)
                px, py = HIST[max(0, f - lag)][w]; s['tx'], s['ty'], s['who'] = px, py, w
    for i, b in enumerate(balls):
        if EATEN_AT[i] is None and i not in caught: b.step(t)
    for i in range(3):   # rival collisions
        for j in range(i + 1, 3):
            a, b = balls[i], balls[j]
            if EATEN_AT[i] is not None or EATEN_AT[j] is not None or i in caught or j in caught: continue
            dx, dy = b.x - a.x, b.y - a.y; d = math.hypot(dx, dy)
            if 0 < d < 2 * R:
                nx, ny = dx / d, dy / d; ov = 2 * R - d
                a.x -= nx * ov / 2; a.y -= ny * ov / 2; b.x += nx * ov / 2; b.y += ny * ov / 2
                rel = (a.vx - b.vx) * nx + (a.vy - b.vy) * ny
                if rel > 0:
                    j_ = rel * 0.95; a.vx -= j_ * nx; a.vy -= j_ * ny; b.vx += j_ * nx; b.vy += j_ * ny
    for si, s in enumerate(STR):   # tongue catches whoever the extending tip touches
        if 'tx' not in s or s['t'] < S.T_START or T_FAIL is not None and s['t'] > T_FAIL: continue
        tip = tongue_tip(s, t)
        if tip and tip[2] and si not in caught.values():
            for i, b in enumerate(balls):
                if EATEN_AT[i] is None and i not in caught and t < S.T_END and math.hypot(b.x - tip[0], b.y - tip[1]) < R + TIP_R:
                    caught[i] = si; s['got'] = i; s['tcatch'] = t
                    if i == 0 and T_FAIL is None: T_FAIL = t
                    break
    for i, si in list(caught.items()):
        s = STR[si]; tip = tongue_tip(s, t)
        if tip is None: EATEN_AT[i] = t; del caught[i]
    POS.append([(b.x, b.y) for b in balls])
S.OUTCOME = 'fail' if T_FAIL else 'win'
S.T_RES = T_FAIL if T_FAIL else S.T_END
END = S.END = Ending(S)
SPIT_T = (EATEN_AT[0] + 0.5) if T_FAIL else None
if T_FAIL:   # flytrap spits Gloop out dizzy & slimy onto the log
    sx, sy = 540, GROUND - R
    S.GRAB = (sx, sy)
else:
    gi = min(int(END.T_GRAB * FPS), N0 - 1); S.GRAB = POS[gi][0]
S.events = []
for s in STR:
    if s['t'] < S.T_RES + 0.1: S.events.append([s['t'], 'whoosh']); S.events.append([s['t'], 'sizzle'])
    if 'got' in s and s['tcatch'] <= S.T_RES + 0.01: S.events.append([s['tcatch'], 'pop']); S.events.append([s['tcatch'] + 0.3, 'thump', 0.8])
for b in balls:
    for (tl, xl, imp) in b.landings:
        if tl < S.T_RES + 1.0: S.events.append([tl, 'hop'])
if T_FAIL: S.events.append([SPIT_T, 'splash'])
S.AMB = {'drone': 45, 'wind': 0.02}
def eaten(i, t): return EATEN_AT[i] is not None and t >= EATEN_AT[i]

def draw_bar(c, t, f):
    for i in range(3):
        x = W / 2 - 170 + i * 170; y = 232; gone = eaten(i, t) or (i in [s.get('got') for s in STR if s.get('tcatch', 99) <= t])
        sk = SKINS[i] if not gone else ('#5a5664', '#3a3644', '#2a2634')
        c.save(); c.translate(x, y)
        c.set_source_rgb(0, 0, 0); c.arc(0, 0, 36, 0, 2 * math.pi); c.fill()
        c.set_source_rgb(*rgb(sk[1])); c.arc(0, 0, 30, 0, 2 * math.pi); c.fill()
        c.set_source_rgb(1, 1, 1); c.arc(-10, -4, 7, 0, 2 * math.pi); c.fill(); c.arc(10, -4, 7, 0, 2 * math.pi); c.fill()
        c.set_source_rgb(0.1, 0.06, 0.05); c.arc(-9, -3, 3.5, 0, 2 * math.pi); c.fill(); c.arc(11, -3, 3.5, 0, 2 * math.pi); c.fill()
        if gone:
            c.set_source_rgb(*rgb('#ff4d4d')); c.set_line_width(8); c.move_to(-26, -26); c.line_to(26, 26); c.stroke(); c.move_to(26, -26); c.line_to(-26, 26); c.stroke()
        c.restore()
        if i == 0: text_at(c, 'YOU?', x, y + 52, 0.0001 + 22, rgb('#ffd36b'), lw=5) if False else None
S.draw_bar = draw_bar


stars = [(rng.uniform(0, W), rng.uniform(HEAD, 760), rng.uniform(1.2, 2.4)) for _ in range(40)]
POT = (540, 1360)
LEAVES = [(rng.uniform(0, W), rng.uniform(1150, 1380), rng.uniform(40, 90), rng.uniform(-0.6, 0.6)) for _ in range(14)]
def draw_bg(c, t):
    c.set_source_rgb(*rgb('#121a1c')); c.rectangle(0, HEAD, W, H - HEAD); c.fill()
    c.set_source_rgba(0.85, 0.9, 0.9, 0.4)
    for x, y, r in stars: c.arc(x, y, r, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#dfe6d6')); c.arc(990, 520, 50, 0, 2 * math.pi); c.fill()
    # moonlight shafts through the glass roof
    c.set_source_rgba(0.8, 0.9, 0.85, 0.04)
    c.move_to(760, HEAD); c.line_to(900, HEAD); c.line_to(700, 1450); c.line_to(420, 1450); c.close_path(); c.fill()
    # greenhouse frame: pitched roof + glass panes
    c.set_source_rgb(*rgb('#2c3a38')); c.set_line_width(10)
    c.move_to(0, 720); c.line_to(540, HEAD + 40); c.line_to(W, 720); c.stroke()
    c.set_line_width(6)
    for x in range(0, W + 1, 180): c.move_to(x, 720 - (540 - abs(x - 540)) * (720 - HEAD - 40) / 540); c.line_to(x, 1420); c.stroke()
    for y in (900, 1120): c.move_to(0, y); c.line_to(W, y); c.stroke()
    c.set_source_rgba(0.7, 0.85, 0.85, 0.05)
    for i, x in enumerate(range(0, W, 180)):
        if i % 2: c.rectangle(x + 4, 724, 172, 172); c.fill()
    # potted plants on a back bench
    c.set_source_rgb(*rgb('#2a2622')); c.rectangle(0, 1380, W, 22); c.fill()
    for (x, y, s, a) in LEAVES:
        c.save(); c.translate(x, 1380); c.rotate(a + 0.05 * math.sin(t * 1.3 + x))
        c.set_source_rgb(*rgb('#1f3a2a')); c.save(); c.translate(0, -s); c.scale(s * 0.35, s); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill(); c.restore()
    for x in range(60, W, 190):
        c.set_source_rgb(*rgb('#6a3e2c')); c.move_to(x - 34, 1340); c.line_to(x + 34, 1340); c.line_to(x + 26, 1382); c.line_to(x - 26, 1382); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#1e2422')); c.rectangle(0, 1400, W, H - 1400); c.fill()

def snake_head(t):
    """Jaw position + open amount: idle sway at MOUTH, or the active lunge's tip."""
    for s in STR:
        if s['t'] > S.T_RES + 0.05 and not (T_FAIL and s['t'] <= T_FAIL): continue
        tip = tongue_tip(s, t)
        if tip: return tip[0], tip[1], (1.0 if tip[2] else 0.15)
    return MOUTH[0] + 26 * math.sin(t * 2.1), MOUTH[1] + 10 * math.sin(t * 4.2), 0.35 + 0.15 * math.sin(t * 3)

def draw_snake(c, t, hx, hy, mo, bulge):
    bx, by = POT
    c.set_line_cap(cairo.LINE_CAP_ROUND)
    c1 = (bx - 50 * math.sin(t * 2.1), by - 170); c2 = (lerp(bx, hx, 0.5), lerp(by - 240, hy, 0.6))
    for wdt, col in ((34, '#25402a'), (22, '#3f6a3a')):   # stalk
        c.set_source_rgb(*rgb(col)); c.set_line_width(wdt); c.move_to(bx, by - 60); c.curve_to(*c1, *c2, hx, hy + 60); c.stroke()
    for sd in (-1, 1):   # side leaves at the base
        c.save(); c.translate(bx + sd * 70, by - 90); c.rotate(sd * 0.7 + 0.05 * math.sin(t * 2))
        c.set_source_rgb(*rgb('#3f6a3a')); c.save(); c.scale(80, 26); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill(); c.restore()
    if bulge > 0:
        mx = 0.125 * bx + 0.375 * c1[0] + 0.375 * c2[0] + 0.125 * hx; my = 0.125 * (by - 60) + 0.375 * c1[1] + 0.375 * c2[1] + 0.125 * (hy + 60)
        c.set_source_rgb(*rgb('#3f6a3a')); c.arc(mx, my, 40 * bulge, 0, 2 * math.pi); c.fill()
    # trap head: two lobes hinged at the bottom, opening sideways (mo 0 closed .. 1 wide)
    ang = 0.15 + 0.95 * mo
    for sd in (-1, 1):
        c.save(); c.translate(hx, hy + 50); c.rotate(sd * ang)
        c.set_source_rgb(*rgb('#5a8a3e')); c.save(); c.translate(0, -60); c.scale(58, 70); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
        c.set_source_rgb(*rgb('#a63a3a')); c.save(); c.translate(sd * -10, -60); c.scale(40, 54); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
        c.set_source_rgb(*rgb('#d9e0b0')); c.set_line_width(4)
        for k in range(9):   # teeth along the outer rim
            a = -math.pi / 2 - sd * (0.25 + k * 0.32)
            px, py = sd * -0 + 58 * math.cos(a) * 1.0, -60 + 70 * math.sin(a)
            c.move_to(px, py); c.line_to(px * 1.32, -60 + (py + 60) * 1.32); c.stroke()
        c.restore()
    # big pot in front
    c.set_source_rgb(*rgb('#8a4e32')); c.move_to(bx - 140, by - 70); c.line_to(bx + 140, by - 70); c.line_to(bx + 110, by + 80); c.line_to(bx - 110, by + 80); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#9a5a3a')); rrect(c, bx - 160, by - 100, 320, 44, 12); c.fill()
    c.set_source_rgb(*rgb('#2a1e18')); c.save(); c.translate(bx, by - 100); c.scale(140, 12); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()

def draw_floor(c):
    c.move_to(0, H)
    for x in range(0, W + 1, 6): c.line_to(x, TER.h[x])
    c.line_to(W, H); c.close_path(); c.set_source_rgb(*rgb('#3a3e3a')); c.fill()
    c.set_source_rgb(*rgb('#555a52')); c.set_line_width(10)
    for x in range(0, W + 1, 6): (c.move_to if x == 0 else c.line_to)(x, TER.h[x] + 3)
    c.stroke()
    c.set_source_rgba(0, 0, 0, 0.25); c.set_line_width(3)
    for x in range(0, W, 120): c.move_to(x, GROUND + 20); c.line_to(x - 60, H); c.stroke()
    for yy in (GROUND + 110, GROUND + 230): c.move_to(0, yy); c.line_to(W, yy); c.stroke()
    for (x0, x1) in ((0, XMIN - R), (XMAX + R, W)):   # stacked flower pots = walls
        cx = (x0 + x1) / 2; wdt = (x1 - x0)
        for j, yy in enumerate((GROUND - 100, GROUND - 300, GROUND - 500)):
            c.set_source_rgb(*rgb('#9a5a3a' if j % 2 == 0 else '#87503a'))
            c.move_to(x0 - 4, yy - 100); c.line_to(x1 + 4, yy - 100); c.line_to(x1 - 10, yy + 100); c.line_to(x0 + 10, yy + 100); c.close_path(); c.fill()
            c.set_source_rgb(*rgb('#6b3a26')); c.rectangle(x0 - 8, yy - 100, wdt + 16, 30); c.fill()
            c.set_source_rgb(*rgb('#2f5a32'))
            for k in range(3): c.save(); c.translate(x0 + wdt * (0.25 + 0.25 * k), yy - 112); c.scale(14, 22); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()

def render(f, c):
    t = f / FPS; fi = min(f, len(POS) - 1)
    c.save()
    draw_bg(c, t)
    hx, hy, mo = snake_head(t)
    active = (None, (hx, hy, True)) if mo > 0 else None
    if SPIT_T and SPIT_T - 0.15 <= t < SPIT_T + 0.3: mo = 1.0
    bulge = 0.0
    for i in range(3):
        if EATEN_AT[i] and EATEN_AT[i] <= t < EATEN_AT[i] + 1.4 and not (i == 0 and SPIT_T and t >= SPIT_T): bulge = max(bulge, 1 - (t - EATEN_AT[i]) / 1.4 * 0.6)
    draw_snake(c, t, hx, hy, mo, bulge)
    draw_floor(c)
    for i in range(3):
        if eaten(i, t) and not (i == 0 and SPIT_T and t >= SPIT_T): continue
        x, y = POS[fi][i]
        for s in STR:   # being reeled in
            if s.get('got') == i and s['tcatch'] <= t:
                tip = tongue_tip(s, t)
                if tip: x, y = tip[0], tip[1]
        if i == 0 and SPIT_T and t >= SPIT_T:
            k = clamp((t - SPIT_T) / 0.5, 0, 1); x = lerp(MOUTH[0], S.GRAB[0], k); y = lerp(MOUTH[1], S.GRAB[1], k) - 260 * math.sin(math.pi * k)
            if t >= END.T_GRAB: x, y = S.GRAB
        if i == 0 and (END.carried(t) or (t >= END.T_GRAB)): x, y = (END.carry_xy(t) if END.carried(t) else S.GRAB)
        hh = max(0, TER.y(x) - R - y); kk = 1 / (1 + hh / 220)
        if not END.carried(t) or i:
            c.set_source_rgba(0, 0, 0, 0.25 * kk); c.save(); c.translate(x, TER.y(x) + 3); c.scale(R * (0.5 + 0.4 * kk), 8); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
        danger = active is not None and math.hypot(active[1][0] - x, active[1][1] - y) < 300
        if i == 0:
            mood = 'happy' if (t >= S.T_END and S.OUTCOME == 'win') else ('scared' if danger or T_FAIL and t >= T_FAIL else 'worried')
            slimy = SPIT_T and t >= SPIT_T
            draw_blob(c, t, x, y, mood, 0, R=R, skin=(('#d8f07a', '#9ac43c', '#5a7a1f') if slimy else SKINS[0]), dizzy=bool(slimy))
            if slimy:
                c.set_source_rgba(0.6, 0.85, 0.3, 0.7)
                for j in range(3): c.arc(x - 30 + j * 30, y + R * 0.8 + 10 * ((t * 1.5 + j * 0.3) % 1), 6, 0, 2 * math.pi); c.fill()
        else:
            draw_blob(c, t + i, x, y, 'scared' if danger else 'worried', 0, R=R, skin=SKINS[i], sweat=False)
    END.draw_claw(c, t)
    c.restore()
    END.header(c, t, fi)

if __name__ == '__main__':
    if sys.argv[1] == 'sim':
        print(SEED, S.OUTCOME, round(S.T_RES - S.T_START, 2), 'eaten', [(NAMES[i], round(EATEN_AT[i] - S.T_START, 1)) for i in range(3) if EATEN_AT[i]], 'strikes', len([s for s in STR if S.T_START <= s['t'] < S.T_RES]), 'dur', S.DUR); sys.exit()
    run(S, render)
