"""2026-11-10 v5 — WHO FIRST: the GIANT ANTEATER. Gloop (orange) and two rival blobs (blue, pink) are passive
rigid balls (Ball) bouncing on the dry ground of a savanna at night between two termite mounds; they collide with
each other (equal-mass elastic). A giant anteater at the back shoots its long sticky tongue at seeded-random
times at where a random remaining blob WAS a moment ago — the tongue tip slurps whoever it touches. Gloop slurped
= fail (spat back out sticky & dizzy). Timer ends unslurped = win."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the giant anteater'
SEED = int(os.environ.get('SEED', 21))
rng = random.Random(SEED)

class S: pass
S.HOOK2 = 'THE GIANT ANTEATER?'; S.HOOK2_SIZE = 84; S.FAIL_WORD = 'SLURP!'; S.FAIL_SIZE = 160
S.T_START = HOOK_T; S.TL = 13.0; S.T_END = S.T_START + S.TL
GROUND = 1610; R = 56; XMIN, XMAX = 160, 920
MOUTH = (540, 1060); TIP_R = 46; T_OUT, T_HOLD, T_BACK = 0.22, 0.08, 0.35
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


stars = [(rng.uniform(0, W), rng.uniform(HEAD, 950), rng.uniform(1.2, 2.4)) for _ in range(45)]
POT = (540, 1360)
def draw_bg(c, t):
    c.set_source_rgb(*rgb('#161a28')); c.rectangle(0, HEAD, W, H - HEAD); c.fill()
    c.set_source_rgba(0.9, 0.9, 0.85, 0.45)
    for x, y, r in stars: c.arc(x, y, r, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#e6dcae')); c.arc(200, 520, 42, 0, 2 * math.pi); c.fill()
    # acacia tree silhouettes + far grass line
    c.set_source_rgb(*rgb('#1e2228'))
    for (x, y, sc) in ((150, 1180, 1.0), (930, 1150, 0.8)):
        c.set_line_width(14 * sc); c.move_to(x, 1320); c.line_to(x + 10 * sc, y); c.stroke()
        c.save(); c.translate(x + 10 * sc, y - 20 * sc); c.scale(160 * sc, 40 * sc); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    c.set_source_rgb(*rgb('#2a2a26')); c.move_to(0, 1320)
    for x in range(0, W + 1, 30): c.line_to(x, 1290 + 12 * math.sin(x * 0.07))
    c.line_to(W, 1330); c.line_to(0, 1330); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#4a3e30')); c.rectangle(0, 1320, W, H - 1320); c.fill()

def snake_head(t):
    """Tongue tip + reach amount: tip resting at MOUTH, or the active lunge's tip."""
    for s in STR:
        if s['t'] > S.T_RES + 0.05 and not (T_FAIL and s['t'] <= T_FAIL): continue
        tip = tongue_tip(s, t)
        if tip: return tip[0], tip[1], (1.0 if tip[2] else 0.15)
    return MOUTH[0] + 10 * math.sin(t * 2.1), MOUTH[1] + 6 * math.sin(t * 4.2), 0.0

