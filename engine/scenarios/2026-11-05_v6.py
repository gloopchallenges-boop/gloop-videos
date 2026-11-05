"""2026-11-05 v6 — FALLING OBJECT ABOVE – CHAIN 6 LINKS: the GIANT DISCO BALL. An empty roller disco at
night; a huge mirror disco ball hangs from a 6-link chain. Gloop is a passive rigid ball (Ball) bouncing
on the checkered rink floor. Every landing shakes the floor (strain + a random swing kick), seeded ceiling
creaks jolt it, and the pendulum swing itself strains the chain. Strain past a seeded threshold pops a
link (ball jerks lower). 0 links = it falls with real gravity from wherever it has swung to; it
only hurts Gloop if it actually touches him (swept check). Timer ends first = win."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the giant disco ball'
SEED = int(os.environ.get('SEED', 24))
rng = random.Random(SEED)

class S: pass
S.HOOK2 = 'THE GIANT DISCO BALL?'; S.HOOK2_SIZE = 84; S.FAIL_WORD = 'CRASH!'; S.FAIL_SIZE = 160
S.T_START = HOOK_T; S.TL = float(os.environ.get('TL', 12.0)); S.T_END = S.T_START + S.TL
GROUND = 1600; R = 58; XMIN, XMAX = 175, 905
NLINK = 6; LINK = 46; CEIL = 470; CX = 540; PIV = (CX, CEIL)
STR = float(os.environ.get('STR', 1.1))
THR = [rng.uniform(9, 20) for _ in range(NLINK)]
JOLTS = []; tt = 0.4
while tt < 40: JOLTS.append((tt, rng.uniform(2, 6), rng.choice((-1, 1)) * rng.uniform(0.15, 0.4))); tt += rng.uniform(1.2, 2.8)

TER = Terrain(GROUND, seed=SEED, bumps=3, amp=6, soft=False)
ball = Ball(rng.uniform(220, 860), TER, R=R, seed=SEED, xmin=XMIN, xmax=XMAX)
BR_ = 125
def body_circles(x, ytop):   # disco ball collision shape: (cx, cy, r)
    return [(x, ytop + 40 + BR_, BR_)]

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
    HL = NLINK * LINK + 30 + 34 * (NLINK - links)   # each popped link lets it slip lower
    Lp = HL + 70
    if T_DROP is None:
        om += (-3200 / max(200, Lp * 1.6) * math.sin(th)) / FPS; om *= (1 - 0.35 / FPS); th += om / FPS
        if live: strain += 10 * abs(om) * STR / FPS
        if links > 0 and strain >= THR[NLINK - links] and live:
            strain -= THR[NLINK - links]; links -= 1; POPS.append(t); om += rng.choice((-1, 1)) * 0.12
            if links == 0:
                T_DROP = t; fx = CX + math.sin(th) * HL; fy = CEIL + HL * math.cos(th); fvy = 0
    HL = NLINK * LINK + 30 + 34 * (NLINK - links)
    chx = CX + math.sin(th) * HL; chy = CEIL + HL * math.cos(th)
    if T_DROP is not None and T_LAND is None:
        py = fy; fvy += 3200 / FPS; fy += fvy / FPS
        rest = GROUND - 40 - 2 * BR_ + 10
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
if T_LAND and T_LAND < S.T_RES + 0.6: S.events += [[T_LAND, 'crash'], [T_LAND + 0.02, 'clink'], [T_LAND + 0.08, 'clink']]
if T_FAIL: S.events += [[T_FAIL, 'crash'], [T_FAIL + 0.05, 'clang']]
S.AMB = {'drone': 50, 'wind': 0.01}

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


WALL, FLOOR_A, FLOOR_B = '#1c1828', '#2c2a3a', '#232130'
SPOT_COLS = [(0.95, 0.45, 0.65), (0.4, 0.8, 0.85), (0.7, 0.55, 0.95), (0.95, 0.8, 0.45)]
def spots(t, f):
    """soft colored light dots thrown by the slowly turning ball (move across walls + floor)"""
    x, y = CHX[f], CHY[f] + 40 + BR_; out = []
    for i in range(10):
        a = t * 0.35 + i * 2 * math.pi / 10
        sx = x + math.cos(a) * 620; sy = y + 160 + math.sin(a * 1.7 + i) * 420
        if math.sin(a) > -0.2: out.append((sx, sy, SPOT_COLS[i % 4], 0.16 * (0.5 + 0.5 * math.sin(a))))
    return out
def draw_bg(c, t, f=0):
    c.set_source_rgb(*rgb(WALL)); c.rectangle(0, HEAD, W, H - HEAD); c.fill()
    c.set_source_rgba(1, 1, 1, 0.025)   # wall panels
    for x in range(0, W, 120): c.rectangle(x + 10, CEIL + 40, 100, 900); c.fill()
    c.set_source_rgb(*rgb('#141120')); c.rectangle(0, HEAD, W, CEIL - HEAD); c.fill()   # ceiling
    c.set_source_rgb(*rgb('#2a2236')); c.rectangle(0, CEIL - 22, W, 22); c.fill()
    for lx in (160, 920):   # dark ceiling spotlights
        c.set_source_rgb(*rgb('#3a3448')); rrect(c, lx - 30, CEIL - 10, 60, 50, 10); c.fill()
    c.set_source_rgb(*rgb('#3a3448')); c.save(); c.translate(CX, CEIL); c.scale(60, 18); c.arc(0, 0, 1, 0, math.pi); c.restore(); c.fill()
    # checkered rink floor
    c.set_source_rgb(*rgb(FLOOR_A)); c.rectangle(0, GROUND, W, H - GROUND); c.fill()
    c.set_source_rgb(*rgb(FLOOR_B))
    for i, yy in enumerate(range(GROUND, H, 64)):
        for x in range((i % 2) * 64, W, 128): c.rectangle(x, yy, 64, 64); c.fill()
    c.set_source_rgba(1, 1, 1, 0.08); c.rectangle(0, GROUND, W, 5); c.fill()
    for (sx, sy, col, al) in spots(t, f):
        c.set_source_rgba(*col, al); c.save(); c.translate(sx, sy); c.scale(1, 0.55 if sy > GROUND else 1); c.arc(0, 0, 22, 0, 2 * math.pi); c.restore(); c.fill()
    for (x0, x1) in ((0, XMIN - R), (XMAX + R, W)):   # padded rink barriers he bounces off
        c.set_source_rgb(*rgb('#3b2f52')); c.rectangle(x0, 1130, x1 - x0, GROUND - 1130); c.fill()
        c.set_source_rgb(*rgb('#4a3c66')); c.rectangle(x0, 1130, x1 - x0, 30); c.fill()
        c.set_source_rgb(*rgb('#2f2543'))
        for yy in range(1200, GROUND, 90): c.rectangle(x0, yy, x1 - x0, 8); c.fill()

def draw_disco(c, t, f, fallen):
    x, y = CHX[f], CHY[f]; th = CTH[f]; n = LK[f]
    if not fallen:   # chain links from the pivot
        c.set_source_rgb(*rgb('#9aa3b5'))
        HL = NLINK * LINK + 30 + 34 * (NLINK - n); sp = HL / max(1, n)
        c.set_line_width(3)
        if n > 0: c.move_to(CX, CEIL); c.line_to(x, y); c.stroke()
        c.set_line_width(7)
        for i in range(n):
            a0 = i * sp; cx = CX + math.sin(th) * (a0 + sp / 2); cy = CEIL + math.cos(th) * (a0 + sp / 2)
            c.save(); c.translate(cx, cy); c.rotate(-th)
            if i % 2: c.scale(0.45, 1)
            rrect(c, -14, -LINK / 2 - 3, 28, LINK + 6, 14); c.restore(); c.stroke()
        last = [p for p in POPS if p <= t]
        if last and t - last[-1] < 0.5:   # broken link falling
            k = (t - last[-1]) / 0.5; c.set_source_rgba(0.6, 0.64, 0.7, 1 - k)
            c.arc(x + 30 * k, y + 600 * k * k, 10, 0, 2 * math.pi); c.stroke()
    c.save(); c.translate(x, y)
    c.set_source_rgb(*rgb('#6f7891')); c.rectangle(-8, 0, 16, 30); c.fill(); rrect(c, -26, 26, 52, 18, 6); c.fill()   # hanger cap
    cy = 40 + BR_
    c.set_source_rgb(*rgb('#8a90a0')); c.arc(0, cy, BR_, 0, 2 * math.pi); c.fill()
    c.save(); c.arc(0, cy, BR_, 0, 2 * math.pi); c.clip()
    rot = t * 0.35; nr = 9
    for j in range(nr):   # facets: latitude rows x longitude cells
        la0 = -math.pi / 2 + j * math.pi / nr; la1 = la0 + math.pi / nr
        y0 = cy + BR_ * math.sin(la0); y1 = cy + BR_ * math.sin(la1)
        ncell = 16
        for k in range(ncell):
            lo = rot + k * 2 * math.pi / ncell
            lo2 = lo + 2 * math.pi / ncell
            if math.cos(lo) < 0 and math.cos(lo2) < 0: continue
            rr = BR_ * math.cos((la0 + la1) / 2)
            xa = rr * math.sin(lo); xb = rr * math.sin(lo2)
            if math.cos(lo) < 0: xa = -rr if math.sin(lo) < 0 else rr
            if math.cos(lo2) < 0: xb = rr if math.sin(lo2) > 0 else -rr
            shade = 0.45 + 0.35 * math.cos(lo + 0.6) * math.cos((la0 + la1) / 2 + 0.5) + 0.12 * ((j + k) % 3 == 0)
            c.set_source_rgb(shade * 0.92, shade * 0.95, shade); c.rectangle(min(xa, xb) + 1, y0 + 1, abs(xb - xa) - 2, y1 - y0 - 2); c.fill()
    c.restore()
    c.set_source_rgba(0, 0, 0, 0.35); c.set_line_width(4); c.arc(0, cy, BR_, 0, 2 * math.pi); c.stroke()
    if not fallen:   # one small sparkle
        k = (t * 0.7) % 1; sx, sy = -50 + 60 * math.sin(k * 6.28), cy - 60
        c.set_source_rgba(1, 1, 1, 0.6 * math.sin(k * math.pi)); star_path(c, sx, sy, 12); c.fill()
    else:   # dented & cracked on the floor
        c.set_source_rgba(0.1, 0.1, 0.12, 0.7); c.set_line_width(4)
        c.move_to(-60, cy - 40); c.line_to(-10, cy); c.line_to(-30, cy + 50); c.stroke(); c.move_to(-10, cy); c.line_to(50, cy + 20); c.stroke()
    c.restore()

PS = Particles(9)
def render(f, c):
    t = f / FPS; fi = min(f, len(GX) - 1); shake = (0, 0)
    if T_LAND and T_LAND <= t < T_LAND + 0.3 and T_LAND < S.T_RES + 0.6: shake = (rng.uniform(-8, 8), rng.uniform(-8, 8))
    if T_LAND and f == int(round(T_LAND * FPS)):
        PS.spawn(CHX[fi], GROUND - 20, 30, (0.8, 0.82, 0.88), 650, 0.55, grav=1500, r=7)
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
        print(SEED, S.OUTCOME, round(S.T_RES - S.T_START, 2), 'links', LK[int(S.T_RES * FPS) - 1], 'pops', [round(p - S.T_START, 1) for p in POPS],
              'drop', T_DROP and round(T_DROP - S.T_START, 1), 'dur', S.DUR); sys.exit()
    run(S, render)
