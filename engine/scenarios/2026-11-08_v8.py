"""2026-11-08 v8 — TEMPERATURE – FREEZE %: the SNOW CANNON. A ski slope at night; a snow cannon on a snowbank on
the right fires seeded-random blasts of snow along the ground (reach + strength + length vary). Gloop is a passive
rigid ball (Ball) bouncing between a log cabin with a campfire (left wall, warm) and the cannon (right wall).
Inside the blast FREEZE rises (faster deep in it), outside it thaws slowly — faster next to the campfire. The
blasts also push him left a little. 100% = frozen solid in an ice cube."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the snow cannon'
SEED = int(os.environ.get('SEED', 18))
rng = random.Random(SEED)

class S: pass
S.HOOK2 = 'THE SNOW CANNON?'; S.HOOK2_SIZE = 92; S.FAIL_WORD = 'FROZEN!'; S.FAIL_SIZE = 150
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
    if b['t'] < S.T_RES and b['s'] > 0.75: S.events.append([max(0, b['t']) + 0.2, 'wind_gust' if False else 'whoosh'])
for b in BL:
    if b['t'] < S.T_RES: S.events.append([max(0, b['t']), 'whoosh'])
for (tl, xl, imp) in ball.landings:
    if tl < S.T_RES: S.events.append([tl, 'hop'])
for tw in ball.walls:
    if tw < S.T_RES: S.events.append([tw, 'thump', 0.4])
if T_FAIL: S.events += [[T_FAIL, 'freeze'], [T_FAIL + 0.1, 'crackle']]
S.AMB = {'drone': 55, 'wind': 0.025}

def draw_bar(c, t, f):
    p = FRZ[f]; up = f > 0 and FRZ[f] > FRZ[f - 1]
    bx = bar(c, p / 100, f'FREEZE {int(p)}%', bad_col(p / 100), 0.12 if up else 0, bw=640, x_off=36)
    c.save(); c.translate(bx - 52, 231); c.set_source_rgb(*rgb('#9ad8ff')); c.set_line_width(6); c.set_line_cap(cairo.LINE_CAP_ROUND)   # snowflake icon
    for k in range(3):
        a = k * math.pi / 3; c.move_to(-26 * math.cos(a), -26 * math.sin(a)); c.line_to(26 * math.cos(a), 26 * math.sin(a)); c.stroke()
    c.restore()
S.draw_bar = draw_bar

FLAKES = [(random.Random(i * 3).uniform(0, W), random.Random(i * 5 + 2).uniform(0, 1), random.Random(i * 11).uniform(2, 4)) for i in range(40)]
def draw_bg(c, t):
    c.set_source_rgb(*rgb('#141a2c')); c.rectangle(0, HEAD, W, H - HEAD); c.fill()
    c.set_source_rgba(0.85, 0.88, 0.95, 0.45)
    for x, y, r in STARS: c.arc(x, y, r, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#d8d4c0')); c.arc(560, 540, 46, 0, 2 * math.pi); c.fill()   # moon
    # snowy mountains + pine silhouettes
    c.set_source_rgb(*rgb('#28304a')); c.move_to(0, 1240); c.line_to(0, 900); c.line_to(250, 700); c.line_to(480, 950); c.line_to(700, 760); c.line_to(1080, 1050); c.line_to(1080, 1240); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#6a7488')); c.move_to(250, 700); c.line_to(310, 750); c.line_to(270, 760); c.line_to(230, 740); c.line_to(200, 742); c.close_path(); c.fill()
    c.move_to(700, 760); c.line_to(770, 812); c.line_to(720, 820); c.line_to(660, 795); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#1a2236'))
    for (x, h_) in ((300, 200), (380, 260), (460, 180), (620, 240), (700, 190)):
        c.move_to(x, 1250 - h_); c.line_to(x + 55, 1250); c.line_to(x - 55, 1250); c.close_path(); c.fill()
    # ski-lift cable + chair silhouette
    c.set_source_rgb(*rgb('#2a3044')); c.set_line_width(3); c.move_to(0, 760); c.line_to(W, 640); c.stroke()
    cx = (t * 40) % (W + 200) - 100; cy = 760 - cx * 120 / W
    c.set_line_width(4); c.move_to(cx, cy); c.line_to(cx, cy + 60); c.stroke(); c.rectangle(cx - 30, cy + 60, 60, 10); c.fill()
    # snow field
    c.set_source_rgb(*rgb('#4a5468')); c.rectangle(0, 1240, W, GROUND - 1240); c.fill()
    c.set_source_rgb(*rgb('#5a6478')); c.rectangle(0, GROUND, W, H - GROUND); c.fill()
    c.set_source_rgba(0, 0, 0, 0.12); c.set_line_width(4)
    for yy in range(GROUND + 60, H, 90): c.move_to(0, yy); c.curve_to(300, yy - 20, 700, yy + 20, W, yy - 10); c.stroke()
    for (x, y0, r) in FLAKES:   # gentle falling snow
        y = HEAD + ((y0 + t * 0.06 * r) % 1) * (H - HEAD); c.set_source_rgba(1, 1, 1, 0.5); c.arc(x + 10 * math.sin(t + y0 * 9), y, r, 0, 2 * math.pi); c.fill()
    # log cabin wall = left wall, with a warm campfire in front of it
    c.set_source_rgb(*rgb('#5a3e2a')); c.rectangle(-20, 1040, WALL_L + 20, GROUND - 1040); c.fill()
    c.set_source_rgb(*rgb('#4a3222'))
    for yy in range(1040, GROUND, 44): c.rectangle(-20, yy, WALL_L + 20, 8); c.fill()
    c.set_source_rgb(*rgb('#8a94a8')); rrect(c, -30, 1010, WALL_L + 50, 44, 20); c.fill()   # snow on top
    c.set_source_rgb(*rgb('#c9a45a')); c.rectangle(30, 1120, 70, 70); c.fill()   # lit window
    c.set_source_rgb(*rgb('#4a3222')); c.set_line_width(6); c.move_to(65, 1120); c.line_to(65, 1190); c.stroke()
    fx = XMIN - 10
    c.set_source_rgb(*rgb('#4a3020')); c.save(); c.translate(fx, GROUND - 8); c.rotate(0.3); c.rectangle(-50, -9, 100, 18); c.restore(); c.fill()
    c.save(); c.translate(fx, GROUND - 8); c.rotate(-0.3); c.rectangle(-50, -9, 100, 18); c.restore(); c.fill()
    for (dx, h_, col) in ((-18, 70, '#e8702a'), (16, 56, '#e8902a'), (0, 90, '#f0a83a'), (0, 44, '#f8d06a')):
        fl = h_ * (1 + 0.15 * math.sin(t * 11 + dx))
        c.set_source_rgb(*rgb(col)); c.move_to(fx + dx - 20, GROUND - 14); c.curve_to(fx + dx - 22, GROUND - 14 - fl * 0.5, fx + dx - 4, GROUND - 14 - fl * 0.8, fx + dx + 2 * math.sin(t * 7), GROUND - 14 - fl)
        c.curve_to(fx + dx + 4, GROUND - 14 - fl * 0.8, fx + dx + 22, GROUND - 14 - fl * 0.5, fx + dx + 20, GROUND - 14); c.close_path(); c.fill()

def draw_dryer(c, t, f):   # the snow cannon on the right + its blast of snow along the ground
    P, reach = BP[f], BR[f]
    edge = WALL_R - reach
    if P > 0.03:
        for i in range(6):
            k = i / 5; y = GROUND - 60 - k * 380
            c.set_source_rgba(0.85, 0.92, 1.0, 0.12 * P * (1.2 - k))
            c.save(); c.translate(WALL_R - reach * 0.5, y); c.scale(reach * 0.55 + 30, 110 - k * 40); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
        for i in range(26):   # snow pellets streaming left
            k = (t * (2.2 + P) + i / 26) % 1; y = GROUND - 40 - (i * 67) % 380 + 30 * k
            x = lerp(WALL_R - 20, edge, k); r = (5 + 8 * k) * (0.5 + 0.5 * P)
            c.set_source_rgba(0.95, 0.98, 1, 0.85 * P * (1 - k * 0.7)); c.arc(x, y, r, 0, 2 * math.pi); c.fill()
    # snowbank + cannon = right wall
    x0 = WALL_R
    c.set_source_rgb(*rgb('#6a7488')); c.move_to(x0, GROUND); c.curve_to(x0, 1300, W - 60, 1260, W, 1250); c.line_to(W, GROUND); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#6a7488')); c.rectangle(x0, 1300, W - x0, GROUND - 1300); c.fill()
    c.set_source_rgb(*rgb('#3a3f4a')); c.set_line_width(14)
    c.move_to(x0 + 150, GROUND - 40); c.line_to(x0 + 150, 1340); c.stroke()   # tripod mast
    c.move_to(x0 + 100, GROUND - 20); c.line_to(x0 + 150, 1400); c.stroke(); c.move_to(x0 + 200, GROUND - 20); c.line_to(x0 + 150, 1400); c.stroke()
    rec = 6 * P * math.sin(t * 30)
    c.save(); c.translate(x0 + 150 + rec, 1330); c.rotate(-0.1); c.scale(0.75, 0.75)
    c.set_source_rgb(*rgb('#d8b02a')); rrect(c, -150, -70, 230, 140, 30); c.fill()   # fan housing
    c.set_source_rgb(*rgb('#2a2e36')); c.arc(-150, 0, 72, 0, 2 * math.pi); c.fill()   # muzzle (faces left)
    c.set_source_rgb(*rgb('#55606e'))
    for k in range(5):
        a = t * (2 + 25 * P) + k * 2 * math.pi / 5; c.save(); c.translate(-150, 0); c.rotate(a); c.save(); c.scale(56, 14); c.arc(0.5, 0, 1, 0, 2 * math.pi); c.restore(); c.fill(); c.restore()
    c.set_source_rgb(*rgb('#1a1a1a')); c.arc(-150, 0, 12, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#b08a1a')); c.rectangle(-60, -70, 16, 140); c.fill()
    on = P > 0.05
    c.set_source_rgb(*(rgb('#5ad0ff') if on else rgb('#2a4a5a'))); c.arc(40, -40, 10, 0, 2 * math.pi); c.fill()
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
