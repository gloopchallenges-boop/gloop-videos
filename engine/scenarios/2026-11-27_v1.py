"""2026-11-27 v1 [STYLE] — BALANCE – TILT: the PLAYFUL SEA LION (bright sunny harbor, style-test scene). Based on 2026-11-21 v1
(koi): a giant sea lion leaps up out of the harbor water under the plank ends. Gloop is a passive rigid ball bouncing on a
plank balanced on a mooring rock; the plank angle follows a damped spring, every landing kicks it by impact x lever arm and
the sea lion shoves an end up at seeded-random times (sometimes the end Gloop is on). |TILT| past 20 deg = Gloop falls in."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the playful sea lion'
SEED = int(os.environ.get('SEED', 1))
rng = random.Random(SEED)

class S: pass
S.HOOK2 = 'THE PLAYFUL SEA LION?'; S.HOOK2_SIZE = 80; S.FAIL_WORD = 'SPLASH!'; S.FAIL_SIZE = 150
S.CARD = ['Every sea lion jump *TILTS* the plank', 'Will Gloop stay *DRY*?']; S.STREAK = int(os.environ.get('STREAK', 2)); S.CTA = True
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



SKY = '#8fd0f2'; SEA = '#3a9cc8'; SEA_D = '#2e86b0'; WATER_C = SEA
clouds = [(rng.uniform(0, W), rng.uniform(520, 740), rng.uniform(0.8, 1.3)) for _ in range(4)]
def cloud(c, x, y, s):
    c.set_source_rgb(1, 1, 1)
    for dx, dy, r in ((-60, 0, 40), (-10, -22, 52), (50, -4, 42), (90, 8, 30)): c.arc(x + dx * s, y + dy * s, r * s, 0, 2 * math.pi); c.fill()
    c.rectangle(x - 60 * s, y, 150 * s, 30 * s); c.fill()
HOUSES = [(-20, 120, 170, '#f3a9c0'), (100, 110, 210, '#a8e0c8'), (210, 130, 150, '#c7b6ee'), (340, 100, 190, '#9fd0f0'),
          (640, 120, 180, '#f3a9c0'), (760, 110, 220, '#c7b6ee'), (870, 120, 160, '#a8e0c8'), (990, 110, 200, '#f6f0e6')]
gulls = [(rng.uniform(0, W), rng.uniform(600, 820), rng.uniform(0.7, 1.1)) for _ in range(3)]
def draw_bg(c, t):
    c.set_source_rgb(*rgb(SKY)); c.rectangle(0, HEAD, W, H - HEAD); c.fill()
    c.set_source_rgb(*rgb('#fff4c8')); c.arc(860, 600, 50, 0, 2 * math.pi); c.fill()
    for (x, y, s) in clouds: cloud(c, (x + t * 12 * s) % (W + 300) - 150, y, s)
    # far green headland
    c.set_source_rgb(*rgb('#7cc48a')); c.move_to(0, 1000); c.curve_to(160, 900, 330, 930, 470, 1010); c.line_to(470, 1120); c.line_to(0, 1120); c.close_path(); c.fill()
    # lighthouse (white + red stripes) on the headland
    c.set_source_rgb(1, 1, 1); c.move_to(150, 960); c.line_to(200, 960); c.line_to(192, 780); c.line_to(158, 780); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#e0505a')); c.rectangle(154, 860, 42, 30); c.fill(); c.rectangle(158, 800, 34, 24); c.fill()
    c.move_to(150, 780); c.line_to(200, 780); c.line_to(175, 750); c.close_path(); c.fill()
    # row of pastel harbor houses on the quay
    for (x, w, h, col) in HOUSES:
        base = 1120
        c.set_source_rgb(*rgb(col)); c.rectangle(x, base - h, w - 6, h); c.fill()
        c.set_source_rgb(*rgb('#5a6a8a')); c.move_to(x - 6, base - h); c.line_to(x + (w - 6) / 2, base - h - 50); c.line_to(x + w, base - h); c.close_path(); c.fill()
        c.set_source_rgba(1, 1, 1, 0.85)
        for k in range(2):
            for j in range(int(h // 70)): c.rectangle(x + 16 + k * (w - 50) / 1.6, base - h + 24 + j * 64, 22, 30); c.fill()
    c.set_source_rgb(*rgb('#c9c2b4')); c.rectangle(0, 1110, W, 30); c.fill()   # quay wall
    # sea
    c.set_source_rgb(*rgb(SEA)); c.rectangle(0, 1140, W, H - 1140); c.fill()
    c.set_source_rgba(1, 1, 1, 0.3)
    for i in range(9):
        y = 1170 + i * 62; ph = t * (0.6 + 0.1 * i) + i
        for k in range(3): c.rectangle((k * 420 + 140 * math.sin(ph) + i * 70) % (W + 200) - 100, y, 120 - i * 6, 4); c.fill()
    # small sailboat drifting far back (blue + white)
    bx = (300 + t * 18) % (W + 200) - 100
    c.set_source_rgb(*rgb('#4a6ab0')); c.move_to(bx - 50, 1150); c.line_to(bx + 50, 1150); c.line_to(bx + 36, 1172); c.line_to(bx - 36, 1172); c.close_path(); c.fill()
    c.set_source_rgb(1, 1, 1); c.move_to(bx, 1146); c.line_to(bx, 1040); c.line_to(bx + 46, 1140); c.close_path(); c.fill()
    for (x, y, s) in gulls:   # gulls
        xx = (x + t * 40 * s) % (W + 100) - 50; fl = 10 * math.sin(t * 7 + x)
        c.set_source_rgb(1, 1, 1); c.set_line_width(6); c.move_to(xx - 26, y + fl); c.curve_to(xx - 14, y - 12, xx - 4, y - 8, xx, y); c.curve_to(xx + 4, y - 8, xx + 14, y - 12, xx + 26, y + fl); c.stroke()
    # pivot: a big round barnacled mooring rock poking out of the water
    c.set_source_rgb(*rgb('#8a8f9a')); c.move_to(PX - 130, MUD); c.curve_to(PX - 120, PY + 60, PX - 40, PY + 12, PX, PY + 12); c.curve_to(PX + 40, PY + 12, PX + 120, PY + 60, PX + 130, MUD); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#a3a8b2')); c.save(); c.translate(PX - 30, PY + 80); c.scale(40, 22); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    c.set_source_rgb(*rgb('#eef0f4'))
    for (bx_, by_) in ((-60, 150), (50, 120), (10, 200), (-20, 110), (70, 180)): c.arc(PX + bx_, PY + by_, 7, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#4caf6a'))   # seaweed line
    c.rectangle(PX - 125, 1650, 250, 14); c.fill()

def sealion(c, x, y, side, t):
    """giant sea lion leaping straight up, nose at (x, y); sleek brown body below"""
    c.save(); c.translate(x, y); c.rotate(side * 0.10 * math.sin(t * 8))
    L = 330; Wd = 76
    c.set_source_rgb(*rgb('#7a5e4c')); c.save(); c.translate(0, L / 2 + 20); c.scale(Wd, L / 2); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    c.set_source_rgb(*rgb('#8e705c')); c.save(); c.translate(0, 70); c.scale(58, 70); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()   # head
    c.set_source_rgb(*rgb('#a88a74')); c.save(); c.translate(0, 18); c.scale(36, 26); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()   # muzzle
    c.set_source_rgb(*rgb('#2a2024')); c.save(); c.translate(0, 4); c.scale(14, 9); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()   # nose
    c.set_source_rgb(*rgb('#6a4e3e'))
    for s in (-1, 1):   # front flippers
        c.move_to(s * Wd * 0.8, 170); c.curve_to(s * (Wd + 70), 190 + 20 * math.sin(t * 12), s * (Wd + 60), 250, s * Wd * 0.6, 240); c.close_path(); c.fill()
    for s in (-1, 1):
        c.set_source_rgb(1, 1, 1); c.arc(s * 30, 62, 14, 0, 2 * math.pi); c.fill()
        c.set_source_rgb(0.05, 0.05, 0.08); c.arc(s * 30, 64, 9, 0, 2 * math.pi); c.fill()
        c.set_source_rgb(1, 1, 1); c.arc(s * 27, 60, 3, 0, 2 * math.pi); c.fill()
        c.set_source_rgb(*rgb('#f2ece2')); c.set_line_width(3)
        for k in range(3): c.move_to(s * 18, 20 + k * 6); c.line_to(s * 62, 10 + k * 12); c.stroke()
    c.restore()

def draw_hippo(c, t, fi):   # the sea lion leaping up out of the water under a plank end
    th = TH[fi]
    for bp in BUMPS:
        if 'side_f' not in bp or t < bp['t'] or t > bp['t'] + RISE + 0.9 or bp['t'] + RISE >= min(S.T_END, S.T_RES + 0.01): continue
        k = (t - bp['t']) / RISE if t < bp['t'] + RISE else 1 - (t - bp['t'] - RISE) / 0.9
        k = ease(clamp(k, 0, 1))
        d = bp['side_f'] * (HALF - 60); x = PX + d * math.cos(th)
        top = PY + d * math.sin(th) + 26
        y = lerp(1900, top + 14, k)
        sealion(c, x, y, bp['side_f'], t)
    # sea lion's head bobbing in the water between leaps
    fx = PX + 320 * math.sin(t * 0.8)
    c.set_source_rgb(*rgb('#7a5e4c')); c.save(); c.translate(fx, 1730); c.scale(34, 24); c.arc(0, 0, 1, math.pi, 2 * math.pi); c.restore(); c.fill()
    for s in (-1, 1): c.set_source_rgb(0.05, 0.05, 0.08); c.arc(fx + s * 12, 1718, 4, 0, 2 * math.pi); c.fill()
    # front water layer hides the sea lion's tail
    c.set_source_rgb(*rgb(SEA_D)); c.rectangle(0, 1735, W, H - 1735); c.fill()
    c.set_source_rgba(1, 1, 1, 0.35); c.set_line_width(6)
    c.move_to(0, 1738)
    for x in range(0, W + 1, 30): c.line_to(x, 1738 + 6 * math.sin(x / 40 + t * 3))
    c.stroke()
    c.set_source_rgba(1, 1, 1, 0.22)
    for i in range(4):
        for k in range(3): c.rectangle((k * 380 + i * 110 + 80 * math.sin(t + i)) % (W + 100) - 50, 1780 + i * 34, 90, 4); c.fill()

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
