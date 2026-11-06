"""2026-11-06 v8 — WHO FIRST: the HUNGRY PELICAN. Gloop (orange) and two rival blobs (blue, pink) are passive
rigid balls (Ball) bouncing on the planks of a fishing pier at night between two stacks of crates; they collide
with each other (equal-mass elastic). A huge pelican perched on a mooring post at the back lunges its long neck
down at seeded-random times at where a random remaining blob WAS a moment ago — the open beak scoops whoever it
touches. Gloop scooped = fail (gulped, spat out soggy & dizzy). Timer ends uneaten = win."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the hungry pelican'
SEED = int(os.environ.get('SEED', 21))
rng = random.Random(SEED)

class S: pass
S.HOOK2 = 'THE HUNGRY PELICAN?'; S.HOOK2_SIZE = 86; S.FAIL_WORD = 'GULP!'; S.FAIL_SIZE = 160
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
if T_FAIL:   # flytrap spits Gloop out dizzy & slimy onto the log
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


stars = [(rng.uniform(0, W), rng.uniform(HEAD, 820), rng.uniform(1.2, 2.4)) for _ in range(45)]
POT = (540, 1360)
def draw_bg(c, t):
    c.set_source_rgb(*rgb('#121824')); c.rectangle(0, HEAD, W, H - HEAD); c.fill()
    c.set_source_rgba(0.85, 0.9, 0.95, 0.45)
    for x, y, r in stars: c.arc(x, y, r, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#e2e0cc')); c.arc(170, 560, 48, 0, 2 * math.pi); c.fill()
    # distant lighthouse on a headland
    c.set_source_rgb(*rgb('#1c2430')); c.move_to(700, 1130); c.curve_to(820, 1040, 960, 1050, W, 1080); c.line_to(W, 1140); c.line_to(700, 1140); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#2e3644')); c.move_to(880, 1060); c.line_to(900, 900); c.line_to(930, 900); c.line_to(950, 1060); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#d8c070')); c.rectangle(898, 875, 34, 25); c.fill()
    # sea
    c.set_source_rgb(*rgb('#16263a')); c.rectangle(0, 1130, W, H - 1130); c.fill()
    c.set_source_rgba(0.9, 0.9, 0.8, 0.10)
    for i in range(7): c.rectangle(170 - 60 + 10 * math.sin(t * 2 + i), 1150 + i * 22, 120 - i * 12, 5); c.fill()
    c.set_source_rgba(1, 1, 1, 0.05); c.set_line_width(3)
    for i in range(8):
        x = (i * 173 + t * 30) % (W + 200) - 100; y = 1170 + (i * 59) % 240
        c.move_to(x, y); c.line_to(x + 80, y); c.stroke()
    # pier railing behind the deck
    c.set_source_rgb(*rgb('#3a2e26'))
    for x in range(20, W, 160): c.rectangle(x, 1300, 18, 120); c.fill()
    c.rectangle(0, 1300, W, 14); c.fill(); c.rectangle(0, 1350, W, 10); c.fill()
    c.set_source_rgb(*rgb('#2a2220')); c.rectangle(0, 1410, W, H - 1410); c.fill()

def snake_head(t):
    """Jaw position + open amount: idle sway at MOUTH, or the active lunge's tip."""
    for s in STR:
        if s['t'] > S.T_RES + 0.05 and not (T_FAIL and s['t'] <= T_FAIL): continue
        tip = tongue_tip(s, t)
        if tip: return tip[0], tip[1], (1.0 if tip[2] else 0.15)
    return MOUTH[0] + 26 * math.sin(t * 2.1), MOUTH[1] + 10 * math.sin(t * 4.2), 0.35 + 0.15 * math.sin(t * 3)

