"""2026-11-27 v3 — FALLING OBJECT ABOVE – CHAIN 6 LINKS: the GIANT PUNCHING BAG (based on 2026-11-22 v1 cheese wheel).
In an old boxing gym at night a huge heavy punching bag hangs from the ceiling girder on a 6-link chain. Gloop is a passive
rigid ball (Ball) bouncing on the wooden gym floor between a stack of gym mats and a stack of old tires. Every landing
shakes the floor (strain + a random swing kick), seeded draughts kick it, and the pendulum swing itself strains the chain.
Strain past a seeded threshold pops a link (bag jerks lower). 0 links = it falls with real gravity from wherever it has
swung to; it only hurts Gloop if it actually touches him (swept check). Timer ends first = win."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the giant punching bag'
SEED = int(os.environ.get('SEED', 17))
rng = random.Random(SEED)

class S: pass
S.HOOK2 = 'THE GIANT PUNCHING BAG?'; S.HOOK2_SIZE = 72; S.FAIL_WORD = 'THUD!'; S.FAIL_SIZE = 160
S.T_START = HOOK_T; S.TL = float(os.environ.get('TL', 12.0)); S.T_END = S.T_START + S.TL
GROUND = 1600; R = 58; XMIN, XMAX = 175, 905
NLINK = 6; LINK = 40; CEIL = 430; CX = 540; PIV = (CX, CEIL)
STR = float(os.environ.get('STR', 1.5))
THR = [rng.uniform(9, 20) for _ in range(NLINK)]
JOLTS = []; tt = 0.4
while tt < 40: JOLTS.append((tt, rng.uniform(2, 6), rng.choice((-1, 1)) * rng.uniform(0.15, 0.4))); tt += rng.uniform(1.2, 2.8)

TER = Terrain(GROUND, seed=SEED, bumps=3, amp=6, soft=False)
ball = Ball(rng.uniform(220, 860), TER, R=R, seed=SEED, xmin=XMIN, xmax=XMAX)
BR_ = 95
def body_circles(x, ytop): return [(x, ytop + 30, 26), (x, ytop + 150, BR_), (x, ytop + 265, BR_)]

N0 = int(40 * FPS)
th, om = rng.uniform(-0.08, 0.08), 0.0
links = NLINK; strain = 0.0; POPS = []; T_DROP = None; T_FAIL = None; T_LAND = None
fx = fy = 0.0; fvy = 0.0; nl = 0; ji = 0
GX, GYS, CHX, CHY, CTH, LK, STRN = [], [], [], [], [], [], []
CONTACT = None
for f in range(N0):
    t = f / FPS; live = S.T_START <= t < S.T_END and T_FAIL is None
    nl0 = len(ball.landings)
    ball.step(t)
    for (tl, xl, imp) in ball.landings[nl0:]:
        k = min(1.0, imp / 1500)
        om += rng.choice((-1, 1)) * 0.25 * k
        if live and T_DROP is None: strain += 1.6 * k * STR
    while ji < len(JOLTS) and JOLTS[ji][0] <= t:
        om += JOLTS[ji][2]
        if live and T_DROP is None: strain += JOLTS[ji][1] * STR * 0.6
        ji += 1
    HL = NLINK * LINK + 30 + 16 * (NLINK - links)   # each popped link lets it slip lower
    Lp = HL + 70
    if T_DROP is None:
        om += (-3200 / max(200, Lp * 1.6) * math.sin(th)) / FPS; om *= (1 - 0.35 / FPS); th += om / FPS
        if live: strain += 10 * abs(om) * STR / FPS
        if links > 0 and strain >= THR[NLINK - links] and live:
            strain -= THR[NLINK - links]; links -= 1; POPS.append(t); om += rng.choice((-1, 1)) * 0.12
            if links == 0:
                T_DROP = t; fx = CX + math.sin(th) * HL; fy = CEIL + HL * math.cos(th); fvy = 0
    HL = NLINK * LINK + 30 + 16 * (NLINK - links)
    chx = CX + math.sin(th) * HL; chy = CEIL + HL * math.cos(th)
    if T_DROP is not None and T_LAND is None:
        py = fy; fvy += 3200 / FPS; fy += fvy / FPS
        rest = GROUND - 360 + 8
        for k in range(1, 9):   # swept check vs Gloop
            yy = lerp(py, fy, k / 8)
            for (cx, cy, r) in body_circles(fx, yy):
                if CONTACT is None and math.hypot(ball.x - cx, ball.y - cy) < r + R * 0.95:
                    CONTACT = (t, ball.x, ball.y)
                    if S.T_START <= t < S.T_END: T_FAIL = t; FX, FY = ball.x, ball.y
        if fy >= rest:
            fy = rest; T_LAND = t
            if T_FAIL is None and abs(ball.x - fx) < 380 and ball.height() < 25:
                kk = 1 - abs(ball.x - fx) / 380; ball.push(math.copysign(360 * kk, ball.x - fx), -380 * kk)
        chx, chy = fx, fy
    elif T_LAND is not None: chx, chy = fx, fy
    if T_FAIL is not None: ball.frozen = True
    GX.append(ball.x); GYS.append(ball.y); CHX.append(chx); CHY.append(chy); CTH.append(th if T_DROP is None else 0.0)
    LK.append(links); STRN.append(strain)
S.OUTCOME = 'fail' if T_FAIL else 'win'
S.T_RES = T_FAIL if T_FAIL else S.T_END
if T_FAIL:   # squashed, then squirts out to the side of the ball
    sg = 1 if FX >= fx else -1; SX = fx + sg * (BR_ + R + 8)
    if not (XMIN <= SX <= XMAX): sg = -sg; SX = fx + sg * (BR_ + R + 8)
    S.GRAB = (SX, GROUND - R - 40)
else: S.GRAB = (540, GROUND - R)
END = S.END = Ending(S)
if not T_FAIL: gi = min(int(END.T_GRAB * FPS), N0 - 1); S.GRAB = (GX[gi], GYS[gi])
S.events = []
for p in POPS:
    if p <= S.T_RES + 0.01: S.events += [[p, 'clink'], [p + 0.02, 'thump', 0.35]]
for (tj, a, kk) in JOLTS:
    if 0.3 < tj < S.T_RES: S.events.append([tj, 'creak'])
for (tl, xl, imp) in ball.landings:
    if tl < S.T_RES: S.events.append([tl, 'hop'])
for tw in ball.walls:
    if tw < S.T_RES: S.events.append([tw, 'thump', 0.4])
if T_DROP and T_DROP < S.T_RES + 0.5: S.events.append([T_DROP, 'whoosh'])
if T_LAND and T_LAND < S.T_RES + 0.6: S.events += [[T_LAND, 'crash'], [T_LAND + 0.02, 'clang']]
if T_FAIL: S.events += [[T_FAIL, 'crash'], [T_FAIL + 0.05, 'clang'], [T_FAIL + 0.6, 'clang']]
S.AMB = {'drone': 44, 'wind': 0.015}

def link_icon(c, x, y, ok, pop):
    c.save(); c.translate(x, y); c.rotate(0.5); c.scale(1 + pop, 1 + pop)
    c.set_line_width(12); c.set_source_rgb(0, 0, 0); rrect(c, -30, -16, 60, 32, 16); c.stroke()
    c.set_line_width(7); c.set_source_rgb(*(rgb('#d7dde8') if ok else rgb('#4a4458'))); rrect(c, -30, -16, 60, 32, 16); c.stroke()
    c.restore()
def draw_bar(c, t, f):
    n = LK[f]; last = [p for p in POPS if p <= t]
    pop = max(0, 1 - (t - last[-1]) / 0.3) if last else 0
    for i in range(NLINK):
        link_icon(c, 190 + i * 70, 232, i < n, 0.4 * pop if i == n else 0)
    col = rgb('#7dff8a') if n > 3 else (rgb('#ffd84a') if n > 1 else rgb('#ff4d4d'))
    text_at(c, f'CHAIN: {n}', 790, 232, 54, col, 1 + 0.2 * pop, lw=9)
S.draw_bar = draw_bar


def draw_bg(c, t, f=0):
    c.set_source_rgb(*rgb('#15131c')); c.rectangle(0, HEAD, W, H - HEAD); c.fill()
    # old gym back wall: brick lines
    c.set_source_rgb(*rgb('#1f1b26')); c.rectangle(0, CEIL + 30, W, GROUND - CEIL); c.fill()
    c.set_source_rgba(0, 0, 0, 0.22); c.set_line_width(3)
    for j, yy in enumerate(range(CEIL + 60, 1250, 50)):
        c.move_to(0, yy); c.line_to(W, yy); c.stroke()
        for x in range(-50 + 50 * (j % 2), W, 100): c.move_to(x, yy); c.line_to(x, yy + 50); c.stroke()
    # high window with the moon
    c.set_source_rgb(*rgb('#2a3450')); rrect(c, 120, 560, 220, 200, 8); c.fill()
    c.set_source_rgb(*rgb('#d8d4c0')); c.arc(270, 620, 30, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#3a3442')); c.set_line_width(10); rrect(c, 120, 560, 220, 200, 8); c.stroke(); c.move_to(230, 560); c.line_to(230, 760); c.stroke(); c.move_to(120, 660); c.line_to(340, 660); c.stroke()
    # boxing ring far back: apron + ropes + corner posts
    c.set_source_rgb(*rgb('#2a2434')); c.rectangle(80, 1170, 920, 90); c.fill()
    c.set_source_rgb(*rgb('#3a2e40')); c.rectangle(80, 1170, 920, 14); c.fill()
    for xp in (100, 980):
        c.set_source_rgb(*rgb('#4a4252')); c.rectangle(xp - 10, 960, 20, 220); c.fill()
    for k, col in enumerate(('#7a3a40', '#c8c4d0', '#3a4a7a')):
        c.set_source_rgb(*rgb(col)); c.set_line_width(7); c.move_to(100, 990 + k * 55); c.curve_to(400, 1000 + k * 55, 680, 1000 + k * 55, 980, 990 + k * 55); c.stroke()
    # wall clock
    c.set_source_rgb(*rgb('#2e2a36')); c.arc(860, 660, 52, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#cfcac0')); c.arc(860, 660, 44, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(0.1, 0.1, 0.12); c.set_line_width(5); c.move_to(860, 660); c.line_to(860 + 30 * math.sin(t * 0.3), 660 - 30 * math.cos(t * 0.3)); c.stroke()
    c.move_to(860, 660); c.line_to(880, 670); c.stroke()
    # steel ceiling girder (pivot hangs from it)
    c.set_source_rgb(*rgb('#3a3e4a')); c.rectangle(-10, CEIL - 50, W + 20, 56); c.fill()
    c.set_source_rgb(*rgb('#2a2e38'))
    for x in range(0, W, 90): c.move_to(x, CEIL - 44); c.line_to(x + 45, CEIL); c.line_to(x + 90, CEIL - 44); c.set_line_width(6); c.stroke()
    c.set_source_rgba(0, 0, 0, 0.25); c.rectangle(-10, CEIL + 4, W + 20, 8); c.fill()
    c.set_source_rgb(*rgb('#2a2a30')); rrect(c, CX - 40, CEIL - 6, 80, 30, 6); c.fill()
    c.set_source_rgb(*rgb('#8a8a90')); c.arc(CX, CEIL + 16, 9, 0, 2 * math.pi); c.fill()
    # one quiet hanging lamp (off to the side)
    c.set_source_rgb(*rgb('#3a3a44')); c.set_line_width(4); c.move_to(760, CEIL); c.line_to(760, 520); c.stroke()
    c.move_to(730, 540); c.line_to(790, 540); c.line_to(776, 516); c.line_to(744, 516); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#e8d890')); c.arc(760, 544, 9, 0, math.pi); c.fill()
    # wooden gym floor
    TER.fill(c, TER.h, '#6a5040', '#3a2c24', '#7e6250')
    c.set_source_rgba(0, 0, 0, 0.18); c.set_line_width(3)
    for x in range(0, W, 90): c.move_to(x, GROUND + 10); c.line_to(x - 40 + (x - 540) * 0.15, H); c.stroke()
    c.move_to(0, GROUND + 110); c.line_to(W, GROUND + 110); c.stroke()
    # left wall: stack of folded gym mats (muted blue)
    x0, x1 = 0, XMIN - R
    for k in range(9):
        y0 = GROUND - 70 - k * 70
        c.set_source_rgb(*rgb('#2e4a6e' if k % 2 else '#34547a')); rrect(c, x0 - 10, y0, x1 - x0 + 14, 68, 12); c.fill()
        c.set_source_rgba(1, 1, 1, 0.08); c.rectangle(x0, y0 + 30, x1 - x0, 4); c.fill()
    # right wall: stack of old tires
    x0, x1 = XMAX + R, W
    for k in range(9):
        y0 = GROUND - 70 - k * 70
        c.set_source_rgb(*rgb('#1c1c22')); rrect(c, x0 - 4, y0, x1 - x0 + 10, 68, 30); c.fill()
        c.set_source_rgb(*rgb('#2c2c34')); rrect(c, x0 + 14, y0 + 20, x1 - x0 - 20, 28, 14); c.fill()

def draw_disco(c, t, f, fallen):   # the giant punching bag on its chain
    x, y = CHX[f], CHY[f]; th = CTH[f]; n = LK[f]
    if not fallen:
        c.set_source_rgb(*rgb('#9aa3b5'))
        HL = NLINK * LINK + 30 + 16 * (NLINK - n); sp = HL / max(1, n)
        c.set_line_width(3)
        if n > 0: c.move_to(CX, CEIL); c.line_to(x, y); c.stroke()
        c.set_line_width(8)
        for i in range(n):
            a0 = i * sp; cx = CX + math.sin(th) * (a0 + sp / 2); cy = CEIL + math.cos(th) * (a0 + sp / 2)
            c.save(); c.translate(cx, cy); c.rotate(-th)
            if i % 2: c.scale(0.45, 1)
            rrect(c, -14, -LINK / 2 - 3, 28, LINK + 6, 14); c.restore(); c.stroke()
        last = [p for p in POPS if p <= t]
        if last and t - last[-1] < 0.5:
            k = (t - last[-1]) / 0.5; c.set_source_rgba(0.6, 0.64, 0.7, 1 - k)
            c.arc(x + 30 * k, y + 600 * k * k, 10, 0, 2 * math.pi); c.stroke()
    c.save(); c.translate(x, y); c.rotate(-th if not fallen else 0)
    c.set_source_rgb(*rgb('#6a6e78')); c.set_line_width(10); c.arc(0, 26, 18, 0, 2 * math.pi); c.stroke()   # swivel ring
    c.set_line_width(5)
    for sx in (-80, -30, 30, 80): c.move_to(0, 40); c.line_to(sx, 66); c.stroke()   # straps
    BW, TOP, BOT = 95, 60, 360
    c.set_source_rgb(*rgb('#7a2a30')); rrect(c, -BW, TOP, 2 * BW, BOT - TOP, 40); c.fill()   # leather bag
    c.set_source_rgb(*rgb('#5e1e24')); rrect(c, -BW, TOP, 2 * BW, 34, 16); c.fill(); rrect(c, -BW, BOT - 34, 2 * BW, 34, 16); c.fill()
    c.set_source_rgb(*rgb('#d8d0c4')); c.rectangle(-BW, 190, 2 * BW, 26); c.fill()   # white band
    c.set_source_rgba(1, 1, 1, 0.12); rrect(c, -BW + 22, TOP + 50, 22, BOT - TOP - 100, 11); c.fill()
    c.set_source_rgba(0, 0, 0, 0.25); c.set_line_width(3)
    for yy in range(TOP + 60, BOT - 40, 42): c.move_to(-BW + 8, yy); c.line_to(BW - 8, yy); c.stroke()
    if fallen:
        c.set_source_rgba(0.1, 0.08, 0.06, 0.7); c.set_line_width(5)
        for sgn in (-1, 1): c.move_to(sgn * 100, BOT); c.line_to(sgn * 150, BOT + 6); c.line_to(sgn * 200, BOT + 2); c.stroke()
    c.restore()


PS = Particles(9)
def render(f, c):
    t = f / FPS; fi = min(f, len(GX) - 1); shake = (0, 0)
    if T_LAND and T_LAND <= t < T_LAND + 0.3 and T_LAND < S.T_RES + 0.6: shake = (rng.uniform(-8, 8), rng.uniform(-8, 8))
    if T_LAND and f == int(round(T_LAND * FPS)):
        PS.spawn(CHX[fi], GROUND - 20, 30, (0.5, 0.4, 0.3), 650, 0.55, grav=1500, r=8)
    c.save(); c.translate(*shake)
    draw_bg(c, t, fi)
    landed = T_LAND is not None and t >= T_LAND
    squashed = T_FAIL is not None and t >= T_FAIL
    if END.carried(t) or t >= END.T_GRAB:
        gx, gy = (END.carry_xy(t) if END.carried(t) else S.GRAB)
    elif squashed:
        gx, gy = FX, FY
    else:
        gx, gy = GX[fi], GYS[fi]
        h = max(0, TER.y(gx) - R - gy); kk = 1 / (1 + h / 220)
        c.set_source_rgba(0, 0, 0, 0.25 * kk); c.save(); c.translate(gx, TER.y(gx) + 3); c.scale(R * (0.5 + 0.4 * kk), 9); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    nlinks = LK[fi]
    danger = nlinks <= 2 or (T_DROP is not None and t >= T_DROP and not landed)
    mood = 'happy' if (t >= S.T_END and S.OUTCOME == 'win') else ('scared' if danger or squashed else 'worried')
    pulled = squashed and t >= END.T_GRAB
    drawn = False
    if squashed and not pulled:   # flattened under it, then squirts out to the side, dizzy
        draw_disco(c, t, fi, landed); drawn = True
        k = clamp((t - T_FAIL) / 0.25, 0, 1); gx2 = lerp(FX, SX, ease(k)); gy2 = GROUND - R * (1 - 0.35 * min(1, k * 2))
        draw_blob(c, t, gx2, gy2, 'scared', 0.35 * min(1, k * 2), R=R, dizzy=t > T_FAIL + 0.4)
    elif not (landed and gy > CHY[fi] + 30 and abs(gx - CHX[fi]) < 150 and False):
        draw_blob(c, t, gx, gy, mood, 0, R=R, dizzy=pulled)
    if not drawn: draw_disco(c, t, fi, landed)
    if CONTACT and abs(t - CONTACT[0]) < 0.5 / FPS: PS.spawn(CONTACT[1], CONTACT[2] - R, 14, (0.8, 0.8, 0.85), 380, 0.5, grav=600, r=7)
    PS.draw(c)
    END.draw_claw(c, t)
    c.restore()
    END.header(c, t, fi)

if __name__ == '__main__':
    if sys.argv[1] == 'sim':
        best = 1e9
        for f in range(min(N0, int(END.T_GRAB * FPS))):
            if T_DROP and f / FPS >= T_DROP: break
            for (cx, cy, r) in body_circles(CHX[f], CHY[f]): best = min(best, math.hypot(GX[f] - cx, GYS[f] - cy) - r - R)
        print('hangclear', round(best), end=' ')
        print(SEED, S.OUTCOME, round(S.T_RES - S.T_START, 2), 'links', LK[int(S.T_RES * FPS) - 1], 'pops', [round(p - S.T_START, 1) for p in POPS],
              'drop', T_DROP and round(T_DROP - S.T_START, 1), 'dur', S.DUR); sys.exit()
    run(S, render)
