"""2026-11-02 v4 — TEMPERATURE – MELT %: the GIANT MAGNIFYING GLASS. Gloop is a passive rigid ball
(Ball) bouncing on a sun-baked patio between two brick walls. A giant magnifying glass focuses a hot
light cone that moves in seeded-random segments (some aimed at where he is, with lag). While Gloop's
body is inside the cone MELT rises fast, outside it cools slowly. 100% = melted puddle."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the giant magnifying glass'
SEED = int(os.environ.get('SEED', 15))
rng = random.Random(SEED)

class S: pass
S.HOOK2 = 'THE MAGNIFYING GLASS?'; S.HOOK2_SIZE = 76; S.FAIL_WORD = 'MELTED!'; S.FAIL_SIZE = 150
S.T_START = HOOK_T; S.TL = 13.0; S.T_END = S.T_START + S.TL
GROUND = 1600; R = 58; XMIN, XMAX = 160, 920; WALL_L, WALL_R = XMIN - R, XMAX + R
LENS_Y = 760; SPOT_R = 62; LENS_R = 175; UP, DOWN = 34.0, 11.0

TER = Terrain(GROUND, seed=SEED, bumps=0, amp=0, soft=False)
N0 = int(40 * FPS); GX, GYS, MELT, SX, LX, INB = [], [], [], [], [], []
ball = Ball(rng.uniform(300, 780), TER, R=R, seed=SEED, xmin=XMIN, xmax=XMAX, hop=rng.uniform(240, 300))
sx = rng.choice((rng.uniform(200, 330), rng.uniform(750, 880))); seg_from = sx; seg_to = sx; seg_t0 = 0; seg_t1 = 0
melt = 0.0; T_FAIL = None; SEGS = []
def in_cone(bx, by, lx, sx):
    k = clamp((by - LENS_Y) / (GROUND - LENS_Y), 0, 1); cx = lerp(lx, sx, k); hw = lerp(LENS_R * 0.9, SPOT_R, k)
    return abs(bx - cx) < hw + R * 0.55 and by > LENS_Y
for f in range(N0):
    t = f / FPS
    if t >= seg_t1:   # next sweep segment: aim at Gloop (with lag) or wander
        seg_from = sx; aim = rng.random() < 0.5
        seg_to = clamp(ball.x + rng.uniform(-90, 90), 190, 890) if aim else rng.uniform(190, 890)
        seg_t0 = t; seg_t1 = t + rng.uniform(0.7, 1.5) + rng.choice((0, 0, 0.6)); SEGS.append((t, aim))
    k = ease(clamp((t - seg_t0) / max(0.4, (seg_t1 - seg_t0) * 0.8), 0, 1)); sx = lerp(seg_from, seg_to, k)
    lx = lerp(W / 2, sx, 0.55)
    ball.step(t)
    inside = T_FAIL is None and in_cone(ball.x, ball.y, lx, sx)
    if T_FAIL is None and S.T_START <= t < S.T_END:
        melt = clamp(melt + (UP if inside else -DOWN) / FPS, 0, 100)
        if melt >= 100: T_FAIL = t
    if T_FAIL is not None: ball.vmin = 0; ball.e = 0.2; ball.vx *= 0.9
    GX.append(ball.x); GYS.append(ball.y); MELT.append(melt); SX.append(sx); LX.append(lx); INB.append(inside)
S.OUTCOME = 'fail' if T_FAIL else 'win'
S.T_RES = T_FAIL if T_FAIL else S.T_END
S.GRAB = (540, GROUND - R)
END = S.END = Ending(S)
gi = min(int(END.T_GRAB * FPS), N0 - 1); S.GRAB = (GX[gi], GROUND - R * 0.55 if T_FAIL else GYS[gi])
S.events = []
for (tl, xl, imp) in ball.landings:
    if tl < S.T_RES + 1.5: S.events.append([tl, 'hop'])
for tw in ball.walls:
    if tw < S.T_RES + 1.5: S.events.append([tw, 'thump', 0.4])
was = False
for f in range(int(S.T_RES * FPS)):
    if INB[f] and not was and f / FPS >= S.T_START: S.events.append([f / FPS, 'sizzle'])
    was = INB[f]
if T_FAIL: S.events.append([T_FAIL, 'sizzle']); S.events.append([T_FAIL + 0.1, 'splash'])
S.AMB = {'drone': 58, 'wind': 0.015}

def draw_bar(c, t, f):
    p = MELT[f]; up = f > 0 and MELT[f] > MELT[f - 1]
    bx = bar(c, p / 100, f'MELT {int(p)}%', bad_col(p / 100), 0.12 if up else 0, bw=640, x_off=36)
    c.save(); c.translate(bx - 52, 231); c.set_source_rgb(*rgb('#ffb347'))
    c.move_to(0, -28); c.curve_to(18, -4, 22, 8, 0, 26); c.curve_to(-22, 8, -18, -4, 0, -28); c.fill(); c.restore()
S.draw_bar = draw_bar

def draw_bg(c, t):
    gr = cairo.LinearGradient(0, HEAD, 0, GROUND)
    gr.add_color_stop_rgb(0, *rgb('#3a2c3e')); gr.add_color_stop_rgb(1, *rgb('#7a5a4a'))
    c.set_source(gr); c.rectangle(0, HEAD, W, GROUND - HEAD); c.fill()
    c.set_source_rgb(*rgb('#e8c27a')); c.arc(190, 520, 70, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#4a3a42'))
    for x, w, h in ((80, 160, 320), (260, 120, 220), (420, 200, 400), (660, 140, 260), (820, 220, 360), (1000, 160, 240)):
        c.rectangle(x - w / 2, 1330 - h, w, h + 40); c.fill()
    c.set_source_rgba(1, 0.85, 0.5, 0.25)
    for x, w, h in ((420, 200, 400), (820, 220, 360)):
        for yy in range(int(1330 - h) + 30, 1320, 60):
            for xx in (x - 50, x + 20): c.rectangle(xx, yy, 24, 30); c.fill()
    c.set_source_rgb(*rgb('#5e4a44')); c.rectangle(0, 1330, W, GROUND - 1330); c.fill()
    c.set_source_rgb(*rgb('#8d7064')); c.rectangle(0, GROUND, W, H - GROUND); c.fill()
    c.set_source_rgba(0, 0, 0, 0.16); c.set_line_width(3)
    for yy in range(GROUND + 80, H, 80): c.move_to(0, yy); c.line_to(W, yy); c.stroke()
    for i, yy in enumerate(range(GROUND, H, 80)):
        for x in range(60 * (i % 2), W, 120): c.move_to(x, yy); c.line_to(x, yy + 80); c.stroke()
    for (x0, x1) in ((0, WALL_L), (WALL_R, W)):
        c.set_source_rgb(*rgb('#6a3f35')); c.rectangle(x0, 1050, x1 - x0, GROUND - 1050); c.fill()
        c.set_source_rgb(*rgb('#55322b'))
        for j, yy in enumerate(range(1050, GROUND, 44)):
            c.rectangle(x0, yy, x1 - x0, 4); c.fill()
            c.rectangle(x0 + (22 if j % 2 else 50), yy, 4, 44); c.fill()

def draw_lens_and_cone(c, t, f):
    sx, lx = SX[f], LX[f]; on = T_FAIL is None or t < T_FAIL + 1.0
    if on:
        c.set_source_rgba(1, 0.92, 0.6, 0.20)
        c.move_to(lx - LENS_R * 0.9, LENS_Y); c.line_to(sx - SPOT_R, GROUND); c.line_to(sx + SPOT_R, GROUND); c.line_to(lx + LENS_R * 0.9, LENS_Y); c.close_path(); c.fill()
        c.set_source_rgba(1, 0.95, 0.7, 0.55); c.save(); c.translate(sx, GROUND + 4); c.scale(SPOT_R * 1.15, 16); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
        c.set_source_rgba(1, 1, 0.9, 0.8); c.save(); c.translate(sx, GROUND + 4); c.scale(SPOT_R * 0.55, 8); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
        for i in range(3):   # heat shimmer wisps above the spot
            k = (t * 1.2 + i / 3) % 1
            c.set_source_rgba(1, 1, 1, 0.25 * (1 - k)); c.set_line_width(4)
            yy = GROUND - 20 - k * 160; c.move_to(sx - 30 + i * 30, yy); c.curve_to(sx - 20 + i * 30, yy - 20, sx - 40 + i * 30, yy - 40, sx - 30 + i * 30, yy - 60); c.stroke()
    # handle from the top-right corner + lens
    c.set_source_rgb(*rgb('#3b2a24')); c.set_line_width(46); c.set_line_cap(cairo.LINE_CAP_ROUND)
    hx, hy = lx + LENS_R * 0.75, LENS_Y - LENS_R * 0.75 - 30
    c.move_to(hx, hy); c.line_to(hx + 260, hy - 260); c.stroke()
    c.set_source_rgb(*rgb('#6d7480')); c.set_line_width(26); c.save(); c.translate(lx, LENS_Y - 30); c.scale(1, 0.32); c.arc(0, 0, LENS_R, 0, 2 * math.pi); c.restore(); c.stroke()
    c.set_source_rgba(0.75, 0.9, 1, 0.35); c.save(); c.translate(lx, LENS_Y - 30); c.scale(1, 0.32); c.arc(0, 0, LENS_R - 10, 0, 2 * math.pi); c.restore(); c.fill()

PS = Particles(9)
def render(f, c):
    t = f / FPS; fi = min(f, len(GX) - 1)
    c.save()
    draw_bg(c, t)
    melted = T_FAIL is not None and t >= T_FAIL
    p = MELT[fi] / 100
    if END.carried(t) or t >= END.T_GRAB: gx, gy = (END.carry_xy(t) if END.carried(t) else S.GRAB); sq = 0.45 if melted and not END.carried(t) else (0.2 if melted else 0)
    else:
        gx, gy = GX[fi], GYS[fi]; sq = 0
        if melted: k = ease((t - T_FAIL) / 0.6); sq = 0.55 * k; gy = lerp(gy, GROUND - R * (1 - sq), k)
        h = max(0, GROUND - R - gy); kk = 1 / (1 + h / 220)
        c.set_source_rgba(0, 0, 0, 0.25 * kk); c.save(); c.translate(gx, GROUND + 3); c.scale(R * (0.5 + 0.4 * kk), 9); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    if melted and not END.carried(t):   # little orange puddle around him
        c.set_source_rgb(*rgb('#ff8a1f')); c.save(); c.translate(gx, GROUND + 2); c.scale(max(1, R * 2.0 * ease((t - T_FAIL) / 0.8)), 14); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    mix = lambda a, b: '#%02x%02x%02x' % tuple(int(lerp(int(a[i:i + 2], 16), int(b[i:i + 2], 16), p * 0.6)) for i in (1, 3, 5))
    skin = (mix('#ffd36b', '#ff9a6b'), mix('#ff8a1f', '#ff4a1f'), mix('#c45a00', '#a02a00'))
    mood = 'happy' if (t >= S.T_END and S.OUTCOME == 'win') else ('scared' if INB[fi] or melted or p > 0.7 else 'worried')
    draw_blob(c, t, gx, gy, mood, sq, R=R, skin=skin, dizzy=melted and t > T_FAIL + 0.5)
    if INB[fi] and f % 4 == 0 and not END.carried(t): PS.spawn(gx + rng.uniform(-30, 30), gy - R * 0.6, 2, (0.85, 0.85, 0.85), 160, 0.7, grav=-300, r=10)
    if p > 0.5 and f % 9 == 0 and not END.carried(t) and t < S.T_RES: PS.spawn(gx + R * 0.5, gy + R * 0.3, 1, (1, 0.55, 0.15), 80, 0.6, grav=900, r=7)
    PS.draw(c)
    draw_lens_and_cone(c, t, fi)
    END.draw_claw(c, t)
    c.restore()
    END.header(c, t, fi)

if __name__ == '__main__':
    if sys.argv[1] == 'sim':
        e = int(S.T_RES * FPS) - 1
        print(SEED, S.OUTCOME, round(S.T_RES - S.T_START, 2), 'peak', round(max(MELT[:e + 1])), 'final', round(MELT[e]), 'dur', S.DUR); sys.exit()
    run(S, render)