def draw_snake(c, t, hx, hy, mo, bulge):   # the pelican: body on a mooring post, long neck, scooping beak
    bx, by = POT
    # mooring post
    c.set_source_rgb(*rgb('#4a3a2e')); c.rectangle(bx - 55, by - 40, 110, 300); c.fill()
    c.set_source_rgb(*rgb('#5a483a')); c.save(); c.translate(bx, by - 40); c.scale(55, 16); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    c.set_source_rgb(*rgb('#2e2420')); c.rectangle(bx - 55, by + 40, 110, 12); c.fill()
    # body
    c.set_source_rgb(*rgb('#d8d4cc')); c.save(); c.translate(bx - 20, by - 110); c.rotate(-0.25); c.scale(120, 80); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    c.set_source_rgb(*rgb('#8a8680')); c.save(); c.translate(bx - 60, by - 120); c.rotate(-0.3); c.scale(100, 46); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()   # folded wing
    c.set_source_rgb(*rgb('#e8a040')); c.set_line_width(10)
    for dx in (-20, 20): c.move_to(bx + dx, by - 50); c.line_to(bx + dx, by - 36); c.stroke()
    # neck
    c.set_line_cap(cairo.LINE_CAP_ROUND)
    n0 = (bx + 60, by - 150); c1 = (bx + 110 - 30 * math.sin(t * 2.1), by - 300); c2 = (lerp(bx + 60, hx, 0.6), lerp(by - 360, hy - 160, 0.6))
    hd = (hx, hy - 110)
    c.set_source_rgb(*rgb('#d8d4cc')); c.set_line_width(40); c.move_to(*n0); c.curve_to(*c1, *c2, *hd); c.stroke()
    if bulge > 0:
        mx = 0.125 * n0[0] + 0.375 * c1[0] + 0.375 * c2[0] + 0.125 * hd[0]; my = 0.125 * n0[1] + 0.375 * c1[1] + 0.375 * c2[1] + 0.125 * hd[1]
        c.arc(mx, my, 44 * bulge, 0, 2 * math.pi); c.fill()
    # head
    c.set_source_rgb(*rgb('#e8e4dc')); c.arc(hd[0], hd[1], 42, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#f0e0a0')); c.save(); c.translate(hd[0] - 10, hd[1] - 40); c.scale(20, 10); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()   # crest
    c.set_source_rgb(0.08, 0.08, 0.1); c.arc(hd[0] + 16, hd[1] - 8, 7, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#5a5650')); c.set_line_width(5); c.move_to(hd[0] + 2, hd[1] - 24); c.line_to(hd[0] + 30, hd[1] - 18); c.stroke()   # grumpy brow
    # beak pointing down from the head; mo opens it (upper bill swings right, pouch swings left)
    ang = 0.08 + 0.55 * mo
    for sd, col in ((1, '#e8a040'), (-1, '#f0c070')):
        c.save(); c.translate(hd[0], hd[1] + 10); c.rotate(-sd * ang)
        c.set_source_rgb(*rgb(col))
        if sd == 1:
            c.move_to(-14, 0); c.line_to(18, 0); c.line_to(6, 150); c.line_to(-2, 150); c.close_path(); c.fill()
            c.set_source_rgb(*rgb('#c06a2a')); c.arc(2, 150, 8, 0, 2 * math.pi); c.fill()
        else:
            c.move_to(-14, 0); c.curve_to(-60 - 30 * mo, 50, -40 - 20 * mo, 130, 0, 146); c.line_to(10, 0); c.close_path(); c.fill()
        c.restore()

def draw_floor(c):
    c.move_to(0, H)
    for x in range(0, W + 1, 6): c.line_to(x, TER.h[x])
    c.line_to(W, H); c.close_path(); c.set_source_rgb(*rgb('#5a4634')); c.fill()
    c.set_source_rgb(*rgb('#6e5640')); c.set_line_width(10)
    for x in range(0, W + 1, 6): (c.move_to if x == 0 else c.line_to)(x, TER.h[x] + 3)
    c.stroke()
    c.set_source_rgba(0, 0, 0, 0.25); c.set_line_width(3)
    for yy in range(GROUND + 50, H, 55): c.move_to(0, yy); c.line_to(W, yy); c.stroke()
    for j, yy in enumerate(range(GROUND + 50, H, 55)):
        for x in range((j % 2) * 150, W, 300): c.move_to(x, yy); c.line_to(x, yy + 55); c.stroke()
    for (x0, x1) in ((0, XMIN - R), (XMAX + R, W)):   # stacked fish crates = walls
        wdt = x1 - x0
        for j, yy in enumerate((GROUND - 130, GROUND - 260, GROUND - 390, GROUND - 520)):
            c.set_source_rgb(*rgb('#7a5a3a' if j % 2 == 0 else '#6a4e34')); c.rectangle(x0, yy, wdt, 126); c.fill()
            c.set_source_rgb(*rgb('#4a3424')); c.set_line_width(5)
            c.rectangle(x0 + 6, yy + 6, wdt - 12, 114); c.stroke(); c.move_to(x0 + 6, yy + 6); c.line_to(x1 - 6, yy + 120); c.stroke()
        c.set_source_rgb(*rgb('#8a9aa8'))
        for k in range(3): c.save(); c.translate(x0 + wdt * (0.3 + 0.2 * k), GROUND - 530); c.rotate(0.3 * k - 0.3); c.scale(26, 9); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()   # fish on top

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
            draw_blob(c, t, x, y, mood, 0, R=R, skin=(('#ffe6a8', '#e8a454', '#9a6428') if slimy else SKINS[0]), dizzy=bool(slimy))
            if slimy:
                c.set_source_rgba(0.6, 0.8, 1.0, 0.7)
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
