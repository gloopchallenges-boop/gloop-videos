"""2026-11-21 v1 [STYLE] — BALANCE – TILT: the GIANT KOI (bright sunny koi-pond garden, style-test scene). Based on 2026-11-16 v3:
a giant koi leaps up under the plank ends instead of the octopus tentacle. Original notes:
2026-11-16 v3 — BALANCE – TILT: the GIANT OCTOPUS. Gloop is a passive rigid ball (Ball) bouncing on a plank
balanced on a barnacled rock in a tide pool on a reef at night. The plank is a real dynamic terrain: its angle
follows a damped spring; every Gloop landing kicks it by impact x lever arm, and a giant octopus shoots a tentacle up
out of the pool at seeded-random times under one end (sometimes the end Gloop is on) and shoves it up with a
seeded-random strength. |TILT| past the red line = it tips and Gloop goes into the pool."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the giant koi'
SEED = int(os.environ.get('SEED', 20))
rng = random.Random(SEED)

class S: pass
S.HOOK2 = 'THE GIANT KOI?'; S.HOOK2_SIZE = 96; S.FAIL_WORD = 'SPLASH!'; S.FAIL_SIZE = 150
S.CARD = ['Every koi jump *TILTS* the plank', 'Will Gloop stay *ON TOP*?']; S.STREAK = int(os.environ.get('STREAK', 2)); S.CTA = True
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
            ball.vx += -tipdir * 120; ball.vy = -1500; ball._pushed = True; ball.xmin, ball.xmax = R + 120, W - R - 120
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


SKY, HILL, HILL2 = '#8fd0f2', '#7cc48a', '#5fae74'
GRASS, GRASS_D = '#86cc6e', '#6db45a'
WATER_C = '#3f9fc4'
clouds = [(rng.uniform(0, W), rng.uniform(560, 760), rng.uniform(0.8, 1.3)) for _ in range(4)]
def cloud(c, x, y, s):
    c.set_source_rgb(1, 1, 1)
    for dx, dy, r in ((-60, 0, 40), (-10, -22, 52), (50, -4, 42), (90, 8, 30)): c.arc(x + dx * s, y + dy * s, r * s, 0, 2 * math.pi); c.fill()
    c.rectangle(x - 60 * s, y, 150 * s, 30 * s); c.fill()
def blossom_tree(c, x, base, s):
    c.set_source_rgb(*rgb('#7a5040')); c.set_line_width(26 * s); c.move_to(x, base); c.curve_to(x - 10 * s, base - 120 * s, x + 20 * s, base - 200 * s, x, base - 260 * s); c.stroke()
    c.set_line_width(12 * s); c.move_to(x, base - 180 * s); c.line_to(x - 90 * s, base - 260 * s); c.stroke(); c.move_to(x + 4 * s, base - 200 * s); c.line_to(x + 100 * s, base - 270 * s); c.stroke()
    for (dx, dy, r, col) in ((-100, -280, 70, '#f6b3cc'), (0, -320, 90, '#f9c4d6'), (100, -290, 74, '#f6b3cc'), (-40, -250, 60, '#f39dbc'), (60, -240, 56, '#f39dbc')):
        c.set_source_rgb(*rgb(col)); c.arc(x + dx * s, base + dy * s, r * s, 0, 2 * math.pi); c.fill()
petals = [(rng.uniform(0, W), rng.uniform(0, 1), rng.uniform(0.5, 1.2)) for _ in range(14)]
def draw_bg(c, t):
    c.set_source_rgb(*rgb(SKY)); c.rectangle(0, HEAD, W, H - HEAD); c.fill()
    c.set_source_rgb(*rgb('#fff4c8')); c.arc(860, 620, 50, 0, 2 * math.pi); c.fill()
    for (x, y, s) in clouds: cloud(c, (x + t * 12 * s) % (W + 300) - 150, y, s)
    c.set_source_rgb(*rgb(HILL)); c.move_to(0, 1060); c.curve_to(200, 930, 420, 960, 560, 1040); c.curve_to(720, 960, 900, 940, W, 1010); c.line_to(W, 1300); c.line_to(0, 1300); c.close_path(); c.fill()
    # little red garden bridge far back
    c.set_source_rgb(*rgb('#d84a4a')); c.set_line_width(12); c.arc(300, 1150, 120, math.pi * 1.15, math.pi * 1.85); c.stroke()
    for k in range(5): xx = 200 + k * 50; c.move_to(xx, 1150 - 120 * math.sin(math.acos(clamp((xx - 300) / 120, -1, 1))) + 6); c.line_to(xx, 1100 - 120 * math.sin(math.acos(clamp((xx - 300) / 120, -1, 1))) + 40); c.set_line_width(6); c.stroke()
    c.set_source_rgb(*rgb(HILL2)); c.move_to(0, 1160); c.curve_to(300, 1100, 700, 1130, W, 1100); c.line_to(W, 1320); c.line_to(0, 1320); c.close_path(); c.fill()
    blossom_tree(c, 120, 1240, 0.9); blossom_tree(c, 980, 1230, 0.85)
    # stone lantern on the right
    c.set_source_rgb(*rgb('#b8b4a8')); c.rectangle(800, 1150, 30, 90); c.fill(); rrect(c, 776, 1110, 78, 44, 6); c.fill()
    c.move_to(760, 1112); c.line_to(870, 1112); c.line_to(815, 1070); c.close_path(); c.fill()
    # grassy bank around the pond
    c.set_source_rgb(*rgb(GRASS)); c.move_to(0, 1270); c.curve_to(200, 1230, 380, 1290, 540, 1280); c.curve_to(700, 1270, 880, 1230, W, 1260); c.line_to(W, H); c.line_to(0, H); c.close_path(); c.fill()
    c.set_source_rgb(*rgb(GRASS_D))
    for j, x in enumerate(range(30, W, 90)):
        y = 1320 + (j * 47) % 120; c.move_to(x, y); c.line_to(x + 8, y - 22); c.line_to(x + 16, y); c.close_path(); c.fill()
    # koi pond under the plank
    c.set_source_rgb(*rgb('#c8c0ac')); c.save(); c.translate(PX, 1700); c.scale(540, 134); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()   # stone rim
    c.set_source_rgb(*rgb(WATER_C)); c.save(); c.translate(PX, 1700); c.scale(510, 120); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    c.set_source_rgba(1, 1, 1, 0.25)
    for i in range(4): c.rectangle(PX - 300 + 30 * math.sin(t + i), 1640 + i * 30, 600 - i * 80, 4); c.fill()
    for (lx, ly) in ((PX - 360, 1690), (PX + 360, 1720), (PX - 220, 1760)):   # lily pads
        c.set_source_rgb(*rgb('#4caf5a')); c.save(); c.translate(lx, ly + 3 * math.sin(t * 1.5 + lx)); c.scale(44, 16); c.arc(0.2, 0, 1, 0.3, 2 * math.pi - 0.3); c.line_to(0, 0); c.restore(); c.fill()
    c.set_source_rgb(*rgb('#ffffff')); c.arc(PX + 380, 1712, 9, 0, 2 * math.pi); c.fill(); c.set_source_rgb(*rgb('#f39dbc')); c.arc(PX + 380, 1712, 5, 0, 2 * math.pi); c.fill()
    # pivot: a big round stepping stone
    c.set_source_rgb(*rgb('#9a978e')); c.move_to(PX - 130, MUD); c.curve_to(PX - 120, PY + 60, PX - 40, PY + 12, PX, PY + 12); c.curve_to(PX + 40, PY + 12, PX + 120, PY + 60, PX + 130, MUD); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#b2afa4')); c.save(); c.translate(PX - 30, PY + 80); c.scale(40, 22); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    c.set_source_rgb(*rgb('#6aa860'))
    for (bx, by) in ((-60, 150), (50, 120), (10, 200)): c.arc(PX + bx, PY + by, 10, 0, 2 * math.pi); c.fill()

def koi(c, x, y, k, side, t):
    """giant koi leaping straight up, head at (x, y); white with red + black patches"""
    c.save(); c.translate(x, y); c.rotate(side * 0.12 * math.sin(t * 9))
    L = 300; Wd = 66
    c.set_source_rgb(*rgb('#f4f1ea')); c.save(); c.translate(0, L / 2); c.scale(Wd, L / 2); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    c.set_source_rgb(*rgb('#d8323e'))
    c.save(); c.translate(-8, 70); c.scale(48, 40); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    c.save(); c.translate(20, 190); c.scale(36, 46); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    c.set_source_rgb(*rgb('#2a2a30')); c.arc(-30, 140, 14, 0, 2 * math.pi); c.fill(); c.arc(26, 110, 9, 0, 2 * math.pi); c.fill()
    # side fins
    c.set_source_rgba(0.96, 0.95, 0.92, 0.9)
    for s in (-1, 1): c.move_to(s * Wd * 0.8, 120); c.curve_to(s * (Wd + 60), 130 + 20 * math.sin(t * 12), s * (Wd + 50), 190, s * Wd * 0.6, 170); c.close_path(); c.fill()
    # face: eyes, round mouth, whiskers
    for s in (-1, 1):
        c.set_source_rgb(1, 1, 1); c.arc(s * 32, 30, 15, 0, 2 * math.pi); c.fill()
        c.set_source_rgb(0.05, 0.05, 0.08); c.arc(s * 32, 32, 8, 0, 2 * math.pi); c.fill()
        c.set_source_rgb(*rgb('#c8b8a0')); c.set_line_width(5); c.move_to(s * 22, 6); c.curve_to(s * 50, -4, s * 70, 10, s * 80, 30); c.stroke()
    c.set_source_rgb(*rgb('#7a2a30')); c.save(); c.translate(0, 0); c.scale(20, 14); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    c.restore()

def draw_hippo(c, t, fi):   # the koi leaping up out of the pond under a plank end
    th = TH[fi]
    for bp in BUMPS:
        if 'side_f' not in bp or t < bp['t'] or t > bp['t'] + RISE + 0.9 or bp['t'] + RISE >= min(S.T_END, S.T_RES + 0.01): continue
        k = (t - bp['t']) / RISE if t < bp['t'] + RISE else 1 - (t - bp['t'] - RISE) / 0.9
        k = ease(clamp(k, 0, 1))
        d = bp['side_f'] * (HALF - 60); x = PX + d * math.cos(th)
        top = PY + d * math.sin(th) + 26
        y = lerp(1900, top + 14, k)
        koi(c, x, y, k, bp['side_f'], t)
    # koi's back fin circling in the pond between leaps
    fx = PX + 300 * math.sin(t * 0.9)
    c.set_source_rgb(*rgb('#d8323e')); c.move_to(fx - 40, 1716); c.curve_to(fx - 20, 1676, fx + 20, 1670, fx + 36, 1716); c.close_path(); c.fill()
    # grassy front bank hides the koi's tail
    c.set_source_rgb(*rgb(GRASS)); c.rectangle(0, 1712, W, H - 1712); c.fill()
    c.set_source_rgb(*rgb(GRASS_D))
    for j, x in enumerate(range(20, W, 64)):
        y = 1770 + (j * 37) % 130; c.move_to(x, y); c.line_to(x + 7, y - 20); c.line_to(x + 14, y); c.close_path(); c.fill()
    c.set_source_rgb(*rgb(WATER_C)); c.save(); c.translate(PX, 1712); c.scale(510, 30); c.arc(0, 0, 1, 0, math.pi); c.restore(); c.fill()
    c.set_source_rgb(*rgb('#c8c0ac')); c.set_line_width(14); c.save(); c.translate(PX, 1712); c.scale(520, 34); c.arc(0, 0, 1, 0, math.pi); c.restore(); c.stroke()
    # drifting petals
    for (x, ph, s) in petals:
        yy = HEAD + ((ph + t * 0.06 * s) % 1) * (1700 - HEAD); xx = x + 40 * math.sin(t * s + ph * 6)
        c.set_source_rgb(*rgb('#f9c4d6')); c.save(); c.translate(xx, yy); c.rotate(t * s); c.scale(9, 5); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()


def draw_anvil(c, x, y, ang): pass

def draw_plank(c, t, f):
    th = TH[f]
    c.save(); c.translate(PX, PY); c.rotate(th)
    c.set_source_rgb(*rgb('#c09060')); rrect(c, -HALF - 20, 0, 2 * HALF + 40, 26, 8); c.fill()
    c.set_source_rgb(*rgb('#9a6e44')); c.rectangle(-HALF - 20, 18, 2 * HALF + 40, 8); c.fill()
    for s in (-1, 1): c.set_source_rgb(*rgb('#9a6e44')); rrect(c, s * (HALF + 2) - 9, -40, 18, 60, 6); c.fill()
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
        c.set_source_rgba(*rgb(WATER_C), 0.9); c.save(); c.translate(gx, MUD + 20); c.scale(110, 30); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
        c.set_source_rgba(0.7, 0.85, 0.95, 0.5); c.set_line_width(5); c.save(); c.translate(gx, MUD + 20); c.scale(110, 30); c.arc(0, 0, 1, math.pi, 2 * math.pi); c.restore(); c.stroke()
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
