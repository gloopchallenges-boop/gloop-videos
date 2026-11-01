"""2026-11-01 v7 — NOISE / WAKE-UP – WAKE %: sneak past the SLEEPING DRAGON. Gloop tiptoe-hops
across stone, creaky boards and loose coins; each landing adds seeded-random noise by surface,
the dragon slowly settles back. WAKE % is simulated; 100% = WOKEN UP!"""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the sleeping dragon'
SEED = int(os.environ.get('SEED', 3))
rng = random.Random(SEED)

class S: pass
S.HOOK2 = 'THE SLEEPING DRAGON?'; S.HOOK2_SIZE = 80; S.FAIL_WORD = 'WOKEN UP!'; S.FAIL_SIZE = 140
S.T_START = 2.6; S.TL = 15.0; S.T_END = S.T_START + S.TL
FLOOR = 1640; R = 70; GY = FLOOR - R * 0.9
SURF = [(0, 250, 'stone'), (250, 470, 'boards'), (470, 640, 'coins'), (640, 820, 'boards'), (820, W, 'stone')]
NOISE = {'stone': (3, 7), 'boards': (10, 18), 'coins': (16, 28)}
DECAY = 4.5
def surf_at(x):
    for a, b, k in SURF:
        if a <= x < b: return k
    return 'stone'

# --- seeded hops: Gloop hops right with random pauses; sometimes stops to hold breath
HOPS = []; t = S.T_START + rng.uniform(0.3, 0.8); x = 130
while t < S.T_END - 0.4 and x < 960:
    nx = min(960, x + rng.uniform(55, 105)); HOPS.append((t, x, nx)); x = nx
    t += 0.4 + rng.uniform(0.25, 0.9) + (rng.uniform(0.8, 1.8) if rng.random() < 0.2 else 0)
LAND = []
for (t0, x0, x1) in HOPS:
    k = surf_at(x1); lo, hi = NOISE[k]; amt = rng.uniform(lo, hi)
    if rng.random() < 0.12: amt *= 2.0; big = True
    else: big = False
    LAND.append((t0 + 0.4, x1, k, amt, big))

N0 = int(40 * FPS); WAKE = []; wk = 0.0; T_FAIL = None; li = 0
for f in range(N0):
    t = f / FPS
    if T_FAIL is None and S.T_START <= t < S.T_END:
        wk = max(0, wk - DECAY / FPS)
        while li < len(LAND) and LAND[li][0] <= t:
            wk += LAND[li][3]; li += 1
            if wk >= 100: wk = 100; T_FAIL = t; break
    WAKE.append(wk)
S.OUTCOME = 'fail' if T_FAIL else 'win'
S.T_RES = T_FAIL if T_FAIL else S.T_END
def gloop_x(t):
    x = 130; hop = None
    for (t0, x0, x1) in HOPS:
        if t >= t0 + 0.4: x = x1
        elif t >= t0: x = lerp(x0, x1, (t - t0) / 0.4); hop = (t - t0) / 0.4; break
        else: break
    return x, hop
S.GRAB = (gloop_x(S.T_RES)[0], GY)
END = S.END = Ending(S)
S.events = []
for (tl, x1, k, amt, big) in LAND:
    if tl <= S.T_RES + 0.01:
        S.events.append([tl, 'creak' if k == 'boards' else ('clink' if k == 'coins' else 'noise_hit'), None if k != 'stone' else 0.5])
        if big: S.events.append([tl, 'clang'])
t = 2.0
while t < S.T_RES: S.events.append([t, 'snore']); t += 2.2
if T_FAIL: S.events += [[T_FAIL + 0.1, 'roar'], [T_FAIL + 0.5, 'whoosh']]
S.AMB = {'drone': 46}

def draw_bar(c, t, f):
    p = WAKE[f]; recent = any(tl <= t < tl + 0.3 for tl, *_ in LAND)
    bx = bar(c, p / 100, f'WAKE {int(p)}%', bad_col(p / 100), 0.15 if recent else 0, bw=620, x_off=40)
    text_at(c, 'Zz' if p < 60 else '!?', bx - 55, 231, 50, rgb('#9ad0ff') if p < 60 else rgb('#ff4d4d'), lw=8)
S.draw_bar = draw_bar