def draw_snake(c, t, hx, hy, mo, bulge):   # the giant anteater at the back: body, long snout, sticky tongue
    sw = 10 * math.sin(t * 2.1); mx, my = MOUTH[0] + sw * 0.6, MOUTH[1] - 10
    fur, dark, light = rgb('#6a625a'), rgb('#3a3430'), rgb('#cfc4b0')
    # bushy tail + body
    BX, BY = 830, 1090
    c.set_source_rgb(*dark); c.save(); c.translate(BX + 170, BY - 70 + 8 * math.sin(t * 1.3)); c.rotate(-0.9); c.scale(150, 60); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    for lx in (BX - 120, BX + 110):   # legs
        c.set_source_rgb(*dark); rrect(c, lx - 28, BY + 40, 56, 1320 - BY - 40, 20); c.fill()
    c.set_source_rgb(*fur); c.save(); c.translate(BX, BY); c.scale(200, 115); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    c.set_source_rgb(*dark); c.move_to(BX - 190, BY - 40); c.curve_to(BX - 80, BY - 10, BX + 40, BY - 60, BX + 160, BY + 10); c.line_to(BX + 140, BY + 50); c.curve_to(BX + 30, BY - 20, BX - 80, BY + 30, BX - 190, BY - 4); c.close_path(); c.fill()   # black stripe
    c.set_source_rgb(*light); c.move_to(BX - 190, BY - 40); c.curve_to(BX - 100, BY - 24, BX, BY - 60, BX + 80, BY - 30); c.line_to(BX + 70, BY - 12); c.curve_to(BX, BY - 40, BX - 100, BY - 6, BX - 190, BY - 22); c.close_path(); c.fill()
    # head + long tapering snout down to the mouth
    hx0, hy0 = 690, 990
    c.set_source_rgb(*fur); c.move_to(BX - 150, BY - 80); c.line_to(hx0 + 20, hy0 - 50); c.line_to(hx0 + 20, hy0 + 55); c.line_to(BX - 150, BY + 60); c.close_path(); c.fill()   # neck
    c.save(); c.translate(hx0, hy0); c.scale(78, 60); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    ang = math.atan2(my - hy0, mx - hx0); px, py = -math.sin(ang), math.cos(ang)
    c.move_to(hx0 + px * 46, hy0 + py * 46); c.line_to(mx + px * 12, my + py * 12); c.line_to(mx - px * 12, my - py * 12); c.line_to(hx0 - px * 46, hy0 - py * 46); c.close_path(); c.fill()
    if bulge > 0: c.arc(lerp(hx0, mx, 0.45), lerp(hy0, my, 0.45), 28 + 18 * bulge, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*dark); c.save(); c.translate(hx0 + 34, hy0 - 56); c.rotate(0.4); c.scale(18, 30); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()   # ear
    c.set_source_rgb(0.95, 0.9, 0.7); c.arc(hx0 - 4, hy0 - 16, 12, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(0.05, 0.05, 0.05); c.arc(hx0 - 8, hy0 - 14, 6, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*dark); c.set_line_width(6); c.move_to(hx0 - 30, hy0 - 38); c.line_to(hx0 + 12, hy0 - 26); c.stroke()   # grumpy brow
    c.set_source_rgb(*dark); c.arc(mx, my, 13, 0, 2 * math.pi); c.fill()   # nose tip
    c.set_source_rgb(*dark); c.save(); c.translate(hx0 + 30, hy0 - 60); c.rotate(0.4); c.scale(18, 30); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()   # ear
    c.set_source_rgb(0.95, 0.9, 0.7); c.arc(hx0 - 10, hy0 - 16, 12, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(0.05, 0.05, 0.05); c.arc(hx0 - 14, hy0 - 14, 6, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*dark); c.set_line_width(6); c.move_to(hx0 - 34, hy0 - 36); c.line_to(hx0 + 8, hy0 - 26); c.stroke()   # grumpy brow
    # sticky tongue
    d = math.hypot(hx - mx, hy - my)
    if d > 16:
        c.set_line_cap(cairo.LINE_CAP_ROUND)
        c.set_source_rgb(*rgb('#c0506a')); c.set_line_width(20); c.move_to(mx, my); c.line_to(hx, hy); c.stroke()
        c.set_source_rgb(*rgb('#e07890')); c.set_line_width(8); c.move_to(mx, my); c.line_to(hx, hy); c.stroke()
        c.set_source_rgb(*rgb('#d0607a')); c.arc(hx, hy, 26, 0, 2 * math.pi); c.fill()
        c.set_source_rgba(1, 1, 1, 0.35); c.arc(hx - 8, hy - 8, 8, 0, 2 * math.pi); c.fill()

def draw_floor(c):
    c.move_to(0, H)
    for x in range(0, W + 1, 6): c.line_to(x, TER.h[x])
    c.line_to(W, H); c.close_path(); c.set_source_rgb(*rgb('#5a4a36')); c.fill()
    c.set_source_rgb(*rgb('#6a5840')); c.set_line_width(10)
    for x in range(0, W + 1, 6): (c.move_to if x == 0 else c.line_to)(x, TER.h[x] + 3)
    c.stroke()
    c.set_source_rgba(0, 0, 0, 0.18)
    for i in range(50): c.arc((i * 137) % W, GROUND + 40 + (i * 53) % (H - GROUND - 60), 5, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#4a5a32'))
    for i in range(14):   # dry grass tufts
        x = 30 + i * 78; y = GROUND + 30 + (i * 71) % 220
        for k in (-1, 0, 1): c.move_to(x + k * 8, y); c.line_to(x + k * 16, y - 26); c.line_to(x + k * 8 + 4, y); c.close_path(); c.fill()
    for (x0, x1, s) in ((0, XMIN - R, 1), (XMAX + R, W, -1)):   # termite mounds = walls
        inner = x1 if s == 1 else x0; outer = -60 if s == 1 else W + 60; peak = inner - s * 50
        c.set_source_rgb(*rgb('#8a6a48')); c.move_to(outer, GROUND + 20); c.line_to(inner, GROUND + 20)
        c.curve_to(inner, GROUND - 350, peak + s * 20, GROUND - 600, peak, GROUND - 640)
        c.curve_to(peak - s * 40, GROUND - 600, outer, GROUND - 420, outer, GROUND - 300); c.close_path(); c.fill()
        c.set_source_rgb(*rgb('#6e5236'))
        for j in range(5): c.save(); c.translate(inner - s * (26 + j * 8), GROUND - 80 - j * 110); c.scale(12, 22); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()

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
            draw_blob(c, t, x, y, mood, 0, R=R, skin=(('#ffc8b0', '#f0806a', '#a04a3a') if slimy else SKINS[0]), dizzy=bool(slimy))
            if slimy:
                c.set_source_rgba(0.88, 0.5, 0.6, 0.6)
                for j in range(4): c.arc(x - 45 + j * 30, y - R - 10 - 30 * ((t * 1.2 + j * 0.27) % 1), 7, 0, 2 * math.pi); c.fill()
        else:
            draw_blob(c, t + i, x, y, 'scared' if danger else 'worried', 0, R=R, skin=SKINS[i], sweat=False)
    END.draw_claw(c, t)
    c.restore()
    END.header(c, t, fi)

if __name__ == '__main__':
    if sys.argv[1] == 'sim':
        print(SEED, S.OUTCOME, round(S.T_RES - S.T_START, 2), 'eaten', [(NAMES[i], round(EATEN_AT[i] - S.T_START, 1)) for i in range(3) if EATEN_AT[i]], 'strikes', len([s for s in STR if S.T_START <= s['t'] < S.T_RES]), 'dur', S.DUR); sys.exit()
    run(S, render)
