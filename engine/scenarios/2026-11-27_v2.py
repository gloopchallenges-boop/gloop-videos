"""2026-11-27 v2 — WHO FIRST: the GIANT MANTIS (based on 2026-11-25 v3 scorpion). Gloop (orange) + two rival blobs bounce as
passive rigid balls on the soil of a vegetable garden at night between a stack of clay flower pots and a stack of garden
bricks. A giant praying mantis behind the hedge shoots its spiky foreleg at seeded-random times at where a random remaining
blob WAS a moment ago; the claw grabs whoever it touches. Gloop grabbed = fail (tossed back out leafy & dizzy).
Timer ends ungrabbed = win."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the giant mantis'
SEED = int(os.environ.get('SEED', 1))
rng = random.Random(SEED)

class S: pass
S.HOOK2 = 'THE GIANT MANTIS?'; S.HOOK2_SIZE = 92; S.FAIL_WORD = 'SNATCHED!'; S.FAIL_SIZE = 160
S.T_START = HOOK_T; S.TL = 12.5; S.T_END = S.T_START + S.TL
GROUND = 1600; R = 56; XMIN, XMAX = 160, 920
MOUTH = (620, 1125); TIP_R = 48; T_OUT, T_HOLD, T_BACK = 0.22, 0.08, 0.35
NAMES = ['GLOOP', 'BLUE', 'ROSIE']
SKINS = [('#ffd36b', '#ff8a1f', '#c45a00'), ('#b8dcff', '#4a90d0', '#2a5a8a'), ('#ffd0e4', '#e070a0', '#8a3a5a')]

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
                w = rng.choice(alive); lag = int(rng.uniform(0.45, 0.8) * FPS)
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
if T_FAIL:   # anteater spits Gloop out sticky & dizzy
    sx, sy = 540, GROUND - R
    S.GRAB = (sx, sy)
else:
    gi = min(int(END.T_GRAB * FPS), N0 - 1); S.GRAB = POS[gi][0]
S.events = []
for s in STR:
    if s['t'] < S.T_RES + 0.1: S.events.append([s['t'], 'whoosh'])
    if 'got' in s and s['tcatch'] <= S.T_RES + 0.01: S.events.append([s['tcatch'], 'pop']); S.events.append([s['tcatch'] + 0.3, 'thump', 0.8])
for b in balls:
    for (tl, xl, imp) in b.landings:
        if tl < S.T_RES + 1.0: S.events.append([tl, 'hop'])
if T_FAIL: S.events.append([SPIT_T, 'pop'])
S.AMB = {'drone': 42, 'wind': 0.03}
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




stars = [(rng.uniform(0, W), rng.uniform(HEAD, 950), rng.uniform(1.2, 2.4)) for _ in range(45)]
BODY = (800, 1110); ARM0 = (700, 905)
flies = [(rng.uniform(80, 1000), rng.uniform(600, 1000), rng.uniform(0.6, 1.3)) for _ in range(6)]
def draw_bg(c, t):
    c.set_source_rgb(*rgb('#121a2a')); c.rectangle(0, HEAD, W, H - HEAD); c.fill()
    c.set_source_rgba(0.9, 0.9, 1, 0.35)
    for x, y, r in stars[:34]: c.arc(x, y * 0.6 + 150, r, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#e2dcc2')); c.arc(230, 560, 42, 0, 2 * math.pi); c.fill()
    # garden shed silhouette + fence far back
    c.set_source_rgb(*rgb('#1c2436')); c.move_to(60, 1000); c.line_to(60, 860); c.line_to(170, 800); c.line_to(280, 860); c.line_to(280, 1000); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#3a3a30')); c.rectangle(150, 890, 40, 40); c.fill()
    c.set_source_rgb(*rgb('#222c3e'))
    for x in range(300, W, 56): c.move_to(x, 1000); c.line_to(x, 930); c.line_to(x + 20, 915); c.line_to(x + 40, 930); c.line_to(x + 40, 1000); c.close_path(); c.fill()
    c.rectangle(300, 950, W - 300, 12); c.fill()
    # sunflowers drooping asleep (muted)
    for (x, h) in ((380, 300), (470, 360), (560, 280)):
        c.set_source_rgb(*rgb('#2a4a32')); c.set_line_width(10); c.move_to(x, 1120); c.line_to(x, 1120 - h); c.stroke()
        c.set_source_rgb(*rgb('#6a6030')); c.arc(x + 10, 1120 - h + 10, 34, 0, 2 * math.pi); c.fill()
        c.set_source_rgb(*rgb('#3a2a1e')); c.arc(x + 10, 1120 - h + 10, 18, 0, 2 * math.pi); c.fill()
    c.set_source_rgba(0.85, 0.95, 0.6, 0.55)   # a few fireflies
    for (x, y, s) in flies:
        a = 0.5 + 0.5 * math.sin(t * 3 * s + x)
        c.set_source_rgba(0.85, 0.95, 0.6, 0.25 + 0.4 * a); c.arc(x + 30 * math.sin(t * s), y + 20 * math.cos(t * s * 1.3), 4, 0, 2 * math.pi); c.fill()

def heron_body(c, t):   # giant praying mantis standing behind the hedge
    bob = 5 * math.sin(t * 1.6); sway = 0.03 * math.sin(t * 1.1)
    c.save(); c.translate(0, bob)
    c.set_line_cap(cairo.LINE_CAP_ROUND)
    G1, G2, G3 = rgb('#3e7a3c'), rgb('#55964a'), rgb('#2c5a2c')
    # hind legs
    c.set_source_rgb(*G3); c.set_line_width(14)
    for (x0, x1, x2) in ((830, 900, 960), (900, 990, 1040)): c.move_to(x0, 1090); c.line_to(x1, 980); c.line_to(x2, 1140); c.stroke()
    # long abdomen lying back to the right
    c.save(); c.translate(900, 1060); c.rotate(-0.25); c.scale(150, 56); c.set_source_rgb(*G1); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    c.set_source_rgba(0, 0, 0, 0.18); c.set_line_width(4)
    for k in range(5): c.move_to(800 + k * 45, 1020 - k * 10); c.line_to(820 + k * 45, 1110 - k * 10); c.stroke()
    # folded wings over the abdomen
    c.save(); c.translate(920, 1030); c.rotate(-0.3); c.scale(130, 34); c.set_source_rgba(0.55, 0.75, 0.45, 0.8); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    # long thorax rising up
    c.save(); c.translate(760, 1080); c.rotate(sway)
    c.set_source_rgb(*G1); c.set_line_width(46); c.move_to(0, 0); c.line_to(-60, -170); c.stroke()
    c.set_source_rgb(*G2); c.set_line_width(26); c.move_to(-4, -10); c.line_to(-56, -160); c.stroke()
    # triangular head with big eyes
    c.translate(-66, -200)
    c.set_source_rgb(*G2); c.move_to(-62, -30); c.line_to(62, -30); c.line_to(0, 50); c.close_path(); c.fill()
    for s in (-1, 1):
        c.set_source_rgb(*rgb('#8ac46a')); c.arc(s * 50, -34, 26, 0, 2 * math.pi); c.fill()
        c.set_source_rgb(0.05, 0.08, 0.05); c.arc(s * 46, -30, 11, 0, 2 * math.pi); c.fill()
        c.set_source_rgb(*rgb('#2c5a2c')); c.set_line_width(4); c.move_to(s * 14, -40); c.curve_to(s * 30, -110, s * 70, -140, s * 110, -150 + 8 * math.sin(t * 2 + s)); c.stroke()   # antennae
    c.set_source_rgb(*rgb('#2c4a26')); c.arc(0, 40, 8, 0, 2 * math.pi); c.fill()
    c.restore()
    c.set_line_cap(cairo.LINE_CAP_BUTT)
    c.restore()

def snake_head(t):
    for s in STR:
        if s['t'] > S.T_RES + 0.05 and not (T_FAIL and s['t'] <= T_FAIL): continue
        tip = tongue_tip(s, t)
        if tip: return tip[0], tip[1], (1.0 if tip[2] else 0.15)
    return MOUTH[0] + 8 * math.sin(t * 2.1), MOUTH[1] + 6 * math.sin(t * 4.2), 0.0

def draw_snake(c, t, hx, hy, mo, bulge):   # mantis raptorial foreleg; (hx, hy) = claw
    nx0, ny0 = ARM0[0], ARM0[1] + 5 * math.sin(t * 1.6)
    d = math.hypot(hx - nx0, hy - ny0)
    mx, my = (nx0 + hx) / 2 + 30 * math.sin(t * 3), min(ny0, hy) - 90 - 0.12 * d
    pts = []
    for j in range(0, 11):
        q = j / 10; u = 1 - q
        pts.append((u * u * nx0 + 2 * u * q * mx + q * q * hx, u * u * ny0 + 2 * u * q * my + q * q * hy))
    c.set_line_cap(cairo.LINE_CAP_ROUND)
    for wdt, col in ((34 + 8 * bulge, '#2c5a2c'), (22 + 6 * bulge, '#55964a')):
        c.set_source_rgb(*rgb(col)); c.set_line_width(wdt); c.move_to(*pts[0])
        for p in pts[1:]: c.line_to(*p)
        c.stroke()
    c.set_source_rgb(*rgb('#2c5a2c'))
    for p in pts[2:-1:2]:   # little spines along the leg
        c.move_to(p[0] - 6, p[1] + 10); c.line_to(p[0], p[1] + 26); c.line_to(p[0] + 6, p[1] + 10); c.close_path(); c.fill()
    c.set_line_cap(cairo.LINE_CAP_BUTT)
    ang = math.atan2(hy - pts[-2][1], hx - pts[-2][0])
    opn = 0.6 if mo >= 1 else (0.12 if mo > 0 else 0.2)
    c.save(); c.translate(hx, hy); c.rotate(ang)
    c.set_source_rgb(*rgb('#3e7a3c')); c.save(); c.scale(40, 26); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    for s in (-1, 1):   # two spiky grasping hooks
        c.save(); c.rotate(s * opn)
        c.set_source_rgb(*rgb('#6aa65a')); c.move_to(16, s * 6); c.curve_to(46, s * 28, 74, s * 20, 82, -s * 2); c.curve_to(62, s * 8, 42, s * 6, 16, -s * 8); c.close_path(); c.fill()
        c.set_source_rgb(*rgb('#2c5a2c'))
        for k in range(3): xx = 30 + k * 16; c.move_to(xx, s * 10); c.line_to(xx + 4, s * 2); c.line_to(xx + 8, s * 12); c.close_path(); c.fill()
        c.restore()
    c.restore()

def draw_floor(c):
    # hedge the mantis stands behind
    c.set_source_rgb(*rgb('#1e3a2a')); c.move_to(0, 1190)
    for k in range(13): x = k * 90; c.curve_to(x + 20, 1140 - 10 * (k % 3), x + 70, 1140 - 10 * ((k + 1) % 3), x + 90, 1180)
    c.line_to(W, 1260); c.line_to(0, 1260); c.close_path(); c.fill()
    c.set_source_rgba(1, 1, 1, 0.05)
    for k in range(20): c.arc((k * 137) % W, 1180 + (k * 29) % 60, 10, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#2e2620')); c.rectangle(0, 1240, W, 400); c.fill()   # garden bed in perspective
    c.set_source_rgb(*rgb('#3a5a34'))
    for k in range(9):   # rows of little lettuces
        for j in range(3):
            x = 60 + k * 120 + j * 30; y = 1290 + j * 90
            c.arc(x, y, 18 + j * 4, math.pi, 2 * math.pi); c.fill()
    c.move_to(0, H)
    for x in range(0, W + 1, 6): c.line_to(x, TER.h[x])
    c.line_to(W, H); c.close_path(); c.set_source_rgb(*rgb('#4a3a2c')); c.fill()   # packed soil
    c.set_source_rgba(0, 0, 0, 0.18)
    for k in range(16): c.arc((k * 173) % W, GROUND + 60 + (k * 61) % 240, 6 + k % 3 * 3, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#5e4a38')); c.set_line_width(8)
    for x in range(0, W + 1, 6): (c.move_to if x == 0 else c.line_to)(x, TER.h[x] + 3)
    c.stroke()
    (x0, x1) = (0, XMIN - R)   # stacked clay flower pots on the left
    for k, yy in enumerate(range(GROUND - 150, 880, -150)):
        c.set_source_rgb(*rgb('#7a4438' if k % 2 else '#6a3c32'))
        c.move_to(x0 - 10, yy); c.line_to(x1 + 6, yy); c.line_to(x1 - 6, yy + 150); c.line_to(x0, yy + 150); c.close_path(); c.fill()
        c.set_source_rgb(*rgb('#8a5044')); c.rectangle(x0 - 10, yy, x1 - x0 + 18, 26); c.fill()
    c.set_source_rgb(*rgb('#6a3c32')); c.rectangle(x0, GROUND, x1 - x0, H - GROUND); c.fill()
    (x0, x1) = (XMAX + R, W)   # stack of garden bricks on the right
    c.set_source_rgb(*rgb('#2e2626')); c.rectangle(x0, 1000, x1 - x0, H - 1000); c.fill()
    for k, yy in enumerate(range(1000, H, 60)):
        off = 0 if k % 2 else 40
        for xx in range(x0 - off, x1, 80):
            c.set_source_rgb(*rgb('#6a4a44' if (k + xx // 80) % 2 else '#5e403a')); rrect(c, xx + 3, yy + 3, 74, 54, 6); c.fill()

def render(f, c):
    t = f / FPS; fi = min(f, len(POS) - 1)
    c.save()
    draw_bg(c, t); heron_body(c, t); draw_floor(c)
    hx, hy, mo = snake_head(t)
    active = (None, (hx, hy, True)) if mo > 0 else None
    if SPIT_T and SPIT_T - 0.15 <= t < SPIT_T + 0.3: mo = 1.0
    bulge = 0.0
    for i in range(3):
        if EATEN_AT[i] and EATEN_AT[i] <= t < EATEN_AT[i] + 1.4 and not (i == 0 and SPIT_T and t >= SPIT_T): bulge = max(bulge, 1 - (t - EATEN_AT[i]) / 1.4 * 0.6)
    draw_snake(c, t, hx, hy, mo, bulge)
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
            draw_blob(c, t, x, y, mood, 0, R=R, skin=SKINS[0], dizzy=bool(slimy))
            if slimy:
                c.set_source_rgba(0.45, 0.75, 0.4, 0.8)
                for j in range(4): c.arc(x - 45 + j * 30, y - R - 10 - 30 * ((t * 1.2 + j * 0.27) % 1), 6, 0, 2 * math.pi); c.fill()
        else:
            draw_blob(c, t + i, x, y, 'scared' if danger else 'worried', 0, R=R, skin=SKINS[i], sweat=False)
    END.draw_claw(c, t)
    c.restore()
    END.header(c, t, fi)

if __name__ == '__main__':
    if sys.argv[1] == 'sim':
        print(SEED, S.OUTCOME, round(S.T_RES - S.T_START, 2), 'eaten', [(NAMES[i], round(EATEN_AT[i] - S.T_START, 1)) for i in range(3) if EATEN_AT[i]], 'strikes', len([s for s in STR if S.T_START <= s['t'] < S.T_RES]), 'dur', S.DUR); sys.exit()
    run(S, render)