crys = [(rng.uniform(60, W - 60), rng.uniform(HEAD + 40, 900), rng.uniform(16, 34), rng.choice(('#7fe3ff', '#c88bff', '#7dffb0'))) for _ in range(12)]
coins_bg = [(rng.uniform(560, 1080), rng.uniform(1150, 1330)) for _ in range(70)]
coins_fl = [(rng.uniform(475, 635), FLOOR - rng.uniform(0, 22)) for _ in range(40)]

def draw_bg(c, t):
    gr = cairo.LinearGradient(0, HEAD, 0, FLOOR)
    gr.add_color_stop_rgb(0, *rgb('#14102a')); gr.add_color_stop_rgb(1, *rgb('#2c2346'))
    c.set_source(gr); c.rectangle(0, HEAD, W, H - HEAD); c.fill()
    c.set_source_rgb(*rgb('#1c1636'))
    c.move_to(0, HEAD);
    for i in range(12): c.line_to(i * 100 + 50, HEAD + 60 + (i % 3) * 50); c.line_to(i * 100 + 100, HEAD)
    c.close_path(); c.fill()
    for x, y, r, col in crys:
        c.set_source_rgba(*hexc(col, 0.15 + 0.08 * math.sin(t * 2 + x))); c.arc(x, y, r * 2.2, 0, 2 * math.pi); c.fill()
        c.set_source_rgb(*rgb(col)); c.move_to(x, y - r); c.line_to(x + r * 0.5, y); c.line_to(x, y + r); c.line_to(x - r * 0.5, y); c.close_path(); c.fill()
    # treasure hill behind dragon
    c.set_source_rgb(*rgb('#c9932a')); c.move_to(520, 1360); c.curve_to(650, 1080, 950, 1080, 1100, 1300); c.line_to(1100, 1400); c.close_path(); c.fill()
    for x, y in coins_bg:
        c.set_source_rgb(*rgb('#ffd34a')); c.save(); c.translate(x, y); c.scale(1, 0.5); c.arc(0, 0, 13, 0, 2 * math.pi); c.restore(); c.fill()
    # exit door right
    c.set_source_rgb(*rgb('#0c0a18')); c.move_to(940, FLOOR); c.line_to(940, 1380); c.curve_to(940, 1290, 1080, 1290, 1080, 1380); c.line_to(1080, FLOOR); c.close_path(); c.fill()
    c.set_source_rgba(0.6, 0.9, 1, 0.15); c.move_to(950, FLOOR); c.line_to(950, 1390); c.curve_to(950, 1305, 1070, 1305, 1070, 1390); c.line_to(1070, FLOOR); c.close_path(); c.fill()
    # floor
    for a, b, k in SURF:
        if k == 'stone':
            c.set_source_rgb(*rgb('#4a4366')); c.rectangle(a, FLOOR, b - a, H - FLOOR); c.fill()
            c.set_source_rgb(*rgb('#3a3454')); c.set_line_width(4)
            for xx in range(int(a), int(b), 90): c.rectangle(xx, FLOOR, 90, 60); c.stroke()
        elif k == 'boards':
            c.set_source_rgb(*rgb('#7a4f2c')); c.rectangle(a, FLOOR, b - a, H - FLOOR); c.fill()
            c.set_source_rgb(*rgb('#5a3820')); c.set_line_width(4)
            for xx in range(int(a), int(b), 44): c.move_to(xx, FLOOR); c.line_to(xx, H); c.stroke()
            c.set_source_rgb(*rgb('#2a1a10'))
            for xx in range(int(a) + 20, int(b), 44): c.arc(xx, FLOOR + 14, 3, 0, 2 * math.pi); c.fill()
        else:
            c.set_source_rgb(*rgb('#4a4366')); c.rectangle(a, FLOOR, b - a, H - FLOOR); c.fill()
    c.set_source_rgb(*rgb('#5a5278')); c.rectangle(0, FLOOR, W, 8); c.fill()
    for x, y in coins_fl:
        c.set_source_rgb(*rgb('#ffd34a')); c.save(); c.translate(x, y); c.scale(1, 0.5); c.arc(0, 0, 14, 0, 2 * math.pi); c.restore(); c.fill()
        c.set_source_rgb(*rgb('#c9932a')); c.save(); c.translate(x, y); c.scale(1, 0.5); c.arc(0, 0, 14, 0, 2 * math.pi); c.restore(); c.set_line_width(3); c.stroke()

