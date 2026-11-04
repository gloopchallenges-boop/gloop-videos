"""2026-11-04 v2 — TEMPERATURE – FREEZE %: the GIANT FREEZER. A kitchen at night; a giant freezer stands
open on the right and blows seeded-random icy blasts along the floor (reach + strength + length vary).
Gloop is a passive rigid ball (Ball) bouncing between a warm radiator (left wall) and the freezer
(right wall). Inside the icy mist FREEZE rises (faster deep in it), outside it thaws slowly — faster
right next to the radiator. The blasts also blow him left a little. 100% = frozen solid in an ice cube."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the giant freezer'
SEED = int(os.environ.get('SEED', 6))
rng = random.Random(SEED)

class S: pass
S.HOOK2 = 'THE GIANT FREEZER?'; S.HOOK2_SIZE = 90; S.FAIL_WORD = 'FROZEN!'; S.FAIL_SIZE = 150
S.T_START = HOOK_T; S.TL = 13.5; S.T_END = S.T_START + S.TL
GROUND = 1600; R = 58; XMIN, XMAX = 200, 800; WALL_L, WALL_R = XMIN - R, XMAX + R
UP = float(os.environ.get('UP', 45)); DOWN = 9.0; BLOW = 260.0

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
    FXp = GX[int(T_FAIL * FPS)]; S.GRAB = (FXp, GROUND - 78)
else:
    gi = min(int(END.T_GRAB * FPS), N0 - 1); S.GRAB = (GX[gi], GYS[gi])
S.events = [[0.05, 'whoosh']]
for b in BL:
    if b['t'] < S.T_RES: S.events.append([max(0, b['t']), 'whoosh'])
for (tl, xl, imp) in ball.landings:
    if tl < S.T_RES: S.events.append([tl, 'hop'])
for tw in ball.walls:
    if tw < S.T_RES: S.events.append([tw, 'thump', 0.4])
if T_FAIL: S.events += [[T_FAIL, 'crackle'], [T_FAIL + 0.15, 'clink']]
S.AMB = {'drone': 60, 'wind': 0.02}

def draw_bar(c, t, f):
    p = FRZ[f]; up = f > 0 and FRZ[f] > FRZ[f - 1]
    bx = bar(c, p / 100, f'FREEZE {int(p)}%', rgb('#7fd4ff') if p < 50 else (rgb('#4aa8ff') if p < 80 else rgb('#2f6bff')), 0.12 if up else 0, bw=640, x_off=36)
    c.save(); c.translate(bx - 52, 231); c.set_source_rgb(*rgb('#bfe9ff')); c.set_line_width(7); c.set_line_cap(cairo.LINE_CAP_ROUND)
    for k in range(3):
        a = k * math.pi / 3; c.move_to(-26 * math.cos(a), -26 * math.sin(a)); c.line_to(26 * math.cos(a), 26 * math.sin(a)); c.stroke()
    c.restore()
S.draw_bar = draw_bar

def draw_bg(c, t):
    c.set_source_rgb(*rgb('#1e2230')); c.rectangle(0, HEAD, W, H - HEAD); c.fill()
    # tiles on the back wall
    c.set_source_rgba(1, 1, 1, 0.035); c.set_line_width(3)
    for yy in range(1000, GROUND, 70): c.move_to(0, yy); c.line_to(W, yy); c.stroke()
    for xx in range(0, W, 70): c.move_to(xx, 1000); c.line_to(xx, GROUND); c.stroke()
    # counter + cupboards up top
    c.set_source_rgb(*rgb('#2b2f40')); c.rectangle(0, 700, W, 300); c.fill()
    c.set_source_rgb(*rgb('#3a3f54')); c.rectangle(0, 990, W, 22); c.fill()
    c.set_source_rgb(*rgb('#24283a'))
    for x in range(40, 700, 220): rrect(c, x, 730, 190, 230, 10); c.fill()
    c.set_source_rgb(*rgb('#141826')); rrect(c, 300, 420, 300, 230, 10); c.fill()        # window
    c.set_source_rgb(*rgb('#cfd6e6')); c.arc(520, 480, 26, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#2b2f40')); c.set_line_width(12); rrect(c, 300, 420, 300, 230, 10); c.stroke(); c.move_to(450, 420); c.line_to(450, 650); c.stroke()
    # floor
    c.set_source_rgb(*rgb('#3b3a46')); c.rectangle(0, GROUND, W, H - GROUND); c.fill()
    c.set_source_rgba(0, 0, 0, 0.2)
    for i, yy in enumerate(range(GROUND, H, 80)):
        for x in range(80 * (i % 2), W, 160): c.rectangle(x, yy, 80, 80); c.fill()
    # radiator = left wall
    c.set_source_rgb(*rgb('#5a4a48')); c.rectangle(0, 1180, WALL_L, GROUND - 1180); c.fill()
    for x in range(12, int(WALL_L) - 10, 30):
        c.set_source_rgb(*rgb('#6f5a55')); rrect(c, x, 1195, 20, GROUND - 1215, 8); c.fill()
    c.set_source_rgba(1, 0.55, 0.2, 0.18 + 0.05 * math.sin(t * 3)); c.rectangle(0, 1180, WALL_L, GROUND - 1180); c.fill()
    for i in range(3):   # warm wavy lines
        k = (t * 0.6 + i / 3) % 1; c.set_source_rgba(1, 0.6, 0.3, 0.35 * (1 - k)); c.set_line_width(4)
        x = 30 + i * 35; y = 1170 - k * 120; c.move_to(x, y); c.curve_to(x + 12, y - 20, x - 12, y - 40, x, y - 60); c.stroke()

def draw_freezer(c, t, f):
    P, reach = BP[f], BR[f]
    if P > 0.03:   # icy mist sheet along the floor
        edge = WALL_R - reach
        for i in range(7):
            k = i / 6; y = GROUND - 30 - k * 420
            c.set_source_rgba(0.75, 0.9, 1, 0.07 * P * (1.2 - k))
            c.save(); c.translate(WALL_R - reach * 0.5, y); c.scale(reach * 0.55 + 30, 120 - k * 40); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
        c.set_line_width(5)
        for i in range(10):
            k = (t * (1.3 + P) + i / 10) % 1; y = GROUND - 40 - (i * 37) % 380
            x = lerp(WALL_R, edge, k); c.set_source_rgba(0.85, 0.95, 1, 0.5 * P * (1 - k))
            c.move_to(x + 70, y); c.line_to(x, y + 6 * math.sin(i)); c.stroke()
        for i in range(8):   # snowflakes flying left
            k = (t * (0.9 + P) + i * 0.13) % 1; x = lerp(WALL_R, edge, k); y = GROUND - 60 - (i * 53) % 400 + 20 * math.sin(t * 4 + i)
            c.set_source_rgba(1, 1, 1, 0.8 * P * (1 - k)); c.arc(x, y, 6, 0, 2 * math.pi); c.fill()
    # freezer body = right wall, door swung open to the right edge
    c.set_source_rgb(*rgb('#c9d1dd')); c.rectangle(WALL_R, 760, W - WALL_R, GROUND - 760); c.fill()
    c.set_source_rgb(*rgb('#9fd8ff')); c.rectangle(WALL_R, 820, 40, GROUND - 840); c.fill()
    c.set_source_rgba(0.8, 0.95, 1, 0.5 + 0.3 * P); c.rectangle(WALL_R + 40, 820, W - WALL_R - 60, GROUND - 840); c.fill()
    c.set_source_rgb(*rgb('#e4f4ff')); c.set_line_width(6)
    for yy in range(900, GROUND - 40, 140): c.move_to(WALL_R + 40, yy); c.line_to(W - 20, yy); c.stroke()
    c.set_source_rgb(*rgb('#a7b0be')); c.rectangle(WALL_R, 760, W - WALL_R, 40); c.fill()
    for x in range(int(WALL_R) + 10, W, 40):   # icicles on the top edge
        c.set_source_rgb(*rgb('#dff3ff')); c.move_to(x, 800); c.line_to(x + 16, 800); c.line_to(x + 8, 800 + 30 + (x * 7) % 25); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#3a5a7a')); c.arc(WALL_R + 70, 730, 12, 0, 2 * math.pi); c.fill()

PS = Particles(9)
def draw_ice(c, x, y, k):
    s = 150 * k
    c.set_source_rgba(0.75, 0.92, 1, 0.55); rrect(c, x - s / 2, y + R + 20 - s, s, s, 16); c.fill()
    c.set_source_rgba(1, 1, 1, 0.7); c.set_line_width(5); rrect(c, x - s / 2, y + R + 20 - s, s, s, 16); c.stroke()
    c.set_source_rgba(1, 1, 1, 0.6); c.move_to(x - s * 0.35, y + R + 20 - s * 0.85); c.line_to(x - s * 0.15, y + R + 20 - s * 0.85); c.line_to(x - s * 0.38, y + R + 20 - s * 0.45); c.close_path(); c.fill()

def render(f, c):
    t = f / FPS; fi = min(f, len(GX) - 1); P = BP[fi]
    c.save(); c.translate(rng.uniform(-1.5, 1.5) * P, 0)
    draw_bg(c, t)
    froze = T_FAIL is not None and t >= T_FAIL
    p = FRZ[fi] / 100
    if END.carried(t) or t >= END.T_GRAB:
        gx, gy = (END.carry_xy(t) if END.carried(t) else S.GRAB)
        if froze: gy += 0
    else:
        gx, gy = GX[fi], GYS[fi]
        if froze: k = ease((t - T_FAIL) / 0.35); gy = lerp(GYS[int(T_FAIL * FPS)], S.GRAB[1], k)
        h = max(0, GROUND - R - gy); kk = 1 / (1 + h / 220)
        c.set_source_rgba(0, 0, 0, 0.25 * kk); c.save(); c.translate(gx, GROUND + 3); c.scale(R * (0.5 + 0.4 * kk), 9); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    mix = lambda a, b: '#%02x%02x%02x' % tuple(int(lerp(int(a[i:i + 2], 16), int(b[i:i + 2], 16), min(1, p) * 0.55)) for i in (1, 3, 5))
    skin = (mix('#ffd36b', '#d8f0ff'), mix('#ff8a1f', '#7fb8e8'), mix('#c45a00', '#3f6f9a'))
    mood = 'happy' if (t >= S.T_END and S.OUTCOME == 'win') else ('scared' if INB[fi] or froze or p > 0.7 else 'worried')
    draw_freezer(c, t, fi)
    draw_blob(c, t, gx, gy, mood, 0, R=R, skin=skin, dizzy=froze and t > T_FAIL + 0.6)
    if froze: draw_ice(c, gx, gy, ease((t - T_FAIL) / 0.3))
    if INB[fi] and f % 5 == 0 and not END.carried(t): PS.spawn(gx + rng.uniform(-30, 30), gy - R * 0.5, 1, (0.9, 0.97, 1), 120, 0.6, grav=200, r=7)
    PS.draw(c)
    END.draw_claw(c, t)
    c.restore()
    END.header(c, t, fi)

if __name__ == '__main__':
    if sys.argv[1] == 'sim':
        e = int(S.T_RES * FPS) - 1
        print(SEED, S.OUTCOME, round(S.T_RES - S.T_START, 2), 'peak', round(max(FRZ[:e + 1])), 'final', round(FRZ[e]), 'dur', S.DUR); sys.exit()
    run(S, render)
