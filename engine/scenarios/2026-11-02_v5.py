"""2026-11-02 v5 — ITEMS LEFT – ICE BLOCKS LEFT: the ORCA and the ICE FLOES. Gloop is a passive rigid
ball (Ball) bouncing along a row of floating ice blocks between two icebergs. Every landing cracks
the block under him (3 cracks = it breaks and sinks); a seeded-random orca breaches under random
blocks (some aimed near him) and smashes one. If his bounce comes down over open water he falls in
(= fail, frozen in an ice cube). Timer ends with him still on the ice = win."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

SAY = 'the ice floes'
SEED = int(os.environ.get('SEED', 3))
rng = random.Random(SEED)

class S: pass
S.HOOK2 = 'THE ICE FLOES?'; S.HOOK2_SIZE = 96; S.FAIL_WORD = 'SPLASH!'; S.FAIL_SIZE = 150
S.T_START = HOOK_T; S.TL = 13.0; S.T_END = S.T_START + S.TL
TOP = 1500; WATER = 1530; R = 58; BERG_L, BERG_R = 110, 970; XMIN, XMAX = BERG_L + R, BERG_R - R
NB = 10; BW = (BERG_R - BERG_L) / NB; HP = int(os.environ.get('HP', 3))

class IceRow:
    soft = False
    def __init__(self): self.alive = [True] * NB; self.hp = [HP] * NB; self.over_water = False
    def idx(self, x): return int(clamp((x - BERG_L) // BW, 0, NB - 1))
    def y(self, x):
        if x < BERG_L + 4 or x > BERG_R - 4: return TOP
        i = self.idx(x)
        if self.alive[i]: return TOP
        a = i
        while a > 0 and not self.alive[a - 1]: a -= 1
        b = i
        while b < NB - 1 and not self.alive[b + 1]: b += 1
        gap = (b - a + 1) * BW
        return TOP + 12 if gap < 2 * R * 0.95 else H + 400   # a one-block gap is narrower than Gloop: he lands on its edges
    def slope(self, x, d=30): return 0.0
    def dig(self, *a): pass
ICE = IceRow()
SEA = Terrain(WATER + R * 0.5, seed=SEED, bumps=0, amp=0, soft=False)

RAMS = []; t = 0.6
while t < S.T_END + 1:
    RAMS.append({'t': t, 'aim': rng.random() < 0.2, 'i': rng.randrange(NB)}); t += rng.uniform(2.4, 4.0)
N0 = int(40 * FPS); GX, GYS, LEFT, ALIVE, HPS = [], [], [], [], []
ball = Ball(rng.uniform(350, 730), ICE, R=R, seed=SEED, xmin=XMIN, xmax=XMAX, hop=rng.uniform(220, 280))
T_FAIL = None; BREAKS = []; CRACKS = []; nl = 0
for f in range(N0):
    t = f / FPS
    live = T_FAIL is None and S.T_START <= t < S.T_END
    for r in RAMS:
        if abs(t - (r['t'] - 0.6)) < 0.5 / FPS and r['aim']: r['i'] = ICE.idx(ball.x + rng.uniform(-BW, BW))
        if abs(t - r['t']) < 0.5 / FPS and live:
            i = r['i']
            if ICE.alive[i]: ICE.alive[i] = False; BREAKS.append((t, i, 'orca')); r['did'] = True
            if abs(ball.x - (BERG_L + (i + 0.5) * BW)) < BW and ball.height() < 30: ball.push(rng.choice((-1, 1)) * 250, -700)
    ball.step(t)
    while nl < len(ball.landings):
        tl, xl, imp = ball.landings[nl]; nl += 1
        if T_FAIL is None and S.T_START <= tl < S.T_END and BERG_L < xl < BERG_R:
            i = ICE.idx(xl)
            if ICE.alive[i]:
                ICE.hp[i] -= 1; CRACKS.append((tl, i, ICE.hp[i]))
                if ICE.hp[i] <= 0: ICE.alive[i] = False; BREAKS.append((tl, i, 'crack'))
    if T_FAIL is None and ball.y > TOP + 10 and live: T_FAIL = t
    if T_FAIL is not None and ball.T is ICE and ball.y > WATER - R * 0.2:
        ball.T = SEA; ball.vmin = 0; ball.e = 0.1; ball.vy = 0
    if ball.T is SEA: ball.vx *= 0.85
    GX.append(ball.x); GYS.append(ball.y); LEFT.append(sum(ICE.alive)); ALIVE.append(list(ICE.alive)); HPS.append(list(ICE.hp))
S.OUTCOME = 'fail' if T_FAIL else 'win'
S.T_RES = T_FAIL if T_FAIL else S.T_END
S.GRAB = (540, TOP - R)
END = S.END = Ending(S)
gi = min(int(END.T_GRAB * FPS), N0 - 1); S.GRAB = (GX[gi], GYS[gi] - (30 if T_FAIL else 0))
S.events = [[0.05, 'rumble', 1.0]]
for r in RAMS:
    if r['t'] < S.T_RES + 0.1 and r['t'] >= S.T_START: S.events.append([r['t'] - 0.1, 'splash'])
for (tb, i, why) in BREAKS: S.events.append([tb, 'crackle']); S.events.append([tb + 0.2, 'splash'])
for (tc, i, hp) in CRACKS:
    if hp > 0: S.events.append([tc, 'clink'])
for (tl, xl, imp) in ball.landings:
    if tl < S.T_RES + 1.5: S.events.append([tl, 'hop'])
for tw in ball.walls:
    if tw < S.T_RES: S.events.append([tw, 'thump', 0.3])
if T_FAIL: S.events += [[T_FAIL + 0.15, 'splash'], [T_FAIL + 0.7, 'freeze']]
S.AMB = {'drone': 50, 'wind': 0.04}

def draw_bar(c, t, f):
    n = LEFT[f]; recent = any(tb <= t < tb + 0.35 for (tb, _, _) in BREAKS)
    bx = bar(c, n / NB, f'ICE BLOCKS LEFT: {n}', rgb('#8fe3ff') if n > 4 else (rgb('#ffd84a') if n > 2 else rgb('#ff4d4d')), 0.15 if recent else 0, bw=660, x_off=36)
    c.save(); c.translate(bx - 52, 231); c.set_source_rgb(*rgb('#cdeffc')); rrect(c, -26, -22, 52, 44, 8); c.fill()
    c.set_source_rgb(*rgb('#8fc8e0')); rrect(c, -26, 6, 52, 16, 6); c.fill(); c.restore()
S.draw_bar = draw_bar

stars = [(rng.uniform(0, W), rng.uniform(HEAD, 1100), rng.uniform(1.2, 2.6)) for _ in range(70)]
flakes = [(rng.uniform(0, W), rng.uniform(0, H), rng.uniform(2, 5), rng.uniform(0.6, 1.4)) for _ in range(90)]
def draw_bg(c, t):
    c.set_source_rgb(*rgb('#101a2b')); c.rectangle(0, HEAD, W, H - HEAD); c.fill()
    c.set_source_rgba(0.85, 0.9, 1, 0.55)
    for x, y, r in stars: c.arc(x, y, r, 0, 2 * math.pi); c.fill()
    c.set_source_rgba(0.4, 0.9, 0.7, 0.08)   # faint flat aurora band
    c.move_to(0, 700); c.curve_to(300, 560 + 30 * math.sin(t), 700, 820, W, 620); c.line_to(W, 700); c.curve_to(700, 900, 300, 640, 0, 790); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#e6e9ee')); c.arc(820, 560, 50, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb('#1c2a40'))
    c.move_to(0, WATER); c.line_to(140, 1250); c.line_to(300, 1330); c.line_to(480, 1180); c.line_to(700, 1320); c.line_to(880, 1220); c.line_to(W, 1300); c.line_to(W, WATER); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#0f2a3d')); c.rectangle(0, WATER, W, H - WATER); c.fill()
    c.set_source_rgba(1, 1, 1, 0.06)
    for i in range(7): c.rectangle(0, WATER + 40 + i * 52, W, 6); c.fill()

def orca_draw(c, x, y, s, ang, mouth=0.0):
    c.save(); c.translate(x, y); c.rotate(ang); c.scale(s, s)
    c.set_source_rgb(*rgb('#1a1d24')); c.save(); c.scale(1.6, 0.75); c.arc(0, 0, 90, 0, 2 * math.pi); c.restore(); c.fill()
    c.move_to(-120, -40); c.line_to(-60, -150); c.line_to(-20, -55); c.close_path(); c.fill()
    c.move_to(-140, 0); c.line_to(-210, -50); c.line_to(-200, 40); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#e8edf2')); c.save(); c.translate(70, -18); c.scale(30, 14); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    c.save(); c.translate(20, 40); c.scale(90, 22); c.arc(0, 0, 1, 0, math.pi); c.restore(); c.fill()
    c.set_source_rgb(0.05, 0.05, 0.08); c.arc(95, -20, 6, 0, 2 * math.pi); c.fill()
    c.restore()

def draw_bergs(c):
    for (xa, xb, s) in ((0, BERG_L, -1), (BERG_R, W, 1)):   # icebergs = walls
        pts = [(0, H), (0, 980), (xb - 40, 1000), (xb, 1060), (xb, H)] if s < 0 else [(xa, H), (xa, 1060), (xa + 40, 990), (W, 970), (W, H)]
        c.set_source_rgb(*rgb('#dbeef6')); c.move_to(*pts[0])
        for pp in pts[1:]: c.line_to(*pp)
        c.close_path(); c.fill()
        c.set_source_rgb(*rgb('#a9d1e2')); c.rectangle(xa, TOP + 40, xb - xa, H - TOP); c.fill()

def draw_orca(c, t):
    for r in RAMS:
        if r['t'] - 0.6 <= t < r['t'] + 0.7 and (r['t'] < S.T_RES + 0.1 or r['t'] < S.T_START):
            x = BERG_L + (r['i'] + 0.5) * BW; k = (t - (r['t'] - 0.6)) / 1.3
            y = WATER + 260 - math.sin(k * math.pi) * 380
            orca_draw(c, x, y, 0.8, -math.pi / 2 + 0.6 * (k - 0.5))
            return
    x = (t * 160 + 300) % (W + 400) - 200   # fin cruising by
    c.set_source_rgb(*rgb('#1a1d24')); c.move_to(x - 40, WATER + 8); c.line_to(x + 10, WATER - 90); c.line_to(x + 30, WATER + 8); c.close_path(); c.fill()

def draw_ice(c, t, f):
    al = ALIVE[f]; hp = HPS[f]
    for i in range(NB):
        x0 = BERG_L + i * BW
        bob = 3 * math.sin(t * 2 + i * 1.3)
        if al[i]:
            c.set_source_rgb(*rgb('#cfe7f2')); rrect(c, x0 + 3, TOP + bob, BW - 6, 52, 8); c.fill()
            c.set_source_rgb(*rgb('#9cc6da')); rrect(c, x0 + 3, TOP + 30 + bob, BW - 6, 22, 6); c.fill()
            c.set_source_rgb(*rgb('#3d6f88')); c.set_line_width(3)
            for k in range(HP - hp[i]):
                rr = random.Random(i * 10 + k); xa = x0 + rr.uniform(15, BW - 15)
                c.move_to(xa, TOP + bob + 2); c.line_to(xa + rr.uniform(-14, 14), TOP + bob + 22); c.line_to(xa + rr.uniform(-10, 10), TOP + bob + 44); c.stroke()
        else:
            br = [b for b in BREAKS if b[1] == i]
            if br and t - br[0][0] < 1.0:
                k = (t - br[0][0]); c.set_source_rgba(0.81, 0.9, 0.95, 1 - k)
                for j, dx in enumerate((-0.25, 0.25)):
                    c.save(); c.translate(x0 + BW * (0.5 + dx) + dx * 80 * k, TOP + 20 + 160 * k * k - (180 * k if br[0][2] == 'orca' else 0)); c.rotate(dx * 4 * k); rrect(c, -BW * 0.22, -20, BW * 0.44, 40, 6); c.fill(); c.restore()

PS = Particles(9)
def render(f, c):
    t = f / FPS; fi = min(f, len(GX) - 1); shake = (0, 0)
    for (tb, i, why) in BREAKS:
        if tb <= t < tb + 0.15 and why == 'orca': shake = (rng.uniform(-4, 4), rng.uniform(-4, 4))
    c.save(); c.translate(*shake)
    draw_bg(c, t); draw_orca(c, t); draw_bergs(c)
    fell = T_FAIL is not None and t >= T_FAIL
    if END.carried(t) or t >= END.T_GRAB: gx, gy = (END.carry_xy(t) if END.carried(t) else S.GRAB)
    else:
        gx, gy = GX[fi], GYS[fi]
        if fell and gy > WATER - R * 0.5: gy = WATER - R * 0.4 + 5 * math.sin(t * 3)
    p = LEFT[fi] / NB
    mood = 'happy' if (t >= S.T_END and S.OUTCOME == 'win') else ('scared' if fell or p < 0.5 else 'worried')
    frozen = fell and t > T_FAIL + 0.7
    skin = ('#d6f2ff', '#8fc8ff', '#2f6fbf') if frozen else ('#ffd36b', '#ff8a1f', '#c45a00')
    draw_blob(c, T_FAIL + 0.7 if frozen else t, gx, gy, 'scared' if frozen else mood, 0, R=R, skin=skin, sweat=not frozen)
    if frozen:
        k = ease((t - T_FAIL - 0.7) / 0.3); s = 92
        c.set_source_rgba(0.75, 0.92, 1, 0.45 * k); rrect(c, gx - s, gy - s, 2 * s, 2 * s, 20); c.fill()
        c.set_source_rgba(1, 1, 1, 0.8 * k); c.set_line_width(6); rrect(c, gx - s, gy - s, 2 * s, 2 * s, 20); c.stroke()
        c.move_to(gx - 60, gy - 70); c.line_to(gx - 25, gy - 78); c.stroke()
    if fell and not END.carried(t):
        c.set_source_rgba(0.06, 0.16, 0.24, 0.6); c.rectangle(BERG_L, WATER + 10, BERG_R - BERG_L, 120); c.fill()
    draw_ice(c, t, fi)
    for (tb, i, why) in BREAKS:
        if abs(t - tb) < 0.5 / FPS: PS.spawn(BERG_L + (i + 0.5) * BW, TOP + 10, 16, (0.85, 0.95, 1), 420, 0.6, grav=1500, r=7)
    if T_FAIL and abs(t - T_FAIL - 0.15) < 0.5 / FPS: PS.spawn(GX[fi], WATER, 26, (0.6, 0.85, 0.95), 650, 0.8, grav=2200, r=9)
    PS.draw(c)
    for x, y, r, sp in flakes:
        c.set_source_rgba(1, 1, 1, 0.6); c.arc((x + t * 30 * sp) % W, (y + t * 120 * sp) % (H - HEAD) + HEAD, r, 0, 2 * math.pi); c.fill()
    END.draw_claw(c, t)
    c.restore()
    END.header(c, t, fi)

if __name__ == '__main__':
    if sys.argv[1] == 'sim':
        e = int(S.T_RES * FPS) - 1
        print(SEED, S.OUTCOME, round(S.T_RES - S.T_START, 2), 'left', LEFT[e], 'breaks', [(round(b[0] - S.T_START, 1), b[2][0]) for b in BREAKS], 'dur', S.DUR); sys.exit()
    run(S, render)
