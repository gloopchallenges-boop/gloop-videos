"""2026-11-15 v2 — TEMPERATURE – MELT %: the GIANT PIZZA OVEN. A pizzeria kitchen at night; a giant brick pizza
oven on the right puffs seeded-random hot-air blasts out of its mouth along the floor (reach + strength + length
vary). Gloop is a passive rigid ball (Ball) bouncing between a tall steel fridge with its door ajar (left wall,
cold mist) and the oven (right wall). Inside the blast MELT rises (faster deep in it), outside it cools
slowly — faster next to the fridge. The blasts also push him left a little. 100% = melted into a puddle."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the giant pizza oven'
SEED = int(os.environ.get('SEED', 1))
rng = random.Random(SEED)

class S: pass
S.HOOK2 = 'THE GIANT PIZZA OVEN?'; S.HOOK2_SIZE = 80; S.FAIL_WORD = 'MELTED!'; S.FAIL_SIZE = 150
S.T_START = HOOK_T; S.TL = 13.5; S.T_END = S.T_START + S.TL
GROUND = 1600; R = 58; XMIN, XMAX = 200, 800; WALL_L, WALL_R = XMIN - R, XMAX + R
UP = float(os.environ.get('UP', 55)); DOWN = 9.0; BLOW = 260.0

BL = []; t = -0.4
while t < S.T_END + 1:
    s = rng.uniform(0.5, 1.0); d = rng.uniform(0.9, 2.0); reach = rng.uniform(260, 720)
    BL.append({'t': t, 'd': d, 's': s, 'reach': reach}); t += d + rng.uniform(0.7, 1.8)
def blast(t):
    for b in BL:
        if b['t'] <= t < b['t'] + b['d']:
            k = min(1, (t - b['t']) / 0.3, (b['t'] + b['d'] - t) / 0.3); return b['s'] * k, b['reach'] * min(1, (t - b['t']) / 0.4 + 0.2)
    return 0.0, 0.0

TER = Terrain(GROUND, seed=SEED, bumps=0, amp=0, soft=False)
N0 = int(40 * FPS); GX, GYS, FRZ, BP, BR, INB = [], [], [], [], [], []
ball = Ball(rng.uniform(300, 700), TER, R=R, seed=SEED, xmin=XMIN, xmax=XMAX, hop=rng.uniform(240, 300))
frz = 0.0; T_FAIL = None
for f in range(N0):
    t = f / FPS; P, reach = blast(t) if T_FAIL is None else (0.0, 0.0)
    edge = WALL_R - reach
    inside = P > 0.08 and ball.x + R * 0.6 > edge and ball.y > GROUND - 520
    if inside and T_FAIL is None: ball.vx -= P * BLOW / FPS
    ball.step(t)
    if T_FAIL is None and S.T_START <= t < S.T_END:
        depth = clamp((ball.x - edge) / max(1, reach), 0, 1) if inside else 0
        warm = 1.8 if ball.x < XMIN + 120 else 1.0
        frz = clamp(frz + (UP * P * (0.5 + depth) if inside else -DOWN * warm) / FPS, 0, 100)
        if frz >= 100: T_FAIL = t
    if T_FAIL is not None: ball.frozen = t > T_FAIL + 0.0; ball.y = min(ball.y, GROUND - R)
    GX.append(ball.x); GYS.append(ball.y); FRZ.append(frz); BP.append(P); BR.append(reach); INB.append(inside)
S.OUTCOME = 'fail' if T_FAIL else 'win'
S.T_RES = T_FAIL if T_FAIL else S.T_END
S.GRAB = (540, GROUND - R)
END = S.END = Ending(S)
if T_FAIL:
    FXp = GX[int(T_FAIL * FPS)]; S.GRAB = (FXp, GROUND - R)
else:
    gi = min(int(END.T_GRAB * FPS), N0 - 1); S.GRAB = (GX[gi], GYS[gi])
S.events = [[0.05, 'whoosh']]
for b in BL:
    if b['t'] < S.T_RES and b['s'] > 0.75: S.events.append([max(0, b['t']) + 0.2, 'sizzle'])
for b in BL:
    if b['t'] < S.T_RES: S.events.append([max(0, b['t']), 'whoosh'])
for (tl, xl, imp) in ball.landings:
    if tl < S.T_RES: S.events.append([tl, 'hop'])
for tw in ball.walls:
    if tw < S.T_RES: S.events.append([tw, 'thump', 0.4])
if T_FAIL: S.events += [[T_FAIL, 'sizzle'], [T_FAIL + 0.1, 'splash'], [T_FAIL + 0.95, 'pop']]
S.AMB = {'drone': 55, 'wind': 0.025}

def draw_bar(c, t, f):
    p = FRZ[f]; up = f > 0 and FRZ[f] > FRZ[f - 1]
    bx = bar(c, p / 100, f'MELT {int(p)}%', bad_col(p / 100), 0.12 if up else 0, bw=640, x_off=36)
    c.save(); c.translate(bx - 52, 231); c.set_source_rgb(*rgb('#ffb04a'))   # drop icon
    c.move_to(0, -30); c.curve_to(14, -10, 24, 2, 24, 12); c.curve_to(24, 26, 12, 32, 0, 32); c.curve_to(-12, 32, -24, 26, -24, 12); c.curve_to(-24, 2, -14, -10, 0, -30); c.fill()
    c.restore()
S.draw_bar = draw_bar

def draw_bg(c, t):
    c.set_source_rgb(*rgb('#181620')); c.rectangle(0, HEAD, W, H - HEAD); c.fill()
    # tiled kitchen wall
    c.set_source_rgb(*rgb('#262832')); c.rectangle(0, HEAD, W, GROUND - HEAD); c.fill()
    c.set_source_rgba(0, 0, 0, 0.18); c.set_line_width(3)
    for yy in range(760, GROUND, 70): c.move_to(0, yy); c.line_to(W, yy); c.stroke()
    for xx in range(0, W, 70): c.move_to(xx, 760); c.line_to(xx, GROUND); c.stroke()
    # window with the moon
    c.set_source_rgb(*rgb('#141c30')); rrect(c, 330, 520, 300, 200, 10); c.fill()
    c.set_source_rgb(*rgb('#d8d4c0')); c.arc(560, 580, 30, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#3a3c48')); c.set_line_width(10); rrect(c, 330, 520, 300, 200, 10); c.stroke(); c.move_to(480, 520); c.line_to(480, 720); c.stroke()
    # shelf with hanging pans + jars
    c.set_source_rgb(*rgb('#3a2c22')); c.rectangle(260, 860, 460, 16); c.fill()
    for (x, col) in ((300, '#5a3a2a'), (350, '#3a4a3a'), (395, '#5a4a2a')):
        c.set_source_rgb(*rgb(col)); rrect(c, x, 800, 34, 60, 8); c.fill()
    c.set_source_rgb(*rgb('#2a2a30')); c.set_line_width(4)
    for (x, r) in ((520, 46), (630, 38)):
        c.move_to(x, 876); c.line_to(x, 900); c.stroke()
        c.set_source_rgb(*rgb('#34343c')); c.arc(x, 900 + r, r, 0, 2 * math.pi); c.fill(); c.set_source_rgb(*rgb('#2a2a30'))
    # steel prep counter in the back
    c.set_source_rgb(*rgb('#3a3e48')); c.rectangle(240, GROUND - 230, 520, 26); c.fill()
    c.set_source_rgb(*rgb('#2c3038')); c.rectangle(260, GROUND - 204, 480, 204); c.fill()
    c.set_source_rgba(0, 0, 0, 0.25)
    for xx in (420, 580): c.rectangle(xx, GROUND - 204, 4, 204); c.fill()
    c.set_source_rgb(*rgb('#c8a060')); c.save(); c.translate(560, GROUND - 240); c.scale(70, 12); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()   # dough on the counter
    # checker floor
    c.set_source_rgb(*rgb('#3a3640')); c.rectangle(0, GROUND, W, H - GROUND); c.fill()
    c.set_source_rgba(0, 0, 0, 0.22)
    for j, yy in enumerate(range(GROUND, H, 80)):
        for i, xx in enumerate(range(0, W, 80)):
            if (i + j) % 2: c.rectangle(xx, yy, 80, 80); c.fill()
    # tall steel fridge with the door ajar = left wall (cold)
    c.set_source_rgb(*rgb('#8a909c')); c.rectangle(-20, 860, WALL_L + 20, GROUND - 860); c.fill()
    c.set_source_rgb(*rgb('#6e7480')); c.rectangle(-20, 1180, WALL_L + 20, 8); c.fill()
    c.set_source_rgb(*rgb('#b8c8d8')); c.rectangle(WALL_L - 26, 900, 18, 250); c.fill()   # bright gap of the open door
    c.set_source_rgb(*rgb('#4a505a')); rrect(c, WALL_L - 60, 980, 12, 120, 6); c.fill(); rrect(c, WALL_L - 60, 1230, 12, 120, 6); c.fill()
    for i in range(4):   # cold mist rolling out of the fridge
        k = (t * 0.45 + i / 4) % 1; c.set_source_rgba(0.78, 0.9, 1, 0.28 * (1 - k)); c.set_line_width(5)
        x = WALL_L - 10 + k * 90; y = 1000 + i * 130 + k * 60; c.move_to(x, y); c.curve_to(x + 20, y - 12, x + 40, y + 12, x + 60, y); c.stroke()

def draw_dryer(c, t, f):   # the giant brick pizza oven on the right + its blast of hot air along the floor
    P, reach = BP[f], BR[f]
    edge = WALL_R - reach
    if P > 0.03:
        for i in range(7):
            k = i / 6; y = GROUND - 40 - k * 400
            c.set_source_rgba(1, 0.5 + 0.2 * k, 0.2, 0.12 * P * (1.2 - k))
            c.save(); c.translate(WALL_R - reach * 0.5, y); c.scale(reach * 0.55 + 30, 110 - k * 40); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
        c.set_line_width(5); c.set_line_cap(cairo.LINE_CAP_ROUND)
        for i in range(18):   # wavy heat streaks + embers streaming left
            k = (t * (1.9 + P) + i / 18) % 1; y = GROUND - 30 - (i * 61) % 380
            x = lerp(WALL_R - 30, edge, k)
            if i % 4:
                c.set_source_rgba(1, 0.7 - 0.3 * k, 0.3, 0.5 * P * (1 - k))
                c.move_to(x, y); c.curve_to(x + 15, y - 10, x + 30, y + 10, x + 48, y); c.stroke()
            else:
                c.set_source_rgba(1, 0.6, 0.2, 0.8 * P * (1 - k)); c.arc(x, y - 20 * k, 6, 0, 2 * math.pi); c.fill()
    # giant brick oven = right wall
    x0 = WALL_R
    c.set_source_rgb(*rgb('#6a3a2e')); c.rectangle(x0, 1060, W - x0, GROUND - 1060); c.fill()
    c.save(); c.translate(x0 + 160, 1060); c.scale(200, 180); c.arc(0, 0, 1, math.pi, 2 * math.pi); c.restore(); c.fill()   # dome
    c.set_source_rgba(0, 0, 0, 0.22); c.set_line_width(3)
    for i, yy in enumerate(range(1080, GROUND, 40)):
        c.move_to(x0, yy); c.line_to(W, yy); c.stroke()
        for xx in range(int(x0) + 40 * (i % 2), W, 80): c.move_to(xx, yy); c.line_to(xx, yy + 40); c.stroke()
    c.set_source_rgb(*rgb('#4a2a22')); c.rectangle(x0 + 100, 760, 70, 130); c.fill()   # chimney
    if P < 0.05 or True:
        for i in range(3):
            k = (t * 0.6 + i / 3) % 1; c.set_source_rgba(0.55, 0.55, 0.6, 0.3 * (1 - k)); c.arc(x0 + 135 + 30 * k, 740 - 160 * k, 14 + 22 * k, 0, 2 * math.pi); c.fill()
    # oven mouth facing left near the floor, glows with the blast
    g = 0.35 + 0.65 * min(1, P * 1.4)
    c.set_source_rgb(*rgb('#2a1612')); c.move_to(x0 - 30, GROUND); c.line_to(x0 - 30, GROUND - 170); c.arc(x0 + 60, GROUND - 170, 90, math.pi, 1.5 * math.pi); c.line_to(x0 + 60, GROUND); c.close_path(); c.fill()
    c.set_source_rgb(0.25 + 0.7 * g, 0.12 + 0.35 * g, 0.05 + 0.08 * g); c.move_to(x0 - 14, GROUND); c.line_to(x0 - 14, GROUND - 160); c.arc(x0 + 60, GROUND - 160, 74, math.pi, 1.5 * math.pi); c.line_to(x0 + 60, GROUND); c.close_path(); c.fill()
    for k in range(5):   # fire inside
        fl = 0.6 + 0.4 * math.sin(t * 12 + k * 1.7)
        c.set_source_rgba(1, 0.75, 0.3, 0.6 * g); c.move_to(x0 + 10 + k * 12, GROUND - 6); c.line_to(x0 + 16 + k * 12, GROUND - 6 - 60 * fl * g); c.line_to(x0 + 24 + k * 12, GROUND - 6); c.close_path(); c.fill()
    # thermometer dial on the oven
    c.set_source_rgb(*rgb('#2a2a30')); c.arc(x0 + 150, 1180, 44, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#d8d4c0')); c.arc(x0 + 150, 1180, 36, 0, 2 * math.pi); c.fill()
    a = math.pi * (0.8 + 1.4 * min(1, 0.3 + P)); c.set_source_rgb(*rgb('#c0392b')); c.set_line_width(5)
    c.move_to(x0 + 150, 1180); c.line_to(x0 + 150 + 28 * math.cos(a), 1180 + 28 * math.sin(a)); c.stroke()
    # wooden pizza peel leaning on the oven
    c.set_source_rgb(*rgb('#8a6a40')); c.save(); c.translate(x0 + 230, GROUND); c.rotate(0.12); c.rectangle(-6, -420, 12, 300); c.fill(); rrect(c, -40, -130, 80, 130, 18); c.fill(); c.restore()

STARS = [(random.Random(i * 7 + 1).uniform(0, W), random.Random(i).uniform(HEAD, 1000), 1.2 + (i % 3) * 0.6) for i in range(50)]

PS = Particles(9)
def render(f, c):
    t = f / FPS; fi = min(f, len(GX) - 1); P = BP[fi]
    c.save(); c.translate(rng.uniform(-1.5, 1.5) * P, 0)
    draw_bg(c, t)
    melted = T_FAIL is not None and t >= T_FAIL
    p = FRZ[fi] / 100
    if END.carried(t) or t >= END.T_GRAB:
        gx, gy = (END.carry_xy(t) if END.carried(t) else S.GRAB)
    else:
        gx, gy = GX[fi], GYS[fi]
        if melted: k = ease((t - T_FAIL) / 0.25); gy = lerp(GYS[int(T_FAIL * FPS)], GROUND - R, k)
        h = max(0, GROUND - R - gy); kk = 1 / (1 + h / 220)
        c.set_source_rgba(0, 0, 0, 0.25 * kk); c.save(); c.translate(gx, GROUND + 3); c.scale(R * (0.5 + 0.4 * kk), 9); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    mix = lambda a, b: '#%02x%02x%02x' % tuple(int(lerp(int(a[i:i + 2], 16), int(b[i:i + 2], 16), min(1, p) * 0.5)) for i in (1, 3, 5))
    skin = (mix('#ffd36b', '#ff9a5a'), mix('#ff8a1f', '#e8501a'), mix('#c45a00', '#9a2a00'))
    mood = 'happy' if (t >= S.T_END and S.OUTCOME == 'win') else ('scared' if INB[fi] or melted or p > 0.7 else 'worried')
    draw_dryer(c, t, fi)
    # melt puddle: flatten after the fail, re-form just before the claw grabs
    sq = 0.0
    if melted and not END.carried(t):
        down = ease((t - T_FAIL) / 0.45); upk = ease((t - (END.T_GRAB - 0.45)) / 0.4)
        sq = 0.62 * down * (1 - upk)
        if sq > 0.02:
            c.set_source_rgba(*rgb(skin[1]), 0.85); c.save(); c.translate(gx, GROUND - 4); c.scale(R * (1 + 1.6 * sq), 14 * sq + 2); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
        gy = gy + R * sq * 0.95
    draw_blob(c, t, gx, gy, mood, sq, R=R, skin=skin, dizzy=melted and t > T_FAIL + 0.6)
    # drips when hot
    if not END.carried(t) and not melted and p > 0.35:
        for i in range(2):
            k = (t * 1.6 + i * 0.5) % 1; dx = gx + (-0.5 + i) * R * 0.9
            c.set_source_rgba(*rgb(skin[1]), 0.9 * (1 - k)); c.arc(dx, gy + R * 0.7 + k * 40, 7, 0, 2 * math.pi); c.fill()
    if INB[fi] and f % 4 == 0 and not END.carried(t) and not melted: PS.spawn(gx + rng.uniform(-30, 30), gy - R * 0.6, 1, (0.85, 0.85, 0.9), 110, 0.7, grav=-150, r=8)
    PS.draw(c)
    END.draw_claw(c, t)
    c.restore()
    END.header(c, t, fi)

if __name__ == '__main__':
    if sys.argv[1] == 'sim':
        e = int(S.T_RES * FPS) - 1
        print(SEED, S.OUTCOME, round(S.T_RES - S.T_START, 2), 'peak', round(max(FRZ[:e + 1])), 'final', round(FRZ[e]), 'dur', S.DUR, [round(FRZ[min(e, int((S.T_START + k) * FPS))]) for k in range(13)]); sys.exit()
    run(S, render)
