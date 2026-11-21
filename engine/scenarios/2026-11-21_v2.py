"""2026-11-21 v2 — WHO FIRST: the HUNGRY HERON (based on 2026-11-19 v3: a giant grey heron perched on a branch above a marsh at night spears its beak down at the blobs; original eel text follows). Gloop (orange) and two rival blobs (blue, pink) are passive
rigid balls (Ball) bouncing on the wet sand of a rocky cove at night between two barnacled rock pillars; they collide
with each other (equal-mass elastic). A giant moray eel hiding in a crevice of the big rock at the back lunges out at
seeded-random times at where a random remaining blob WAS a moment ago — its jaws grab whoever they touch.
Gloop grabbed = fail (spat back out slimy & dizzy). Timer ends ungrabbed = win. (Adapted from 2026-11-14 v4.)"""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the hungry heron'
SEED = int(os.environ.get('SEED', 8))
rng = random.Random(SEED)

class S: pass
S.HOOK2 = 'THE HUNGRY HERON?'; S.HOOK2_SIZE = 90; S.FAIL_WORD = 'SNATCHED!'; S.FAIL_SIZE = 160
S.T_START = HOOK_T; S.TL = 13.0; S.T_END = S.T_START + S.TL
GROUND = 1610; R = 56; XMIN, XMAX = 160, 920
MOUTH = (520, 1080); TIP_R = 56; T_OUT, T_HOLD, T_BACK = 0.22, 0.08, 0.35
NAMES = ['GLOOP', 'BLUE', 'ROSIE']
SKINS = [('#ffd36b', '#ff8a1f', '#c45a00'), ('#b8dcff', '#4a90d0', '#2a5a8a'), ('#ffd0e4', '#e070a0', '#8a3a5a')]

TER = Terrain(GROUND, seed=SEED, bumps=4, amp=10, soft=False)
xs0 = rng.sample([250, 420, 600, 780], 3)
balls = [Ball(xs0[i], TER, R=R, seed=SEED * 3 + i, xmin=XMIN, xmax=XMAX, hop=rng.uniform(220, 300)) for i in range(3)]
STR = []; t = 0.45
while t < S.T_END + 1:
    STR.append({'t': t}); t += rng.uniform(1.2, 2.2)
N0 = int(40 * FPS); POS = [], ; POS = []; EATEN_AT = [None, None, None]; T_FAIL = None; HIST = []
caught = {}   # blob -> strike index
def tongue_tip(s, t):
    k = t - s['t']
    if k < 0 or k > T_OUT + T_HOLD + T_BACK: return None
    tx, ty = s['tx'], s['ty']
    if k < T_OUT: a = ease(k / T_OUT)
    elif k < T_OUT + T_HOLD: a = 1
    else: a = 1 - ease((k - T_OUT - T_HOLD) / T_BACK)
    return lerp(MOUTH[0], tx, a), lerp(MOUTH[1], ty, a), k < T_OUT + T_HOLD
