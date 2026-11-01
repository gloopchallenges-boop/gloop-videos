"""2026-11-01 v6 — RISING DANGER – LAVA GAP m: rising LAVA inside a volcano. Lava rate has seeded
random surges; Gloop hesitates a random time on each ledge, some ledges crumble (he drops a level
if still on it). The gap between Gloop and the lava is simulated — 0 m = fail."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the rising lava'
SEED = int(os.environ.get('SEED', 3))
rng = random.Random(SEED)

class S: pass
S.HOOK2 = 'THE RISING LAVA?'; S.HOOK2_SIZE = 92; S.FAIL_WORD = 'TOO HOT!'; S.FAIL_SIZE = 150
S.T_START = 2.6; S.TL = 16.0; S.T_END = S.T_START + S.TL
R = 70; PXM = 100.0
NL = 8
PLAT = []
for i in range(NL):
    x = (300 if i % 2 == 0 else 780) + rng.uniform(-40, 40)
    PLAT.append({'x': x, 'y': 1570 - i * 150, 'w': 230, 'crumble': i > 0 and rng.random() < 0.3})
LAVA0 = 1890; BASE_RATE = 50
SURGES = []; t = S.T_START + rng.uniform(1, 3)
while t < S.T_END:
    SURGES.append((t, rng.uniform(0.6, 1.4), rng.uniform(40, 90))); t += rng.uniform(2.0, 4.0)

N0 = int(40 * FPS)
LAVA, GPOS, LVL = [], [], []
lava = LAVA0; lvl = 0; state = 'stand'; t_next = S.T_START + rng.uniform(0.6, 1.4); jump = None
crack = {}; broken = {}; T_FAIL = None; JUMPS = []; DROPS = []
for f in range(N0):
    t = f / FPS
    if t >= S.T_START:
        rate = BASE_RATE + sum(a for (s0, d, a) in SURGES if s0 <= t < s0 + d)
        if T_FAIL is not None: rate = 0
        elif t >= S.T_END: rate = BASE_RATE * max(0, 1 - (t - S.T_END) / 0.8)
        lava -= rate / FPS
    if T_FAIL is None and t < S.T_END:
        if state == 'stand' and t >= t_next and lvl < NL - 1 and t >= S.T_START:
            nx = lvl + 1
            while nx in broken and nx < NL - 1: nx += 1
            if nx not in broken: state = 'jump'; jump = (t, lvl, nx); JUMPS.append(t)
        if state == 'jump' and jump[2] > jump[1] and t >= jump[0] + 0.55:
            lvl = jump[2]; state = 'stand'; t_next = t + rng.uniform(0.9, 2.3)
            if PLAT[lvl]['crumble'] and lvl not in crack:
                crack[lvl] = t + rng.uniform(0.7, 1.3)
                t_next = min(t_next, crack[lvl] + rng.uniform(-0.5, 0.4))
        for k, tb in list(crack.items()):
            if t >= tb and k not in broken:
                broken[k] = t
                if state == 'stand' and lvl == k:
                    lo = k - 1
                    while lo in broken and lo > 0: lo -= 1
                    DROPS.append(t); state = 'jump'; jump = (t, k, lo)
    gy_plat = lambda i: PLAT[i]['y'] - R * 0.9
    if state == 'jump' and T_FAIL is None and t < S.T_END + 0.6:
        k = clamp((t - jump[0]) / 0.55, 0, 1); a, b = PLAT[jump[1]], PLAT[jump[2]]
        up = jump[2] > jump[1]
        gx = lerp(a['x'], b['x'], ease(k)); gy = lerp(gy_plat(jump[1]), gy_plat(jump[2]), k) - (210 if up else 60) * 4 * k * (1 - k)
        if k >= 1 and not up: lvl = jump[2]; state = 'stand'; t_next = t + rng.uniform(0.5, 1.2)
    elif T_FAIL is None:
        gx, gy = PLAT[lvl]['x'], gy_plat(lvl)
    else:
        gx, gy = GPOS[-1]
    if T_FAIL is None and S.T_START <= t < S.T_END and lava <= gy + R * 0.85:
        T_FAIL = t
    LAVA.append(lava); GPOS.append((gx, gy)); LVL.append(lvl)
S.OUTCOME = 'fail' if T_FAIL else 'win'
S.T_RES = T_FAIL if T_FAIL else S.T_END
fx, fy = GPOS[int(S.T_RES * FPS)]
FLOAT_Y = LAVA[int(S.T_RES * FPS)] - R * 0.55
S.GRAB = (fx, FLOAT_Y if T_FAIL else fy)
END = S.END = Ending(S)
GAP = [max(0, (LAVA[i] - (GPOS[i][1] + R * 0.85)) / PXM) for i in range(N0)]
S.events = [[S.T_START, 'rumble', 1.5]]
for j in JUMPS:
    if j < S.T_RES: S.events.append([j, 'hop']); S.events.append([j + 0.55, 'thump', 0.4])
for k, tb in broken.items():
    if tb < S.T_RES: S.events.append([tb, 'crash'])
for s0, d, a in SURGES:
    if s0 < S.T_RES: S.events.append([s0, 'rumble', d])
if T_FAIL: S.events += [[T_FAIL, 'sizzle'], [T_FAIL + 0.05, 'pop']]
S.AMB = {'drone': 45, 'rumble': 0.05}

def draw_bar(c, t, f):
    g = GAP[f]; col = good_bad_col(g / 4.0)
    surge = any(s0 <= t < s0 + d for s0, d, a in SURGES)
    bx = bar(c, g / 6.0, f'LAVA GAP {g:.1f} m', col, 0.12 if surge else 0, bw=620, x_off=40)
    c.save(); c.translate(bx - 58, 231)
    c.set_source_rgb(*rgb('#ff6a1f')); c.move_to(-26, 26); c.curve_to(-30, -5, -5, -10, 0, -30); c.curve_to(5, -10, 30, -5, 26, 26); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#ffd34a')); c.move_to(-12, 26); c.curve_to(-14, 8, -2, 2, 0, -8); c.curve_to(2, 2, 14, 8, 12, 26); c.close_path(); c.fill()
    c.restore()
S.draw_bar = draw_bar

rocks = [(rng.uniform(0, W), rng.uniform(HEAD, H), rng.uniform(30, 90)) for _ in range(26)]
embers = [(rng.uniform(0, W), rng.uniform(0, 1), rng.uniform(0.5, 1.5)) for _ in range(30)]

def draw_bg(c, t):
    gr = cairo.LinearGradient(0, HEAD, 0, H)
    gr.add_color_stop_rgb(0, *rgb('#1a0b0b')); gr.add_color_stop_rgb(1, *rgb('#4a1a10'))
    c.set_source(gr); c.rectangle(0, HEAD, W, H - HEAD); c.fill()
    c.set_source_rgb(*rgb('#2a1310'))
    for x, y, r in rocks: c.save(); c.translate(x, y); c.scale(1, 0.7); c.arc(0, 0, r, 0, 2 * math.pi); c.restore(); c.fill()
    # walls
    c.set_source_rgb(*rgb('#3a1d16'))
    c.move_to(0, HEAD); c.line_to(120, HEAD); c.line_to(80, 800); c.line_to(140, 1300); c.line_to(70, H); c.line_to(0, H); c.close_path(); c.fill()
    c.move_to(W, HEAD); c.line_to(W - 110, HEAD); c.line_to(W - 70, 900); c.line_to(W - 140, 1400); c.line_to(W - 60, H); c.line_to(W, H); c.close_path(); c.fill()
    # sky opening at top
    c.set_source_rgba(1, 0.6, 0.3, 0.12); c.rectangle(0, HEAD, W, 60); c.fill()

def draw_plats(c, t):
    for i, p in enumerate(PLAT):
        tb = broken.get(i); x0 = p['x'] - p['w'] / 2
        if tb is not None and t >= tb:
            k = t - tb
            if k > 1.2: continue
            for j in range(4):
                c.set_source_rgb(*rgb('#6b5a52')); rrect(c, x0 + j * p['w'] / 4 + (j - 1.5) * 30 * k, p['y'] + 600 * k * k + 60 * k, p['w'] / 4 - 6, 40, 8); c.fill()
            continue
        sh = 0
        if i in crack and t >= crack[i] - 0.9 and LVL[min(int(t * FPS), len(LVL) - 1)] >= i: sh = 4 * math.sin(t * 60) if t > crack[i] - 0.9 else 0
        c.set_source_rgb(*rgb('#5a4a44')); rrect(c, x0 + sh, p['y'], p['w'], 44, 12); c.fill()
        c.set_source_rgb(*rgb('#7d6b63')); rrect(c, x0 + sh, p['y'], p['w'], 14, 8); c.fill()
        c.set_source_rgb(*rgb('#3d302b'))
        c.move_to(x0 + 20 + sh, p['y'] + 44); c.line_to(p['x'] + sh, p['y'] + 95); c.line_to(x0 + p['w'] - 20 + sh, p['y'] + 44); c.close_path(); c.fill()
        if p['crumble']:
            c.set_source_rgb(*rgb('#2a201c')); c.set_line_width(4)
            c.move_to(p['x'] - 30 + sh, p['y'] + 2); c.line_to(p['x'] - 10 + sh, p['y'] + 22); c.line_to(p['x'] - 25 + sh, p['y'] + 40); c.stroke()
            c.move_to(p['x'] + 50 + sh, p['y'] + 4); c.line_to(p['x'] + 62 + sh, p['y'] + 30); c.stroke()

def draw_lava(c, t, f):
    ly = LAVA[min(f, len(LAVA) - 1)]
    c.set_source_rgba(1, 0.45, 0.1, 0.18); c.rectangle(0, ly - 120, W, 120); c.fill()
    c.move_to(0, H)
    for x in range(0, W + 20, 20): c.line_to(x, ly + 10 * math.sin(x * 0.02 + t * 2.4) + 6 * math.sin(x * 0.05 - t * 3))
    c.line_to(W, H); c.close_path()
    gr = cairo.LinearGradient(0, ly, 0, ly + 400)
    gr.add_color_stop_rgb(0, *rgb('#ffcf3a')); gr.add_color_stop_rgb(0.15, *rgb('#ff6a1f')); gr.add_color_stop_rgb(1, *rgb('#b0200c'))
    c.set_source(gr); c.fill()
    for x, ph, sp in embers:
        k = (t * 0.5 * sp + ph) % 1
        c.set_source_rgba(1, 0.75, 0.25, 1 - k); c.arc(x + 20 * math.sin(t + ph * 9), ly - k * 500, 4, 0, 2 * math.pi); c.fill()
    for i in range(5):
        k = (t * 0.8 + i * 0.37) % 1; bx = (i * 233 + 90) % W
        c.set_source_rgba(1, 0.85, 0.4, 0.8 * (1 - k)); c.set_line_width(4); c.arc(bx, ly + 30 - k * 20, 10 + 18 * k, math.pi, 2 * math.pi); c.stroke()

def draw_ruler(c, f):
    gx, gy = GPOS[min(f, len(GPOS) - 1)]; ly = LAVA[min(f, len(LAVA) - 1)]
    x = gx + (130 if gx < 540 else -130); y0 = gy + R * 0.85
    if ly - y0 < 10: return
    c.set_source_rgba(1, 1, 1, 0.6); c.set_line_width(4); c.set_dash([10, 8]); c.move_to(x, y0); c.line_to(x, ly); c.stroke(); c.set_dash([])
    for yy in (y0, ly): c.move_to(x - 16, yy); c.line_to(x + 16, yy); c.stroke()
    text_at(c, f'{GAP[min(f, len(GAP) - 1)]:.1f} m', x + (70 if gx < 540 else -70), (y0 + ly) / 2, 40, (1, 1, 1), lw=7)

PS = Particles(2)
def render(f, c):
    t = f / FPS; fi = min(f, len(GPOS) - 1); shake = (0, 0)
    if any(s0 <= t < s0 + d for s0, d, a in SURGES) and t < S.T_RES: shake = (rng.uniform(-5, 5), rng.uniform(-5, 5))
    for k, tb in broken.items():
        if abs(t - tb) < 0.5 / FPS and tb < S.T_RES: PS.spawn(PLAT[k]['x'], PLAT[k]['y'], 18, (0.5, 0.42, 0.38), 400, 0.7)
    c.save(); c.translate(*shake)
    draw_bg(c, t); draw_plats(c, t)
    dizzy = False; sq = 0.04 * math.sin(t * 6) + 0.06
    if END.carried(t):
        gx, gy = END.carry_xy(t); gy -= 10
    elif T_FAIL and t >= T_FAIL:
        k = t - T_FAIL; ly = LAVA[fi]
        gx = fx; gy = lerp(fy, FLOAT_Y, ease(k / 0.25)) - 260 * max(0, math.sin(min(1, k / 0.7) * math.pi)) if k < 0.7 else FLOAT_Y + 6 * math.sin(t * 4)
        dizzy = k > 0.7
    else:
        gx, gy = GPOS[fi]
    gap = GAP[fi]
    mood = 'happy' if (t >= S.T_END and S.OUTCOME == 'win') else ('scared' if gap < 1.6 or (T_FAIL and t >= T_FAIL) else 'worried')
    scorched = T_FAIL and t >= T_FAIL
    skin = ('#c98a50', '#8a3a10', '#3a1a05') if scorched else ('#ffd36b', '#ff8a1f', '#c45a00')
    if not (T_FAIL and t >= T_FAIL and not END.carried(t)): draw_ruler(c, f)
    draw_lava(c, t, f)
    draw_blob(c, t, gx, gy, mood, sq, R=R, skin=skin, dizzy=dizzy)
    if scorched:
        for j in range(4):
            k = (t * 1.2 + j / 4) % 1
            c.set_source_rgba(0.3, 0.3, 0.3, 0.5 * (1 - k)); c.arc(gx + (j - 1.5) * 25, gy - R - k * 160, 18 + 20 * k, 0, 2 * math.pi); c.fill()
    for d in DROPS:
        if d <= t < d + 0.7 and d < S.T_RES:
            dx_, dy_ = GPOS[int(d * FPS)]; text_at(c, 'CRACK!', clamp(dx_, 220, 860), dy_ - 170, 90, rgb('#ffb347'), 1 + 0.2 * max(0, 1 - (t - d) * 5))
    PS.draw(c)
    END.draw_claw(c, t)
    c.restore()
    END.header(c, t, fi)

if __name__ == '__main__':
    if sys.argv[1] == 'sim':
        rs = int(S.T_RES * FPS) - 1
        print(SEED, S.OUTCOME, round(S.T_RES, 2), 'lvl', LVL[rs], 'mingap', round(min(GAP[int(S.T_START * FPS):rs]), 2), 'final', round(GAP[rs], 2), 'drops', len([d for d in DROPS if d < S.T_RES]), 'dur', S.DUR); sys.exit()
    run(S, render)
