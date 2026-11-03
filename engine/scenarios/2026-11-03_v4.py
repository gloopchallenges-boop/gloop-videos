"""2026-11-03 v4 — FALLING OBJECT ABOVE – CHAIN 6 LINKS: the GIANT CHANDELIER. An old ballroom at night;
a huge crystal chandelier hangs from a rusty 6-link chain. Gloop is a passive rigid ball (Ball) bouncing
on the creaky dance floor. Every landing shakes the floor (strain + a random swing kick), seeded ceiling
creaks jolt it, and the pendulum swing itself strains the chain. Strain past a seeded threshold pops a
link (chandelier jerks lower). 0 links = it falls with real gravity from wherever it has swung to; it
only hurts Gloop if it actually touches him (swept check). Timer ends first = win."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the giant chandelier'
SEED = int(os.environ.get('SEED', 12))
rng = random.Random(SEED)

class S: pass
S.HOOK2 = 'THE GIANT CHANDELIER?'; S.HOOK2_SIZE = 80; S.FAIL_WORD = 'CRASH!'; S.FAIL_SIZE = 160
S.T_START = HOOK_T; S.TL = float(os.environ.get('TL', 12.0)); S.T_END = S.T_START + S.TL
GROUND = 1600; R = 58; XMIN, XMAX = 175, 905
NLINK = 6; LINK = 46; CEIL = 470; CX = 540; PIV = (CX, CEIL)
STR = float(os.environ.get('STR', 1.4))
THR = [rng.uniform(9, 20) for _ in range(NLINK)]
JOLTS = []; tt = 0.4
while tt < 40: JOLTS.append((tt, rng.uniform(2, 6), rng.choice((-1, 1)) * rng.uniform(0.15, 0.4))); tt += rng.uniform(1.2, 2.8)

TER = Terrain(GROUND, seed=SEED, bumps=3, amp=6, soft=False)
ball = Ball(rng.uniform(220, 860), TER, R=R, seed=SEED, xmin=XMIN, xmax=XMAX)
def body_circles(x, ytop):   # chandelier collision shape: (cx, cy, r)
    return [(x, ytop + 95, 80), (x - 120, ytop + 95, 46), (x + 120, ytop + 95, 46)]

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
        rest = GROUND - 175
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
S.AMB = {'drone': 52, 'wind': 0.012}

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

WALL, WALL2, FLOOR_C, FLOOR_D = '#211b2c', '#271f33', '#5a3e2e', '#4a3226'
def draw_bg(c, t):
    c.set_source_rgb(*rgb(WALL)); c.rectangle(0, HEAD, W, H - HEAD); c.fill()
    c.set_source_rgb(*rgb(WALL2))
    for x in range(0, W, 180): c.rectangle(x + 20, CEIL + 60, 140, GROUND - CEIL - 120); c.fill()
    for wx in (150, 930):   # tall arched windows with moonlight
        c.set_source_rgb(*rgb('#141c33')); c.rectangle(wx - 70, 700, 140, 420); c.arc(wx, 700, 70, math.pi, 0); c.fill()
        c.set_source_rgb(*rgb('#2e3550')); c.set_line_width(8); c.move_to(wx, 640); c.line_to(wx, 1120); c.stroke(); c.move_to(wx - 70, 880); c.line_to(wx + 70, 880); c.stroke()
    c.set_source_rgb(*rgb('#d8d0b0')); c.arc(905, 760, 22, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#17121f')); c.rectangle(0, HEAD, W, CEIL - HEAD); c.fill()   # ceiling
    c.set_source_rgb(*rgb('#2b2236')); c.rectangle(0, CEIL - 22, W, 22); c.fill()
    c.set_source_rgb(*rgb('#3a2e48')); c.save(); c.translate(CX, CEIL); c.scale(90, 26); c.arc(0, 0, 1, 0, math.pi); c.restore(); c.fill()   # ceiling rose
    c.set_source_rgb(*rgb(FLOOR_C)); c.rectangle(0, GROUND, W, H - GROUND); c.fill()
    c.set_source_rgb(*rgb(FLOOR_D))
    for i, yy in enumerate(range(GROUND, H, 56)):
        c.rectangle(0, yy, W, 4); c.fill()
        for x in range((i % 2) * 90, W, 180): c.rectangle(x, yy, 4, 56); c.fill()
    for (x0, x1) in ((0, XMIN - R), (XMAX + R, W)):   # walls / curtains he bounces off
        c.set_source_rgb(*rgb('#5a2733')); c.rectangle(x0, CEIL, x1 - x0, GROUND - CEIL); c.fill()
        c.set_source_rgb(*rgb('#4a1f2a'))
        for x in range(int(x0) + 14, int(x1), 34): c.rectangle(x, CEIL, 9, GROUND - CEIL); c.fill()

def draw_chandelier(c, t, f, fallen):
    x, y = CHX[f], CHY[f]; th = CTH[f]; n = LK[f]
    if not fallen:   # chain links from the pivot
        c.set_source_rgb(*rgb('#9aa3b5')); c.set_line_width(7)
        HL = NLINK * LINK + 30 + 34 * (NLINK - n); sp = HL / max(1, n)
        c.set_line_width(3)
        if n > 0: c.move_to(CX, CEIL); c.line_to(x, y); c.stroke()
        c.set_line_width(7)
        for i in range(n):
            a0 = i * sp; cx = CX + math.sin(th) * (a0 + sp / 2); cy = CEIL + math.cos(th) * (a0 + sp / 2)
            c.save(); c.translate(cx, cy); c.rotate(-th + (math.pi / 2 if i % 2 else 0) * 0 );
            if i % 2: c.scale(0.45, 1)
            rrect(c, -14, -LINK / 2 - 3, 28, LINK + 6, 14); c.restore(); c.stroke()
        last = [p for p in POPS if p <= t]
        if last and t - last[-1] < 0.5:   # broken link half falling
            k = (t - last[-1]) / 0.5; c.set_source_rgba(0.6, 0.64, 0.7, 1 - k)
            c.arc(x + 30 * k, y + 600 * k * k, 10, 0, 2 * math.pi); c.stroke()
    c.save(); c.translate(x, y)
    if not fallen: c.rotate(-th * 0.0)
    c.set_source_rgb(*rgb('#b89a52')); c.set_line_width(10)
    c.move_to(0, 0); c.line_to(0, 70); c.stroke()
    c.save(); c.translate(0, 95); c.scale(150, 38); c.arc(0, 0, 1, 0, math.pi); c.restore(); c.stroke()
    c.set_source_rgb(*rgb('#c9aa5c')); c.save(); c.translate(0, 95); c.scale(80, 36); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    c.set_source_rgb(*rgb('#8f7638')); rrect(c, -165, 82, 330, 16, 8); c.fill()
    for i in range(7):   # candles + crystals
        cx = -150 + i * 50
        c.set_source_rgb(*rgb('#e8e0cc')); c.rectangle(cx - 7, 50, 14, 32); c.fill()
        if not fallen:
            fl = 1 + 0.15 * math.sin(t * 13 + i)
            c.set_source_rgb(*rgb('#ffd27a')); c.save(); c.translate(cx, 42); c.scale(6 * fl, 11 * fl); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
        c.set_source_rgba(0.75, 0.85, 1, 0.85)
        c.move_to(cx, 110); c.line_to(cx + 8, 125); c.line_to(cx, 145 + (i % 2) * 14); c.line_to(cx - 8, 125); c.close_path(); c.fill()
    c.restore()

PS = Particles(9)
def render(f, c):
    t = f / FPS; fi = min(f, len(GX) - 1); shake = (0, 0)
    if T_LAND and T_LAND <= t < T_LAND + 0.3 and T_LAND < S.T_RES + 0.6: shake = (rng.uniform(-8, 8), rng.uniform(-8, 8))
    if T_LAND and f == int(round(T_LAND * FPS)):
        PS.spawn(CHX[fi], GROUND - 20, 24, (0.75, 0.85, 1.0), 650, 0.55, grav=1500, r=7); PS.spawn(CHX[fi], GROUND - 20, 12, (0.72, 0.6, 0.32), 450, 0.5, grav=1500, r=8)
    c.save(); c.translate(*shake)
    draw_bg(c, t)
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
    draw_chandelier(c, t, fi, landed)
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
