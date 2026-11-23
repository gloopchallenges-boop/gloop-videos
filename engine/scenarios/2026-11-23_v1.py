"""2026-11-23 v1 — WHO FIRST: the GIANT SQUID (based on 2026-11-21 v2 heron). Gloop (orange) + two rival blobs bounce as
passive rigid balls on the deck of a shipwreck at night between the cabin wall and a barrel stack. A giant squid behind
the rail shoots a tentacle at seeded-random times at where a random remaining blob WAS a moment ago; the club grabs
whoever it touches. Gloop grabbed = fail (flung back out slimy & dizzy). Timer ends ungrabbed = win."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the giant squid'
SEED = int(os.environ.get('SEED', 25))
rng = random.Random(SEED)

class S: pass
S.HOOK2 = 'THE GIANT SQUID?'; S.HOOK2_SIZE = 92; S.FAIL_WORD = 'GRABBED!'; S.FAIL_SIZE = 160
S.T_START = HOOK_T; S.TL = 13.0; S.T_END = S.T_START + S.TL
GROUND = 1600; R = 56; XMIN, XMAX = 160, 920
MOUTH = (620, 1125); TIP_R = 46; T_OUT, T_HOLD, T_BACK = 0.22, 0.08, 0.35
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
    c.set_source_rgb(*rgb('#0f1626')); c.rectangle(0, HEAD, W, H - HEAD); c.fill()
    c.set_source_rgba(0.85, 0.9, 1, 0.35)
    for x, y, r in stars[:34]: c.arc(x, y * 0.6 + 150, r, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#d8d4bc')); c.arc(230, 540, 34, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#16243a')); c.rectangle(0, 960, W, 700); c.fill()   # open sea
    c.set_source_rgba(0.85, 0.85, 0.7, 0.16)
    for i in range(6): c.rectangle(195 + 8 * math.sin(t * 2 + i), 990 + i * 34, 70 - i * 8, 5); c.fill()
    c.set_source_rgba(1, 1, 1, 0.05)
    for i in range(6): c.rectangle(0, 1000 + i * 40 + 4 * math.sin(t * 1.2 + i), W, 3); c.fill()
    # tilted broken mast + torn sail of the shipwreck
    c.set_source_rgb(*rgb('#3a2c22')); c.set_line_width(30)
    c.move_to(300, 1260); c.line_to(380, 560); c.stroke()
    c.set_line_width(12); c.move_to(250, 720); c.line_to(520, 760); c.stroke()
    c.set_source_rgb(*rgb('#2c3440')); c.move_to(262, 732); c.line_to(505, 768); c.line_to(470, 960); c.line_to(400, 930); c.line_to(330, 990); c.line_to(290, 900); c.close_path(); c.fill()

def heron_body(c, t):   # giant squid head rising behind the ship rail
    bx, by = BODY; bob = 8 * math.sin(t * 1.6)
    c.save(); c.translate(bx, by + bob)
    c.set_source_rgb(*rgb('#7a2e4a'))
    c.move_to(-120, 60); c.curve_to(-130, -120, -60, -260, 0, -300); c.curve_to(60, -260, 130, -120, 120, 60); c.close_path(); c.fill()
    c.move_to(-150, -170); c.line_to(-60, -230); c.line_to(-70, -120); c.close_path(); c.fill()   # fins
    c.move_to(150, -170); c.line_to(60, -230); c.line_to(70, -120); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#9a4262'))
    for (sx, sy, sr) in ((-50, -170, 14), (30, -220, 10), (60, -120, 12), (-20, -80, 9)): c.arc(sx, sy, sr, 0, 2 * math.pi); c.fill()
    for ex in (-55, 55):   # big eyes
        c.set_source_rgb(*rgb('#e8e2c8')); c.arc(ex, -10, 34, 0, 2 * math.pi); c.fill()
        c.set_source_rgb(0.05, 0.05, 0.08); c.save(); c.translate(ex + 4, -8); c.scale(10, 24); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    c.restore()

def snake_head(t):
    for s in STR:
        if s['t'] > S.T_RES + 0.05 and not (T_FAIL and s['t'] <= T_FAIL): continue
        tip = tongue_tip(s, t)
        if tip: return tip[0], tip[1], (1.0 if tip[2] else 0.15)
    return MOUTH[0] + 8 * math.sin(t * 2.1), MOUTH[1] + 6 * math.sin(t * 4.2), 0.0

def draw_snake(c, t, hx, hy, mo, bulge):   # squid tentacle from behind the rail; (hx, hy) = club tip
    nx0, ny0 = BODY[0] - 90, BODY[1] + 40
    d = math.hypot(hx - nx0, hy - ny0)
    mx, my = (nx0 + hx) / 2 - 40 * math.sin(t * 3), min(ny0, hy) - 120 - 0.15 * d
    c.set_line_cap(cairo.LINE_CAP_ROUND)
    for wdt, col in ((40 + 10 * bulge, '#7a2e4a'), (24 + 6 * bulge, '#9a4262')):
        c.set_source_rgb(*rgb(col)); c.set_line_width(wdt)
        c.move_to(nx0, ny0); c.curve_to(mx, my, mx, my, hx, hy); c.stroke()
    c.set_source_rgb(*rgb('#e8b8c8'))   # suckers along the arm
    for j in range(1, 9):
        q = j / 9; u = 1 - q
        px = u * u * u * nx0 + 3 * u * u * q * mx + 3 * u * q * q * mx + q * q * q * hx
        py = u * u * u * ny0 + 3 * u * u * q * my + 3 * u * q * q * my + q * q * q * hy
        c.arc(px, py + 8, 5, 0, 2 * math.pi); c.fill()
    c.set_line_cap(cairo.LINE_CAP_BUTT)
    c.save(); c.translate(hx, hy)   # club at the tip
    c.set_source_rgb(*rgb('#7a2e4a')); c.save(); c.scale(48 if mo >= 1 else 40, 38); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    c.set_source_rgb(*rgb('#e8b8c8'))
    for (sx, sy) in ((-20, 6), (0, 12), (20, 6), (-10, -8), (10, -8)): c.arc(sx, sy, 6, 0, 2 * math.pi); c.fill()
    c.restore()

def draw_floor(c):
    c.set_source_rgb(*rgb('#4a3424')); c.rectangle(0, 1140, W, 60); c.fill()   # ship rail
    c.set_source_rgb(*rgb('#5e4430')); c.rectangle(0, 1130, W, 16); c.fill()
    for x in range(30, W, 90): c.set_source_rgb(*rgb('#3a2818')); c.rectangle(x, 1146, 14, 54); c.fill()
    c.set_source_rgb(*rgb('#4a3624')); c.rectangle(0, 1200, W, 420); c.fill()   # deck in perspective
    c.set_source_rgb(*rgb('#3c2c1c')); c.set_line_width(3)
    for k in range(9): yy = 1200 + 420 * (k / 9) ** 1.4; c.move_to(0, yy); c.line_to(W, yy); c.stroke()
    for k in range(-6, 7): c.move_to(540 + k * 70, 1200); c.line_to(540 + k * 190, 1620); c.stroke()
    c.move_to(0, H)
    for x in range(0, W + 1, 6): c.line_to(x, TER.h[x])
    c.line_to(W, H); c.close_path(); c.set_source_rgb(*rgb('#5a4430')); c.fill()   # deck planks
    c.set_source_rgb(*rgb('#46341f')); c.set_line_width(4)
    for yy in range(GROUND + 40, H, 56): c.move_to(0, yy); c.line_to(W, yy); c.stroke()
    for k in range(14): xx = (k * 157) % W; yy = GROUND + 40 + (k % 5) * 56; c.move_to(xx, yy); c.line_to(xx, yy + 56); c.stroke()
    c.set_source_rgb(*rgb('#6e5440')); c.set_line_width(8)
    for x in range(0, W + 1, 6): (c.move_to if x == 0 else c.line_to)(x, TER.h[x] + 3)
    c.stroke()
    (x0, x1) = (0, XMIN - R)   # cabin wall on the left
    c.set_source_rgb(*rgb('#3e2e20')); c.rectangle(x0, 1000, x1 - x0, H - 1000); c.fill()
    c.set_source_rgb(*rgb('#2c2016'))
    for yy in range(1000, H, 40): c.rectangle(x0, yy, x1 - x0, 4); c.fill()
    c.set_source_rgb(*rgb('#c8a860')); c.arc((x0 + x1) / 2, 1080, 22, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#1c2a3a')); c.arc((x0 + x1) / 2, 1080, 15, 0, 2 * math.pi); c.fill()
    (x0, x1) = (XMAX + R, W)   # barrel stack on the right
    c.set_source_rgb(*rgb('#2a1e14')); c.rectangle(x0, 1060, x1 - x0, H - 1060); c.fill()
    for k, yy in enumerate(range(1060, H, 130)):
        c.set_source_rgb(*rgb('#6a4a2c')); rrect(c, x0 + 6, yy + 6, x1 - x0 - 12, 118, 20); c.fill()
        c.set_source_rgb(*rgb('#3a3a40'))
        for dy in (30, 88): c.rectangle(x0 + 6, yy + dy, x1 - x0 - 12, 8); c.fill()

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
