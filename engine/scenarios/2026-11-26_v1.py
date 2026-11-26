"""2026-11-26 v1 — TEMPERATURE – MELT %: the STEAM TRAIN. An old railway platform at night; a steam locomotive
stands at the right, its cylinder cocks blasting seeded-random jets of hot steam along the platform (reach + strength +
length vary). Gloop is a passive rigid ball (Ball) bouncing between a water-tower crane (left wall, dripping cold water)
and the locomotive (right wall). Inside the steam MELT rises (faster deep in it), outside it cools slowly — faster next
to the water tower. The blasts also push him left a little. 100% = melted into a puddle."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the steam train'
SEED = int(os.environ.get('SEED', 29))
rng = random.Random(SEED)

class S: pass
S.HOOK2 = 'THE STEAM TRAIN?'; S.HOOK2_SIZE = 96; S.FAIL_WORD = 'MELTED!'; S.FAIL_SIZE = 150
S.T_START = HOOK_T; S.TL = float(os.environ.get('TL', 13.5)); S.T_END = S.T_START + S.TL
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
    # night sky over an old railway station
    c.set_source_rgb(*rgb('#121428')); c.rectangle(0, HEAD, W, H - HEAD); c.fill()
    for (sx, sy, r) in STARS:
        c.set_source_rgba(1, 1, 0.95, 0.25 + 0.2 * math.sin(t * 1.7 + sx)); c.arc(sx, sy, r, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#d8d4c0')); c.arc(300, 560, 34, 0, 2 * math.pi); c.fill()
    # station building in the back with lit windows
    c.set_source_rgb(*rgb('#24222e')); c.rectangle(0, 900, W, GROUND - 900); c.fill()
    c.set_source_rgb(*rgb('#2e2a36')); c.move_to(-20, 900); c.line_to(W / 2, 760); c.line_to(W + 20, 900); c.close_path(); c.fill()
    for xx in (230, 420, 610):
        c.set_source_rgb(*rgb('#3a3020')); rrect(c, xx, 1010, 110, 150, 50); c.fill()
        c.set_source_rgba(0.95, 0.75, 0.4, 0.35); rrect(c, xx + 10, 1020, 90, 130, 44); c.fill()
    # station clock
    c.set_source_rgb(*rgb('#1a1820')); c.arc(W / 2, 860, 52, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#d8d4c0')); c.arc(W / 2, 860, 42, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#1a1820')); c.set_line_width(5); c.set_line_cap(cairo.LINE_CAP_ROUND)
    c.move_to(W / 2, 860); c.line_to(W / 2, 830); c.stroke(); c.move_to(W / 2, 860); c.line_to(W / 2 + 22, 868); c.stroke()
    # platform canopy roof with iron posts
    c.set_source_rgb(*rgb('#3a2e2a')); c.rectangle(0, 1200, W, 34); c.fill()
    c.set_source_rgb(*rgb('#4a3a32'))
    for xx in range(0, W, 46): c.move_to(xx, 1234); c.line_to(xx + 23, 1258); c.line_to(xx + 46, 1234); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#2a2a34'))
    for xx in (300, 640): c.rectangle(xx, 1234, 16, GROUND - 1234); c.fill()
    # hanging lamp (the one quiet light)
    c.set_source_rgb(*rgb('#2a2a34')); c.rectangle(468, 1234, 4, 60); c.fill()
    c.set_source_rgb(*rgb('#f0d28a')); c.arc(470, 1306, 14, 0, 2 * math.pi); c.fill()
    # platform floor: stone slabs + yellow safety line
    c.set_source_rgb(*rgb('#3a3840')); c.rectangle(0, GROUND, W, H - GROUND); c.fill()
    c.set_source_rgb(*rgb('#c8a83a')); c.rectangle(0, GROUND + 26, W, 10); c.fill()
    c.set_source_rgba(0, 0, 0, 0.22); c.set_line_width(3)
    for yy in range(GROUND + 80, H, 90): c.move_to(0, yy); c.line_to(W, yy); c.stroke()
    for i, yy in enumerate(range(GROUND + 80, H, 90)):
        for xx in range(60 * (i % 2), W, 120): c.move_to(xx, yy); c.line_to(xx, yy + 90); c.stroke()
    # water tower crane = left wall (cool side), dripping cold water
    c.set_source_rgb(*rgb('#3c5266')); c.rectangle(-20, 980, WALL_L + 20, GROUND - 980); c.fill()
    c.set_source_rgb(*rgb('#2e4050'))
    for yy in range(1020, GROUND, 110): c.rectangle(-20, yy, WALL_L + 20, 10); c.fill()
    c.set_source_rgb(*rgb('#4a6480')); rrect(c, -40, 900, WALL_L + 80, 90, 14); c.fill()   # tank lid
    c.set_source_rgb(*rgb('#2e4050')); c.rectangle(WALL_L - 10, 940, 90, 22); c.fill()        # spout arm
    for i in range(3):   # drips
        k = (t * 1.1 + i / 3) % 1; c.set_source_rgba(0.6, 0.8, 1, 0.7 * (1 - k)); c.arc(WALL_L + 70, 970 + k * 260, 6, 0, 2 * math.pi); c.fill()
    for i in range(4):   # cool mist
        k = (t * 0.45 + i / 4) % 1; c.set_source_rgba(0.7, 0.85, 1, 0.22 * (1 - k)); c.set_line_width(5)
        x = WALL_L - 10 + k * 90; y = 1100 + i * 120 + k * 50; c.move_to(x, y); c.curve_to(x + 20, y - 12, x + 40, y + 12, x + 60, y); c.stroke()

def draw_dryer(c, t, f):   # the steam locomotive on the right + hot steam blasting out of its cylinder along the floor
    P, reach = BP[f], BR[f]
    edge = WALL_R - reach
    if P > 0.03:
        for i in range(7):
            k = i / 6; y = GROUND - 40 - k * 400
            c.set_source_rgba(0.92, 0.9, 0.88, 0.16 * P * (1.2 - k))
            c.save(); c.translate(WALL_R - reach * 0.5, y); c.scale(reach * 0.55 + 30, 110 - k * 40); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
        for i in range(20):   # rolling steam puffs + hot streaks streaming left
            k = (t * (1.9 + P) + i / 20) % 1; y = GROUND - 40 - (i * 61) % 380
            x = lerp(WALL_R - 30, edge, k)
            if i % 3:
                c.set_source_rgba(0.95, 0.94, 0.92, 0.45 * P * (1 - k)); c.arc(x, y - 30 * k, 16 + 30 * k, 0, 2 * math.pi); c.fill()
            else:
                c.set_source_rgba(1, 0.65, 0.35, 0.55 * P * (1 - k)); c.set_line_width(5); c.set_line_cap(cairo.LINE_CAP_ROUND)
                c.move_to(x, y); c.curve_to(x + 15, y - 10, x + 30, y + 10, x + 48, y); c.stroke()
    x0 = WALL_R
    # locomotive body (facing left): smokebox front = right wall
    c.set_source_rgb(*rgb('#1c1c22')); c.rectangle(x0 + 40, 820, W - x0, GROUND - 820 - 60); c.fill()   # boiler side
    c.set_source_rgb(*rgb('#26262e')); rrect(c, x0, 900, 200, GROUND - 960, 26); c.fill()               # smokebox door
    c.set_source_rgb(*rgb('#3a3a44')); c.arc(x0 + 100, 1080, 70, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#26262e')); c.arc(x0 + 100, 1080, 56, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#8a8a94')); c.arc(x0 + 100, 1080, 10, 0, 2 * math.pi); c.fill()
    # headlamp
    c.set_source_rgb(*rgb('#2a2a30')); rrect(c, x0 + 70, 940, 60, 50, 10); c.fill()
    c.set_source_rgb(*rgb('#f0d28a')); c.arc(x0 + 100, 965, 16, 0, 2 * math.pi); c.fill()
    # chimney stack with smoke
    c.set_source_rgb(*rgb('#1c1c22')); c.rectangle(x0 + 120, 730, 70, 100); c.fill(); c.rectangle(x0 + 110, 720, 90, 22); c.fill()
    for i in range(4):
        k = (t * 0.55 + i / 4) % 1; c.set_source_rgba(0.5, 0.5, 0.56, 0.32 * (1 - k)); c.arc(x0 + 155 - 60 * k, 700 - 200 * k, 18 + 30 * k, 0, 2 * math.pi); c.fill()
    # red buffer beam + buffers
    c.set_source_rgb(*rgb('#8a2a24')); c.rectangle(x0 - 10, GROUND - 260, W - x0 + 10, 50); c.fill()
    c.set_source_rgb(*rgb('#3a3a44'))
    for yy in (GROUND - 250,): c.rectangle(x0 - 40, yy, 34, 30); c.fill()
    # steam cylinder low at the floor with the cock nozzle pointing left (where the blasts come from)
    c.set_source_rgb(*rgb('#2e2e36')); rrect(c, x0 - 6, GROUND - 200, 180, 130, 18); c.fill()
    c.set_source_rgb(*rgb('#44444e'))
    for xx in (x0 + 30, x0 + 90, x0 + 150): c.rectangle(xx, GROUND - 200, 6, 130); c.fill()
    g = min(1, P * 1.4)
    c.set_source_rgb(*rgb('#5a5a64')); c.rectangle(x0 - 30, GROUND - 100, 30, 22); c.fill()
    c.set_source_rgba(1, 0.6, 0.3, 0.6 * g); c.arc(x0 - 30, GROUND - 89, 10, 0, 2 * math.pi); c.fill()
    # big driving wheel (partly) with red spokes
    ang = t * 1.2
    c.set_source_rgb(*rgb('#8a2a24')); c.arc(x0 + 330, GROUND - 110, 110, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#1c1c22')); c.arc(x0 + 330, GROUND - 110, 90, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#8a2a24')); c.set_line_width(8)
    for k in range(6):
        a_ = ang + k * math.pi / 3; c.move_to(x0 + 330, GROUND - 110); c.line_to(x0 + 330 + 88 * math.cos(a_), GROUND - 110 + 88 * math.sin(a_)); c.stroke()
    # pressure gauge dial
    c.set_source_rgb(*rgb('#2a2a30')); c.arc(x0 + 100, 1250, 34, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#d8d4c0')); c.arc(x0 + 100, 1250, 27, 0, 2 * math.pi); c.fill()
    a = math.pi * (0.8 + 1.4 * min(1, 0.3 + P)); c.set_source_rgb(*rgb('#c0392b')); c.set_line_width(4)
    c.move_to(x0 + 100, 1250); c.line_to(x0 + 100 + 21 * math.cos(a), 1250 + 21 * math.sin(a)); c.stroke()

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