for f in range(N0):
    t = f / FPS
    HIST.append([(b.x, b.y) for b in balls])
    for si, s in enumerate(STR):
        if 'tx' not in s and t >= s['t'] - 0.001:
            alive = [i for i in range(3) if EATEN_AT[i] is None and i not in caught.values()]
            if s['t'] < S.T_START or not alive or T_FAIL is not None:
                s['tx'], s['ty'], s['who'] = rng.choice((XMIN + 20, XMAX - 20)), GROUND - 40, None
            else:
                w = rng.choice(alive); lag = int(rng.uniform(0.3, 0.55) * FPS)
                px, py = HIST[max(0, f - lag)][w]; s['tx'], s['ty'], s['who'] = px, py, w
    for i, b in enumerate(balls):
        if EATEN_AT[i] is None and i not in caught: b.step(t)
    for i in range(3):   # rival collisions
        for j in range(i + 1, 3):
            a, b = balls[i], balls[j]
            if EATEN_AT[i] is not None or EATEN_AT[j] is not None or i in caught or j in caught: continue
            dx, dy = b.x - a.x, b.y - a.y; d = math.hypot(dx, dy)
            if 0 < d < 2 * R:
                nx, ny = dx / d, dy / d; ov = 2 * R - d
                a.x -= nx * ov / 2; a.y -= ny * ov / 2; b.x += nx * ov / 2; b.y += ny * ov / 2
                rel = (a.vx - b.vx) * nx + (a.vy - b.vy) * ny
                if rel > 0:
                    j_ = rel * 0.95; a.vx -= j_ * nx; a.vy -= j_ * ny; b.vx += j_ * nx; b.vy += j_ * ny
    for si, s in enumerate(STR):   # tongue catches whoever the extending tip touches
        if 'tx' not in s or s['t'] < S.T_START or T_FAIL is not None and s['t'] > T_FAIL: continue
        tip = tongue_tip(s, t)
        if tip and tip[2] and si not in caught.values():
            for i, b in enumerate(balls):
                if EATEN_AT[i] is None and i not in caught and t < S.T_END and math.hypot(b.x - tip[0], b.y - tip[1]) < R + TIP_R:
                    caught[i] = si; s['got'] = i; s['tcatch'] = t
                    if i == 0 and T_FAIL is None: T_FAIL = t
                    break
    for i, si in list(caught.items()):
        s = STR[si]; tip = tongue_tip(s, t)
        if tip is None: EATEN_AT[i] = t; del caught[i]
    POS.append([(b.x, b.y) for b in balls])
S.OUTCOME = 'fail' if T_FAIL else 'win'
S.T_RES = T_FAIL if T_FAIL else S.T_END
END = S.END = Ending(S)
SPIT_T = (EATEN_AT[0] + 0.5) if T_FAIL else None
if T_FAIL:   # anteater spits Gloop out sticky & dizzy
    sx, sy = 540, GROUND - R
    S.GRAB = (sx, sy)
else:
    gi = min(int(END.T_GRAB * FPS), N0 - 1); S.GRAB = POS[gi][0]
S.events = []
for s in STR:
    if s['t'] < S.T_RES + 0.1: S.events.append([s['t'], 'whoosh'])
    if 'got' in s and s['tcatch'] <= S.T_RES + 0.01: S.events.append([s['tcatch'], 'pop']); S.events.append([s['tcatch'] + 0.3, 'thump', 0.8])
for b in balls:
    for (tl, xl, imp) in b.landings:
        if tl < S.T_RES + 1.0: S.events.append([tl, 'hop'])
if T_FAIL: S.events.append([SPIT_T, 'pop'])
S.AMB = {'drone': 42, 'wind': 0.03}
def eaten(i, t): return EATEN_AT[i] is not None and t >= EATEN_AT[i]

def draw_bar(c, t, f):
    for i in range(3):
        x = W / 2 - 170 + i * 170; y = 232; gone = eaten(i, t) or (i in [s.get('got') for s in STR if s.get('tcatch', 99) <= t])
        sk = SKINS[i] if not gone else ('#5a5664', '#3a3644', '#2a2634')
        c.save(); c.translate(x, y)
        c.set_source_rgb(0, 0, 0); c.arc(0, 0, 36, 0, 2 * math.pi); c.fill()
        c.set_source_rgb(*rgb(sk[1])); c.arc(0, 0, 30, 0, 2 * math.pi); c.fill()
        c.set_source_rgb(1, 1, 1); c.arc(-10, -4, 7, 0, 2 * math.pi); c.fill(); c.arc(10, -4, 7, 0, 2 * math.pi); c.fill()
        c.set_source_rgb(0.1, 0.06, 0.05); c.arc(-9, -3, 3.5, 0, 2 * math.pi); c.fill(); c.arc(11, -3, 3.5, 0, 2 * math.pi); c.fill()
        if gone:
            c.set_source_rgb(*rgb('#ff4d4d')); c.set_line_width(8); c.move_to(-26, -26); c.line_to(26, 26); c.stroke(); c.move_to(26, -26); c.line_to(-26, 26); c.stroke()
        c.restore()
        if i == 0: text_at(c, 'YOU?', x, y + 52, 0.0001 + 22, rgb('#ffd36b'), lw=5) if False else None
