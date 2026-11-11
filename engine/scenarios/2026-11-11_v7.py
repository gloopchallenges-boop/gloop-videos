"""2026-11-11 v7 — TEMPERATURE – FREEZE %: the GIANT AIR CONDITIONER. An empty office at night; a giant AC unit
on the right blasts seeded-random gusts of icy air along the floor (reach + strength + length vary). Gloop is a
passive rigid ball (Ball) bouncing between an office desk with a glowing space heater (left wall, warm) and the
AC (right wall). Inside the blast FREEZE rises (faster deep in it), outside it thaws slowly — faster next to the
heater. The blasts also push him left a little. 100% = frozen solid in an ice cube."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the giant air conditioner'
SEED = int(os.environ.get('SEED', 2))
rng = random.Random(SEED)

class S: pass
S.HOOK2 = 'THE GIANT AIR CONDITIONER?'; S.HOOK2_SIZE = 66; S.FAIL_WORD = 'FROZEN!'; S.FAIL_SIZE = 150
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
    # office wall
    c.set_source_rgb(*rgb('#22262e')); c.rectangle(0, 560, W, GROUND - 560); c.fill()
    c.set_source_rgba(0, 0, 0, 0.15)
    for xx in range(0, W, 140): c.rectangle(xx, 560, 3, GROUND - 560); c.fill()
    # big window with the city skyline + moon
    c.set_source_rgb(*rgb('#141c30')); c.rectangle(240, 620, 560, 360); c.fill()
    c.set_source_rgb(*rgb('#d8d4c0')); c.arc(700, 690, 32, 0, 2 * math.pi); c.fill()
    for (bx, bw, bh) in ((250, 70, 160), (330, 50, 230), (390, 90, 130), (490, 60, 260), (560, 80, 180), (650, 50, 140), (710, 80, 210)):
        c.set_source_rgb(*rgb('#1e2638')); c.rectangle(bx, 980 - bh, bw, bh); c.fill()
        c.set_source_rgba(1, 0.85, 0.5, 0.35)
        for wy in range(int(980 - bh + 16), 970, 34):
            for wx in range(int(bx + 10), int(bx + bw - 10), 20):
                if (wx * 7 + wy * 3) % 5 == 0: c.rectangle(wx, wy, 8, 12); c.fill()
    c.set_source_rgb(*rgb('#3a404c')); c.set_line_width(12); c.rectangle(240, 620, 560, 360); c.stroke(); c.move_to(520, 620); c.line_to(520, 980); c.stroke()
    
    c.set_source_rgb(*rgb('#3a404c')); rrect(c, 390, GROUND - 170, 70, 170, 8); c.fill()
    c.set_source_rgba(0.5, 0.7, 0.9, 0.5); rrect(c, 398, GROUND - 260, 54, 90, 20); c.fill()
    # clock
    c.set_source_rgb(*rgb('#2c3240')); c.arc(150, 760, 50, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#c8ccd4')); c.arc(150, 760, 40, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#1a1a1a')); c.set_line_width(5); c.move_to(150, 760); c.line_to(150, 732); c.stroke(); c.move_to(150, 760); c.line_to(172, 768); c.stroke()
    # carpet-tile floor
    c.set_source_rgb(*rgb('#363c48')); c.rectangle(0, GROUND, W, H - GROUND); c.fill()
    c.set_source_rgba(0, 0, 0, 0.15)
    for j, yy in enumerate(range(GROUND, H, 100)):
        c.rectangle(0, yy, W, 3); c.fill()
        for xx in range(0, W, 100): c.rectangle(xx, yy, 3, 100); c.fill()
    # office desk with a monitor = left wall, glowing space heater in front
    c.set_source_rgb(*rgb('#5a4a3a')); c.rectangle(-20, 1180, WALL_L + 20, GROUND - 1180); c.fill()
    c.set_source_rgb(*rgb('#3a2e24')); c.rectangle(-20, 1160, WALL_L + 34, 26); c.fill()
    c.set_source_rgb(*rgb('#4a3c2e'))
    for yy in (1240, 1400): rrect(c, 10, yy, WALL_L - 30, 130, 6); c.fill()
    c.set_source_rgb(*rgb('#8a8f9a'))
    for yy in (1300, 1460): c.rectangle(50, yy, 40, 8); c.fill()
    c.set_source_rgb(*rgb('#1a1c22')); rrect(c, 20, 1040, 100, 70, 6); c.fill(); c.rectangle(64, 1110, 12, 50); c.fill()   # monitor
    c.set_source_rgba(0.4, 0.6, 0.9, 0.35); c.rectangle(28, 1048, 84, 54); c.fill()
    hx = XMIN - 12
    c.set_source_rgb(*rgb('#3a3e46')); rrect(c, hx - 36, GROUND - 150, 72, 150, 10); c.fill()
    for k in range(4):
        g = 0.75 + 0.25 * math.sin(t * 5 + k)
        c.set_source_rgb(0.9 * g + 0.1, 0.42 * g, 0.12); rrect(c, hx - 24, GROUND - 136 + k * 30, 48, 12, 6); c.fill()

def draw_dryer(c, t, f):   # the giant air conditioner on the right + its blast of icy air along the floor
    P, reach = BP[f], BR[f]
    edge = WALL_R - reach
    if P > 0.03:
        for i in range(6):
            k = i / 5; y = GROUND - 60 - k * 380
            c.set_source_rgba(0.8, 0.92, 1.0, 0.12 * P * (1.2 - k))
            c.save(); c.translate(WALL_R - reach * 0.5, y); c.scale(reach * 0.55 + 30, 110 - k * 40); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
        c.set_line_width(4); c.set_line_cap(cairo.LINE_CAP_ROUND)
        for i in range(22):   # icy wind streaks + snowflakes streaming left
            k = (t * (2.4 + P) + i / 22) % 1; y = GROUND - 40 - (i * 67) % 380 + 20 * math.sin(k * 6 + i)
            x = lerp(WALL_R - 20, edge, k)
            if i % 3:
                c.set_source_rgba(0.85, 0.95, 1, 0.45 * P * (1 - k * 0.8)); c.move_to(x, y); c.line_to(x + 50 + 30 * P, y); c.stroke()
            else:
                c.set_source_rgba(0.95, 0.98, 1, 0.7 * P * (1 - k * 0.8)); c.arc(x, y, 6, 0, 2 * math.pi); c.fill()
    # giant air conditioner = right wall
    x0 = WALL_R; cx = (x0 + W) / 2 + 30
    c.set_source_rgb(*rgb('#c8ccd2')); rrect(c, x0, 960, W - x0 + 60, GROUND - 960, 30); c.fill()
    c.set_source_rgb(*rgb('#a8aeb6')); c.rectangle(x0, 1060, W - x0, 14); c.fill()
    c.set_source_rgb(*rgb('#8a9098'))
    for yy in range(1110, 1440, 26): c.rectangle(x0 + 20, yy, W - x0 - 20, 10); c.fill()   # intake grille
    c.set_source_rgb(*rgb('#2a2e36')); rrect(c, x0 + 26, 990, 80, 44, 6); c.fill()   # display
    temp = int(round(lerp(18, -12, P)))
    text_at(c, f'{temp}°', x0 + 66, 1012, 34, rgb('#5ad0ff'), lw=0)
    # outlet louvers facing left near the floor (flap with the blast)
    c.set_source_rgb(*rgb('#9aa0a8')); rrect(c, x0 - 40, GROUND - 160, 60, 150, 8); c.fill()
    c.set_source_rgb(*rgb('#4a5058')); c.set_line_width(6)
    for k in range(5):
        yy = GROUND - 145 + k * 28; a = 0.35 * P * math.sin(t * 20 + k) + 0.3 * P
        c.move_to(x0 - 36, yy); c.line_to(x0 - 36 - 22 * math.cos(a), yy + 22 * math.sin(a)); c.stroke()
    on = P > 0.05
    c.set_source_rgb(*(rgb('#5ad0ff') if on else rgb('#2a4a5a'))); c.arc(x0 + 130, 1012, 10, 0, 2 * math.pi); c.fill()


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
