"""2026-11-28 v3 — RISING DANGER – POPCORN GAP m: the POPCORN FLOOD (normal style; based on 2026-11-23 v3). Gloop is a
passive rigid ball bouncing on a long glass concession counter between two stacks of popcorn buckets (walls) in a
cinema lobby at night. Popcorn piles up from frame 0 at a seeded-random rate: three runaway popcorn kettles on the
back wall burst out popcorn (surges) and sometimes the pile settles / caves in (gulps). POPCORN GAP = distance from
the popcorn up to the counter. If the popcorn touches Gloop he's buried = fail (covered in popcorn & dizzy, claw
collects him)."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the popcorn flood'
SEED = int(os.environ.get('SEED', 13))
rng = random.Random(SEED)

class S: pass
S.HOOK2 = 'THE POPCORN FLOOD?'; S.HOOK2_SIZE = 88; S.FAIL_WORD = 'BURIED!'; S.FAIL_SIZE = 150
S.T_START = HOOK_T; S.TL = float(os.environ.get('TL', 13.0)); S.T_END = S.T_START + S.TL
GRATE = 1270; R = 58; XMIN, XMAX = 190, 890; PXM = 100.0
SL0 = 1880; BASE = float(os.environ.get('BASE', 18))

EVS = []; t = rng.uniform(0.0, 0.4)   # pipe surges (+) and drain gulps (-)
while t < S.T_END + 1:
    gulp = rng.random() < 0.3
    EVS.append({'t': t, 'd': rng.uniform(0.8, 1.6), 'a': (-rng.uniform(25, 45) if gulp else rng.uniform(30, 75)), 'pipe': rng.randrange(3)})
    t += rng.uniform(1.0, 2.2)
PIPES = [(300, 820), (790, 760), (560, 1000)]   # outflow pipes (x, y) on the back wall

TER = Terrain(GRATE, seed=SEED, bumps=0, amp=0, soft=False)
N0 = int(40 * FPS); GX, GYS, SL, GAP = [], [], [], []
ball = Ball(rng.uniform(320, 760), TER, R=R, seed=SEED, xmin=XMIN, xmax=XMAX, hop=rng.uniform(230, 300))
sl = SL0; T_FAIL = None
for f in range(N0):
    t = f / FPS
    if T_FAIL is None and t < S.T_END:
        rate = BASE + sum(e['a'] for e in EVS if e['t'] <= t < e['t'] + e['d'])
        sl -= rate / FPS
    elif t >= S.T_END and T_FAIL is None:
        sl -= BASE * max(0, 1 - (t - S.T_END) / 0.6) / FPS
    if T_FAIL is None: ball.step(t)
    if T_FAIL is None and S.T_START <= t < S.T_END and ball.y + R > sl + 4:
        T_FAIL = t; FX, FY = ball.x, ball.y
    GX.append(ball.x); GYS.append(ball.y); SL.append(sl); GAP.append(max(0.0, (sl - GRATE) / PXM))
S.OUTCOME = 'fail' if T_FAIL else 'win'
S.T_RES = T_FAIL if T_FAIL else S.T_END
END = S.END = Ending(S)
if T_FAIL: S.GRAB = (FX, SL[int(T_FAIL * FPS)] - R * 0.45)
else: gi = min(int(END.T_GRAB * FPS), N0 - 1); S.GRAB = (GX[gi], GYS[gi])
S.events = [[0.05, 'rumble', 1.2], [0.3, 'creak']]
for e in EVS:
    if e['t'] < S.T_RES: S.events.append([e['t'], 'crackle' if e['a'] > 0 else 'whoosh']); S.events.append([e['t'], 'rumble', min(e['d'], 1.2)])
for (tl, xl, imp) in ball.landings:
    if tl < S.T_RES: S.events.append([tl, 'hop'])
for tw in ball.walls:
    if tw < S.T_RES: S.events.append([tw, 'thump', 0.35])
if T_FAIL: S.events += [[T_FAIL, 'crackle'], [T_FAIL + 0.1, 'pop'], [T_FAIL + 0.4, 'thump', 0.6]]
S.AMB = {'drone': 52, 'rumble': 0.02}
for e in EVS:
    if e['a'] > 0 and e['t'] < S.T_RES: S.events.append([max(0, e['t'] - 0.15), 'creak'])

def draw_bar(c, t, f):
    g = GAP[f]; surge = any(e['t'] <= t < e['t'] + e['d'] and e['a'] > 0 for e in EVS)
    bx = bar(c, g / 6.0, f'POPCORN GAP {g:.1f} m', good_bad_col(g / 4.0), 0.12 if surge else 0, bw=640, x_off=36)
    c.save(); c.translate(bx - 52, 236); c.set_source_rgb(*rgb('#f4ead0'))
    for (dx, dy, r_) in ((-12, 4, 14), (12, 4, 14), (0, -10, 15), (0, 12, 13)): c.arc(dx, dy, r_, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#e0c070')); c.arc(4, 2, 5, 0, 2 * math.pi); c.fill(); c.restore()
S.draw_bar = draw_bar

PIPES = [(300, 820), (790, 760), (560, 1000)]   # popcorn kettle chutes (x, y) on the back wall
PRNG = random.Random(99)
LUMPS = [(PRNG.uniform(0, W), PRNG.uniform(-14, 40), PRNG.uniform(14, 24), PRNG.random()) for _ in range(90)]
def draw_bg(c, t, f):
    # cinema lobby at night: dark maroon wall, dim marquee lights, dark movie posters, three big popcorn kettles
    c.set_source_rgb(*rgb('#1a1016')); c.rectangle(0, HEAD, W, H - HEAD); c.fill()
    c.set_source_rgb(*rgb('#2a1620')); c.rectangle(0, HEAD + 120, W, H); c.fill()
    c.set_source_rgb(*rgb('#3a1e28'))
    for xx in range(0, W, 90): c.rectangle(xx, HEAD + 120, 44, H); c.fill()   # velvet wall stripes
    for k in range(18):   # marquee bulbs along the top
        on = 0.35 + 0.25 * (math.sin(t * 3 + k * 0.9) > 0)
        c.set_source_rgba(1.0, 0.9, 0.7, on); c.arc(30 + k * 60, HEAD + 70, 9, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#2a2230')); rrect(c, 240, HEAD + 100, 600, 70, 10); c.fill()
    c.set_source_rgb(*rgb('#8a7a9a')); font(c, 44); c.move_to(390, HEAD + 152); c.show_text('NOW SHOWING')
    for (px, col) in ((70, '#2a3a5a'), (900, '#3a2a4a')):   # dim movie posters
        c.set_source_rgb(*rgb('#14101a')); rrect(c, px - 8, 560, 136, 196, 6); c.fill()
        c.set_source_rgb(*rgb(col)); c.rectangle(px, 568, 120, 180); c.fill()
        c.set_source_rgba(1, 1, 1, 0.15); c.arc(px + 60, 640, 34, 0, 2 * math.pi); c.fill(); c.rectangle(px + 16, 712, 88, 10); c.fill()
    for (px, py) in PIPES:   # popcorn kettle cabinets: dark red frame, glass full of popcorn
        c.set_source_rgb(*rgb('#6a1e22')); rrect(c, px - 100, py - 150, 200, 230, 14); c.fill()
        c.set_source_rgb(*rgb('#3a2a24')); c.rectangle(px - 80, py - 130, 160, 150); c.fill()
        c.set_source_rgb(*rgb('#d8c896'))
        for j in range(14): c.arc(px - 66 + (j * 37) % 132, py + 6 - (j // 4) * 16, 12, 0, 2 * math.pi); c.fill()
        c.set_source_rgb(*rgb('#8a8a90')); c.arc(px, py - 104, 22, 0, 2 * math.pi); c.fill()   # kettle
        c.set_source_rgba(1, 1, 1, 0.08); c.move_to(px - 70, py - 130); c.line_to(px - 30, py - 130); c.line_to(px - 70, py + 10); c.close_path(); c.fill()

def kern(c, x, y, r_, sh):
    c.set_source_rgb(*rgb('#efe4c4' if sh < 0.6 else '#e2d4ac'))
    c.arc(x - r_ * 0.4, y, r_ * 0.7, 0, 2 * math.pi); c.fill(); c.arc(x + r_ * 0.4, y + 2, r_ * 0.65, 0, 2 * math.pi); c.fill(); c.arc(x, y - r_ * 0.4, r_ * 0.6, 0, 2 * math.pi); c.fill()
    if sh > 0.7: c.set_source_rgb(*rgb('#d8b45a')); c.arc(x + r_ * 0.2, y + r_ * 0.2, r_ * 0.22, 0, 2 * math.pi); c.fill()

def draw_gush(c, t, f):
    for e in EVS:
        if e['a'] > 0 and e['t'] <= t < e['t'] + e['d'] and (e['t'] < S.T_RES or e['t'] < S.T_START):
            px, py = PIPES[e['pipe']]; k = min(1, (t - e['t']) / 0.2, (e['t'] + e['d'] - t) / 0.2)
            ly = SL[min(f, len(SL) - 1)]; dirx = 1 if px < 540 else -1
            for j in range(16):   # popcorn tumbling out of the chute in an arc down to the pile
                q = (t * 1.6 + j / 16) % 1; jx = 30 * math.sin(j * 2.7)
                xx = px + dirx * (40 + 150 * q) + jx; yy = py + 40 + (ly - py - 40) * q * q
                if q < 1 - k * 0.999 and k < 1: continue
                kern(c, xx, yy, 13, (j * 0.37) % 1)
        if e['a'] < 0 and e['t'] <= t < e['t'] + e['d'] and e['t'] < S.T_RES:   # the pile settles: a dip swirl
            ly = SL[min(f, len(SL) - 1)]; c.set_source_rgba(0.35, 0.28, 0.2, 0.6); c.set_line_width(5)
            for j in range(3): c.save(); c.translate(560, ly + 40); c.scale(1, 0.3); c.arc(0, 0, 50 + j * 45, t * 4 + j, t * 4 + j + 3.5); c.restore(); c.stroke()

def draw_leaks(c, t):
    for i, (px, py) in enumerate(PIPES):   # chute mouth under each kettle cabinet
        c.set_source_rgb(*rgb('#4a1418')); rrect(c, px - 34, py + 74, 68, 36, 8); c.fill()
        c.set_source_rgb(*rgb('#140c0e')); c.rectangle(px - 24, py + 92, 48, 18); c.fill()
        q = (t * 0.9 + i * 0.37) % 1; kern(c, px + 6 * math.sin(i + t), py + 112 + q * 140, 9, 0.3)

def choc_surf(x, t, ly): return ly + 8 * math.sin(x * 0.015 + t * 0.6) + 5 * math.sin(x * 0.05 - t * 0.9)
def draw_water(c, t, f):
    ly = SL[min(f, len(SL) - 1)]
    c.move_to(0, H)
    for x in range(0, W + 20, 20): c.line_to(x, choc_surf(x, t, ly) + 10)
    c.line_to(W, H); c.close_path(); c.set_source_rgb(*rgb('#d4c498')); c.fill()
    c.set_source_rgb(*rgb('#bcab7e')); c.rectangle(0, ly + 110, W, H - ly); c.fill()
    for (x, dy, r_, sh) in LUMPS:   # lumpy popcorn surface
        y = choc_surf(x, t, ly) + dy + 2 * math.sin(t * 5 + x)
        if dy > 25: kern(c, x, y + 30, r_ * 0.8, min(sh, 0.65))
        else: kern(c, x, y, r_, sh)

def draw_deck(c, t):
    for (x0, x1) in ((0, XMIN - R), (XMAX + R, W)):   # stacks of striped popcorn buckets = walls
        c.set_source_rgb(*rgb('#2a1a1e')); c.rectangle(x0, 760, x1 - x0, H - 760); c.fill()
        for k, yy in enumerate(range(760, H, 92)):
            c.save(); c.translate((x0 + x1) / 2, yy)
            w0 = (x1 - x0) * 0.42
            c.move_to(-w0, 6); c.line_to(w0, 6); c.line_to(w0 * 0.8, 88); c.line_to(-w0 * 0.8, 88); c.close_path()
            c.set_source_rgb(*rgb('#d8d0c8')); c.fill_preserve(); c.clip()
            c.set_source_rgb(*rgb('#a8343a'))
            for sx in range(-90, 90, 30): c.move_to(sx, 0); c.line_to(sx + 14, 0); c.line_to(sx + 10, 96); c.line_to(sx - 4, 96); c.close_path(); c.fill()
            c.reset_clip()
            c.set_source_rgb(*rgb('#e2d4ac'))
            for j in range(4): c.arc(-w0 + 14 + j * (w0 * 2 - 28) / 3, 4, 13, 0, 2 * math.pi); c.fill()
            c.restore()
    c.set_source_rgb(*rgb('#8aa8b8')); c.rectangle(XMIN - R, GRATE, XMAX - XMIN + 2 * R, 22); c.fill()   # glass counter top
    c.set_source_rgba(1, 1, 1, 0.35); c.rectangle(XMIN - R, GRATE, XMAX - XMIN + 2 * R, 5); c.fill()
    c.set_source_rgb(*rgb('#4a2a30')); c.rectangle(XMIN - R, GRATE + 22, XMAX - XMIN + 2 * R, 10); c.fill()
    c.set_source_rgb(*rgb('#5a5a64')); c.set_line_width(12)
    for x in (XMIN + 20, 450, 680, XMAX - 40):   # steel legs
        c.move_to(x, GRATE + 32); c.line_to(x, H); c.stroke()
    c.set_source_rgb(*rgb('#3a6aa0')); rrect(c, 640, GRATE - 46, 30, 46, 4); c.fill()   # a soda cup on the counter (decor)
    c.set_source_rgb(*rgb('#d8d0c8')); c.rectangle(636, GRATE - 50, 38, 6); c.fill(); c.set_line_width(4); c.move_to(660, GRATE - 50); c.line_to(668, GRATE - 74); c.stroke()

def draw_ruler(c, f):
    ly = SL[min(f, len(SL) - 1)]; x = 1000
    if ly - GRATE < 10: return
    c.set_source_rgba(0.9, 0.85, 0.7, 0.6); c.set_line_width(4); c.set_dash([10, 8]); c.move_to(x, GRATE + 24); c.line_to(x, ly); c.stroke(); c.set_dash([])
    for yy in (GRATE + 24, ly): c.move_to(x - 16, yy); c.line_to(x + 16, yy); c.stroke()

PS = Particles(4)
def render(f, c):
    t = f / FPS; fi = min(f, len(GX) - 1); shake = (0, 0)
    if any(e['t'] <= t < e['t'] + 0.25 and e['a'] > 0 for e in EVS) and t < S.T_RES: shake = (rng.uniform(-3, 3), rng.uniform(-3, 3))
    c.save(); c.translate(*shake)
    draw_bg(c, t, f); draw_leaks(c, t); draw_deck(c, t)
    soaked = T_FAIL is not None and t >= T_FAIL
    if END.carried(t) or t >= END.T_GRAB: gx, gy = (END.carry_xy(t) if END.carried(t) else S.GRAB)
    elif soaked: k = ease((t - T_FAIL) / 0.35); gx = FX; gy = lerp(FY, S.GRAB[1], k) + 6 * math.sin(t * 3) * k
    else:
        gx, gy = GX[fi], GYS[fi]
        h = max(0, GRATE - R - gy); kk = 1 / (1 + h / 220)
        c.set_source_rgba(0, 0, 0, 0.3 * kk); c.save(); c.translate(gx, GRATE + 2); c.scale(R * (0.5 + 0.4 * kk), 8); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    g = GAP[fi]
    mood = 'happy' if (t >= S.T_END and S.OUTCOME == 'win') else ('scared' if soaked or g < 1.5 else 'worried')
    draw_blob(c, t, gx, gy, mood, 0, R=R, dizzy=soaked and t > T_FAIL + 0.5)
    if soaked and t > T_FAIL + 0.2:
        for j in range(5): kern(c, gx - 40 + j * 20, gy - R * 0.55 + 6 * math.sin(j * 2.1), 11, (j * 0.31) % 1)
    draw_ruler(c, f)
    draw_water(c, t, f); draw_gush(c, t, f)
    if T_FAIL and abs(t - T_FAIL) < 0.5 / FPS: PS.spawn(FX, SL[fi], 24, (0.94, 0.9, 0.78), 650, 0.7, grav=2000, r=10)
    for (tl, xl, imp) in ball.landings:
        if abs(t - tl) < 0.5 / FPS and tl < S.T_RES: PS.spawn(xl, GRATE, 5, (0.75, 0.8, 0.85), 200, 0.35, grav=900, r=4)
    PS.draw(c)
    END.draw_claw(c, t)
    c.restore()
    END.header(c, t, fi)

if __name__ == '__main__':
    if sys.argv[1] == 'sim':
        rs = int(S.T_RES * FPS) - 1
        print(SEED, S.OUTCOME, round(S.T_RES - S.T_START, 2), 'mingap', round(min(GAP[int(S.T_START * FPS):rs + 1]), 2), 'final', round(GAP[rs], 2), 'gulps', len([e for e in EVS if e['a'] < 0 and e['t'] < S.T_RES]), 'dur', S.DUR); sys.exit()
    run(S, render)
