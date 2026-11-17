"""2026-11-17 v3 — WHO FIRST: the GIANT MORAY EEL. Gloop (orange) and two rival blobs (blue, pink) are passive
rigid balls (Ball) bouncing on the wet sand of a rocky cove at night between two barnacled rock pillars; they collide
with each other (equal-mass elastic). A giant moray eel hiding in a crevice of the big rock at the back lunges out at
seeded-random times at where a random remaining blob WAS a moment ago — its jaws grab whoever they touch.
Gloop grabbed = fail (spat back out slimy & dizzy). Timer ends ungrabbed = win. (Adapted from 2026-11-14 v4.)"""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the giant moray eel'
SEED = int(os.environ.get('SEED', 24))
rng = random.Random(SEED)

class S: pass
S.HOOK2 = 'THE GIANT MORAY EEL?'; S.HOOK2_SIZE = 76; S.FAIL_WORD = 'CHOMP!'; S.FAIL_SIZE = 160
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
S.AMB = {'drone': 44, 'wind': 0.02}
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
def draw_bg(c, t):
    c.set_source_rgb(*rgb('#141a24')); c.rectangle(0, HEAD, W, H - HEAD); c.fill()
    c.set_source_rgba(0.85, 0.9, 1, 0.35)
    for x, y, r in stars[:24]: c.arc(x, y * 0.6 + 150, r, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#dcd8c0')); c.arc(200, 470, 34, 0, 2 * math.pi); c.fill()
    # calm sea on the horizon
    c.set_source_rgb(*rgb('#1a2838')); c.rectangle(0, 760, W, 600); c.fill()
    c.set_source_rgba(0.9, 0.88, 0.75, 0.1)
    for k in range(5): c.rectangle(170 + 10 * math.sin(t * 1.4 + k) - k * 8, 790 + k * 30, 60 + k * 16, 4); c.fill()
    # big rock cliff with the eel's crevice
    c.set_source_rgb(*rgb('#2c2a30')); c.move_to(160, 1340); c.curve_to(180, 1020, 300, 860, 480, 830); c.curve_to(640, 800, 860, 860, 930, 1060); c.curve_to(960, 1200, 940, 1300, 930, 1340); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#36343c'))
    for (x, y, sx, sy) in ((330, 960, 70, 40), (720, 920, 90, 36), (820, 1180, 60, 50), (300, 1220, 80, 44)):
        c.save(); c.translate(x, y); c.scale(sx, sy); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    c.set_source_rgb(*rgb('#3a5a44'))   # seaweed strands on the rock
    for x in (260, 380, 700, 860):
        c.set_line_width(7); c.move_to(x, 1340); c.curve_to(x + 10 * math.sin(t * 1.5 + x), 1250, x - 14, 1200, x + 8 * math.sin(t * 1.2 + x), 1150); c.stroke()
    c.set_source_rgb(*rgb('#0c0a10')); c.save(); c.translate(*MOUTH); c.scale(96, 74); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()   # crevice
    c.set_source_rgb(*rgb('#24222a')); c.set_line_width(10); c.save(); c.translate(*MOUTH); c.scale(96, 74); c.arc(0, 0, 1, math.pi * 1.05, math.pi * 1.95); c.restore(); c.stroke()
    c.set_source_rgb(*rgb('#3a3a34')); c.rectangle(0, 1330, W, H - 1330); c.fill()

def snake_head(t):
    """Tongue tip + reach amount: tip resting at MOUTH, or the active lunge's tip."""
    for s in STR:
        if s['t'] > S.T_RES + 0.05 and not (T_FAIL and s['t'] <= T_FAIL): continue
        tip = tongue_tip(s, t)
        if tip: return tip[0], tip[1], (1.0 if tip[2] else 0.15)
    return MOUTH[0] + 10 * math.sin(t * 2.1), MOUTH[1] + 6 * math.sin(t * 4.2), 0.0

def draw_snake(c, t, hx, hy, mo, bulge):   # the giant moray eel lunging out of the rock crevice
    mx, my = MOUTH
    skin, dark, spot = rgb('#5a6a2e'), rgb('#3a4620'), rgb('#c8c060')
    if mo == 0:   # resting: head peeks out of the crevice and sways
        hx, hy = mx + 10 * math.sin(t * 2.1), my + 26 + 6 * math.sin(t * 4.2)
    ang = math.atan2(hy - my, hx - mx) if math.hypot(hx - mx, hy - my) > 5 else math.pi / 2
    # body: a thick S-curve from inside the crevice to the head
    d = math.hypot(hx - mx, hy - my); px, py = -math.sin(ang), math.cos(ang); wig = 0.18 * d * math.sin(t * 6)
    c1x, c1y = mx + (hx - mx) * 0.33 + px * wig, my + (hy - my) * 0.33 + py * wig
    c2x, c2y = mx + (hx - mx) * 0.66 - px * wig, my + (hy - my) * 0.66 - py * wig
    c.set_line_cap(cairo.LINE_CAP_ROUND)
    c.set_source_rgb(*skin); c.set_line_width(66 + 20 * bulge); c.move_to(mx, my - 6); c.curve_to(c1x, c1y, c2x, c2y, hx, hy); c.stroke()
    c.set_source_rgb(*dark); c.set_line_width(8); c.move_to(mx, my - 30); c.curve_to(c1x - px * 0, c1y - 26, c2x, c2y - 26, hx, hy - 26); c.stroke()   # dorsal fin line
    c.set_line_cap(cairo.LINE_CAP_BUTT)
    c.set_source_rgb(*spot)   # leopard spots along the body
    for k in range(1, 7):
        u = k / 7.5; bx = (1 - u) ** 3 * mx + 3 * (1 - u) ** 2 * u * c1x + 3 * (1 - u) * u * u * c2x + u ** 3 * hx
        by = (1 - u) ** 3 * my + 3 * (1 - u) ** 2 * u * c1y + 3 * (1 - u) * u * u * c2y + u ** 3 * hy
        c.arc(bx + 10 * math.sin(k * 2.3), by + 10 * math.cos(k * 1.7), 7, 0, 2 * math.pi); c.fill()
    # head with gaping jaw
    open_ = 0.25 + 0.75 * (mo >= 1.0)
    c.save(); c.translate(hx, hy); c.rotate(ang)
    c.set_source_rgb(*skin); c.save(); c.scale(66, 44); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    c.set_source_rgb(*rgb('#2a0e14')); c.move_to(10, 0); c.line_to(76, -26 * open_); c.line_to(76, 26 * open_); c.close_path(); c.fill()
    c.set_source_rgb(*skin); c.move_to(-10, -44); c.line_to(80, -18 - 22 * open_); c.line_to(80, -6 - 18 * open_); c.line_to(0, -6); c.close_path(); c.fill()
    c.move_to(-10, 44); c.line_to(76, 18 + 22 * open_); c.line_to(76, 6 + 18 * open_); c.line_to(0, 6); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#f0ecd8'))
    for k in range(4):
        x = 30 + k * 14; c.move_to(x, -10 - 16 * open_ * x / 76); c.line_to(x + 5, -10 - 16 * open_ * x / 76 + 12); c.line_to(x + 10, -10 - 16 * open_ * x / 76); c.close_path(); c.fill()
        c.move_to(x, 10 + 16 * open_ * x / 76); c.line_to(x + 5, 10 + 16 * open_ * x / 76 - 12); c.line_to(x + 10, 10 + 16 * open_ * x / 76); c.close_path(); c.fill()
    c.restore()
    ex, ey = hx + math.cos(ang) * 14 - math.sin(ang) * -24 * (1 if math.cos(ang) >= 0 else -1), hy + math.sin(ang) * 14 + math.cos(ang) * -24 * (1 if math.cos(ang) >= 0 else -1)
    c.set_source_rgb(*rgb('#e8e060')); c.arc(ex, ey, 13, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(0.05, 0.05, 0.05); c.arc(ex + math.cos(ang) * 3, ey + math.sin(ang) * 3, 6, 0, 2 * math.pi); c.fill()

def draw_floor(c):
    c.move_to(0, H)
    for x in range(0, W + 1, 6): c.line_to(x, TER.h[x])
    c.line_to(W, H); c.close_path(); c.set_source_rgb(*rgb('#5a5040')); c.fill()   # wet sand
    c.set_source_rgb(*rgb('#6e6450')); c.set_line_width(8)
    for x in range(0, W + 1, 6): (c.move_to if x == 0 else c.line_to)(x, TER.h[x] + 3)
    c.stroke()
    c.set_source_rgba(0, 0, 0, 0.16)
    for i in range(50): c.arc((i * 137) % W, GROUND + 40 + (i * 53) % (H - GROUND - 60), 4, 0, 2 * math.pi); c.fill()
    for i in range(7):   # shells + pebbles
        x = 70 + i * 150; y = GROUND + 60 + (i * 83) % 200
        c.set_source_rgb(*rgb(('#c8a8a0', '#a0a8b0', '#d0c0a0')[i % 3])); c.save(); c.translate(x, y); c.scale(14, 9); c.arc(0, 0, 1, math.pi, 2 * math.pi); c.restore(); c.fill()
    for (x0, x1, s) in ((0, XMIN - R, 1), (XMAX + R, W, -1)):   # barnacled rock pillars = walls
        inner = x1 if s == 1 else x0; outer = -60 if s == 1 else W + 60
        c.set_source_rgb(*rgb('#3e3c44')); c.move_to(outer, GROUND + 20); c.line_to(inner, GROUND + 20)
        c.curve_to(inner + s * 10, GROUND - 300, inner - s * 30, GROUND - 520, inner - s * 50, GROUND - 600)
        c.line_to(outer, GROUND - 620); c.close_path(); c.fill()
        c.set_source_rgb(*rgb('#8a8a90'))
        for j in range(6): c.arc(inner - s * (14 + (j % 2) * 18), GROUND - 60 - j * 85, 7, 0, 2 * math.pi); c.fill()
        c.set_source_rgb(*rgb('#3a5a44'))
        for j in range(4): c.save(); c.translate(inner - s * (30 + j * 6), GROUND - 140 - j * 120); c.scale(10, 20); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()

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
            draw_blob(c, t, x, y, mood, 0, R=R, skin=(('#d8e0a0', '#a8b860', '#5a6a2e') if slimy else SKINS[0]), dizzy=bool(slimy))
            if slimy:
                c.set_source_rgba(0.7, 0.8, 0.4, 0.6)
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