def draw_dragon(c, t, f):
    p = WAKE[min(f, len(WAKE) - 1)] / 100; woke = T_FAIL is not None and t >= T_FAIL
    br = math.sin(t * 2 * math.pi / 2.2)
    sc = 1 + 0.025 * br
    body, dark, belly = rgb('#3f8f5a'), rgb('#2c6a41'), rgb('#bfe08a')
    # tail
    c.set_source_rgb(*body); c.set_line_width(46); c.set_line_cap(cairo.LINE_CAP_ROUND)
    c.move_to(980, 1440); c.curve_to(1080, 1380, 1060, 1250, 990, 1230); c.stroke()
    c.set_source_rgb(*dark); c.move_to(975, 1205); c.line_to(1010, 1190); c.line_to(1000, 1240); c.close_path(); c.fill()
    # body
    c.save(); c.translate(800, 1420); c.scale(sc, sc)
    c.set_source_rgb(*body); c.save(); c.scale(1.45, 1); c.arc(0, 0, 150, 0, 2 * math.pi); c.restore(); c.fill()
    c.set_source_rgb(*belly); c.save(); c.translate(0, 70); c.scale(1.3, 0.5); c.arc(0, 0, 130, 0, 2 * math.pi); c.restore(); c.fill()
    c.set_source_rgb(*dark)
    for i in range(6):
        a = math.pi + 0.35 + i * 0.42; x, y = math.cos(a) * 210, math.sin(a) * 145
        c.move_to(x - 18, y + 8); c.line_to(x + math.cos(a) * 40, y + math.sin(a) * 40); c.line_to(x + 18, y + 8); c.close_path(); c.fill()
    # folded wing
    c.set_source_rgb(*rgb('#357a4c')); c.move_to(-60, -40); c.curve_to(0, -170, 150, -160, 200, -60); c.curve_to(120, -90, 60, -40, -60, -40); c.fill()
    c.restore()
    # head resting on floor, facing left
    lift = ease((t - T_FAIL) / 0.3) * 120 if woke else 0
    hx, hy = 560, 1530 - lift
    c.set_source_rgb(*body); c.set_line_width(80); c.move_to(700, 1450); c.curve_to(650, 1480, 620, 1520 - lift, hx + 40, hy); c.stroke()
    c.save(); c.translate(hx, hy)
    c.set_source_rgb(*body); rrect(c, -150, -70, 220, 130, 60); c.fill()
    c.set_source_rgb(*dark); rrect(c, -165, -10, 120, 70, 30); c.fill()
    c.set_source_rgb(*rgb('#1a3a24')); c.arc(-140, 5, 9, 0, 2 * math.pi); c.fill(); c.arc(-110, 0, 9, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#e9e2c8'))
    for hxo in (10, 50):
        c.move_to(hxo, -60); c.line_to(hxo + 40, -120); c.line_to(hxo + 25, -55); c.close_path(); c.fill()
    # eye
    ex, ey = -40, -25
    open_ = 1.0 if woke else (0 if p < 0.55 else (p - 0.55) / 0.45 * 0.45)
    c.set_source_rgb(*rgb('#ffd34a')); c.save(); c.translate(ex, ey); c.scale(1, max(0.08, open_)); c.arc(0, 0, 24, 0, 2 * math.pi); c.restore(); c.fill()
    if open_ > 0.1:
        c.set_source_rgb(0.05, 0.05, 0.05); c.save(); c.translate(ex - 6, ey); c.scale(0.3, max(0.08, open_)); c.arc(0, 0, 22, 0, 2 * math.pi); c.restore(); c.fill()
    c.set_source_rgb(*dark); c.set_line_width(6); c.move_to(ex - 28, ey); c.line_to(ex + 28, ey); c.stroke() if open_ < 0.1 else c.new_path()
    if woke:
        k = ease((t - T_FAIL) / 0.2)
        c.set_source_rgb(*rgb('#8a2020')); c.move_to(-165, 50); c.line_to(-40, 50); c.line_to(-160, 50 + 90 * k); c.close_path(); c.fill()
    c.restore()
    # breath smoke / Z's
    if not woke:
        k = (t / 2.2) % 1
        c.set_source_rgba(0.8, 0.8, 0.85, 0.35 * (1 - k)); c.arc(hx - 170 - 60 * k, hy - 10 - 40 * k, 14 + 22 * k, 0, 2 * math.pi); c.fill()
        for j in range(3):
            kk = (t * 0.45 + j / 3) % 1
            if p > 0.6: continue
            text_at(c, 'Z', hx + 40 + 60 * kk + 15 * math.sin(kk * 9), hy - 140 - 220 * kk, 40 + 40 * kk, rgb('#bfe6ff'), lw=6)
    else:
        k = clamp((t - T_FAIL - 0.4) / 0.6, 0, 1)
        if 0 < k < 1:
            for j in range(9):
                c.set_source_rgba(0.35, 0.35, 0.4, 0.6 * (1 - k)); c.arc(hx - 180 - 380 * k * (0.5 + j / 9), hy + 20 + (j - 4) * 22 * k, 30 + 40 * k, 0, 2 * math.pi); c.fill()

PS = Particles(6)
def render(f, c):
    t = f / FPS; fi = min(f, len(WAKE) - 1); shake = (0, 0)
    if T_FAIL and T_FAIL <= t < T_FAIL + 0.6: shake = (rng.uniform(-14, 14), rng.uniform(-14, 14))
    c.save(); c.translate(*shake)
    draw_bg(c, t); draw_dragon(c, t, f)
    for (tl, x1, k, amt, big) in LAND:
        if tl <= t < tl + 0.8 and tl <= S.T_RES + 0.01:
            kk = (t - tl) / 0.8
            for j in range(3 if amt > 10 else 2):
                r = 40 + (kk + j * 0.25) * (160 + amt * 8)
                c.set_source_rgba(1, 0.85, 0.4, max(0, 0.6 * (1 - kk - j * 0.2))); c.set_line_width(6)
                c.arc(x1, FLOOR - 20, r, math.pi * 1.05, math.pi * 1.95); c.stroke()
            if big: text_at(c, 'CLATTER!', clamp(x1, 200, 880), GY - 420, 80, rgb('#ffd34a'), 1 + 0.25 * max(0, 1 - kk * 5))
            text_at(c, f'+{int(round(amt))}%', x1 + 20, GY - 150 - 60 * kk, 60 if not big else 80, rgb('#ffb347') if not big else rgb('#ff4d4d'), lw=8)
        if abs(t - tl) < 0.5 / FPS and k == 'coins' and tl <= S.T_RES: PS.spawn(x1, FLOOR - 10, 8, (1, 0.83, 0.3), 380, 0.6, r=8)
    sooty = T_FAIL and t >= T_FAIL + 0.6
    if END.carried(t): gx, gy = END.carry_xy(t); gy -= 10; sq = 0
    else:
        tt = min(t, S.T_RES) if T_FAIL else t
        gx, hop = gloop_x(tt)
        gy = GY - (60 * 4 * hop * (1 - hop) if hop is not None and not (T_FAIL and t >= T_FAIL) else 0)
        sq = (-0.08 if hop is not None else 0.1) + 0.03 * math.sin(t * 6)
        if T_FAIL and t >= T_FAIL + 0.4: gx -= 0  # stays put, gets sooted
    p = WAKE[fi]
    mood = 'happy' if (t >= S.T_END and S.OUTCOME == 'win') else ('scared' if p > 55 or (T_FAIL and t >= T_FAIL) else 'worried')
    skin = ('#7a6a60', '#4a3a34', '#201814') if sooty else ('#ffd36b', '#ff8a1f', '#c45a00')
    draw_blob(c, t, gx, gy, mood, sq, R=R, skin=skin, dizzy=bool(sooty))
    PS.draw(c)
    END.draw_claw(c, t)
    c.restore()
    END.header(c, t, fi)

if __name__ == '__main__':
    if sys.argv[1] == 'sim':
        rs = int(S.T_RES * FPS) - 1
        print(SEED, S.OUTCOME, round(S.T_RES, 2), 'peak', round(max(WAKE[:rs + 1])), 'final', round(WAKE[rs]), 'x', round(gloop_x(S.T_RES)[0]), 'hops', len(HOPS), 'dur', S.DUR); sys.exit()
    run(S, render)
