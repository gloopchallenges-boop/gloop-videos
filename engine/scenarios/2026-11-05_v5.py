"""2026-11-05 v5 — TEMPERATURE – MELT %: the GIANT HAIR DRYER. A bathroom at night; a giant hair dryer on
the right blows seeded-random hot blasts along the floor (reach + strength + length vary). Gloop is a
passive rigid ball (Ball) bouncing between a cold bathtub full of ice (left wall) and the dryer (right
wall). Inside the hot air MELT rises (faster deep in it), outside it cools slowly — faster right next to
the icy tub. The blasts also blow him left a little. 100% = melted into a puddle (re-forms dizzy)."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the giant hair dryer'
SEED = int(os.environ.get('SEED', 18))
rng = random.Random(SEED)

class S: pass
S.HOOK2 = 'THE GIANT HAIR DRYER?'; S.HOOK2_SIZE = 84; S.FAIL_WORD = 'MELTED!'; S.FAIL_SIZE = 150
S.T_START = HOOK_T; S.TL = 13.0; S.T_END = S.T_START + S.TL
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
    c.set_source_rgb(*rgb('#1d2430')); c.rectangle(0, HEAD, W, H - HEAD); c.fill()
    c.set_source_rgba(1, 1, 1, 0.04); c.set_line_width(3)   # wall tiles
    for yy in range(HEAD, GROUND, 90): c.move_to(0, yy); c.line_to(W, yy); c.stroke()
    for xx in range(0, W, 90): c.move_to(xx, HEAD); c.line_to(xx, GROUND); c.stroke()
    c.set_source_rgb(*rgb('#26303e')); c.rectangle(0, 1080, W, 26); c.fill()   # tile trim strip
    # mirror + sink in the middle back
    c.set_source_rgb(*rgb('#3a4556')); rrect(c, 330, 470, 330, 420, 24); c.fill()
    c.set_source_rgb(*rgb('#24303f')); rrect(c, 348, 488, 294, 384, 16); c.fill()
    c.set_source_rgba(1, 1, 1, 0.07); c.move_to(380, 860); c.line_to(470, 500); c.line_to(510, 500); c.line_to(420, 860); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#d9dee6')); c.arc(495, 445, 16, 0, 2 * math.pi); c.fill()   # small lamp
    c.set_source_rgba(1, 0.95, 0.8, 0.06); c.arc(495, 445, 70, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#b8c0cc')); rrect(c, 360, 950, 270, 70, 30); c.fill()     # sink basin
    c.set_source_rgb(*rgb('#8d96a4')); c.rectangle(470, 1020, 50, 160); c.fill()       # pedestal
    c.set_source_rgb(*rgb('#8d96a4')); c.rectangle(485, 915, 20, 40); c.rectangle(485, 915, 50, 14); c.fill()  # tap
    # towel hook + towel
    c.set_source_rgb(*rgb('#5b6f8a')); rrect(c, 760, 600, 120, 230, 14); c.fill()
    c.set_source_rgba(1, 1, 1, 0.08)
    for yy in (650, 760): c.rectangle(760, yy, 120, 16); c.fill()
    # floor tiles
    c.set_source_rgb(*rgb('#3a3e4a')); c.rectangle(0, GROUND, W, H - GROUND); c.fill()
    c.set_source_rgba(0, 0, 0, 0.2)
    for i, yy in enumerate(range(GROUND, H, 80)):
        for x in range(80 * (i % 2), W, 160): c.rectangle(x, yy, 80, 80); c.fill()
    # bathtub with ice = left wall
    c.set_source_rgb(*rgb('#c8d0dc')); rrect(c, -60, 1260, WALL_L + 60, GROUND - 1260 + 10, 30); c.fill()
    c.set_source_rgb(*rgb('#a9b3c2')); c.rectangle(-60, 1260, WALL_L + 60, 26); c.fill()
    for i, (ix, iy) in enumerate([(20, 1222), (70, 1232), (110, 1218), (45, 1200)]):
        c.set_source_rgba(0.8, 0.94, 1, 0.85); rrect(c, ix - 22, iy - 22, 44, 44, 8); c.fill()
    c.set_source_rgb(*rgb('#8d96a4')); c.rectangle(30, GROUND, 14, 18); c.rectangle(WALL_L - 40, GROUND, 14, 18); c.fill()
    for i in range(3):   # cold mist wisps
        k = (t * 0.5 + i / 3) % 1; c.set_source_rgba(0.8, 0.92, 1, 0.3 * (1 - k)); c.set_line_width(4)
        x = 25 + i * 40; y = 1190 - k * 110; c.move_to(x, y); c.curve_to(x + 12, y - 20, x - 12, y - 40, x, y - 60); c.stroke()

def draw_dryer(c, t, f):
    P, reach = BP[f], BR[f]
    if P > 0.03:   # hot air sheet along the floor
        edge = WALL_R - reach
        for i in range(7):
            k = i / 6; y = GROUND - 40 - k * 420
            c.set_source_rgba(1, 0.62, 0.3, 0.09 * P * (1.2 - k))
            c.save(); c.translate(WALL_R - reach * 0.5, y); c.scale(reach * 0.55 + 30, 120 - k * 40); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
        c.set_line_width(5)
        for i in range(10):   # heat shimmer streaks
            k = (t * (1.4 + P) + i / 10) % 1; y = GROUND - 50 - (i * 37) % 380
            x = lerp(WALL_R, edge, k); c.set_source_rgba(1, 0.75, 0.45, 0.5 * P * (1 - k))
            c.move_to(x + 70, y)
            c.curve_to(x + 45, y - 10, x + 25, y + 10, x, y); c.stroke()
    # dryer: body up high on the right, nozzle aimed down-left at the floor, handle down
    x0 = WALL_R; vib = 2 * P * math.sin(t * 60)
    c.save(); c.translate(vib, 0)
    c.set_source_rgb(*rgb('#6a5a7a')); rrect(c, x0 + 30, 1300, 110, 300, 30); c.fill()   # handle (wall)
    c.set_source_rgb(*rgb('#584a68')); c.rectangle(x0 + 30, 1520, 110, 20); c.fill()
    c.set_source_rgb(*rgb('#3a3046')); c.move_to(x0 + 85, 1600); c.curve_to(x0 + 90, 1660, x0 + 150, 1700, W, 1690); c.set_line_width(10); c.stroke()   # cord
    c.set_source_rgb(*rgb('#7c6a90')); rrect(c, x0 - 10, 1080, W - x0 + 60, 260, 120); c.fill()   # body
    c.set_source_rgb(*rgb('#8f7ca4')); rrect(c, x0 + 40, 1110, W - x0, 70, 35); c.fill()
    c.set_source_rgb(*rgb('#4a3e58')); rrect(c, x0 - 60, 1130, 90, 170, 30); c.fill()   # nozzle
    c.set_source_rgb(*rgb('#2a2234')); rrect(c, x0 - 64, 1150, 30, 130, 12); c.fill()
    glow = 0.25 + 0.6 * P
    c.set_source_rgba(1, 0.45, 0.15, glow); c.set_line_width(5)
    for yy in range(1165, 1270, 22): c.move_to(x0 - 60, yy); c.line_to(x0 - 38, yy); c.stroke()
    c.set_source_rgb(*rgb('#e0d6ea')); c.arc(x0 + 110, 1250, 14, 0, 2 * math.pi); c.fill()   # button
    c.set_source_rgb(*(rgb('#ff8040') if P > 0.05 else rgb('#5a3030'))); c.arc(x0 + 110, 1250, 7, 0, 2 * math.pi); c.fill()
    c.restore()

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
