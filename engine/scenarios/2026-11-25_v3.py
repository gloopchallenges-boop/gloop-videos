"""2026-11-25 v3 — WHO FIRST: the GIANT SCORPION (based on 2026-11-23 v1 squid). Gloop (orange) + two rival blobs bounce as
passive rigid balls on the sand of a desert canyon at night between a sandstone pillar and a boulder stack. A giant
scorpion behind the dune ridge shoots its pincer at seeded-random times at where a random remaining blob WAS a moment
ago; the pincer grabs whoever it touches. Gloop grabbed = fail (tossed back out sandy & dizzy). Timer ends ungrabbed = win."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the giant scorpion'
SEED = int(os.environ.get('SEED', 1))
rng = random.Random(SEED)

class S: pass
S.HOOK2 = 'THE GIANT SCORPION?'; S.HOOK2_SIZE = 86; S.FAIL_WORD = 'PINCHED!'; S.FAIL_SIZE = 160
S.T_START = HOOK_T; S.TL = 12.5; S.T_END = S.T_START + S.TL
GROUND = 1600; R = 56; XMIN, XMAX = 160, 920
MOUTH = (620, 1125); TIP_R = 48; T_OUT, T_HOLD, T_BACK = 0.22, 0.08, 0.35
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
                w = rng.choice(alive); lag = int(rng.uniform(0.45, 0.8) * FPS)
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
BODY = (800, 1110)
def draw_bg(c, t):
    c.set_source_rgb(*rgb('#141428')); c.rectangle(0, HEAD, W, H - HEAD); c.fill()
    c.set_source_rgba(0.9, 0.9, 1, 0.35)
    for x, y, r in stars[:34]: c.arc(x, y * 0.6 + 150, r, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#e2dcc2')); c.arc(240, 560, 40, 0, 2 * math.pi); c.fill()
    # far mesas
    c.set_source_rgb(*rgb('#2a2236'))
    c.move_to(0, 1000); c.line_to(80, 1000); c.line_to(110, 880); c.line_to(330, 880); c.line_to(360, 1000); c.line_to(560, 1000)
    c.line_to(600, 930); c.line_to(700, 930); c.line_to(730, 1000); c.line_to(W, 1000); c.line_to(W, 1200); c.line_to(0, 1200); c.fill()
    # a saguaro cactus silhouette
    c.set_source_rgb(*rgb('#1e3028')); c.set_line_cap(cairo.LINE_CAP_ROUND); c.set_line_width(34)
    c.move_to(420, 1150); c.line_to(420, 900); c.stroke()
    c.set_line_width(24); c.move_to(420, 1030); c.line_to(370, 1030); c.line_to(370, 960); c.stroke()
    c.move_to(420, 1000); c.line_to(468, 1000); c.line_to(468, 930); c.stroke()
    c.set_line_cap(cairo.LINE_CAP_BUTT)

def heron_body(c, t):   # giant scorpion behind the dune ridge (tail curled up behind it)
    bx, by = BODY; bob = 5 * math.sin(t * 1.8)
    c.save(); c.translate(bx, by + bob)
    c.set_line_cap(cairo.LINE_CAP_ROUND)
    P0, P1, P2, P3 = (70, -30), (210, -140), (190, -330), (40, -370)
    tail = []
    for k in range(13):
        q = k / 12; u = 1 - q
        tail.append((u ** 3 * P0[0] + 3 * u * u * q * P1[0] + 3 * u * q * q * P2[0] + q ** 3 * P3[0], u ** 3 * P0[1] + 3 * u * u * q * P1[1] + 3 * u * q * q * P2[1] + q ** 3 * P3[1]))
    for k, (x, y) in enumerate(tail):   # segmented tail curling over
        r = 46 - k * 2.2
        c.set_source_rgb(*rgb('#4a2a1e')); c.arc(x, y, r + 4, 0, 2 * math.pi); c.fill()
    for k, (x, y) in enumerate(tail):
        r = 46 - k * 2.2
        c.set_source_rgb(*rgb('#6a3a2a' if k % 2 else '#7e4630')); c.arc(x, y, r, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#4a2a1e'))   # stinger (just there, never used)
    c.move_to(30, -400); c.curve_to(-30, -410, -55, -370, -45, -330); c.curve_to(-20, -345, 0, -345, 20, -340); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#6a3a2a')); c.save(); c.scale(1.5, 1.0); c.arc(0, 0, 110, math.pi, 2 * math.pi); c.restore(); c.fill()   # body shell
    c.set_source_rgb(*rgb('#7e4630'))
    for k in range(4): c.save(); c.translate(0, -18 - k * 0); c.scale(1.5 - k * 0.28, 0.8 - k * 0.15); c.arc(0, 0, 110 - k * 12, math.pi * 1.1, math.pi * 1.9); c.restore(); c.set_line_width(6); c.stroke()
    c.set_source_rgb(*rgb('#4a2a1e')); c.set_line_width(12)
    for s in (-1, 1):   # legs
        for k in range(3): c.move_to(s * (60 + k * 40), -20); c.line_to(s * (110 + k * 45), -70 + k * 10); c.line_to(s * (130 + k * 45), 10); c.stroke()
    for ex in (-28, 28):   # little eyes
        c.set_source_rgb(*rgb('#e8e2c8')); c.arc(ex - 80, -50, 16, 0, 2 * math.pi); c.fill()
        c.set_source_rgb(0.05, 0.05, 0.08); c.arc(ex - 78, -48, 7, 0, 2 * math.pi); c.fill()
    c.set_line_cap(cairo.LINE_CAP_BUTT)
    c.restore()

def snake_head(t):
    for s in STR:
        if s['t'] > S.T_RES + 0.05 and not (T_FAIL and s['t'] <= T_FAIL): continue
        tip = tongue_tip(s, t)
        if tip: return tip[0], tip[1], (1.0 if tip[2] else 0.15)
    return MOUTH[0] + 8 * math.sin(t * 2.1), MOUTH[1] + 6 * math.sin(t * 4.2), 0.0

def draw_snake(c, t, hx, hy, mo, bulge):   # segmented scorpion arm from behind the ridge; (hx, hy) = pincer
    nx0, ny0 = BODY[0] - 120, BODY[1] - 10
    d = math.hypot(hx - nx0, hy - ny0)
    mx, my = (nx0 + hx) / 2 + 30 * math.sin(t * 3), min(ny0, hy) - 90 - 0.12 * d
    pts = []
    for j in range(0, 11):
        q = j / 10; u = 1 - q
        pts.append((u * u * nx0 + 2 * u * q * mx + q * q * hx, u * u * ny0 + 2 * u * q * my + q * q * hy))
    c.set_line_cap(cairo.LINE_CAP_ROUND)
    for wdt, col in ((40 + 8 * bulge, '#4a2a1e'), (28 + 6 * bulge, '#7e4630')):
        c.set_source_rgb(*rgb(col)); c.set_line_width(wdt); c.move_to(*pts[0])
        for p in pts[1:]: c.line_to(*p)
        c.stroke()
    c.set_source_rgb(*rgb('#4a2a1e'))
    for p in pts[2:-1:2]: c.arc(p[0], p[1], 8, 0, 2 * math.pi); c.fill()   # joints
    c.set_line_cap(cairo.LINE_CAP_BUTT)
    ang = math.atan2(hy - pts[-2][1], hx - pts[-2][0])
    opn = 0.55 if mo >= 1 else (0.15 if mo > 0 else 0.25)
    c.save(); c.translate(hx, hy); c.rotate(ang)
    c.set_source_rgb(*rgb('#6a3a2a')); c.save(); c.scale(46, 34); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()   # pincer palm
    for s in (-1, 1):   # two jaws
        c.save(); c.rotate(s * opn)
        c.set_source_rgb(*rgb('#8a4c34')); c.move_to(20, s * 6); c.curve_to(50, s * 30, 78, s * 22, 84, s * 4); c.curve_to(64, s * 10, 46, s * 8, 20, -s * 8); c.close_path(); c.fill()
        c.restore()
    c.set_source_rgba(1, 1, 1, 0.25); c.arc(-12, -12, 9, 0, 2 * math.pi); c.fill()
    c.restore()

def draw_floor(c):
    # dune ridge the scorpion hides behind
    c.set_source_rgb(*rgb('#5a4632')); c.move_to(0, 1210); c.curve_to(260, 1120, 520, 1170, 700, 1130); c.curve_to(860, 1100, 980, 1150, W, 1140); c.line_to(W, 1260); c.line_to(0, 1260); c.fill()
    c.set_source_rgb(*rgb('#4a3a2a')); c.rectangle(0, 1240, W, 400); c.fill()   # sand flat in perspective
    c.set_source_rgba(0, 0, 0, 0.12); c.set_line_width(4)
    for k in range(7): yy = 1260 + 340 * (k / 7) ** 1.3; c.move_to(0, yy); c.curve_to(300, yy - 10, 700, yy + 10, W, yy); c.stroke()
    c.move_to(0, H)
    for x in range(0, W + 1, 6): c.line_to(x, TER.h[x])
    c.line_to(W, H); c.close_path(); c.set_source_rgb(*rgb('#6a5440')); c.fill()   # packed sand
    c.set_source_rgba(0, 0, 0, 0.15)
    for k in range(16): c.arc((k * 173) % W, GROUND + 60 + (k * 61) % 240, 6 + k % 3 * 3, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#7c6450')); c.set_line_width(8)
    for x in range(0, W + 1, 6): (c.move_to if x == 0 else c.line_to)(x, TER.h[x] + 3)
    c.stroke()
    (x0, x1) = (0, XMIN - R)   # sandstone pillar on the left
    c.set_source_rgb(*rgb('#7a4a36')); c.rectangle(x0, 900, x1 - x0, H - 900); c.fill()
    c.set_source_rgb(*rgb('#6a3e2c'))
    for yy in range(940, H, 90): c.rectangle(x0, yy, x1 - x0, 10); c.fill()
    c.set_source_rgb(*rgb('#8a5640')); c.rectangle(x0, 900, x1 - x0, 24); c.fill()
    (x0, x1) = (XMAX + R, W)   # boulder stack on the right
    c.set_source_rgb(*rgb('#4a2e22')); c.rectangle(x0, 1000, x1 - x0, H - 1000); c.fill()
    for k, yy in enumerate(range(1000, H, 120)):
        c.set_source_rgb(*rgb('#7a4a36' if k % 2 else '#6e4430')); rrect(c, x0 + 4 + (k % 2) * 8, yy + 4, x1 - x0 - 16, 112, 40); c.fill()
        c.set_source_rgba(1, 1, 1, 0.08); c.arc(x0 + 40, yy + 34, 14, 0, 2 * math.pi); c.fill()

def render(f, c):
    t = f / FPS; fi = min(f, len(POS) - 1)
    c.save()
    draw_bg(c, t); heron_body(c, t); draw_floor(c)
    hx, hy, mo = snake_head(t)
    active = (None, (hx, hy, True)) if mo > 0 else None
    if SPIT_T and SPIT_T - 0.15 <= t < SPIT_T + 0.3: mo = 1.0
    bulge = 0.0
    for i in range(3):
        if EATEN_AT[i] and EATEN_AT[i] <= t < EATEN_AT[i] + 1.4 and not (i == 0 and SPIT_T and t >= SPIT_T): bulge = max(bulge, 1 - (t - EATEN_AT[i]) / 1.4 * 0.6)
    draw_snake(c, t, hx, hy, mo, bulge)
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
                c.set_source_rgba(0.85, 0.72, 0.5, 0.7)
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
