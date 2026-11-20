"""2026-11-20 v1 — TEMPERATURE – FREEZE %: the ICE DRAGON. A frozen ice cave at night; an ice dragon's head pokes
out of the ice ledge on the right and breathes seeded-random frost blasts along the floor (reach + strength + length
vary). Gloop is a passive rigid ball (Ball) bouncing between a rock pillar with a fire bowl (left wall, warm) and
the ledge (right wall). Inside the blast FREEZE rises (faster deep in it), outside it thaws slowly — faster next to the
heater. The blasts also push him left a little. 100% = frozen solid in an ice cube."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the ice dragon'
SEED = int(os.environ.get('SEED', 1))
rng = random.Random(SEED)

class S: pass
S.HOOK2 = 'THE ICE DRAGON?'; S.HOOK2_SIZE = 96; S.FAIL_WORD = 'FROZEN!'; S.FAIL_SIZE = 150
S.T_START = HOOK_T; S.TL = float(os.environ.get('TL', 13.0)); S.T_END = S.T_START + S.TL
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
    if b['t'] < S.T_RES and b['s'] > 0.75: S.events.append([max(0, b['t']) + 0.2, 'wind_gust' if False else 'whoosh'])
for b in BL:
    if b['t'] < S.T_RES: S.events.append([max(0, b['t']), 'whoosh'])
for (tl, xl, imp) in ball.landings:
    if tl < S.T_RES: S.events.append([tl, 'hop'])
for tw in ball.walls:
    if tw < S.T_RES: S.events.append([tw, 'thump', 0.4])
if T_FAIL: S.events += [[T_FAIL, 'freeze'], [T_FAIL + 0.1, 'crackle']]
S.AMB = {'drone': 58, 'wind': 0.02}

def draw_bar(c, t, f):
    p = FRZ[f]; up = f > 0 and FRZ[f] > FRZ[f - 1]
    bx = bar(c, p / 100, f'FREEZE {int(p)}%', bad_col(p / 100), 0.12 if up else 0, bw=640, x_off=36)
    c.save(); c.translate(bx - 52, 231); c.set_source_rgb(*rgb('#9ad8ff')); c.set_line_width(6); c.set_line_cap(cairo.LINE_CAP_ROUND)   # snowflake icon
    for k in range(3):
        a = k * math.pi / 3; c.move_to(-26 * math.cos(a), -26 * math.sin(a)); c.line_to(26 * math.cos(a), 26 * math.sin(a)); c.stroke()
    c.restore()
S.draw_bar = draw_bar
ICIC = [(x, random.Random(x).uniform(40, 140)) for x in range(20, W, 70)]
def draw_bg(c, t):
    c.set_source_rgb(*rgb('#10162a')); c.rectangle(0, HEAD, W, H - HEAD); c.fill()
    # ice cave back wall: big faceted ice blocks
    for i, (x, y, w, h, col) in enumerate(((0, 520, 420, 700, '#1c2a44'), (380, 600, 380, 640, '#182440'), (700, 480, 420, 760, '#1e2c48'),
                                           (120, 900, 300, 500, '#22324e'), (560, 980, 320, 420, '#203050'))):
        c.set_source_rgb(*rgb(col)); c.move_to(x, y + 60); c.line_to(x + w * 0.4, y); c.line_to(x + w, y + 90); c.line_to(x + w, GROUND); c.line_to(x, GROUND); c.close_path(); c.fill()
        c.set_source_rgba(0.7, 0.85, 1, 0.06); c.move_to(x + w * 0.4, y); c.line_to(x + w * 0.55, GROUND); c.line_to(x + w * 0.4, GROUND); c.close_path(); c.fill()
    # cave mouth showing the night sky + moon
    c.set_source_rgb(*rgb('#0a1020')); c.save(); c.translate(500, 700); c.scale(170, 130); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    for i in range(12):
        sx = 380 + (i * 73) % 240; sy = 610 + (i * 41) % 170
        c.set_source_rgba(1, 1, 0.95, 0.3 + 0.25 * math.sin(t * 2 + i)); c.arc(sx, sy, 2.2, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#d8dccc')); c.arc(560, 660, 28, 0, 2 * math.pi); c.fill()
    # icicles hanging from the cave ceiling
    c.set_source_rgb(*rgb('#2a3c5a'))
    c.rectangle(0, HEAD, W, 120); c.fill()
    for (x, l) in ICIC:
        c.move_to(x - 22, HEAD + 118); c.line_to(x, HEAD + 118 + l); c.line_to(x + 22, HEAD + 118); c.close_path(); c.fill()
    # frozen floor with snow drifts
    c.set_source_rgb(*rgb('#2c3a52')); c.rectangle(0, GROUND, W, H - GROUND); c.fill()
    c.set_source_rgb(*rgb('#3a4a66')); c.rectangle(0, GROUND, W, 14); c.fill()
    c.set_source_rgba(1, 1, 1, 0.05)
    for yy in range(GROUND + 60, H, 70): c.rectangle(0, yy, W, 4); c.fill()
    # left wall: rock pillar with a crackling fire bowl (the warm side)
    c.set_source_rgb(*rgb('#3a3036')); c.rectangle(-20, 1050, WALL_L + 20, GROUND - 1050); c.fill()
    c.set_source_rgba(0, 0, 0, 0.22)
    for yy in range(1100, GROUND, 90): c.rectangle(-20, yy, WALL_L + 20, 5); c.fill()
    c.set_source_rgb(*rgb('#5a3a2a')); rrect(c, -10, 1010, WALL_L + 30, 50, 12); c.fill()     # bowl
    for k in range(5):
        fl = 0.6 + 0.4 * math.sin(t * 11 + k * 1.9)
        c.set_source_rgb(*rgb('#e8702a' if k % 2 else '#ffb04a'))
        x = 10 + k * 28; c.move_to(x - 16, 1012); c.line_to(x, 1012 - 80 * fl); c.line_to(x + 16, 1012); c.close_path(); c.fill()
    for i in range(4):   # warm shimmer
        k = (t * 0.5 + i / 4) % 1; c.set_source_rgba(1, 0.7, 0.4, 0.22 * (1 - k)); c.set_line_width(4)
        x = WALL_L + 6 + k * 70; y = 1150 + i * 110; c.move_to(x, y); c.curve_to(x + 15, y - 12, x + 30, y + 12, x + 45, y); c.stroke()

def draw_dryer(c, t, f):   # the ice dragon on the right + its frost breath along the floor
    P, reach = BP[f], BR[f]
    edge = WALL_R - reach
    if P > 0.03:
        for i in range(6):
            k = i / 5; y = GROUND - 60 - k * 380
            c.set_source_rgba(0.75, 0.9, 1.0, 0.13 * P * (1.2 - k))
            c.save(); c.translate(WALL_R - reach * 0.5, y); c.scale(reach * 0.55 + 30, 110 - k * 40); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
        c.set_line_width(4); c.set_line_cap(cairo.LINE_CAP_ROUND)
        for i in range(24):   # frost streaks + ice shards streaming left
            k = (t * (2.2 + P) + i / 24) % 1; y = GROUND - 50 - (i * 67) % 360 + 18 * math.sin(k * 6 + i)
            x = lerp(WALL_R - 30, edge, k)
            if i % 3:
                c.set_source_rgba(0.8, 0.95, 1, 0.45 * P * (1 - k * 0.8)); c.move_to(x, y); c.line_to(x + 46 + 30 * P, y); c.stroke()
            else:
                c.set_source_rgba(0.95, 0.99, 1, 0.75 * P * (1 - k * 0.8)); c.save(); c.translate(x, y); c.rotate(t * 4 + i)
                c.move_to(0, -9); c.line_to(6, 0); c.line_to(0, 9); c.line_to(-6, 0); c.close_path(); c.fill(); c.restore()
    # ice ledge = right wall, the dragon's head pokes out of a hole in it near the floor
    x0 = WALL_R
    c.set_source_rgb(*rgb('#5a7aa0')); c.move_to(x0, GROUND); c.line_to(x0, 1000); c.line_to(x0 + 60, 900); c.line_to(W + 20, 860); c.line_to(W + 20, GROUND); c.close_path(); c.fill()
    c.set_source_rgba(1, 1, 1, 0.08); c.move_to(x0 + 60, 900); c.line_to(x0 + 110, GROUND); c.line_to(x0 + 60, GROUND); c.close_path(); c.fill()
    # long neck going up behind the ledge, swaying
    sw = 10 * math.sin(t * 1.3)
    c.set_source_rgb(*rgb('#6a9ac8')); c.set_line_width(70); c.set_line_cap(cairo.LINE_CAP_ROUND)
    c.move_to(W + 40, 700); c.curve_to(W - 60 + sw, 760, W - 120 + sw, 820, x0 + 120 + sw, 930); c.stroke()
    c.set_source_rgb(*rgb('#d8ecff'))
    for k in range(5):   # back spikes
        u = k / 4; px = lerp(W + 10, x0 + 140, u) + sw * u; py = lerp(690, 900, u) - 34
        c.move_to(px - 12, py + 6); c.line_to(px, py - 24); c.line_to(px + 12, py + 6); c.close_path(); c.fill()
    # the head, low at the floor, facing left
    hx, hy = x0 + 40, GROUND - 120 + 4 * math.sin(t * 2); op = 0.15 + 0.85 * min(1, P * 1.3)
    c.set_source_rgb(*rgb('#6a9ac8')); c.set_line_width(80); c.move_to(x0 + 130 + sw, 950); c.curve_to(x0 + 160, 1100, x0 + 140, 1250, hx + 50, hy); c.stroke()
    c.save(); c.translate(hx, hy); c.scale(1.4, 1.4)
    c.set_source_rgb(*rgb('#6a9ac8')); rrect(c, -10, -90, 150, 120, 40); c.fill()            # skull
    c.set_source_rgb(*rgb('#7aaad6')); rrect(c, -10, -46, 60, 50, 18); c.fill()              # upper snout
    c.set_source_rgb(*rgb('#24304a')); c.move_to(-6, 4); c.line_to(60, 4); c.line_to(60, 4 + 70 * op); c.close_path(); c.fill()   # open mouth
    c.set_source_rgb(*rgb('#5a88b8')); c.save(); c.translate(60, 4); c.rotate(0.5 * op); rrect(c, -66, 0, 70, 26, 10); c.restore(); c.fill()   # jaw
    c.set_source_rgb(1, 1, 1)
    for k in range(3): c.move_to(4 + k * 18, 4); c.line_to(10 + k * 18, 18); c.line_to(16 + k * 18, 4); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#d8ecff'))   # horns
    c.move_to(70, -80); c.line_to(140, -150); c.line_to(100, -70); c.close_path(); c.fill()
    c.move_to(100, -70); c.line_to(170, -120); c.line_to(126, -56); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#bfe4ff')); c.save(); c.translate(48, -56); c.scale(18, 12 + 3 * op); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()   # eye
    c.set_source_rgb(*rgb('#10162a')); c.save(); c.translate(44, -56); c.scale(5, 10); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    c.set_source_rgb(*rgb('#3a5a80')); c.set_line_width(6); c.move_to(30, -78); c.line_to(66, -70); c.stroke()   # brow
    c.set_source_rgb(*rgb('#24304a')); c.arc(0, -30, 5, 0, 2 * math.pi); c.fill()   # nostril
    if P < 0.1:   # idle frosty puffs from the nostril
        for i in range(2):
            k = (t * 0.7 + i / 2) % 1; c.set_source_rgba(0.85, 0.95, 1, 0.3 * (1 - k)); c.arc(-10 - 30 * k, -40 - 40 * k, 8 + 12 * k, 0, 2 * math.pi); c.fill()
    c.restore()

STARS = [(random.Random(i * 7 + 1).uniform(0, W), random.Random(i).uniform(HEAD, 1000), 1.2 + (i % 3) * 0.6) for i in range(50)]

PS = Particles(9)
def render(f, c):
    t = f / FPS; fi = min(f, len(GX) - 1); P = BP[fi]
    c.save(); c.translate(rng.uniform(-1.5, 1.5) * P, 0)
    draw_bg(c, t)
    frozen = T_FAIL is not None and t >= T_FAIL
    p = FRZ[fi] / 100
    if END.carried(t) or t >= END.T_GRAB:
        gx, gy = (END.carry_xy(t) if END.carried(t) else S.GRAB)
    else:
        gx, gy = GX[fi], GYS[fi]
        if frozen: k = ease((t - T_FAIL) / 0.25); gy = lerp(GYS[int(T_FAIL * FPS)], GROUND - R, k)
        h = max(0, GROUND - R - gy); kk = 1 / (1 + h / 220)
        c.set_source_rgba(0, 0, 0, 0.25 * kk); c.save(); c.translate(gx, GROUND + 3); c.scale(R * (0.5 + 0.4 * kk), 9); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    mix = lambda a, b: '#%02x%02x%02x' % tuple(int(lerp(int(a[i:i + 2], 16), int(b[i:i + 2], 16), min(1, p) * 0.55)) for i in (1, 3, 5))
    skin = ('#ffd36b', '#ff8a1f', '#c45a00')
    mood = 'happy' if (t >= S.T_END and S.OUTCOME == 'win') else ('scared' if INB[fi] or frozen or p > 0.7 else 'worried')
    draw_dryer(c, t, fi)
    draw_blob(c, t, gx, gy, mood, 0, R=R, skin=skin, dizzy=frozen and t > END.T_GRAB - 0.3)
    fr = min(1, p) if not END.carried(t) else 0
    if fr > 0.05:   # frost layer over him
        c.set_source_rgba(0.78, 0.92, 1.0, 0.42 * fr); c.arc(gx, gy, R * 1.02, 0, 2 * math.pi); c.fill()
    # frozen in an ice cube after the fail; it cracks off just before the claw grabs
    if frozen and not END.carried(t):
        a_ = 1 - ease((t - (END.T_GRAB - 0.5)) / 0.3); gr = ease((t - T_FAIL) / 0.2)
        if a_ > 0.02:
            s_ = R * 1.35 * gr
            c.set_source_rgba(0.75, 0.9, 1.0, 0.45 * a_); rrect(c, gx - s_, gy - s_, 2 * s_, 2 * s_, 14); c.fill()
            c.set_source_rgba(0.92, 0.97, 1.0, 0.8 * a_); c.set_line_width(5); rrect(c, gx - s_, gy - s_, 2 * s_, 2 * s_, 14); c.stroke()
            c.set_source_rgba(1, 1, 1, 0.6 * a_); c.rectangle(gx - s_ + 14, gy - s_ + 12, s_ * 0.5, 10); c.fill()
        if abs(t - (END.T_GRAB - 0.5)) < 0.5 / FPS: PS.spawn(gx, gy, 18, (0.85, 0.95, 1.0), 420, 0.6, grav=1400, r=7)
    if not END.carried(t) and not frozen and p > 0.35 and f % 5 == 0:   # frost sparkles when cold
        PS.spawn(gx + rng.uniform(-40, 40), gy + rng.uniform(-40, 30), 1, (0.9, 0.97, 1.0), 60, 0.5, grav=0, r=5)
    if INB[fi] and f % 4 == 0 and not END.carried(t) and not frozen: PS.spawn(gx + rng.uniform(-30, 30), gy - R * 0.6, 1, (0.95, 0.98, 1.0), 110, 0.7, grav=300, r=7)
    PS.draw(c)
    END.draw_claw(c, t)
    c.restore()
    END.header(c, t, fi)

if __name__ == '__main__':
    if sys.argv[1] == 'sim':
        e = int(S.T_RES * FPS) - 1
        print(SEED, S.OUTCOME, round(S.T_RES - S.T_START, 2), 'peak', round(max(FRZ[:e + 1])), 'final', round(FRZ[e]), 'dur', S.DUR, [round(FRZ[min(e, int((S.T_START + k) * FPS))]) for k in range(13)]); sys.exit()
    run(S, render)
