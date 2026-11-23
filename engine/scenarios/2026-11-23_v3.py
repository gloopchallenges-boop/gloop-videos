"""2026-11-23 v3 — RISING DANGER – WATER GAP m: the WAVE POOL (STYLE-TEST video: sunny water park, rule+question card,
streak badge, subscribe outro; based on 2026-11-18 v2 foam flood). Gloop is a passive rigid ball bouncing on a long
white pool-side bench between two stacks of swim rings (walls). Pool water rises from frame 0 at a seeded-random rate:
wave-machine outlets on the back wall gush (surges) and the pool drain sometimes gulps it back. WATER GAP = distance
from the water up to the bench. If the water touches Gloop he's washed off = fail (soaked & dizzy, claw collects him)."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the wave pool'
SEED = int(os.environ.get('SEED', 13))
rng = random.Random(SEED)

class S: pass
S.HOOK2 = 'THE WAVE POOL?'; S.HOOK2_SIZE = 92; S.FAIL_WORD = 'SPLASH!'; S.FAIL_SIZE = 150
S.CARD = ['The pool keeps *RISING|#3aa0d8*', 'Will Gloop stay *DRY*?']; S.STREAK = int(os.environ.get('STREAK', 1)); S.CTA = True
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
    if e['t'] < S.T_RES: S.events.append([e['t'], 'splash' if e['a'] > 0 else 'whoosh']); S.events.append([e['t'], 'rumble', min(e['d'], 1.2)])
for (tl, xl, imp) in ball.landings:
    if tl < S.T_RES: S.events.append([tl, 'hop'])
for tw in ball.walls:
    if tw < S.T_RES: S.events.append([tw, 'thump', 0.35])
if T_FAIL: S.events += [[T_FAIL, 'splash'], [T_FAIL + 0.1, 'pop'], [T_FAIL + 0.4, 'splash']]
S.AMB = {'drone': 52, 'rumble': 0.02}
for e in EVS:
    if e['a'] > 0 and e['t'] < S.T_RES: S.events.append([max(0, e['t'] - 0.15), 'creak'])

def draw_bar(c, t, f):
    g = GAP[f]; surge = any(e['t'] <= t < e['t'] + e['d'] and e['a'] > 0 for e in EVS)
    bx = bar(c, g / 6.0, f'WATER GAP {g:.1f} m', good_bad_col(g / 4.0), 0.12 if surge else 0, bw=640, x_off=36)
    c.save(); c.translate(bx - 52, 231); c.set_source_rgb(*rgb('#cfe6f5'))
    c.move_to(0, -28); c.curve_to(10, -10, 24, 2, 24, 12); c.curve_to(24, 26, 12, 32, 0, 32); c.curve_to(-12, 32, -24, 26, -24, 12); c.curve_to(-24, 2, -10, -10, 0, -28); c.fill()
    c.set_source_rgba(1, 1, 1, 0.6); c.arc(-8, 12, 6, 0, 2 * math.pi); c.fill(); c.restore()
S.draw_bar = draw_bar

RINGCOL = ['#e86a9a', '#3aa0d8', '#5ac07a', '#a070d0', '#f0f0f0']
PIPES = [(300, 820), (790, 760), (560, 1000)]   # wave-machine outlets (x, y) on the back wall
CLOUDS = [(160, 470, 1.0), (620, 420, 1.3), (900, 560, 0.8)]
def draw_bg(c, t, f):
    # bright sunny water park: sky, clouds, a twisty slide tower, pastel tiled back wall with wave-machine outlets
    c.set_source_rgb(*rgb('#8fd0f2')); c.rectangle(0, HEAD, W, H - HEAD); c.fill()
    c.set_source_rgb(*rgb('#fdfbe8')); c.arc(940, HEAD + 110, 50, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(1, 1, 1)
    for (cx, cy, sc) in CLOUDS:
        cx = (cx + t * 12 * sc) % (W + 200) - 100
        for (dx, dy, r) in ((0, 0, 40), (40, -16, 48), (86, 0, 38), (44, 14, 36)): c.arc(cx + dx * sc, cy + dy * sc, r * sc, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#d8e4ee')); c.rectangle(80, 500, 26, 200); c.rectangle(250, 470, 26, 230); c.fill()   # slide tower legs
    c.set_source_rgb(*rgb('#e86a9a')); c.set_line_width(42); c.set_line_cap(cairo.LINE_CAP_ROUND)
    c.move_to(60, 480); c.curve_to(300, 470, 330, 560, 120, 600); c.curve_to(-40, 640, 300, 690, 420, 640); c.stroke()
    c.set_source_rgb(*rgb('#3aa0d8')); c.set_line_width(42)
    c.move_to(1020, 520); c.curve_to(800, 530, 780, 620, 980, 650); c.curve_to(1100, 670, 820, 700, 700, 690); c.stroke()
    c.set_line_cap(cairo.LINE_CAP_BUTT)
    c.set_source_rgb(*rgb('#d6f0ee')); c.rectangle(0, 680, W, H - 680); c.fill()   # tiled back wall
    c.set_source_rgb(*rgb('#bfe2e0'))
    for yy in range(680, H, 70): c.rectangle(0, yy, W, 4); c.fill()
    for xx in range(0, W, 70): c.rectangle(xx, 680, 4, H - 680); c.fill()
    c.set_source_rgb(*rgb('#3aa0d8')); c.rectangle(0, 680, W, 18); c.fill()
    c.set_source_rgb(*rgb('#2a6a9a')); font(c, 40); c.move_to(420, 770); c.show_text('WAVE POOL')
    for (px, py) in PIPES:   # big square wave-machine housing behind each outlet
        c.set_source_rgb(*rgb('#a8d8e8')); rrect(c, px - 100, py - 100, 200, 200, 22); c.fill()

def draw_gush(c, t, f):
    for e in EVS:
        if e['a'] > 0 and e['t'] <= t < e['t'] + e['d'] and (e['t'] < S.T_RES or e['t'] < S.T_START):
            px, py = PIPES[e['pipe']]; k = min(1, (t - e['t']) / 0.2, (e['t'] + e['d'] - t) / 0.2)
            ly = SL[min(f, len(SL) - 1)]; dirx = 1 if px < 540 else -1
            c.set_line_cap(cairo.LINE_CAP_ROUND)
            for wdt, col in ((46, (0.25, 0.65, 0.92, 0.95)), (20, (0.75, 0.92, 1.0, 0.95))):
                c.set_source_rgba(*col); c.set_line_width(wdt * k)
                c.move_to(px, py); c.curve_to(px + dirx * 70, py, px + dirx * 100, py + 80, px + dirx * 110, ly + 10); c.stroke()
            for j in range(5):
                q = (t * 2.4 + j / 5) % 1; dx_ = px + dirx * 110 * min(1, q * 3); dy_ = lerp(py, ly, q * q)
                c.set_source_rgba(0.9, 0.97, 1.0, 0.9 * k); c.arc(dx_ + 10 * math.sin(j * 2.3), dy_, 9, 0, 2 * math.pi); c.fill()
            c.set_source_rgba(0.95, 0.99, 1.0, 0.9 * k)
            for j in range(4): c.arc(px + dirx * 110 + (j - 1.5) * 26, ly - 8 - 20 * abs(math.sin(t * 9 + j)), 8, 0, 2 * math.pi); c.fill()
        if e['a'] < 0 and e['t'] <= t < e['t'] + e['d'] and e['t'] < S.T_RES:   # pool drain gulp: swirl
            ly = SL[min(f, len(SL) - 1)]; c.set_source_rgba(0.9, 0.97, 1, 0.8); c.set_line_width(5)
            for j in range(3): c.save(); c.translate(560, ly + 30); c.scale(1, 0.3); c.arc(0, 0, 50 + j * 45, t * 6 + j, t * 6 + j + 4); c.restore(); c.stroke()

def draw_leaks(c, t):
    for i, (px, py) in enumerate(PIPES):   # round outlet grates with water churning behind
        c.set_source_rgb(*rgb('#f0f6fa')); c.arc(px, py, 68, 0, 2 * math.pi); c.fill()
        c.set_source_rgb(*rgb('#2a7ab8')); c.arc(px, py, 54, 0, 2 * math.pi); c.fill()
        c.set_source_rgb(*rgb('#d0e8f4')); c.set_line_width(6)
        for dy in (-30, -10, 10, 30):
            hw = math.sqrt(max(0, 54 * 54 - dy * dy)); c.move_to(px - hw, py + dy); c.line_to(px + hw, py + dy); c.stroke()
        q = (t * 1.0 + i * 0.37) % 1; c.set_source_rgba(0.5, 0.8, 1, 0.9 * (1 - q)); c.arc(px, py + 60 + q * 120, 7, 0, 2 * math.pi); c.fill()

def choc_surf(x, t, ly): return ly + 10 * math.sin(x * 0.012 + t * 1.6) + 5 * math.sin(x * 0.04 - t * 2.1)
def draw_water(c, t, f):
    ly = SL[min(f, len(SL) - 1)]
    c.move_to(0, H)
    for x in range(0, W + 20, 20): c.line_to(x, choc_surf(x, t, ly))
    c.line_to(W, H); c.close_path(); c.set_source_rgba(0.22, 0.68, 0.88, 0.96); c.fill()
    c.set_source_rgba(0.16, 0.56, 0.78, 1); c.rectangle(0, ly + 90, W, H - ly); c.fill()
    c.set_source_rgba(1, 1, 1, 0.95); c.set_line_width(7)   # white wave crest
    for x in range(0, W + 20, 20): (c.move_to if x == 0 else c.line_to)(x, choc_surf(x, t, ly))
    c.stroke()
    c.set_source_rgba(1, 1, 1, 0.35); c.set_line_width(4)   # light ripples
    for j in range(5):
        xx = (j * 230 + t * 40) % (W + 100) - 50; c.move_to(xx, ly + 40 + j * 9); c.line_to(xx + 80, ly + 40 + j * 9); c.stroke()
    c.set_source_rgba(1, 1, 1, 0.12)   # tile lines seen through the water
    for yy in range(int(ly) + 120, H, 70): c.rectangle(0, yy, W, 3); c.fill()

def draw_deck(c, t):
    for (x0, x1) in ((0, XMIN - R), (XMAX + R, W)):   # stacks of swim rings = walls
        c.set_source_rgb(*rgb('#b8dce8')); c.rectangle(x0, 760, x1 - x0, H - 760); c.fill()
        for k, yy in enumerate(range(760, H, 64)):
            col = RINGCOL[(k + (x0 > 0) * 2) % 5]
            c.set_source_rgb(*rgb(col)); rrect(c, x0 + 4, yy + 4, x1 - x0 - 8, 56, 28); c.fill()
            c.set_source_rgba(1, 1, 1, 0.5); rrect(c, x0 + 20, yy + 12, x1 - x0 - 60, 10, 5); c.fill()
    c.set_source_rgb(*rgb('#ffffff')); c.rectangle(XMIN - R, GRATE, XMAX - XMIN + 2 * R, 26); c.fill()   # white pool-side bench
    c.set_source_rgb(*rgb('#3aa0d8')); c.rectangle(XMIN - R, GRATE + 20, XMAX - XMIN + 2 * R, 8); c.fill()
    c.set_source_rgb(*rgb('#9ab8c8')); c.set_line_width(12)
    for x in (XMIN + 20, 450, 680, XMAX - 40):   # steel legs
        c.move_to(x, GRATE + 28); c.line_to(x, H); c.stroke()
    c.set_source_rgb(*rgb('#5ac07a')); rrect(c, 620, GRATE - 22, 96, 22, 8); c.fill()   # a folded green towel on the bench (decor)
    c.set_source_rgb(*rgb('#ffffff')); c.rectangle(620, GRATE - 14, 96, 4); c.fill()

def draw_ruler(c, f):
    ly = SL[min(f, len(SL) - 1)]; x = 1000
    if ly - GRATE < 10: return
    c.set_source_rgba(0.1, 0.3, 0.5, 0.7); c.set_line_width(4); c.set_dash([10, 8]); c.move_to(x, GRATE + 24); c.line_to(x, ly); c.stroke(); c.set_dash([])
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
        c.set_source_rgba(0.5, 0.82, 1.0, 0.95)
        for j in range(4): c.arc(gx - 36 + j * 24, gy - R * 0.2 + 30 * ((t * 1.3 + j * 0.27) % 1), 9, 0, 2 * math.pi); c.fill()
    draw_ruler(c, f)
    draw_water(c, t, f); draw_gush(c, t, f)
    if T_FAIL and abs(t - T_FAIL) < 0.5 / FPS: PS.spawn(FX, SL[fi], 24, (0.6, 0.85, 1.0), 650, 0.7, grav=2000, r=9)
    for (tl, xl, imp) in ball.landings:
        if abs(t - tl) < 0.5 / FPS and tl < S.T_RES: PS.spawn(xl, GRATE, 5, (0.75, 0.85, 0.9), 200, 0.35, grav=900, r=4)
    PS.draw(c)
    END.draw_claw(c, t)
    c.restore()
    END.header(c, t, fi)

if __name__ == '__main__':
    if sys.argv[1] == 'sim':
        rs = int(S.T_RES * FPS) - 1
        print(SEED, S.OUTCOME, round(S.T_RES - S.T_START, 2), 'mingap', round(min(GAP[int(S.T_START * FPS):rs + 1]), 2), 'final', round(GAP[rs], 2), 'gulps', len([e for e in EVS if e['a'] < 0 and e['t'] < S.T_RES]), 'dur', S.DUR); sys.exit()
    run(S, render)
