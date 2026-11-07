"""2026-11-07 v1 — TEMPERATURE – MELT %: the DRAGON'S BREATH. A castle courtyard at night; a dragon's head
pokes through a broken gate on the right and breathes seeded-random fire blasts along the flagstones
(reach + strength + length vary). Gloop is a passive rigid ball (Ball) bouncing between a cold stone well
(left wall) and the gate (right wall). Inside the fire MELT rises (faster deep in it), outside it cools
slowly — faster next to the well. The blasts also push him left a little. 100% = melted into a puddle."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the dragon’s breath'
SEED = int(os.environ.get('SEED', 18))
rng = random.Random(SEED)

class S: pass
S.HOOK2 = "THE DRAGON'S BREATH?"; S.HOOK2_SIZE = 84; S.FAIL_WORD = 'MELTED!'; S.FAIL_SIZE = 150
S.T_START = HOOK_T; S.TL = 12.5; S.T_END = S.T_START + S.TL
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
    c.set_source_rgb(*rgb('#16182a')); c.rectangle(0, HEAD, W, H - HEAD); c.fill()
    c.set_source_rgba(0.85, 0.88, 0.95, 0.45)
    for x, y, r in STARS: c.arc(x, y, r, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#d8d4c0')); c.arc(250, 520, 46, 0, 2 * math.pi); c.fill()   # moon
    c.set_source_rgb(*rgb('#16182a')); c.arc(268, 508, 40, 0, 2 * math.pi); c.fill()
    # distant castle towers
    c.set_source_rgb(*rgb('#22253a'))
    for (x, w_, h_) in ((380, 120, 520), (560, 90, 420), (690, 140, 600)):
        c.rectangle(x, GROUND - 300 - h_, w_, h_ + 300); c.fill()
        for k in range(0, w_, 30): c.rectangle(x + k, GROUND - 330 - h_, 18, 32); c.fill()
    c.set_source_rgba(1, 0.8, 0.45, 0.35)
    for (x, y) in ((420, 980), (595, 1060), (735, 900), (760, 1010)): c.rectangle(x, y, 18, 30); c.fill()
    # courtyard wall
    c.set_source_rgb(*rgb('#2c2f44')); c.rectangle(0, 1240, W, GROUND - 1240); c.fill()
    c.set_source_rgba(0, 0, 0, 0.22); c.set_line_width(3)
    for i, yy in enumerate(range(1240, GROUND, 60)):
        c.move_to(0, yy); c.line_to(W, yy); c.stroke()
        for x in range(60 * (i % 2), W, 120): c.move_to(x, yy); c.line_to(x, yy + 60); c.stroke()
    # flagstone floor
    c.set_source_rgb(*rgb('#3b3a44')); c.rectangle(0, GROUND, W, H - GROUND); c.fill()
    c.set_source_rgba(0, 0, 0, 0.25); c.set_line_width(4)
    for i, yy in enumerate(range(GROUND, H, 90)):
        c.move_to(0, yy); c.line_to(W, yy); c.stroke()
        for x in range(70 * (i % 2), W, 140): c.move_to(x, yy); c.line_to(x, yy + 90); c.stroke()
    # stone well = left wall (cold)
    c.set_source_rgb(*rgb('#5a6070')); c.rectangle(-20, 1300, WALL_L + 20, GROUND - 1300); c.fill()
    c.set_source_rgba(0, 0, 0, 0.25)
    for i, yy in enumerate(range(1300, GROUND, 50)):
        for x in range(-20 + 35 * (i % 2), WALL_L, 70): c.rectangle(x, yy, 4, 50); c.fill()
        c.rectangle(-20, yy, WALL_L + 20, 4); c.fill()
    c.set_source_rgb(*rgb('#6b7284')); c.rectangle(-20, 1280, WALL_L + 30, 30); c.fill()
    c.set_source_rgb(*rgb('#4a3a2c')); c.rectangle(20, 1060, 14, 220); c.rectangle(WALL_L - 30, 1060, 14, 220); c.rectangle(10, 1050, WALL_L - 10, 18); c.fill()
    c.set_source_rgb(*rgb('#6e5a40')); rrect(c, 50, 1150, 60, 60, 8); c.fill()   # bucket
    for i in range(3):   # cold mist from the well
        k = (t * 0.5 + i / 3) % 1; c.set_source_rgba(0.75, 0.88, 1, 0.3 * (1 - k)); c.set_line_width(4)
        x = 30 + i * 40; y = 1270 - k * 110; c.move_to(x, y); c.curve_to(x + 12, y - 20, x - 12, y - 40, x, y - 60); c.stroke()

def draw_dryer(c, t, f):
    P, reach = BP[f], BR[f]
    edge = WALL_R - reach
    if P > 0.03:   # fire sheet along the floor
        for i in range(7):
            k = i / 6; y = GROUND - 40 - k * 400
            c.set_source_rgba(1, 0.45 + 0.2 * k, 0.15, 0.13 * P * (1.2 - k))
            c.save(); c.translate(WALL_R - reach * 0.5, y); c.scale(reach * 0.55 + 30, 110 - k * 40); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
        for i in range(14):   # flame tongues
            k = (t * (1.8 + P) + i / 14) % 1; y = GROUND - 30 - (i * 53) % 360
            x = lerp(WALL_R - 40, edge, k); r = (18 + 30 * k) * P
            c.set_source_rgba(1, 0.75 - 0.4 * k, 0.2, 0.75 * P * (1 - k)); c.arc(x, y, r, 0, 2 * math.pi); c.fill()
    # gate pillar = right wall + dragon head poking through
    x0 = WALL_R
    c.set_source_rgb(*rgb('#3a3d52')); c.rectangle(x0, 900, W - x0, GROUND - 900); c.fill()
    c.set_source_rgba(0, 0, 0, 0.3)
    for yy in range(900, GROUND, 60): c.rectangle(x0, yy, W - x0, 4); c.fill()
    c.set_source_rgb(*rgb('#14121c')); rrect(c, x0 + 20, 1260, W - x0, GROUND - 1260, 40); c.fill()   # gate hole
    open_ = 0.15 + 0.85 * min(1, P * 1.5); bob = 6 * math.sin(t * 2.2)
    c.save(); c.translate(x0 - 10, 1450 + bob)
    c.set_source_rgb(*rgb('#2f5a44')); rrect(c, 40, -110, 260, 220, 90); c.fill()   # head
    c.set_source_rgb(*rgb('#3a6e52'))
    c.move_to(80, -100); c.line_to(130, -190); c.line_to(150, -95); c.close_path(); c.fill()   # horn
    c.move_to(170, -100); c.line_to(230, -200); c.line_to(240, -90); c.close_path(); c.fill()
    # jaws
    c.set_source_rgb(*rgb('#3a6e52')); rrect(c, -60, -70 - 25 * open_, 160, 70, 26); c.fill()
    c.set_source_rgb(*rgb('#2a4a3a')); rrect(c, -50, 10 + 25 * open_, 150, 56, 22); c.fill()
    c.set_source_rgb(*rgb('#1a0c0c')); c.rectangle(-40, -4 - 25 * open_, 140, 18 + 50 * open_); c.fill()
    c.set_source_rgb(*rgb('#e8e2cc'))
    for k in range(4):
        x = -40 + k * 34; c.move_to(x, -4 - 25 * open_); c.line_to(x + 10, 14 - 25 * open_); c.line_to(x + 20, -4 - 25 * open_); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#1a1a1a')); c.arc(-30, -70 - 25 * open_, 7, 0, 2 * math.pi); c.fill()   # nostril
    c.set_source_rgb(*rgb('#ffc94a')); c.save(); c.translate(130, -50); c.scale(26, 16); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()   # eye
    c.set_source_rgb(*rgb('#1a1a1a')); c.rectangle(126, -64, 8, 28); c.fill()
    if P < 0.05:   # smoke puffs while idle
        for i in range(2):
            k = (t * 0.7 + i * 0.5) % 1; c.set_source_rgba(0.6, 0.6, 0.65, 0.35 * (1 - k)); c.arc(-30 - 20 * k, -80 - 25 * open_ - 120 * k, 10 + 18 * k, 0, 2 * math.pi); c.fill()
    c.restore()

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
