"""2026-11-02 v3 — BALANCE – TILT: the ANVIL SEESAW. Gloop is a passive rigid ball (Ball) bouncing on
a spring-loaded seesaw plank over a mud pit. The plank is a real dynamic terrain: its angle follows a
damped spring around the load torque; every Gloop landing kicks it by impact x lever arm; seeded-random
anvils drop from the sky (some near him), hit him if they touch him on the way down, and stay on the
plank adding torque (they are solid — he bounces on/off them). |TILT| past the red line = it tips."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the anvil seesaw'
SEED = int(os.environ.get('SEED', 40))
rng = random.Random(SEED)

class S: pass
S.HOOK2 = 'THE ANVIL SEESAW?'; S.HOOK2_SIZE = 90; S.FAIL_WORD = 'TIPPED!'; S.FAIL_SIZE = 150
S.T_START = HOOK_T; S.TL = 13.0; S.T_END = S.T_START + S.TL
PX, PY = 540, 1430; HALF = 400; R = 58; MUD = 1790
LIM = 20.0; A_LOAD = float(os.environ.get('ALOAD', 0.00042)); K, D, B = 22.0, 3.2, 6.5e-7
AW, AH = 110, 66; AG = 2000.0

ANV = []; t = 0.55
while t < S.T_END:
    ANV.append({'t': t, 'd': rng.uniform(-HALF + 70, HALF - 70), 'aim': rng.random() < 0.3, 'state': 'wait'})
    t += rng.uniform(1.6, 3.0)

class Plank:
    soft = False
    def __init__(self): self.th = 0.0; self.w = 0.0; self.loads = []
    def top(self, d):   # extra height from anvils sitting at lever offset d
        for a in self.loads:
            if abs(d - a) < AW / 2: return AH
        return 0
    def y(self, x):
        d = (x - PX) / math.cos(self.th); return PY + (x - PX) * math.tan(self.th) - self.top(d) / math.cos(self.th)
    def slope(self, x, dd=30): return (self.y(x + dd) - self.y(x - dd)) / (2 * dd)
    def dig(self, *a): pass
PL = Plank()
PIT = Terrain(MUD, seed=SEED, bumps=0, amp=0, soft=False)

def anv_drop_pos(a, t):
    k = t - a['t0']; y = a['y0'] + 0.5 * AG * k * k; return a['x'], y, AG * k

N0 = int(40 * FPS); GX, GYS, TH, LOADS, AST = [], [], [], [], []
ball = Ball(rng.uniform(380, 700), PL, R=R, seed=SEED, xmin=PX - HALF + R + 18, xmax=PX + HALF - R - 18, hop=rng.uniform(220, 280))
T_FAIL = None; HITS = []; nl = 0; tipdir = 0
for f in range(N0):
    t = f / FPS
    live = T_FAIL is None and S.T_START <= t < S.T_END
    # anvils: drop, touch Gloop (swept), land on plank and stay
    for a in ANV:
        if a['state'] == 'wait' and t >= a['t'] and T_FAIL is None:
            if a['aim']: a['d'] = clamp((ball.x - PX) + rng.uniform(-80, 80), -HALF + 70, HALF - 70)
            for _ in range(8):   # anvils don't overlap: slide to the nearest free spot on the plank
                near = [d for d in PL.loads if abs(d - a['d']) < AW + 6]
                if not near: break
                a['d'] = near[0] + (AW + 8) * (1 if a['d'] >= near[0] else -1)
                if abs(a['d']) > HALF - 60: a['d'] = clamp(-a['d'], -HALF + 60, HALF - 60)
            a['state'] = 'fall'; a['t0'] = t; a['x'] = PX + a['d'] * math.cos(PL.th); a['y0'] = HEAD - 80
        if a['state'] == 'fall':
            x, y, vy = anv_drop_pos(a, t)
            gy = PY + a['d'] * math.sin(PL.th) - AH / 2
            if not a.get('hit') and abs(ball.x - x) < AW / 2 + R * 0.8 and y - AH / 2 - 10 < ball.y + R and y + AH / 2 > ball.y - R:
                a['hit'] = True; HITS.append(t); ball.push((1 if ball.x > x else -1) * 260, 0); ball.vy = max(ball.vy, 700)
            if y >= gy:
                a['state'] = 'on'; a['tl'] = t; PL.loads.append(a['d']); PL.w += 1.2e-6 * AG * 0.9 * a['d']
    ball.step(t)
    while nl < len(ball.landings):
        tl, xl, imp = ball.landings[nl]; nl += 1
        if T_FAIL is None and ball.T is PL: PL.w += B * imp * (xl - PX)
    if T_FAIL is None:
        th_load = A_LOAD * sum(PL.loads)
        PL.w += (-K * (PL.th - th_load) - D * PL.w) / FPS; PL.th += PL.w / FPS
        if live and abs(math.degrees(PL.th)) >= LIM:
            T_FAIL = t; tipdir = 1 if PL.th > 0 else -1
            ball.vx += -tipdir * 120; ball.vy = -1500; ball._pushed = True; ball.xmin, ball.xmax = R + 10, W - R - 10
            ball.T = PIT; ball.vmin = 0; ball.e = 0.12
    else:
        PL.th = lerp(PL.th, tipdir * math.radians(34), 0.25)
    if ball.T is PIT and ball.y > MUD - R - 5: ball.vx *= 0.8
    if not live and T_FAIL is None and t < S.T_START: PL.th *= 1.0
    GX.append(ball.x); GYS.append(ball.y); TH.append(PL.th); LOADS.append(list(PL.loads)); AST.append(None)
S.OUTCOME = 'fail' if T_FAIL else 'win'
S.T_RES = T_FAIL if T_FAIL else S.T_END
S.GRAB = (540, PY - R)
END = S.END = Ending(S)
gi = min(int(END.T_GRAB * FPS), N0 - 1); S.GRAB = (GX[gi], GYS[gi])
S.events = [[0.05, 'whoosh']]
for a in ANV:
    if 'tl' in a and a['tl'] <= S.T_RES + 0.2: S.events.append([a['t0'], 'whoosh']); S.events.append([a['tl'], 'clang']); S.events.append([a['tl'], 'thump', 0.9])
for h in HITS: S.events.append([h, 'thump', 0.8])
for (tl, xl, imp) in ball.landings:
    if tl < S.T_RES + 1.5: S.events.append([tl, 'hop'])
for tw in ball.walls:
    if tw < S.T_RES: S.events.append([tw, 'thump', 0.3])
if T_FAIL: S.events += [[T_FAIL, 'creak'], [T_FAIL + 0.05, 'whoosh'], [T_FAIL + 0.9, 'splash']]
S.AMB = {'drone': 47, 'wind': 0.03}

def draw_bar(c, t, f):
    deg = math.degrees(TH[f]); bw, by_ = 680, 205; bx = (W - bw) / 2 + 30
    c.set_source_rgb(0.2, 0.2, 0.25); rrect(c, bx, by_, bw, 52, 26); c.fill()
    z = bw / 2 * (1 - 14 / 26)   # red zones beyond +-14 deg on a +-26 deg scale (tips at +-20)
    c.set_source_rgb(*rgb('#6a2a2e')); rrect(c, bx, by_, z, 52, 26); c.fill(); rrect(c, bx + bw - z, by_, z, 52, 26); c.fill()
    lim = bw / 2 * LIM / 26
    c.set_source_rgb(*rgb('#ff4d4d')); c.rectangle(bx + bw / 2 - lim - 3, by_ - 6, 6, 64); c.fill(); c.rectangle(bx + bw / 2 + lim - 3, by_ - 6, 6, 64); c.fill()
    c.set_source_rgb(1, 1, 1); c.rectangle(bx + bw / 2 - 2, by_ + 8, 4, 36); c.fill()
    mx = bx + bw / 2 + clamp(deg / 26, -1, 1) * bw / 2
    col = rgb('#7dff8a') if abs(deg) < 8 else (rgb('#ffd84a') if abs(deg) < 14 else rgb('#ff4d4d'))
    c.set_source_rgb(0, 0, 0); c.arc(mx, by_ + 26, 30, 0, 2 * math.pi); c.fill(); c.set_source_rgb(*col); c.arc(mx, by_ + 26, 24, 0, 2 * math.pi); c.fill()
    text_at(c, f'TILT {abs(deg):.0f}°', bx - 92, by_ + 26, 34, (1, 1, 1), lw=7)
S.draw_bar = draw_bar

stars = [(rng.uniform(0, W), rng.uniform(HEAD, 1100), rng.uniform(1.2, 2.4)) for _ in range(60)]
def draw_bg(c, t):
    c.set_source_rgb(*rgb('#1a1524')); c.rectangle(0, HEAD, W, H - HEAD); c.fill()
    c.set_source_rgba(0.9, 0.85, 0.75, 0.5)
    for x, y, r in stars: c.arc(x, y, r, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#e6d6ae')); c.arc(230, 560, 54, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#2c2230'))
    c.move_to(0, 1300); c.line_to(0, 980); c.line_to(150, 960); c.line_to(170, 1120); c.line_to(260, 1140); c.line_to(280, 1300); c.close_path(); c.fill()
    c.move_to(W, 1300); c.line_to(W, 900); c.line_to(900, 930); c.line_to(880, 1100); c.line_to(800, 1130); c.line_to(790, 1300); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#3a2c33')); c.rectangle(0, 1300, W, H - 1300); c.fill()
    c.set_source_rgb(*rgb('#4a3a34')); c.move_to(0, 1520); c.line_to(120, 1520); c.line_to(170, H); c.line_to(0, H); c.close_path(); c.fill()
    c.move_to(W, 1520); c.line_to(W - 120, 1520); c.line_to(W - 170, H); c.line_to(W, H); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#4b3626')); c.rectangle(150, MUD - 10, W - 300, H - MUD + 10); c.fill()   # mud pit
    c.set_source_rgb(*rgb('#5d4430'))
    for i in range(6): c.save(); c.translate(220 + i * 130, MUD + 30 + 10 * math.sin(i)); c.scale(40, 8); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    for x in (60, W - 60):   # flat cacti silhouettes on the ledges
        c.set_source_rgb(*rgb('#2f4a3a')); rrect(c, x - 16, 1400, 32, 120, 14); c.fill(); rrect(c, x - 46, 1430, 22, 50, 10); c.fill(); rrect(c, x + 24, 1420, 22, 46, 10); c.fill()
    # pivot stand
    c.set_source_rgb(*rgb('#5a5f6b')); c.move_to(PX - 90, MUD); c.line_to(PX, PY + 14); c.line_to(PX + 90, MUD); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#3c414c')); c.rectangle(PX - 110, MUD - 14, 220, 24); c.fill()

def draw_anvil(c, x, y, ang):
    c.save(); c.translate(x, y); c.rotate(ang)
    c.set_source_rgb(*rgb('#4a4f5a'))
    c.move_to(-AW / 2, -AH / 2); c.line_to(AW / 2 + 18, -AH / 2); c.line_to(AW / 2 - 8, -AH / 2 + 22); c.line_to(AW / 4, -AH / 2 + 22)
    c.line_to(AW / 4, AH / 2 - 14); c.line_to(AW / 2 - 6, AH / 2); c.line_to(-AW / 2 + 6, AH / 2); c.line_to(-AW / 4, AH / 2 - 14); c.line_to(-AW / 4, -AH / 2 + 22); c.line_to(-AW / 2, -AH / 2 + 18); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#6a707c')); c.rectangle(-AW / 2, -AH / 2, AW + 18, 7); c.fill()
    c.restore()

def draw_plank(c, t, f):
    th = TH[f]; ca, sa = math.cos(th), math.sin(th)
    c.save(); c.translate(PX, PY); c.rotate(th)
    c.set_source_rgb(*rgb('#8a6442')); rrect(c, -HALF - 20, 0, 2 * HALF + 40, 26, 8); c.fill()
    c.set_source_rgb(*rgb('#6b4b31')); c.rectangle(-HALF - 20, 18, 2 * HALF + 40, 8); c.fill()
    for s in (-1, 1): c.set_source_rgb(*rgb('#6b4b31')); rrect(c, s * (HALF + 2) - 9, -40, 18, 60, 6); c.fill()
    c.restore()
    c.set_source_rgb(*rgb('#2a2d34')); c.arc(PX, PY + 13, 16, 0, 2 * math.pi); c.fill()
    for d in LOADS[f]:
        draw_anvil(c, PX + d * ca + (AH / 2) * sa, PY + d * sa - (AH / 2) * ca, th)

PS = Particles(9)
def render(f, c):
    t = f / FPS; fi = min(f, len(GX) - 1); shake = (0, 0)
    for a in ANV:
        if 'tl' in a and a['tl'] <= t < a['tl'] + 0.18 and a['tl'] < S.T_RES + 0.2: shake = (rng.uniform(-4, 4), rng.uniform(-4, 4))
        if 'tl' in a and abs(t - a['tl']) < 0.5 / FPS: PS.spawn(PX + a['d'] * math.cos(TH[fi]), PY + a['d'] * math.sin(TH[fi]) - 4, 10, (0.6, 0.55, 0.5), 300, 0.5, grav=900, r=6)
    c.save(); c.translate(*shake)
    draw_bg(c, t)
    fell = T_FAIL is not None and t >= T_FAIL
    if END.carried(t) or t >= END.T_GRAB: gx, gy = (END.carry_xy(t) if END.carried(t) else S.GRAB)
    else: gx, gy = GX[fi], GYS[fi]
    draw_plank(c, t, fi)
    for a in ANV:   # falling anvils
        if 't0' in a and a['t0'] <= t and ('tl' not in a or t < a['tl']):
            x, y, _ = anv_drop_pos(a, t); draw_anvil(c, x, y, 0)
            c.set_source_rgba(0, 0, 0, 0.18); c.save(); c.translate(x, PY + a['d'] * math.sin(TH[fi]) - 2); c.scale(AW * 0.5, 7); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    deg = abs(math.degrees(TH[fi]))
    mood = 'happy' if (t >= S.T_END and S.OUTCOME == 'win') else ('scared' if fell or deg > 12 or any(abs(t - h) < 0.6 for h in HITS) else 'worried')
    muddy = fell and gy > MUD - R - 30
    skin = ('#b08a5a', '#8a6038', '#5a3a20') if muddy and t > T_FAIL + 0.3 else ('#ffd36b', '#ff8a1f', '#c45a00')
    draw_blob(c, t, gx, gy, mood, 0, R=R, skin=skin, dizzy=muddy and t > T_FAIL + 0.6)
    if muddy and not END.carried(t):
        c.set_source_rgb(*rgb('#4b3626')); c.rectangle(gx - 90, MUD + 4, 180, 40); c.fill()
    if T_FAIL and abs(t - T_FAIL - 0.9) < 0.5 / FPS: PS.spawn(GX[fi], MUD, 24, (0.35, 0.25, 0.16), 600, 0.8, grav=2200, r=10)
    PS.draw(c)
    END.draw_claw(c, t)
    c.restore()
    END.header(c, t, fi)

if __name__ == '__main__':
    if sys.argv[1] == 'sim':
        e = int(S.T_RES * FPS) - 1
        print(SEED, S.OUTCOME, round(S.T_RES - S.T_START, 2), 'maxtilt', round(max(abs(math.degrees(x)) for x in TH[int(S.T_START * FPS):e + 1]), 1), 'anvils', len([a for a in ANV if 'tl' in a and a['tl'] < S.T_RES]), 'hits', len(HITS), 'dur', S.DUR); sys.exit()
    run(S, render)
