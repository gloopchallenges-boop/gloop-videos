"""2026-11-11 v8 — BALANCE – TILT: the ANGRY WALRUS. Gloop is a passive rigid ball (Ball) bouncing on a plank
balanced on a snowy rock in an ice hole on a frozen lake at night. The plank is a real dynamic terrain: its angle
follows a damped spring; every Gloop landing kicks it by impact x lever arm, and an angry walrus pops up out of
the water at seeded-random times under one end (sometimes the end Gloop is on) and shoves it up with a
seeded-random strength. |TILT| past the red line = it tips and Gloop goes into the icy water."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the angry walrus'
SEED = int(os.environ.get('SEED', 14))
rng = random.Random(SEED)

class S: pass
S.HOOK2 = 'THE ANGRY WALRUS?'; S.HOOK2_SIZE = 88; S.FAIL_WORD = 'SPLOOSH!'; S.FAIL_SIZE = 150
S.T_START = HOOK_T; S.TL = 13.0; S.T_END = S.T_START + S.TL
PX, PY = 540, 1430; HALF = 400; R = 58; MUD = 1790
LIM = 20.0; KICK = float(os.environ.get('KICK', 1.5)); K, D, B = 9.0, 1.6, 6.5e-7
AW, AH = 110, 66; AG = 2000.0

BUMPS = []; t = 0.3
while t < S.T_END + 2:
    BUMPS.append({'t': t, 'side': rng.choice((-1, 1)), 'aim': rng.random() < 0.4, 's': rng.uniform(0.45, 1.0)})
    t += rng.uniform(1.3, 2.6)
RISE = 0.35   # hippo rises for RISE s, shoves at the top, then sinks back
ANV = []; AW = AH = 0
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
PIT = Terrain(MUD - 10, seed=SEED, bumps=0, amp=0, soft=False)

def anv_drop_pos(a, t):
    k = t - a['t0']; y = a['y0'] + 0.5 * AG * k * k; return a['x'], y, AG * k

N0 = int(40 * FPS); GX, GYS, TH, LOADS, AST = [], [], [], [], []
ball = Ball(rng.uniform(380, 700), PL, R=R, seed=SEED, xmin=PX - HALF + R + 18, xmax=PX + HALF - R - 18, hop=rng.uniform(220, 280))
T_FAIL = None; HITS = []; nl = 0; tipdir = 0
for f in range(N0):
    t = f / FPS
    live = T_FAIL is None and S.T_START <= t < S.T_END
    for bp in BUMPS:
        if 'side_f' not in bp and t >= bp['t']:
            bp['side_f'] = (1 if ball.x > PX else -1) if bp['aim'] else bp['side']
        if 'done' not in bp and t >= bp['t'] + RISE and T_FAIL is None:
            bp['done'] = True; HITS.append(t) if live else None
            if 0.6 <= t < S.T_END: PL.w += -bp['side_f'] * KICK * bp['s']
    ball.step(t)
    while nl < len(ball.landings):
        tl, xl, imp = ball.landings[nl]; nl += 1
        if T_FAIL is None and ball.T is PL: PL.w += B * imp * (xl - PX)
    if T_FAIL is None:
        th_load = 0.0
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
for bp in BUMPS:
    if bp['t'] + RISE < min(S.T_END, S.T_RES + 0.01): S.events.append([bp['t'], 'rumble', 0.6]); S.events.append([bp['t'] + RISE, 'thump', 0.9 * bp['s'] + 0.2])
for (tl, xl, imp) in ball.landings:
    if tl < S.T_RES + 1.5: S.events.append([tl, 'hop'])
for tw in ball.walls:
    if tw < S.T_RES: S.events.append([tw, 'thump', 0.3])
if T_FAIL: S.events += [[T_FAIL, 'creak'], [T_FAIL + 0.05, 'whoosh'], [T_FAIL + 0.9, 'thump', 0.8], [T_FAIL + 0.9, 'crackle']]
S.AMB = {'drone': 45, 'wind': 0.04}

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

stars = [(rng.uniform(0, W), rng.uniform(HEAD, 900), rng.uniform(1.2, 2.4)) for _ in range(50)]
SAND, SAND_D, SAND_F = '#b8c4d0', '#a2b0be', '#c8d4de'   # snow on the frozen lake
WATER_C = '#1a2a3a'
def pine(c, x, y, s, col):
    c.set_source_rgb(*rgb(col)); c.move_to(x, y - 220 * s)
    for k in range(3):
        w = 40 * s + k * 30 * s; yy = y - 220 * s + (k + 1) * 60 * s
        c.line_to(x + w, yy); c.line_to(x + w * 0.45, yy)
    c.line_to(x + 10 * s, y); c.line_to(x - 10 * s, y)
    for k in range(2, -1, -1):
        w = 40 * s + k * 30 * s; yy = y - 220 * s + (k + 1) * 60 * s
        c.line_to(x - w * 0.45, yy); c.line_to(x - w, yy)
    c.close_path(); c.fill()
def draw_bg(c, t):
    c.set_source_rgb(*rgb('#141a2a')); c.rectangle(0, HEAD, W, H - HEAD); c.fill()
    c.set_source_rgba(0.9, 0.9, 0.95, 0.45)
    for x, y, r in stars: c.arc(x, y, r, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#e6e2cc')); c.arc(820, 560, 42, 0, 2 * math.pi); c.fill()
    # far snowy hills + pine silhouettes
    c.set_source_rgb(*rgb('#283244')); c.move_to(0, 1060); c.curve_to(250, 940, 450, 1020, 620, 1000); c.curve_to(800, 980, 920, 940, W, 1000); c.line_to(W, 1250); c.line_to(0, 1250); c.close_path(); c.fill()
    for (x, s) in ((60, 1.0), (150, 0.8), (240, 1.1), (830, 0.9), (920, 1.2), (1020, 0.85)): pine(c, x, 1180, s, '#1a2230')
    # frozen lake surface
    c.set_source_rgb(*rgb(SAND)); c.rectangle(0, 1220, W, H - 1220); c.fill()
    c.set_source_rgb(*rgb(SAND_D))
    for j, x in enumerate(range(30, W, 90)): c.save(); c.translate(x, 1270 + (j * 47) % 120); c.scale(40, 3); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    # ice hole under the plank
    c.set_source_rgb(*rgb(WATER_C)); c.save(); c.translate(PX, 1700); c.scale(520, 120); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    c.set_source_rgba(1, 1, 1, 0.06)
    for i in range(4): c.rectangle(PX - 300 + 30 * math.sin(t + i), 1640 + i * 30, 600 - i * 80, 4); c.fill()
    # pivot: a big snowy rock poking out of the hole
    c.set_source_rgb(*rgb('#4a5260')); c.move_to(PX - 130, MUD); c.curve_to(PX - 120, PY + 60, PX - 40, PY + 12, PX, PY + 12); c.curve_to(PX + 40, PY + 12, PX + 120, PY + 60, PX + 130, MUD); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#d8e2ea')); c.move_to(PX - 90, PY + 60); c.curve_to(PX - 50, PY + 22, PX + 50, PY + 22, PX + 90, PY + 60); c.curve_to(PX + 40, PY + 50, PX - 40, PY + 50, PX - 90, PY + 60); c.fill()
    c.set_source_rgb(*rgb('#3a4250')); c.move_to(PX - 20, PY + 70); c.line_to(PX + 30, PY + 140); c.line_to(PX + 10, PY + 210); c.set_line_width(5); c.stroke()

def draw_hippo(c, t, fi):   # the angry walrus popping up through the water under a plank end
    th = TERR = TH[fi]
    for bp in BUMPS:
        if 'side_f' not in bp or t < bp['t'] or t > bp['t'] + RISE + 0.9 or bp['t'] + RISE >= min(S.T_END, S.T_RES + 0.01): continue
        k = (t - bp['t']) / RISE if t < bp['t'] + RISE else 1 - (t - bp['t'] - RISE) / 0.9
        k = ease(clamp(k, 0, 1))
        d = bp['side_f'] * (HALF - 60); x = PX + d * math.cos(th)
        top = PY + d * math.sin(th) + 28
        y = lerp(1880, top + 60, k)
        skin, skin2 = rgb('#8a6a52'), rgb('#7a5a44')
        c.save(); c.translate(x, y)
        c.set_source_rgb(*skin2); c.save(); c.translate(0, 160); c.scale(130, 150); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()   # bulky body
        c.set_source_rgb(*skin); c.save(); c.translate(0, 30); c.scale(105, 85); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()   # head
        c.set_source_rgb(*rgb('#a88a6e'))
        for sx in (-1, 1): c.save(); c.translate(sx * 34, 72); c.scale(42, 32); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()   # whisker pads
        c.set_source_rgb(*rgb('#5a4030'))
        for sx in (-1, 1):
            for q in range(3): c.arc(sx * (24 + q * 14), 66 + (q % 2) * 10, 3, 0, 2 * math.pi); c.fill()
        c.set_source_rgb(*rgb('#3a2a20')); c.save(); c.translate(0, 46); c.scale(16, 10); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()   # nose
        c.set_source_rgb(*rgb('#efe6d0'))
        for sx in (-1, 1): c.move_to(sx * 22 - 9, 92); c.line_to(sx * 22 + 9, 92); c.line_to(sx * 26, 200); c.close_path(); c.fill()   # long tusks
        for sx in (-1, 1):   # angry little eyes
            c.set_source_rgb(0.05, 0.05, 0.05); c.arc(sx * 44, 2, 9, 0, 2 * math.pi); c.fill()
            c.set_source_rgb(*rgb('#3a2a20')); c.set_line_width(6); c.move_to(sx * 66, -16); c.line_to(sx * 26, -6); c.stroke()
        c.restore()
    c.set_source_rgb(*rgb(SAND)); c.rectangle(0, 1700, W, H - 1700); c.fill()   # ice shelf in front hides the body
    c.set_source_rgb(*rgb(SAND_D))
    for j, x in enumerate(range(20, W, 70)): c.save(); c.translate(x, 1750 + (j * 37) % 150); c.scale(24, 3); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    c.set_source_rgb(*rgb(WATER_C)); c.save(); c.translate(PX, 1700); c.scale(520, 26); c.arc(0, 0, 1, 0, math.pi); c.restore(); c.fill()   # hole's front water
    c.set_source_rgb(*rgb('#e0e8f0')); c.set_line_width(8); c.save(); c.translate(PX, 1700); c.scale(520, 26); c.arc(0, 0, 1, 0, math.pi); c.restore(); c.stroke()   # ice rim


def draw_anvil(c, x, y, ang): pass

def draw_plank(c, t, f):
    th = TH[f]
    c.save(); c.translate(PX, PY); c.rotate(th)
    c.set_source_rgb(*rgb('#8a6442')); rrect(c, -HALF - 20, 0, 2 * HALF + 40, 26, 8); c.fill()
    c.set_source_rgb(*rgb('#6b4b31')); c.rectangle(-HALF - 20, 18, 2 * HALF + 40, 8); c.fill()
    for s in (-1, 1): c.set_source_rgb(*rgb('#6b4b31')); rrect(c, s * (HALF + 2) - 9, -40, 18, 60, 6); c.fill()
    c.restore()

PS = Particles(9)
def render(f, c):
    t = f / FPS; fi = min(f, len(GX) - 1); shake = (0, 0)
    for bp in BUMPS:
        if 'side_f' in bp and bp['t'] + RISE <= t < bp['t'] + RISE + 0.15 and bp['t'] < S.T_RES: shake = (rng.uniform(-4, 4), rng.uniform(-4, 4))
        if 'side_f' in bp and abs(t - bp['t'] - 0.15) < 0.5 / FPS and bp['t'] + RISE < min(S.T_END, S.T_RES + 0.01): PS.spawn(PX + bp['side_f'] * (HALF - 60), 1690, 14, (0.7, 0.8, 0.9), 500, 0.6, grav=1800, r=8)
    c.save(); c.translate(*shake)
    draw_bg(c, t)
    fell = T_FAIL is not None and t >= T_FAIL
    if END.carried(t) or t >= END.T_GRAB: gx, gy = (END.carry_xy(t) if END.carried(t) else S.GRAB)
    else: gx, gy = GX[fi], GYS[fi]
    draw_hippo(c, t, fi)
    draw_plank(c, t, fi)
    for a in ANV:   # falling anvils
        if 't0' in a and a['t0'] <= t and ('tl' not in a or t < a['tl']):
            x, y, _ = anv_drop_pos(a, t); draw_anvil(c, x, y, 0)
            c.set_source_rgba(0, 0, 0, 0.18); c.save(); c.translate(x, PY + a['d'] * math.sin(TH[fi]) - 2); c.scale(AW * 0.5, 7); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    deg = abs(math.degrees(TH[fi]))
    mood = 'happy' if (t >= S.T_END and S.OUTCOME == 'win') else ('scared' if fell or deg > 12 or any(abs(t - h) < 0.6 for h in HITS) else 'worried')
    muddy = fell and gy > MUD - R - 40
    skin = ('#ffd36b', '#ff8a1f', '#c45a00')
    draw_blob(c, t, gx, gy, mood, 0, R=R, skin=skin, dizzy=muddy and t > T_FAIL + 0.6)
    if muddy and not END.carried(t):
        c.set_source_rgba(*rgb(WATER_C), 0.85); c.rectangle(gx - 90, MUD - 6, 180, 60); c.fill()
    if T_FAIL and abs(t - T_FAIL - 0.9) < 0.5 / FPS: PS.spawn(GX[fi], MUD - 20, 24, (0.6, 0.75, 0.9), 700, 0.8, grav=2200, r=10)
    PS.draw(c)
    END.draw_claw(c, t)
    c.restore()
    END.header(c, t, fi)

if __name__ == '__main__':
    if sys.argv[1] == 'sim':
        e = int(S.T_RES * FPS) - 1
        print(SEED, S.OUTCOME, round(S.T_RES - S.T_START, 2), 'maxtilt', round(max(abs(math.degrees(x)) for x in TH[int(S.T_START * FPS):e + 1]), 1), 'bumps', len(HITS), 'dur', S.DUR); sys.exit()
    run(S, render)
