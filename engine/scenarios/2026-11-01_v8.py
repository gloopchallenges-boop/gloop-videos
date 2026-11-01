"""2026-11-01 v8 — FALLING OBJECT ABOVE – CHAIN N LINKS: a PIANO hangs over Gloop, who is stuck in
bubblegum. Links pop at seeded-random times (piano jerks lower each time); Gloop's wiggles add
seeded-random FREE %. If he's still stuck when the last link goes = fail."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the falling piano'
SEED = int(os.environ.get('SEED', 3))
rng = random.Random(SEED)

class S: pass
S.HOOK2 = 'THE FALLING PIANO?'; S.HOOK2_SIZE = 88; S.FAIL_WORD = 'CRASH!'; S.FAIL_SIZE = 160
S.T_START = 2.6; S.TL = 15.0; S.T_END = S.T_START + S.TL
FLOOR = 1650; R = 76; GX0 = 470; GY = FLOOR - R * 0.85; SAFE_X = 860
NLINK = 7
POPS = []; t = S.T_START + rng.uniform(0.8, 2.0)
while len(POPS) < NLINK and t < 40:
    POPS.append(t); t += rng.uniform(1.0, 2.9)
WIG = []; t = S.T_START + rng.uniform(0.2, 0.6); fr = 0.0; T_FREE = None
while t < S.T_END and T_FREE is None:
    a = rng.uniform(3, 11)
    if rng.random() < 0.15: a = 0.5  # slips back, barely moves
    fr = min(100, fr + a); WIG.append((t, a, fr))
    if fr >= 100: T_FREE = t
    t += rng.uniform(0.45, 0.85)
T_LAST = POPS[-1] if len(POPS) == NLINK else 99
T_FAIL = T_LAST if (T_LAST < S.T_END and (T_FREE is None or T_FREE > T_LAST)) else None
if T_FAIL: WIG = [w for w in WIG if w[0] < T_FAIL]; T_FREE = None
S.OUTCOME = 'fail' if T_FAIL else 'win'
S.T_RES = T_FAIL if T_FAIL else S.T_END
T_DROP = T_LAST if T_LAST < S.T_END else None
T_HIT = T_DROP + 0.3 if T_DROP else None
def links_at(t): return NLINK - len([p for p in POPS if p <= t])
def free_at(t):
    v = 0
    for (tw, a, fr) in WIG:
        if tw <= t: v = fr
    return v
def gloop_xy(t):
    if T_FREE is not None and t >= T_FREE:
        k = clamp((t - T_FREE) / 0.9, 0, 1); x = lerp(GX0, SAFE_X, ease(k))
        return x, GY - (abs(math.sin(k * 2 * math.pi)) * 110 if k < 1 else 0)
    return GX0, GY
PIANO_TOP0 = 760; DROP_STEP = 52
def piano_y(t):
    y = PIANO_TOP0 + DROP_STEP * (NLINK - links_at(min(t, T_DROP - 0.001 if T_DROP else t)))
    for p in POPS:
        if p <= t < p + 0.25 and (not T_DROP or p < T_DROP): y += 10 * math.sin((t - p) * 40) * (1 - (t - p) / 0.25)
    if T_DROP and t >= T_DROP:
        k = clamp((t - T_DROP) / 0.3, 0, 1); y = lerp(y, FLOOR - (330 if T_FAIL else 270), k * k)
    return y
if T_FAIL: S.GRAB = (GX0, FLOOR - 400)
else: S.GRAB = gloop_xy(S.T_END)
END = S.END = Ending(S)
S.events = []
for p in POPS:
    if p <= S.T_RES + 0.01: S.events.append([p, 'clink']); S.events.append([p + 0.02, 'thump', 0.35])
for (tw, a, fr) in WIG: S.events.append([tw, 'hop'])
if T_FREE: S.events += [[T_FREE, 'pop'], [T_FREE + 0.1, 'blip']]
if T_HIT and T_HIT < S.T_RES + 0.5: S.events += [[T_HIT, 'crash'], [T_HIT + 0.02, 'clang']]
S.AMB = {'drone': 58, 'wind': 0.015}

def link_icon(c, x, y, ok, pop):
    c.save(); c.translate(x, y); c.rotate(0.5); c.scale(1 + pop, 1 + pop)
    c.set_line_width(12); c.set_source_rgb(0, 0, 0); rrect(c, -30, -16, 60, 32, 16); c.stroke()
    c.set_line_width(7); c.set_source_rgb(*(rgb('#d7dde8') if ok else rgb('#4a4458'))); rrect(c, -30, -16, 60, 32, 16); c.stroke()
    c.restore()
def draw_bar(c, t, f):
    n = links_at(t); last = [p for p in POPS if p <= t]
    pop = max(0, 1 - (t - last[-1]) / 0.3) if last else 0
    for i in range(NLINK):
        link_icon(c, 175 + i * 62, 232, i < n, 0.4 * pop if i == n else 0)
    col = rgb('#7dff8a') if n > 4 else (rgb('#ffd84a') if n > 2 else rgb('#ff4d4d'))
    text_at(c, f'CHAIN: {n}', 800, 232, 54, col, 1 + 0.2 * pop, lw=9)
S.draw_bar = draw_bar

wins = [(x, y) for x in (110, 330, 750, 970) for y in (440, 640, 840, 1040, 1240)]
def draw_bg(c, t):
    gr = cairo.LinearGradient(0, HEAD, 0, FLOOR)
    gr.add_color_stop_rgb(0, *rgb('#7ec8f0')); gr.add_color_stop_rgb(1, *rgb('#ffd9a0'))
    c.set_source(gr); c.rectangle(0, HEAD, W, FLOOR - HEAD); c.fill()
    c.set_source_rgb(*rgb('#c96f4a')); c.rectangle(0, HEAD, W, 1420 - HEAD); c.fill()
    c.set_source_rgb(*rgb('#b25f3e')); c.set_line_width(3)
    for y in range(HEAD + 30, 1420, 40):
        c.move_to(0, y); c.line_to(W, y); c.stroke()
        for x in range(((y // 40) % 2) * 60, W, 120): c.move_to(x, y); c.line_to(x, y + 40); c.stroke()
    for x, y in wins:
        c.set_source_rgb(*rgb('#f4e9d8')); rrect(c, x - 70, y - 70, 140, 140, 8); c.fill()
        c.set_source_rgb(*rgb('#5a8fb8')); rrect(c, x - 58, y - 58, 116, 116, 4); c.fill()
        c.set_source_rgba(1, 1, 1, 0.3); c.move_to(x - 58, y + 20); c.line_to(x - 10, y - 58); c.line_to(x + 10, y - 58); c.line_to(x - 38, y + 58); c.line_to(x - 58, y + 58); c.close_path(); c.fill()
        c.set_source_rgb(*rgb('#f4e9d8')); c.rectangle(x - 4, y - 58, 8, 116); c.fill()
    # big open window + beam with pulley
    c.set_source_rgb(*rgb('#2a2030')); rrect(c, 430, 380, 220, 230, 10); c.fill()
    c.set_source_rgb(*rgb('#5a4a3a')); c.rectangle(380, 360, 330, 30); c.fill()
    c.set_source_rgb(*rgb('#4a4f5c')); c.rectangle(470, 400, 260, 26); c.fill()
    c.set_source_rgb(*rgb('#8a92a3')); c.arc(GX0, 440, 30, 0, 2 * math.pi); c.fill(); c.set_source_rgb(*rgb('#4a4f5c')); c.arc(GX0, 440, 10, 0, 2 * math.pi); c.fill()
    # awning
    for i in range(9):
        c.set_source_rgb(*(rgb('#e8574f') if i % 2 else rgb('#f4f0e8'))); c.move_to(i * 120, 1300); c.line_to(i * 120 + 120, 1300); c.line_to(i * 120 + 120, 1360); c.line_to(i * 120, 1360); c.close_path(); c.fill()
    # sidewalk
    c.set_source_rgb(*rgb('#9aa0ab')); c.rectangle(0, 1420, W, FLOOR - 1420); c.fill()
    c.set_source_rgb(*rgb('#b8bdc6')); c.rectangle(0, FLOOR, W, H - FLOOR); c.fill()
    c.set_source_rgb(*rgb('#8a909b')); c.set_line_width(4)
    for x in range(0, W, 180): c.move_to(x, FLOOR); c.line_to(x - 60, H); c.stroke()
    c.set_source_rgb(*rgb('#6a707b')); c.rectangle(0, FLOOR, W, 8); c.fill()

def draw_chain(c, t):
    py = piano_y(t); n = links_at(t)
    if T_FAIL and t >= T_FAIL: top_end = 440 + 30 + (t - T_FAIL) * 0  # chain end dangles
    c.set_line_width(8)
    y = 470; end = py - 40 if not (T_DROP and t >= T_DROP) else 470 + 30 * n + 120
    i = 0
    while y < end:
        c.set_source_rgb(*rgb('#6d7480'));
        if i % 2 == 0: rrect(c, GX0 - 11, y, 22, 42, 11)
        else: c.move_to(GX0, y); c.line_to(GX0, y + 42)
        c.stroke(); y += 34; i += 1
    # weakened 'links' cluster on the hook clamp (the ones that pop)
    for j in range(NLINK):
        ok = j < n
        if not ok:
            p = POPS[NLINK - 1 - j] if NLINK - 1 - j < len(POPS) else None
            if p is not None and t - p < 1.0:
                k = t - p; c.save(); c.translate(GX0 + 60 + 260 * k, 520 + 40 * j + 900 * k * k); c.rotate(k * 12)
                c.set_source_rgb(*rgb('#d7dde8')); c.set_line_width(7); rrect(c, -18, -10, 36, 20, 10); c.stroke(); c.restore()

def draw_piano(c, t):
    py = piano_y(t); x0 = GX0 - 200
    sw = 0.0 if (T_DROP and t >= T_DROP) else 0.02 * math.sin(t * 2.3)
    c.save(); c.translate(GX0, py); c.rotate(sw); c.translate(-GX0, -py)
    c.set_source_rgb(*rgb('#6d7480')); c.set_line_width(6)
    c.move_to(GX0, py - 40); c.line_to(x0 + 30, py + 10); c.stroke(); c.move_to(GX0, py - 40); c.line_to(x0 + 370, py + 10); c.stroke()
    c.set_source_rgb(*rgb('#1c1a22')); rrect(c, x0, py, 400, 270, 18); c.fill()
    c.set_source_rgb(*rgb('#2c2834')); rrect(c, x0 + 20, py + 20, 360, 100, 10); c.fill()
    c.set_source_rgb(*rgb('#f4f0e8')); c.rectangle(x0 + 20, py + 140, 360, 50); c.fill()
    c.set_source_rgb(*rgb('#1c1a22'))
    for k in range(13): c.rectangle(x0 + 30 + k * 28, py + 140, 14, 30); c.fill()
    c.set_source_rgb(*rgb('#c9a24a')); c.rectangle(x0 + 20, py + 128, 360, 8); c.fill()
    c.set_source_rgb(*rgb('#1c1a22')); c.rectangle(x0 + 20, py + 190, 22, 80); c.fill(); c.rectangle(x0 + 358, py + 190, 22, 80); c.fill()
    c.restore()
    # shadow on ground grows as it lowers
    k = clamp((py - PIANO_TOP0) / (FLOOR - 330 - PIANO_TOP0), 0, 1)
    c.set_source_rgba(0, 0, 0, 0.12 + 0.25 * k); c.save(); c.translate(GX0, FLOOR + 6); c.scale(1, 0.12); c.arc(0, 0, 160 + 60 * k, 0, 2 * math.pi); c.restore(); c.fill()

def draw_gum(c, t, gx, gy):
    stuck = T_FREE is None or t < T_FREE
    c.set_source_rgb(*rgb('#ff8ec7')); c.save(); c.translate(GX0, FLOOR + 4); c.scale(1, 0.25); c.arc(0, 0, 120, 0, 2 * math.pi); c.restore(); c.fill()
    c.set_source_rgb(*rgb('#ffb6dc')); c.save(); c.translate(GX0 - 30, FLOOR); c.scale(1, 0.2); c.arc(0, 0, 50, 0, 2 * math.pi); c.restore(); c.fill()
    if stuck:
        fr = free_at(t) / 100; wig = 0
        for (tw, a, f_) in WIG:
            if tw <= t < tw + 0.35: wig = math.sin((t - tw) / 0.35 * math.pi)
        c.set_source_rgb(*rgb('#ff8ec7')); c.set_line_width(14 * (1 - fr * 0.7) + 4)
        for dx in (-40, 0, 40):
            c.move_to(GX0 + dx * 1.6, FLOOR); c.curve_to(GX0 + dx * 1.3, FLOOR - 20, gx + dx, gy + R * 0.6, gx + dx * 0.8, gy + R * 0.7); c.stroke()
    elif t < T_FREE + 0.5:
        k = (t - T_FREE) / 0.5; c.set_source_rgba(1, 0.56, 0.78, 1 - k); c.set_line_width(6)
        for dx in (-40, 0, 40): c.move_to(GX0 + dx * 1.6, FLOOR); c.line_to(GX0 + dx * 1.2, FLOOR - 60 * (1 - k)); c.stroke()

PS = Particles(8)
def render(f, c):
    t = f / FPS; shake = (0, 0)
    if T_HIT and T_HIT <= t < T_HIT + 0.4: shake = (rng.uniform(-18, 18), rng.uniform(-18, 18))
    if T_HIT and f == int(T_HIT * FPS):
        PS.spawn(GX0, FLOOR - 20, 30, (0.95, 0.94, 0.9), 700, 0.9, r=11); PS.spawn(GX0, FLOOR - 20, 20, (0.15, 0.13, 0.17), 600, 0.9, r=11)
    c.save(); c.translate(*shake)
    draw_bg(c, t)
    crashed = T_FAIL and T_HIT and t >= T_HIT
    if END.carried(t): gx, gy = END.carry_xy(t); gy -= 5; wig = 0
    elif crashed:
        k = t - T_HIT; gx = GX0; gy = lerp(FLOOR, FLOOR - 400, ease(clamp((k - 0.4) / 0.4, 0, 1)))
    else:
        gx, gy = gloop_xy(t)
    wig = 0
    for (tw, a, f_) in WIG:
        if tw <= t < tw + 0.35 and not crashed: wig = math.sin((t - tw) / 0.35 * math.pi)
    draw_gum(c, t, gx, gy)
    n = links_at(t)
    near_drop = T_DROP and T_DROP - 0.2 <= t < T_DROP + 1.0
    mood = 'scared' if near_drop and not T_FAIL else 'happy' if ((T_FREE and t >= T_FREE + 0.9) or (t >= S.T_END and S.OUTCOME == 'win')) else ('scared' if n <= 3 or crashed else 'worried')
    sq = (0.12 * wig * (1 if int(t * 5) % 2 else -1)) + 0.03 * math.sin(t * 6)
    if crashed and not END.carried(t):
        draw_piano(c, t)
        if t >= T_HIT + 0.4:
            draw_blob(c, t, gx, gy, mood, 0.0, R=R, dizzy=True)
            for i in range(3):  # piano keys stuck on him
                c.save(); c.translate(gx - 40 + i * 40, gy - R + 10); c.rotate(-0.4 + i * 0.4)
                c.set_source_rgb(*rgb('#f4f0e8')); rrect(c, -9, -36, 18, 50, 4); c.fill(); c.set_source_rgb(0, 0, 0); c.set_line_width(2); rrect(c, -9, -36, 18, 50, 4); c.stroke(); c.restore()
    else:
        draw_blob(c, t, gx + 12 * wig * math.sin(t * 40), gy, mood, sq, R=R)
        if not END.carried(t): draw_chain(c, t); draw_piano(c, t)
        else: draw_chain(c, t); draw_piano(c, t)
    if (T_FREE is None or t < T_FREE + 0.6) and not crashed and t >= S.T_START:
        fr = free_at(t); fx, fy = (GX0, GY)
        c.set_source_rgba(0, 0, 0, 0.45); rrect(c, fx + 95, fy - 40, 210, 70, 30); c.fill()
        text_at(c, f'FREE {int(fr)}%', fx + 200, fy - 5, 40, rgb('#ff8ec7') if fr < 100 else rgb('#7dff8a'), lw=7)
    for (tw, a, fr) in WIG:
        if tw <= t < tw + 0.6 and not crashed:
            k = (t - tw) / 0.6; text_at(c, f'+{int(round(a))}%', GX0 - 170, GY - 100 - 50 * k, 52, rgb('#ff8ec7'), lw=7)
    if T_FREE and T_FREE <= t < T_FREE + 0.7: text_at(c, 'FREE!', GX0 + 120, GY - 230, 100, rgb('#7dff8a'), 1 + 0.3 * max(0, 1 - (t - T_FREE) * 5))
    PS.draw(c)
    END.draw_claw(c, t)
    c.restore()
    END.header(c, t, f)

if __name__ == '__main__':
    if sys.argv[1] == 'sim':
        print(SEED, S.OUTCOME, round(S.T_RES, 2), 'free', T_FREE and round(T_FREE - S.T_START, 1), 'links_left', links_at(S.T_RES - 0.01) if T_FAIL else links_at(S.T_END), 'pops', [round(p - S.T_START, 1) for p in POPS], 'dur', S.DUR); sys.exit()
    run(S, render)
