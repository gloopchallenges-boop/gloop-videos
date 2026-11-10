"""2026-11-10 v4 — TEMPERATURE – FREEZE %: the NITROGEN TANK. A science lab at night; a big liquid-nitrogen tank
on the right sprays seeded-random blasts of freezing mist along the floor (reach + strength + length vary). Gloop
is a passive rigid ball (Ball) bouncing between a lab bench with a glowing space heater (left wall, warm) and the
tank (right wall). Inside the blast FREEZE rises (faster deep in it), outside it thaws slowly — faster next to
the heater. The blasts also push him left a little. 100% = frozen solid in an ice cube."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the nitrogen tank'
SEED = int(os.environ.get('SEED', 18))
rng = random.Random(SEED)

class S: pass
S.HOOK2 = 'THE NITROGEN TANK?'; S.HOOK2_SIZE = 86; S.FAIL_WORD = 'FROZEN!'; S.FAIL_SIZE = 150
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
S.AMB = {'drone': 58, 'wind': 0.02}

def draw_bar(c, t, f):
    p = FRZ[f]; up = f > 0 and FRZ[f] > FRZ[f - 1]
    bx = bar(c, p / 100, f'FREEZE {int(p)}%', bad_col(p / 100), 0.12 if up else 0, bw=640, x_off=36)
    c.save(); c.translate(bx - 52, 231); c.set_source_rgb(*rgb('#9ad8ff')); c.set_line_width(6); c.set_line_cap(cairo.LINE_CAP_ROUND)   # snowflake icon
    for k in range(3):
        a = k * math.pi / 3; c.move_to(-26 * math.cos(a), -26 * math.sin(a)); c.line_to(26 * math.cos(a), 26 * math.sin(a)); c.stroke()
    c.restore()
S.draw_bar = draw_bar

def draw_bg(c, t):
    c.set_source_rgb(*rgb('#161a24')); c.rectangle(0, HEAD, W, H - HEAD); c.fill()
    # tiled lab wall
    c.set_source_rgb(*rgb('#1e2430')); c.rectangle(0, 560, W, GROUND - 560); c.fill()
    c.set_source_rgba(0, 0, 0, 0.18)
    for yy in range(560, GROUND, 60): c.rectangle(0, yy, W, 3); c.fill()
    for xx in range(0, W, 60): c.rectangle(xx, 560, 3, GROUND - 560); c.fill()
    # window with moon
    c.set_source_rgb(*rgb('#2a3450')); c.rectangle(380, 640, 320, 240); c.fill()
    c.set_source_rgb(*rgb('#d8d4c0')); c.arc(620, 710, 34, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#3a4050')); c.set_line_width(12); c.rectangle(380, 640, 320, 240); c.stroke(); c.move_to(540, 640); c.line_to(540, 880); c.stroke()
    # shelf with flasks (silhouettes + soft colors)
    c.set_source_rgb(*rgb('#2c3240')); c.rectangle(260, 1000, 520, 16); c.fill()
    for (x, col, h_) in ((300, '#3a7a5a', 70), (380, '#7a4a8a', 90), (470, '#8a7a3a', 60), (560, '#3a6a8a', 80), (660, '#8a4a4a', 70), (730, '#4a7a7a', 56)):
        c.set_source_rgb(*rgb('#3a4250')); c.rectangle(x - 8, 1000 - h_, 16, h_ * 0.4); c.fill()
        c.set_source_rgb(*rgb(col)); c.move_to(x - 8, 1000 - h_ * 0.6); c.line_to(x - 26, 1000); c.line_to(x + 26, 1000); c.line_to(x + 8, 1000 - h_ * 0.6); c.close_path(); c.fill()
    # clock
    c.set_source_rgb(*rgb('#2c3240')); c.arc(200, 760, 50, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#c8ccd4')); c.arc(200, 760, 40, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#1a1a1a')); c.set_line_width(5); c.move_to(200, 760); c.line_to(200, 732); c.stroke(); c.move_to(200, 760); c.line_to(222, 768); c.stroke()
    # floor
    c.set_source_rgb(*rgb('#3a4048')); c.rectangle(0, GROUND, W, H - GROUND); c.fill()
    c.set_source_rgba(0, 0, 0, 0.15)
    for j, yy in enumerate(range(GROUND, H, 80)):
        c.rectangle(0, yy, W, 3); c.fill()
        for xx in range((j % 2) * 80, W, 160): c.rectangle(xx, yy, 3, 80); c.fill()
    # lab bench = left wall, with a glowing space heater in front
    c.set_source_rgb(*rgb('#4a5260')); c.rectangle(-20, 1180, WALL_L + 20, GROUND - 1180); c.fill()
    c.set_source_rgb(*rgb('#2a2e36')); c.rectangle(-20, 1160, WALL_L + 34, 26); c.fill()
    c.set_source_rgb(*rgb('#3a404c'))
    for yy in (1240, 1400): rrect(c, 10, yy, WALL_L - 30, 130, 6); c.fill()
    c.set_source_rgb(*rgb('#8a8f9a'))
    for yy in (1300, 1460): c.rectangle(50, yy, 40, 8); c.fill()
    c.set_source_rgb(*rgb('#3a7a5a')); c.move_to(60, 1160); c.line_to(40, 1110); c.line_to(80, 1110); c.close_path(); c.fill()   # beaker on bench
    hx = XMIN - 12
    c.set_source_rgb(*rgb('#3a3e46')); rrect(c, hx - 36, GROUND - 150, 72, 150, 10); c.fill()
    for k in range(4):
        g = 0.75 + 0.25 * math.sin(t * 5 + k)
        c.set_source_rgb(0.9 * g + 0.1, 0.42 * g, 0.12); rrect(c, hx - 24, GROUND - 136 + k * 30, 48, 12, 6); c.fill()

def draw_dryer(c, t, f):   # the nitrogen tank on the right + its blast of freezing mist along the floor
    P, reach = BP[f], BR[f]
    edge = WALL_R - reach
    if P > 0.03:
        for i in range(6):
            k = i / 5; y = GROUND - 60 - k * 380
            c.set_source_rgba(0.85, 0.92, 1.0, 0.12 * P * (1.2 - k))
            c.save(); c.translate(WALL_R - reach * 0.5, y); c.scale(reach * 0.55 + 30, 110 - k * 40); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
        for i in range(26):   # mist puffs streaming left
            k = (t * (2.2 + P) + i / 26) % 1; y = GROUND - 40 - (i * 67) % 380 + 30 * k
            x = lerp(WALL_R - 20, edge, k); r = (8 + 16 * k) * (0.5 + 0.5 * P)
            c.set_source_rgba(0.9, 0.95, 1, 0.5 * P * (1 - k * 0.8)); c.arc(x, y, r, 0, 2 * math.pi); c.fill()
    # nitrogen tank = right wall
    x0 = WALL_R; cx = (x0 + W) / 2 + 30
    c.set_source_rgb(*rgb('#8a9aaa')); rrect(c, x0, 960, W - x0 + 60, GROUND - 960, 60); c.fill()
    c.set_source_rgb(*rgb('#6a7a8a')); c.rectangle(x0, 1100, W - x0, 20); c.fill(); c.rectangle(x0, 1460, W - x0, 20); c.fill()
    c.set_source_rgb(*rgb('#2a5aa0')); c.rectangle(x0 + 20, 1200, W - x0 - 20, 150); c.fill()
    text_at(c, 'N2', cx, 1275, 70, (1, 1, 1), lw=0)
    c.set_source_rgb(*rgb('#5a6a7a')); c.rectangle(cx - 16, 900, 32, 60); c.fill()
    c.set_source_rgb(*rgb('#3a4250')); c.arc(cx, 900, 26, 0, 2 * math.pi); c.fill()   # valve wheel
    # gauge
    c.set_source_rgb(*rgb('#e8e8e8')); c.arc(x0 + 50, 1040, 26, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#c03030')); c.set_line_width(4); a = -2.2 + 2.6 * P; c.move_to(x0 + 50, 1040); c.line_to(x0 + 50 + 20 * math.cos(a), 1040 + 20 * math.sin(a)); c.stroke()
    # nozzle pipe facing left near the floor
    rec = 4 * P * math.sin(t * 30)
    c.set_source_rgb(*rgb('#5a6470')); rrect(c, x0 - 70 + rec, GROUND - 110, 90, 50, 10); c.fill()
    c.set_source_rgb(*rgb('#2a2e36')); c.save(); c.translate(x0 - 70 + rec, GROUND - 85); c.scale(12, 25); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    on = P > 0.05
    c.set_source_rgb(*(rgb('#5ad0ff') if on else rgb('#2a4a5a'))); c.arc(x0 + 40, 1160, 10, 0, 2 * math.pi); c.fill()

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
