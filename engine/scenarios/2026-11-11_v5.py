"""2026-11-11 v5 — FALLING OBJECT ABOVE – CHAIN 6 LINKS: the GIANT ANCHOR. On a harbor dock at night a huge ship
anchor hangs from a dock crane's boom on a 6-link chain. Gloop is a passive rigid ball (Ball) bouncing on the
wooden dock between two stacks of cargo crates. Every landing shakes the dock (strain + a random swing kick),
seeded sea-wind gusts kick it, and the pendulum swing itself strains the chain. Strain past a seeded threshold
pops a link (anchor jerks lower). 0 links = it falls with real gravity from wherever it has swung to; it only
hurts Gloop if it actually touches him (swept check). Timer ends first = win."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the giant anchor'
SEED = int(os.environ.get('SEED', 8))
rng = random.Random(SEED)

class S: pass
S.HOOK2 = 'THE GIANT ANCHOR?'; S.HOOK2_SIZE = 92; S.FAIL_WORD = 'CLANG!'; S.FAIL_SIZE = 160
S.T_START = HOOK_T; S.TL = float(os.environ.get('TL', 12.0)); S.T_END = S.T_START + S.TL
GROUND = 1600; R = 58; XMIN, XMAX = 175, 905
NLINK = 6; LINK = 40; CEIL = 470; CX = 540; PIV = (CX, CEIL)
STR = float(os.environ.get('STR', 1.5))
THR = [rng.uniform(9, 20) for _ in range(NLINK)]
JOLTS = []; tt = 0.4
while tt < 40: JOLTS.append((tt, rng.uniform(2, 6), rng.choice((-1, 1)) * rng.uniform(0.15, 0.4))); tt += rng.uniform(1.2, 2.8)

TER = Terrain(GROUND, seed=SEED, bumps=3, amp=6, soft=False)
ball = Ball(rng.uniform(220, 860), TER, R=R, seed=SEED, xmin=XMIN, xmax=XMAX)
BR_ = 125
def body_circles(x, ytop):   # disco ball collision shape: (cx, cy, r)
    return [(x, ytop + 30, 34), (x, ytop + 90, 110 * 0 + 30), (x, ytop + 160, 26), (x, ytop + 240, 40), (x - 95, ytop + 255, 40), (x + 95, ytop + 255, 40), (x - 135, ytop + 190, 34), (x + 135, ytop + 190, 34)]

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
        rest = GROUND - 300 + 8
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
if T_FAIL: S.GRAB = (clamp(FX, 220, 860), GROUND - R - 40)
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
S.AMB = {'drone': 48, 'wind': 0.03}

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


STARS = [(rng.uniform(0, W), rng.uniform(HEAD + 20, 900), rng.uniform(1, 2.2)) for _ in range(40)]
def draw_bg(c, t, f=0):
    c.set_source_rgb(*rgb('#121a2a')); c.rectangle(0, HEAD, W, H - HEAD); c.fill()
    c.set_source_rgba(0.85, 0.88, 0.95, 0.5)
    for (sx, sy, rr) in STARS: c.arc(sx, sy, rr, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#e6dfc4')); c.arc(860, 640, 46, 0, 2 * math.pi); c.fill()
    # sea at the horizon + a moored cargo ship silhouette
    c.set_source_rgb(*rgb('#16223a')); c.rectangle(0, 1180, W, GROUND - 1180); c.fill()
    c.set_source_rgba(1, 1, 1, 0.06)
    for i in range(5): c.rectangle(0, 1210 + i * 70 + 5 * math.sin(t * 1.3 + i), W, 4); c.fill()
    c.set_source_rgb(*rgb('#1c2436')); c.move_to(-20, 1080); c.line_to(700, 1080); c.line_to(660, 1200); c.line_to(20, 1200); c.close_path(); c.fill()
    c.rectangle(80, 960, 160, 120); c.fill(); c.rectangle(130, 900, 30, 60); c.fill()
    for k in range(4): c.set_source_rgb(*rgb(('#2a3046', '#30283a', '#263040', '#342c30')[k])); c.rectangle(280 + k * 95, 1010, 88, 70); c.fill()   # containers on deck
    c.set_source_rgba(1, 0.82, 0.5, 0.4)
    for wx in (110, 150, 190): c.rectangle(wx, 990, 16, 16); c.fill()
    # dock crane: yellow steel tower on the right, boom across the top (pivot hangs from it)
    c.set_source_rgb(*rgb('#8a7430'))
    c.rectangle(980, CEIL - 50, 50, GROUND - CEIL + 50); c.fill()
    c.set_source_rgb(*rgb('#6a5a26')); c.set_line_width(5)
    for yy in range(CEIL, GROUND, 90): c.move_to(980, yy); c.line_to(1030, yy + 90); c.stroke()
    c.set_source_rgb(*rgb('#8a7430')); c.rectangle(-10, CEIL - 50, W + 20, 18); c.fill(); c.rectangle(-10, CEIL - 4, W + 20, 14); c.fill()
    c.set_source_rgb(*rgb('#8a7430')); c.set_line_width(6)
    for x in range(-10, W, 70): c.move_to(x, CEIL - 34); c.line_to(x + 35, CEIL - 4); c.line_to(x + 70, CEIL - 34); c.stroke()   # truss
    c.set_source_rgb(*rgb('#2a2a30')); rrect(c, CX - 40, CEIL - 6, 80, 30, 6); c.fill()
    c.set_source_rgb(*rgb('#8a8a90')); c.arc(CX, CEIL + 16, 9, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#ff5a4a')); c.arc(1005, CEIL - 60, 7 + 2 * math.sin(t * 4), 0, 2 * math.pi); c.fill()   # warning light
    # wooden dock floor
    TER.fill(c, TER.h, '#5a4430', '#33261a', '#6e563c')
    c.set_source_rgba(0, 0, 0, 0.2); c.set_line_width(3)
    for yy in range(GROUND + 60, H, 60): c.move_to(0, yy); c.line_to(W, yy); c.stroke()
    for x in range(40, W, 160):
        c.set_source_rgba(0, 0, 0, 0.25)
        for yy in range(GROUND + 30, H, 60): c.arc(x, yy, 4, 0, 2 * math.pi); c.fill()   # nail heads
    for (x0, x1) in ((0, XMIN - R), (XMAX + R, W)):   # stacked wooden cargo crates = walls
        for k, yy in enumerate(range(GROUND - 120, 1000, -120)):
            c.set_source_rgb(*rgb(('#6a4e30', '#5e4428')[k % 2])); c.rectangle(x0 - 10, yy, x1 - x0 + 20, 120); c.fill()
            c.set_source_rgb(*rgb('#3e2c1a')); c.set_line_width(5); c.rectangle(x0 - 4, yy + 4, x1 - x0 + 8, 112); c.stroke()
            c.move_to(x0 - 4, yy + 4); c.line_to(x1 + 4, yy + 116); c.stroke()
        c.set_source_rgb(*rgb('#5e4428')); c.rectangle(x0 - 10, GROUND - 10, x1 - x0 + 20, 50); c.fill()

def draw_disco(c, t, f, fallen):   # the giant ship anchor on its chain
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
    bot = 300; iron, iron2, rust = rgb('#4a505c'), rgb('#5e6674'), rgb('#7a4a30')
    c.set_source_rgb(*iron); c.set_line_width(14); c.arc(0, 30, 22, 0, 2 * math.pi); c.stroke()   # ring
    c.set_source_rgb(*iron); rrect(c, -20, 50, 40, bot - 70, 10); c.fill()   # shank
    c.set_source_rgb(*iron2); c.rectangle(-8, 56, 10, bot - 90); c.fill()
    c.set_source_rgb(*rgb('#5a4028')); rrect(c, -110, 66, 220, 28, 12); c.fill()   # wooden stock
    c.set_source_rgb(*iron); c.arc(-112, 80, 12, 0, 2 * math.pi); c.fill(); c.arc(112, 80, 12, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*iron); c.set_line_width(34); c.set_line_cap(cairo.LINE_CAP_ROUND)   # curved arms
    c.arc(0, bot - 150, 140, 0.18 * math.pi, 0.82 * math.pi); c.stroke()
    for sgn in (-1, 1):   # flukes
        a = (0.18 if sgn > 0 else 0.82) * math.pi; fx_, fy_ = 140 * math.cos(a), bot - 150 + 140 * math.sin(a)
        c.move_to(fx_ - sgn * 10, fy_ + 24); c.line_to(fx_ + sgn * 46, fy_ - 66); c.line_to(fx_ - sgn * 36, fy_ - 20); c.close_path(); c.fill()
    c.set_source_rgba(*rust, 0.6)
    for (rx, ry) in ((-6, 140), (8, 200), (-60, bot - 34), (70, bot - 40)): c.arc(rx, ry, 7, 0, 2 * math.pi); c.fill()
    if fallen:   # cracked planks around it
        c.set_source_rgba(0.1, 0.08, 0.06, 0.7); c.set_line_width(5)
        for sgn in (-1, 1): c.move_to(sgn * 120, bot); c.line_to(sgn * 180, bot + 6); c.line_to(sgn * 230, bot + 2); c.stroke()
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
    if squashed and not pulled:   # pinned under it: peeks out flattened & dizzy
        k = clamp((t - T_FAIL) / 0.15, 0, 1); gx2 = gx; gy2 = GROUND - R * (1 - 0.35 * k)
        draw_blob(c, t, gx2, gy2, 'scared', 0.35 * k, R=R, dizzy=t > T_FAIL + 0.4)
    elif not (landed and gy > CHY[fi] + 30 and abs(gx - CHX[fi]) < 150 and False):
        draw_blob(c, t, gx, gy, mood, 0, R=R, dizzy=pulled)
    draw_disco(c, t, fi, landed)
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
