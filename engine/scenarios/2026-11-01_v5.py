"""2026-11-01 v5 — TEMPERATURE – FREEZE %: BLIZZARD on a snowy mountain. Gloop hugs a campfire;
seeded-random wind gusts blow him away from it and knock the flame down, snow clumps drop from a
pine branch. FREEZE % is simulated from Gloop's distance to the fire and the flame strength."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the blizzard'
SEED = int(os.environ.get('SEED', 3))
rng = random.Random(SEED)

class S: pass
S.HOOK2 = 'THE BLIZZARD?'; S.HOOK2_SIZE = 100; S.FAIL_WORD = 'FROZEN!'; S.FAIL_SIZE = 150
S.T_START = 2.6; S.TL = 15.0; S.T_END = S.T_START + S.TL
GROUND = 1580; R = 80; GY = GROUND - R * 0.9; FIRE_X = 560; WARM = 175
COLD_UP, GUST_UP, WARM_DOWN = 9.0, 9.0, 8.0

GUSTS = []; t = S.T_START + rng.uniform(0.6, 1.6)
while t < S.T_END - 0.5:
    s = rng.uniform(0.35, 1.0); d = rng.choice((-1, 1)) if GUSTS else -1
    GUSTS.append({'t': t, 'dur': 0.6 + 0.8 * s, 's': s, 'dir': d, 'push': (180 + 330 * s) * d})
    t += rng.uniform(1.6, 3.0)
CLUMPS = [{'t': rng.uniform(S.T_START + 2, S.T_END - 1), 'x': x} for x in (rng.uniform(800, 880),)]
CLUMPS += [{'t': rng.uniform(S.T_START + 2, S.T_END - 1), 'x': rng.uniform(170, 260)}]

N0 = int(40 * FPS); GX, FRZ, FIRE, GUSTING = [], [], [], []
gx = FIRE_X + 150; target = gx; fz = 0.0; fire = 1.0; vx = 0.0; T_FAIL = None; ret_at = None
for f in range(N0):
    t = f / FPS; g = None
    for G in GUSTS:
        if G['t'] <= t < G['t'] + G['dur']: g = G
        if abs(t - G['t']) < 0.5 / FPS:
            fire = max(0.1, fire - 0.7 * G['s']); vx = G['push'] / G['dur']
            ret_at = G['t'] + G['dur'] + rng.uniform(0.25, 1.0)
    if T_FAIL is None and t >= S.T_START:
        if g: gx = clamp(gx + vx / FPS * 1.0, 110, W - 110)
        elif ret_at and t >= ret_at:
            tx = FIRE_X + (150 if gx > FIRE_X else -150)
            step = 430 / FPS; gx += clamp(tx - gx, -step, step)
        warm = abs(gx - FIRE_X) < WARM and fire > 0.45
        for Cl in CLUMPS:
            if abs(t - Cl['t'] - 0.45) < 0.5 / FPS and abs(gx - Cl['x']) < 120: fz += 14; Cl['hit'] = True
        if t < S.T_END:
            fz = clamp(fz + ((-WARM_DOWN) if warm else (COLD_UP + (GUST_UP * g['s'] if g else 0))) / FPS, 0, 100)
            if fz >= 100: T_FAIL = t
    fire = min(1.0, fire + 0.28 / FPS)
    GX.append(gx); FRZ.append(fz); FIRE.append(fire); GUSTING.append(g)
S.OUTCOME = 'fail' if T_FAIL else 'win'
S.T_RES = T_FAIL if T_FAIL else S.T_END
S.GRAB = (GX[int(S.T_RES * FPS)], GY - 10)
END = S.END = Ending(S)
S.events = []
for G in GUSTS:
    if G['t'] < S.T_RES: S.events.append([G['t'], 'whoosh']); S.events.append([G['t'] + 0.2, 'whoosh'])
for Cl in CLUMPS:
    if Cl['t'] < S.T_RES: S.events.append([Cl['t'] + 0.45, 'thump', 0.6])
if T_FAIL: S.events.append([T_FAIL, 'freeze'])
S.AMB = {'drone': 50, 'wind': 0.06}

def draw_bar(c, t, f):
    p = FRZ[f]; col = rgb('#8fe3ff') if p < 50 else (rgb('#45a8ff') if p < 80 else rgb('#2f5bff'))
    rising = f > 0 and FRZ[f] > FRZ[f - 1]
    bx = bar(c, p / 100, f'FREEZE {int(p)}%', col, 0.12 if rising and GUSTING[f] else 0, bw=620, x_off=40)
    c.save(); c.translate(bx - 58, 231); c.set_source_rgb(*rgb('#bfefff')); c.set_line_width(6); c.set_line_cap(cairo.LINE_CAP_ROUND)
    for i in range(3):
        c.save(); c.rotate(i * math.pi / 3); c.move_to(0, -28); c.line_to(0, 28); c.stroke()
        for s in (-1, 1): c.move_to(0, s * 16); c.line_to(9, s * 24); c.stroke(); c.move_to(0, s * 16); c.line_to(-9, s * 24); c.stroke()
        c.restore()
    c.restore()
S.draw_bar = draw_bar

flakes = [(rng.uniform(0, W), rng.uniform(0, H), rng.uniform(2, 6), rng.uniform(0.6, 1.4)) for _ in range(140)]
pines = [(x, rng.uniform(0.8, 1.25)) for x in range(-30, W + 60, 110)]
def wind_at(f):
    g = GUSTING[min(f, len(GUSTING) - 1)]; return (g['dir'] * g['s']) if g else 0.0

def pine(c, x, base, s, col, snow=True):
    c.set_source_rgb(*rgb('#3a2a20')); c.rectangle(x - 10 * s, base - 40 * s, 20 * s, 40 * s); c.fill()
    for k in range(3):
        w = (110 - k * 28) * s; y = base - 30 * s - k * 75 * s
        c.set_source_rgb(*rgb(col)); c.move_to(x - w, y); c.line_to(x, y - 120 * s); c.line_to(x + w, y); c.close_path(); c.fill()
        if snow:
            c.set_source_rgb(*rgb('#eef6ff')); c.move_to(x - w * 0.45, y - 66 * s); c.line_to(x, y - 120 * s); c.line_to(x + w * 0.45, y - 66 * s)
            c.curve_to(x + w * 0.2, y - 56 * s, x - w * 0.2, y - 60 * s, x - w * 0.45, y - 66 * s); c.fill()

def draw_bg(c, t, f):
    gr = cairo.LinearGradient(0, HEAD, 0, GROUND)
    gr.add_color_stop_rgb(0, *rgb('#0f1d3a')); gr.add_color_stop_rgb(1, *rgb('#3b5b86'))
    c.set_source(gr); c.rectangle(0, HEAD, W, GROUND - HEAD); c.fill()
    c.set_source_rgb(*rgb('#2a3f63'))
    c.move_to(0, 1250); c.line_to(220, 760); c.line_to(420, 1100); c.line_to(640, 650); c.line_to(900, 1080); c.line_to(1080, 820); c.line_to(1080, 1400); c.line_to(0, 1400); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#dfeaf7'))
    for (px, py) in ((220, 760), (640, 650), (1080, 820)):
        c.move_to(px - 70, py + 120); c.line_to(px, py); c.line_to(px + 70, py + 120); c.line_to(px + 30, py + 100); c.line_to(px, py + 130); c.line_to(px - 30, py + 100); c.close_path(); c.fill()
    for x, s in pines: pine(c, x, 1440, s * 0.8, '#1d3b3a')
    # big pine on the right with the snow-loaded branch
    pine(c, 960, GROUND, 1.9, '#24503f')
    pine(c, 110, GROUND, 1.9, '#24503f')
    c.set_source_rgb(*rgb('#e9f3ff')); c.rectangle(0, GROUND - 10, W, H - GROUND + 10); c.fill()
    c.set_source_rgb(*rgb('#c9dcf0'))
    for x in range(-40, W, 160): c.save(); c.translate(x + 60, GROUND + 140); c.scale(1, 0.25); c.arc(0, 0, 90, 0, 2 * math.pi); c.restore(); c.fill()
    # warm glow
    fi = FIRE[min(f, len(FIRE) - 1)]
    gg = cairo.RadialGradient(FIRE_X, GROUND - 60, 10, FIRE_X, GROUND - 60, 360)
    gg.add_color_stop_rgba(0, 1, 0.6, 0.2, 0.42 * fi); gg.add_color_stop_rgba(1, 1, 0.5, 0.2, 0)
    c.set_source(gg); c.rectangle(0, HEAD, W, H - HEAD); c.fill()

def draw_fire(c, t, f):
    fi = FIRE[min(f, len(FIRE) - 1)]; w = wind_at(f)
    c.set_source_rgb(*rgb('#5a3a22'))
    for a in (-0.35, 0.35):
        c.save(); c.translate(FIRE_X, GROUND - 14); c.rotate(a); rrect(c, -80, -14, 160, 28, 12); c.fill(); c.restore()
    c.set_source_rgb(*rgb('#7d8590'))
    for dx in (-95, -60, 60, 95): c.arc(FIRE_X + dx, GROUND - 6, 20, 0, 2 * math.pi); c.fill()
    for k, (col, sc) in enumerate((('#ff5a1f', 1.0), ('#ffb02e', 0.7), ('#fff1a0', 0.4))):
        h = (150 + 25 * math.sin(t * 13 + k)) * fi * sc; wd = 62 * sc * (0.5 + 0.5 * fi)
        lean = w * 90 * fi
        c.set_source_rgb(*rgb(col)); c.move_to(FIRE_X - wd, GROUND - 22)
        c.curve_to(FIRE_X - wd, GROUND - 22 - h * 0.6, FIRE_X + lean - 10, GROUND - 22 - h * 0.8, FIRE_X + lean, GROUND - 22 - h)
        c.curve_to(FIRE_X + lean + 10, GROUND - 22 - h * 0.8, FIRE_X + wd, GROUND - 22 - h * 0.6, FIRE_X + wd, GROUND - 22); c.close_path(); c.fill()
    for i in range(6):
        k = (t * 0.9 + i / 6) % 1
        c.set_source_rgba(1, 0.7, 0.2, (1 - k) * fi); c.arc(FIRE_X + 40 * math.sin(i * 2.1 + t * 2) + w * 200 * k, GROUND - 60 - k * 260 * fi, 4, 0, 2 * math.pi); c.fill()

CLY = 1290
def draw_clumps(c, t):
    for Cl in CLUMPS:
        if Cl['t'] <= t < Cl['t'] + 1.4 and Cl['t'] < S.T_RES:
            k = (t - Cl['t']) / 0.45; y = lerp(CLY, GY - 40, min(1, k * k))
            if k < 1:
                c.set_source_rgb(*rgb('#f4f9ff')); c.arc(Cl['x'], y, 46, 0, 2 * math.pi); c.fill(); c.arc(Cl['x'] + 30, y - 10, 30, 0, 2 * math.pi); c.fill()
            else:
                a = max(0, 1 - (t - Cl['t'] - 0.45) / 0.9)
                c.set_source_rgba(0.96, 0.98, 1, a)
                for j in range(7): c.arc(Cl['x'] + (j - 3) * 26, GY + R * 0.4 + 10 * math.sin(j), 18, 0, 2 * math.pi); c.fill()
        elif t < Cl['t'] and Cl['t'] < S.T_RES:
            wob = 4 * math.sin(t * 20) if Cl['t'] - t < 0.6 else 0
            c.set_source_rgb(*rgb('#f4f9ff')); c.arc(Cl['x'] + wob, CLY, 46, 0, 2 * math.pi); c.fill(); c.arc(Cl['x'] + 30 + wob, CLY - 10, 30, 0, 2 * math.pi); c.fill()

def draw_snow(c, t, f):
    w = wind_at(f)
    for x, y, r, sp in flakes:
        yy = (y + t * 180 * sp) % (H - HEAD) + HEAD
        xx = (x + t * 40 * sp + w * 900 * sp * 0.4 * (t % 1)) % W
        c.set_source_rgba(1, 1, 1, 0.75); c.arc(xx, yy, r, 0, 2 * math.pi); c.fill()
    if w:
        c.set_source_rgba(1, 1, 1, 0.35 * abs(w)); c.set_line_width(5); c.set_line_cap(cairo.LINE_CAP_ROUND)
        for i in range(14):
            y = HEAD + 80 + i * 90 + 30 * math.sin(i * 3.3); x = ((i * 173 + t * 1800 * (1 if w > 0 else -1)) % (W + 400)) - 200
            c.move_to(x, y); c.curve_to(x + 80 * math.copysign(1, w), y - 10, x + 160 * math.copysign(1, w), y + 10, x + 240 * math.copysign(1, w), y); c.stroke()

def draw_gloop(c, t, f, x, y, sq, mood):
    p = FRZ[min(f, len(FRZ) - 1)] / 100
    a = lambda h1, h2: '#%02x%02x%02x' % tuple(int(lerp(int(h1[i:i + 2], 16), int(h2[i:i + 2], 16), p * 0.7)) for i in (1, 3, 5))
    skin = (a('#ffd36b', '#d6f2ff'), a('#ff8a1f', '#6fb6ff'), a('#c45a00', '#2f6fbf'))
    frozen = T_FAIL is not None and t >= T_FAIL
    draw_blob(c, t if not frozen else T_FAIL, x, y, mood, sq if not frozen else 0, R=R, skin=skin, sweat=False)
    if p > 0.35 and not frozen:  # frost specks
        c.set_source_rgba(1, 1, 1, min(0.9, p))
        for j in range(int(p * 10)): c.arc(x + math.cos(j * 2.4) * R * 0.75, y + math.sin(j * 2.4) * R * 0.7, 5, 0, 2 * math.pi); c.fill()
    if frozen:
        k = ease((t - T_FAIL) / 0.3)
        c.set_source_rgba(0.75, 0.92, 1, 0.45 * k); rrect(c, x - 125, y - 125 + 250 * (1 - k), 250, 250 * k, 26); c.fill()
        c.set_source_rgba(1, 1, 1, 0.8 * k); c.set_line_width(6); rrect(c, x - 125, y - 125 + 250 * (1 - k), 250, 250 * k, 26); c.stroke()
        c.set_source_rgba(1, 1, 1, 0.6 * k); c.set_line_width(8); c.move_to(x - 90, y - 90); c.line_to(x - 40, y - 100); c.stroke(); c.move_to(x + 60, y + 90); c.line_to(x + 95, y + 50); c.stroke()

PS = Particles(4)
def render(f, c):
    t = f / FPS; fi = min(f, len(GX) - 1)
    c.save()
    draw_bg(c, t, f); draw_fire(c, t, f)
    if END.carried(t): gx, gy = END.carry_xy(t); gy -= 10; sq = 0
    else:
        gx = GX[fi]; moving = fi > 0 and abs(GX[fi] - GX[fi - 1]) > 1.5
        g = GUSTING[fi]
        gy = GY - (abs(math.sin(t * 3.4 * math.pi)) * 50 if moving and not g else 0) - (30 if g else 0)
        sq = 0.04 * math.sin(t * 6) + (-0.08 if g else 0.06)
    frz = FRZ[fi]
    mood = 'happy' if (t >= S.T_END and S.OUTCOME == 'win') else ('scared' if GUSTING[fi] or frz > 70 else 'worried')
    draw_gloop(c, t, f, gx, gy, sq, mood)
    if f > 0 and FRZ[fi] > FRZ[fi - 1] and int(t * 3) != int((t - 1 / FPS) * 3) and t < S.T_RES and not END.carried(t):
        PS.spawn(gx, gy - 40, 3, (0.85, 0.95, 1), 200, 0.6, grav=200, r=6)
    draw_clumps(c, t)
    for Cl in CLUMPS:
        if Cl.get('hit') and Cl['t'] + 0.45 <= t < Cl['t'] + 1.15:
            k = (t - Cl['t'] - 0.45) / 0.7; text_at(c, '+14%', gx + 120, gy - 140 - 50 * k, 70, rgb('#8fe3ff'))
    draw_snow(c, t, f)
    PS.draw(c)
    END.draw_claw(c, t)
    c.restore()
    END.header(c, t, fi)

if __name__ == '__main__':
    if sys.argv[1] == 'sim':
        print(SEED, S.OUTCOME, round(S.T_RES, 2), 'peak', round(max(FRZ[:int(S.T_RES * FPS)])), 'final', round(FRZ[int(S.T_RES * FPS) - 1]), 'gusts', len(GUSTS), 'clumphit', [c.get('hit', 0) for c in CLUMPS], 'dur', S.DUR); sys.exit()
    run(S, render)