S.draw_bar = draw_bar



stars = [(rng.uniform(0, W), rng.uniform(HEAD, 950), rng.uniform(1.2, 2.4)) for _ in range(45)]
BODY = (700, 830)
def cattail(c, x, base, h, sway, t):
    c.set_source_rgb(*rgb('#2c4a2a')); c.set_line_width(7)
    tx = x + sway * 14 * math.sin(t * 1.3 + x)
    c.move_to(x, base); c.curve_to(x, base - h * 0.5, tx, base - h * 0.8, tx, base - h); c.stroke()
    c.set_source_rgb(*rgb('#5a3a24')); rrect(c, tx - 9, base - h - 10, 18, 70, 9); c.fill()
def draw_bg(c, t):
    c.set_source_rgb(*rgb('#111827')); c.rectangle(0, HEAD, W, H - HEAD); c.fill()
    c.set_source_rgba(0.85, 0.9, 1, 0.35)
    for x, y, r in stars[:30]: c.arc(x, y * 0.6 + 150, r, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#dcd8c0')); c.arc(250, 560, 36, 0, 2 * math.pi); c.fill()
    # far treeline + marsh water
    c.set_source_rgb(*rgb('#16202a'))
    for k in range(12): c.arc(k * 100, 1180 + (k % 3) * 14, 90, math.pi, 2 * math.pi); c.fill()
    c.rectangle(0, 1180, W, 40); c.fill()
    c.set_source_rgb(*rgb('#1a2c3a')); c.rectangle(0, 1210, W, 420); c.fill()
    c.set_source_rgba(0.9, 0.88, 0.75, 0.18)
    for i in range(6): c.rectangle(215 + 8 * math.sin(t * 2 + i), 1240 + i * 46, 70 - i * 8, 5); c.fill()
    c.set_source_rgba(1, 1, 1, 0.05)
    for i in range(7): c.rectangle(0, 1250 + i * 52 + 4 * math.sin(t * 1.2 + i), W, 3); c.fill()
    for i, x in enumerate(range(140, 960, 95)): cattail(c, x, 1330, 150 + (i * 47) % 90, 1, t)
    # dead tree with the branch the heron stands on (from the right)
    c.set_source_rgb(*rgb('#3a3026')); c.set_line_width(34); c.set_line_cap(cairo.LINE_CAP_ROUND)
    c.move_to(1040, 1330); c.curve_to(1000, 1100, 1010, 900, 980, 720); c.stroke()
    c.set_line_width(22); c.move_to(990, 900); c.curve_to(880, 900, 760, 920, 600, 905); c.stroke()
    c.set_line_width(12); c.move_to(985, 760); c.line_to(880, 640); c.stroke(); c.move_to(700, 912); c.line_to(640, 860); c.stroke()
    c.set_line_cap(cairo.LINE_CAP_BUTT)

def heron_body(c, t):
    bx, by = BODY
    c.set_source_rgb(*rgb('#3a3e44')); c.set_line_width(7)   # legs gripping the branch
    for dx in (-14, 14): c.move_to(bx + dx, by + 10); c.line_to(bx + dx + 4, by + 70); c.stroke()
    c.set_source_rgb(*rgb('#8a96a4')); c.save(); c.translate(bx, by - 40); c.rotate(-0.35); c.scale(110, 62); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    c.set_source_rgb(*rgb('#5e6a78')); c.save(); c.translate(bx + 40, by - 34); c.rotate(-0.35); c.scale(90, 40); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()   # folded wing
    c.set_source_rgb(*rgb('#3e4652')); c.move_to(bx + 110, by - 20); c.line_to(bx + 190, by + 10); c.line_to(bx + 120, by - 50); c.close_path(); c.fill()   # tail feathers

def snake_head(t):
    for s in STR:
        if s['t'] > S.T_RES + 0.05 and not (T_FAIL and s['t'] <= T_FAIL): continue
        tip = tongue_tip(s, t)
        if tip: return tip[0], tip[1], (1.0 if tip[2] else 0.15)
    return MOUTH[0] + 8 * math.sin(t * 2.1), MOUTH[1] + 6 * math.sin(t * 4.2), 0.0

def draw_snake(c, t, hx, hy, mo, bulge):   # heron neck + head; (hx, hy) = beak tip
    nx0, ny0 = BODY[0] - 80, BODY[1] - 70
    ang = math.atan2(hy - ny0, hx - nx0)
    if math.hypot(hx - nx0, hy - ny0) < 140: ang = math.atan2(1, -0.4)
    dx, dy = math.cos(ang), math.sin(ang)
    headx, heady = hx - dx * 100, hy - dy * 100
    c.set_line_cap(cairo.LINE_CAP_ROUND)
    c.set_source_rgb(*rgb('#c8ccd4')); c.set_line_width(36 + 10 * bulge)
    mxp, myp = (nx0 + headx) / 2 - 60, (ny0 + heady) / 2 - 30   # S-curved neck
    c.move_to(nx0, ny0); c.curve_to(mxp - 30, myp - 40, mxp + 30, myp + 40, headx, heady); c.stroke()
    c.set_line_cap(cairo.LINE_CAP_BUTT)
    c.save(); c.translate(headx, heady); c.rotate(ang)
    c.set_source_rgb(*rgb('#dfe2e8')); c.arc(0, 0, 34, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#2a2e36')); c.move_to(-30, -20); c.curve_to(-60, -36, -90, -30, -110, -16); c.line_to(-30, -8); c.close_path(); c.fill()   # black crest plume
    gap = 9 if mo >= 1.0 else 2
    c.set_source_rgb(*rgb('#e0b83a'))
    c.move_to(20, -12); c.line_to(104, -gap * 0.3); c.line_to(22, -2); c.close_path(); c.fill()
    c.move_to(20, 4 + gap * 0.4); c.line_to(104, gap * 0.5); c.line_to(22, 14 + gap * 0.4); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#f0d040')); c.arc(4, -10, 9, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(0.05, 0.05, 0.05); c.arc(6, -10, 4.5, 0, 2 * math.pi); c.fill()
    c.restore()

def draw_floor(c):
    c.move_to(0, H)
    for x in range(0, W + 1, 6): c.line_to(x, TER.h[x])
    c.line_to(W, H); c.close_path(); c.set_source_rgb(*rgb('#3e3a2c')); c.fill()   # muddy bank
    c.set_source_rgb(*rgb('#55503a')); c.set_line_width(8)
    for x in range(0, W + 1, 6): (c.move_to if x == 0 else c.line_to)(x, TER.h[x] + 3)
    c.stroke()
    for i in range(8):   # little mud puddles + pebbles
        x = 60 + i * 130; y = GROUND + 80 + (i * 83) % 200
        c.set_source_rgba(0.1, 0.16, 0.2, 0.7) if i % 2 else c.set_source_rgb(*rgb('#5a5650'))
        c.save(); c.translate(x, y); c.scale(34 if i % 2 else 14, 9); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    for (x0, x1) in ((0, XMIN - R), (XMAX + R, W)):   # thick reed beds = walls
        c.set_source_rgb(*rgb('#22381f')); c.rectangle(x0 - 10, 1040, x1 - x0 + 20, H - 1040); c.fill()
        c.set_source_rgb(*rgb('#2e4a2a')); c.set_line_width(8)
        for k in range(int((x1 - x0) / 18) + 1):
            xx = x0 + k * 18; top = 980 + (k * 53) % 90
            c.move_to(xx, H); c.line_to(xx + 6, top); c.stroke()
        c.set_source_rgb(*rgb('#5a3a24'))
        for k in range(3): xx = x0 + 20 + k * (x1 - x0 - 30) / 3; rrect(c, xx, 960 + k * 30, 16, 60, 8); c.fill()

def render(f, c):
    t = f / FPS; fi = min(f, len(POS) - 1)
    c.save()
    draw_bg(c, t); heron_body(c, t)
    hx, hy, mo = snake_head(t)
    active = (None, (hx, hy, True)) if mo > 0 else None
    if SPIT_T and SPIT_T - 0.15 <= t < SPIT_T + 0.3: mo = 1.0
    bulge = 0.0
    for i in range(3):
        if EATEN_AT[i] and EATEN_AT[i] <= t < EATEN_AT[i] + 1.4 and not (i == 0 and SPIT_T and t >= SPIT_T): bulge = max(bulge, 1 - (t - EATEN_AT[i]) / 1.4 * 0.6)
    draw_snake(c, t, hx, hy, mo, bulge)
    draw_floor(c)
    for i in range(3):
        if eaten(i, t) and not (i == 0 and SPIT_T and t >= SPIT_T): continue
        x, y = POS[fi][i]
        for s in STR:   # being reeled in
            if s.get('got') == i and s['tcatch'] <= t:
                tip = tongue_tip(s, t)
                if tip: x, y = tip[0], tip[1]
        if i == 0 and SPIT_T and t >= SPIT_T:
            k = clamp((t - SPIT_T) / 0.5, 0, 1); x = lerp(MOUTH[0], S.GRAB[0], k); y = lerp(MOUTH[1], S.GRAB[1], k) - 260 * math.sin(math.pi * k)
            if t >= END.T_GRAB: x, y = S.GRAB
        if i == 0 and (END.carried(t) or (t >= END.T_GRAB)): x, y = (END.carry_xy(t) if END.carried(t) else S.GRAB)
        hh = max(0, TER.y(x) - R - y); kk = 1 / (1 + hh / 220)
        if not END.carried(t) or i:
            c.set_source_rgba(0, 0, 0, 0.25 * kk); c.save(); c.translate(x, TER.y(x) + 3); c.scale(R * (0.5 + 0.4 * kk), 8); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
        danger = active is not None and math.hypot(active[1][0] - x, active[1][1] - y) < 300
        if i == 0:
            mood = 'happy' if (t >= S.T_END and S.OUTCOME == 'win') else ('scared' if danger or T_FAIL and t >= T_FAIL else 'worried')
            slimy = SPIT_T and t >= SPIT_T
            draw_blob(c, t, x, y, mood, 0, R=R, skin=SKINS[0], dizzy=bool(slimy))
            if slimy:
                c.set_source_rgba(0.45, 0.5, 0.35, 0.6)
                for j in range(4): c.arc(x - 45 + j * 30, y - R - 10 - 30 * ((t * 1.2 + j * 0.27) % 1), 6, 0, 2 * math.pi); c.fill()
        else:
            draw_blob(c, t + i, x, y, 'scared' if danger else 'worried', 0, R=R, skin=SKINS[i], sweat=False)
    END.draw_claw(c, t)
    c.restore()
    END.header(c, t, fi)

if __name__ == '__main__':
    if sys.argv[1] == 'sim':
        print(SEED, S.OUTCOME, round(S.T_RES - S.T_START, 2), 'eaten', [(NAMES[i], round(EATEN_AT[i] - S.T_START, 1)) for i in range(3) if EATEN_AT[i]], 'strikes', len([s for s in STR if S.T_START <= s['t'] < S.T_RES]), 'dur', S.DUR); sys.exit()
    run(S, render)
