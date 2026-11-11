"""Gloop ARENA generator (2026-11-11). Built on gloop_common (Ball, Terrain, Ending, header, draw_blob, run).

One video = one ARENA (shape + colours + walls/floor obstacles) + 1-2 HAZARDS. Gloop is the usual passive
rigid Ball: dropped by the claw at frame 0, gravity, real bounces off the arena floor/walls, hazards push him
only through real contact (momentum along the contact normal). One touch of a hazard during the countdown =
GLOOP FAILED. Every hazard ramps up (speed / rate / count) as the SURVIVE timer runs.

Nothing is scripted: the outcome, the near-misses and the hook all come out of the sim. gloop_daily.py runs
the sim headless for many seeds/difficulties, scores every run (near-misses, hook, late drama, outcome) and
only the best run is rendered.

Scenario files just do:  from gloop_arena import main; SAY = '...'; main({...cfg...})
  python3 scen.py sim x          -> one-line JSON summary of the run
  python3 scen.py out.mp4 ev.json [t1,t2,...]   -> render (or stills), like every other scenario
"""
import sys, os, math, random, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gloop_common import *

GROUND = 1600; R = 58; NEAR = 60.0; SUB = 4; RAMP = 1.0; HEARTS = 3; GRACE = 0.45

# ------------------------------------------------------------------------------------------------ arenas
def _prof(kind, WL, WR):
    xs = np.arange(W + 1, dtype=float); g = float(GROUND); c = (WL + WR) / 2; hw = (WR - WL) / 2
    if kind == 'flat': h = np.full(W + 1, g)
    elif kind == 'bowl': h = g - 170 * np.clip(((xs - c) / hw) ** 2, 0, 1.3)
    elif kind == 'wavy': h = g - 22 - 26 * np.sin((xs - WL) / 70.0)
    elif kind == 'twin': h = g - 115 * np.exp(-((xs - (c - 210)) / 72) ** 2) - 115 * np.exp(-((xs - (c + 210)) / 72) ** 2)
    elif kind == 'valley': h = g - 150 * np.clip(np.abs(xs - c) / hw, 0, 1)
    elif kind == 'steps': h = g - 110 / (1 + np.exp((xs - (c - 160)) / 22)) - 60 / (1 + np.exp(-(xs - (c + 170)) / 22))
    elif kind == 'mound': h = g - 165 * np.exp(-((xs - c) / 115) ** 2)
    elif kind == 'ramp': h = g - 150 * np.clip(1 - (xs - WL) / (WR - WL), 0, 1)
    return h

ARENAS = {   # shape, walls, palette, backdrop motif
    'neon_lab':      dict(label='a neon lab', shape='flat',   WL=110, WR=970, bg='#0f1424', bg2='#16203a', wall='#1c2a44', wall2='#2a3e62', top='#2a3a5a', deep='#121a2c', rim='#5ad0ff', acc='#5ad0ff'),
    'lava_forge':    dict(label='a lava forge', shape='bowl', WL=100, WR=980, bg='#1a1012', bg2='#24161a', wall='#3a2420', wall2='#4e2e26', top='#4a2e26', deep='#1e1210', rim='#ff8a3a', acc='#ff8a3a'),
    'ice_cave':      dict(label='an ice cave', shape='wavy',  WL=150, WR=930, bg='#0e1a26', bg2='#14263a', wall='#2a4a66', wall2='#3e6688', top='#9ec4e0', deep='#3a5a78', rim='#d8f0ff', acc='#bfe6ff'),
    'jungle_temple': dict(label='a jungle temple', shape='twin', WL=110, WR=970, bg='#0f1a14', bg2='#16261c', wall='#3a4434', wall2='#4c5844', top='#4a5a3c', deep='#1e2618', rim='#7ab05a', acc='#9ad06a'),
    'space_dock':    dict(label='a space dock', shape='valley', WL=110, WR=970, bg='#0c0a1c', bg2='#16122e', wall='#2a2444', wall2='#3e3462', top='#3a3458', deep='#16122a', rim='#b08aff', acc='#b08aff'),
    'factory':       dict(label='a factory', shape='steps', WL=120, WR=960, bg='#16161a', bg2='#202026', wall='#34343c', wall2='#4a4a54', top='#4a4a52', deep='#1e1e22', rim='#ffcf3a', acc='#ffcf3a'),
    'candy_box':     dict(label='a candy box', shape='mound', WL=130, WR=950, bg='#24121e', bg2='#341a2c', wall='#5a2a46', wall2='#7a3a60', top='#e07aa8', deep='#7a3a5a', rim='#ffd0e4', acc='#7ae0c0'),
    'desert_ruins':  dict(label='desert ruins', shape='ramp', WL=110, WR=970, bg='#141626', bg2='#1c2036', wall='#5a4a36', wall2='#6e5c44', top='#b08a5a', deep='#5a4430', rim='#d8b47a', acc='#e6c48a'),
}

# ------------------------------------------------------------------------------------------------ hazards
HAZ = {   # say (voice/hook), title words, fail word, hashtag
    'saws':       ('the saws', 'saws', 'BONK!', '#saws'),
    'lasers':     ('the lasers', 'lasers', 'ZAPPED!', '#lasers'),
    'spikes':     ('the spike traps', 'spike traps', 'POKED!', '#spikes'),
    'crusher':    ('the crushing walls', 'crushing walls', 'SQUISHED!', '#crusher'),
    'blocks':     ('the falling blocks', 'falling blocks', 'BONK!', '#fallingblocks'),
    'lava':       ('the lava waves', 'lava waves', 'TOO HOT!', '#lava'),
    'spikeballs': ('the spike balls', 'spike balls', 'OUCH!', '#bouncingballs'),
    'cannons':    ('the cannonballs', 'cannonballs', 'BOOM!', '#cannons'),
}
def ring(rng, lo, hi): return rng.choice((-1, 1)) * rng.uniform(lo, hi)   # aim just past Gloop (he keeps moving)
INCOMPAT = [{'lava', 'spikes'}, {'crusher', 'spikeballs'}, {'crusher', 'cannons'}]

def _seg_gap(px, py, x1, y1, x2, y2, hw):
    dx, dy = x2 - x1, y2 - y1; L2 = dx * dx + dy * dy or 1
    u = clamp(((px - x1) * dx + (py - y1) * dy) / L2, 0, 1); qx, qy = x1 + u * dx, y1 + u * dy
    d = math.hypot(px - qx, py - qy); return d - hw - R, ((px - qx) / (d or 1), (py - qy) / (d or 1) if d else -1)
def _rect_gap(px, py, x0, y0, x1, y1):
    qx, qy = clamp(px, x0, x1), clamp(py, y0, y1); d = math.hypot(px - qx, py - qy)
    if d > 0: return d - R, ((px - qx) / d, (py - qy) / d)
    return -R - min(px - x0, x1 - px, py - y0, y1 - py), (0.0, -1.0)

class Hz:
    def __init__(s, w, rng, opening): s.w, s.rng, s.op = w, rng, opening; s.n = 0; s.D = w.D * (w.WGT[0] if opening else w.WGT[1])
    def nid(s): s.n += 1; return f'{s.__class__.__name__}{s.n}'
    def ev(s, t, *a): s.w.events.append([t, *a])

class Saws(Hz):
    """Spinning saw blades flying in straight lines, bouncing off walls/ceiling/floor. More + faster over time."""
    def __init__(s, w, rng, op):
        super().__init__(w, rng, op); s.saws = []; s.halt = 1.0
        b = w.ball
        if op:
            sd = 1 if b.x < (w.WL + w.WR) / 2 else -1
            d = rng.uniform(220, 320); x = clamp(b.x + sd * d, w.WL + 80, w.WR - 80); y = clamp(b.y - rng.uniform(150, 300), HEAD + 90, GROUND - 400)
            s.add(x, y, b.x + sd * rng.uniform(-40, 160), b.y + 300)
        else: s.add_far()
        s.more = [w.T_START + w.TL * 0.5]
    def add(s, x, y, tx, ty):
        a = math.atan2(ty - y, tx - x); s.saws.append(dict(x=x, y=y, dx=math.cos(a), dy=math.sin(a), r=48, rot=0.0, id=s.nid(), a=1.0))
    def add_far(s, top=False):
        b = s.w.ball
        for _ in range(40):
            x = s.rng.uniform(s.w.WL + 90, s.w.WR - 90); y = HEAD + 40 if top else s.rng.uniform(HEAD + 150, GROUND - 260)
            if math.hypot(x - b.x, y - b.y) > 420: break
        a = math.pi / 2 + s.rng.uniform(-0.7, 0.7) if top else s.rng.uniform(0, 2 * math.pi)
        s.saws.append(dict(x=x, y=y, dx=math.cos(a), dy=math.sin(a), r=48, rot=0.0, id=s.nid(), a=0.0 if top else 1.0))
    def step(s, t, dt, k, live):
        if live and s.more and t >= s.more[0]: s.more.pop(0); s.add_far(top=True); s.ev(t, 'whoosh')
        if not live: s.halt = max(0.0, s.halt - dt / 0.6)
        v = 300 * k * s.D * s.halt; T = s.w.TER
        for q in s.saws:
            q['a'] = min(1.0, q['a'] + dt / 0.3)
            q['x'] += q['dx'] * v * dt; q['y'] += q['dy'] * v * dt; q['rot'] += v * dt / q['r']
            r = q['r']
            if q['x'] < s.w.WL + r: q['x'] = s.w.WL + r; q['dx'] = abs(q['dx']); s.ev(t, 'clink')
            if q['x'] > s.w.WR - r: q['x'] = s.w.WR - r; q['dx'] = -abs(q['dx']); s.ev(t, 'clink')
            if q['y'] < HEAD + 20 + r and q['dy'] < 0: q['dy'] = abs(q['dy'])
            gy = T.y(q['x'])
            if q['y'] + r > gy and q['dy'] > 0:
                g = T.slope(q['x']); n = math.hypot(g, 1); nx, ny = g / n, -1 / n
                vn = q['dx'] * nx + q['dy'] * ny; q['dx'] -= 2 * vn * nx; q['dy'] -= 2 * vn * ny; q['y'] = gy - r; s.ev(t, 'clink')
            if abs(q['dy']) < 0.6: q['dy'] = math.copysign(0.6, q['dy'] or 1)   # saw rails: always steep diagonals
            m = math.hypot(q['dx'], q['dy']) or 1; q['dx'] /= m; q['dy'] /= m
        s.v = v
    def shapes(s):
        return [('c', q['x'], q['y'], q['r'], q['dx'] * s.v, q['dy'] * s.v, q['id']) for q in s.saws if q['a'] > 0.5]
    def snap(s): return [(q['x'], q['y'], q['r'], q['rot'], q['a']) for q in s.saws]
    def draw_front(s, c, sn, t, A):
        for (x, y, r, rot, a) in sn:
            c.save(); c.translate(x, y); c.rotate(rot); c.push_group()
            c.set_source_rgb(*rgb('#9aa2ae'))
            for i in range(16):
                b = i * math.pi / 8; c.move_to(math.cos(b) * (r - 8), math.sin(b) * (r - 8)); c.line_to(math.cos(b + 0.12) * (r + 10), math.sin(b + 0.12) * (r + 10)); c.line_to(math.cos(b + 0.3) * (r - 8), math.sin(b + 0.3) * (r - 8)); c.close_path(); c.fill()
            c.set_source_rgb(*rgb('#c4cad4')); c.arc(0, 0, r - 4, 0, 2 * math.pi); c.fill()
            c.set_source_rgb(*rgb('#8a909c')); c.arc(0, 0, r * 0.55, 0, 2 * math.pi); c.fill()
            c.set_source_rgb(*rgb('#2a2e36')); c.arc(0, 0, 12, 0, 2 * math.pi); c.fill()
            c.set_source_rgba(1, 1, 1, 0.35); c.set_line_width(5); c.arc(0, 0, r * 0.78, 0.2, 1.2); c.stroke()
            c.pop_group_to_source(); c.paint_with_alpha(a * A); c.restore()

class Lasers(Hz):
    """Wall/ceiling emitters: 0.6 s thin warning line, then a 0.4 s beam. Faster cycles over time."""
    WARN, ACT = 0.6, 0.3
    def __init__(s, w, rng, op):
        super().__init__(w, rng, op); s.beams = []; b = w.ball
        s.next = w.T_START - 0.45
        if op: s.beams.append(dict(k='v', p=clamp(b.x + b.vx * 0.5 + ring(rng, R + 20, R + 120), w.WL + 40, w.WR - 40), t0=-0.15, id=s.nid()))
    def step(s, t, dt, k, live):
        w = s.w; b = w.ball
        if live and t >= s.next:
            if s.rng.random() < 0.35:
                y = b.y + ring(s.rng, R + 15, R + 130) if s.rng.random() < 0.4 else s.rng.uniform(HEAD + 200, GROUND - 60)
                s.beams.append(dict(k='h', p=clamp(y, HEAD + 140, w.TER.h[w.WL:w.WR].min() - 25), t0=t, id=s.nid()))
            else:
                x = b.x + b.vx * (s.WARN + 0.1) + ring(s.rng, R + 14, R + 110) if s.rng.random() < 0.75 else s.rng.uniform(w.WL + 40, w.WR - 40)
                s.beams.append(dict(k='v', p=clamp(x, w.WL + 40, w.WR - 40), t0=t, id=s.nid()))
            s.ev(t, 'blip'); s.ev(t + s.WARN, 'sizzle')
            s.next = t + 1.2 / (k * s.D) + s.rng.uniform(0, 0.3)
        if not live and getattr(s, 'stop', None) is None: s.stop = t; s.beams = []
        s.beams = [q for q in s.beams if t < q['t0'] + s.WARN + s.ACT + 0.05]
        s.t = t
    def _seg(s, q):
        if q['k'] == 'h': return (s.w.WL, q['p'], s.w.WR, q['p'])
        return (q['p'], HEAD, q['p'], s.w.TER.y(q['p']))
    def active(s, q, t): return q['t0'] + s.WARN <= t < q['t0'] + s.WARN + s.ACT and (getattr(s, 'stop', None) is None or t < s.stop)
    def shapes(s):
        return [('s', *s._seg(q), 10, 0, 0, q['id']) for q in s.beams if s.active(q, s.t)]
    def threats(s): return [('s', *s._seg(q), 10, 0, 0, q['id']) for q in s.beams]
    def snap(s): return [(s._seg(q), s.t - q['t0'], s.active(q, s.t)) for q in s.beams]
    def draw_walls(s, c, sn, t, A):
        c.set_source_rgb(*rgb('#3a3a46'))
        for y in (HEAD + 140, GROUND - 160):
            rrect(c, s.w.WL - 26, y - 22, 26, 44, 6); c.fill(); rrect(c, s.w.WR, y - 22, 26, 44, 6); c.fill()
    def draw_front(s, c, sn, t, A):
        for (seg, age, act) in sn:
            x1, y1, x2, y2 = seg
            if age < s.WARN:
                c.set_source_rgba(1, 0.3, 0.3, 0.35 + 0.35 * ((age * 8) % 1 < 0.5)); c.set_line_width(4); c.set_dash([18, 14])
                c.move_to(x1, y1); c.line_to(x2, y2); c.stroke(); c.set_dash([])
            elif act:
                c.set_source_rgb(*rgb('#ff3b4a')); c.set_line_width(22); c.move_to(x1, y1); c.line_to(x2, y2); c.stroke()
                c.set_source_rgb(*rgb('#ffe0e0')); c.set_line_width(7); c.move_to(x1, y1); c.line_to(x2, y2); c.stroke()
            c.set_source_rgb(*rgb('#5a5a66')); rrect(c, x1 - 20, y1 - 20, 40, 40, 8) if seg[1] == seg[3] else rrect(c, x1 - 22, HEAD, 44, 26, 6); c.fill()

class Spikes(Hz):
    """Floor spike traps: 0.5 s warning marks, then the spikes shoot up, hold, retract. More often over time."""
    TW, TR, TH, TF, WD, HM = 0.5, 0.07, 0.25, 0.15, 130, 92
    def __init__(s, w, rng, op):
        super().__init__(w, rng, op); s.traps = []; b = w.ball; s.next = w.T_START - 0.35
        x = b.x + b.vx * 0.55 + ring(rng, R + 75, R + 160) if op else rng.uniform(w.WL + 80, w.WR - 80)
        s.traps.append(dict(x=clamp(x, w.WL + 72, w.WR - 72), t0=-0.2, id=s.nid()))
    def h(s, q, t):
        a = t - q['t0'] - s.TW
        if a < 0: return 0.0, 0.0
        if a < s.TR: return s.HM * a / s.TR, -s.HM / s.TR
        if a < s.TR + s.TH: return s.HM, 0.0
        a -= s.TR + s.TH
        if a < s.TF: return s.HM * (1 - a / s.TF), s.HM / s.TF
        return 0.0, 0.0
    def step(s, t, dt, k, live):
        w = s.w; b = w.ball
        if live and t >= s.next:
            x = b.x + b.vx * 0.55 + ring(s.rng, R + 66, R + 135) if s.rng.random() < 0.8 else s.rng.uniform(w.WL + 80, w.WR - 80)
            s.traps.append(dict(x=clamp(x, w.WL + 72, w.WR - 72), t0=t, id=s.nid())); s.ev(t + s.TW, 'slam', 0.6)
            s.next = t + 1.1 / (k * s.D) + s.rng.uniform(0, 0.3)
        if not live and getattr(s, 'stop', None) is None:
            s.stop = t; s.traps = [q for q in s.traps if t - q['t0'] > s.TW]   # armed ones still finish, warnings cancel
        s.traps = [q for q in s.traps if t < q['t0'] + s.TW + s.TR + s.TH + s.TF + 0.05]; s.t = t
    def shapes(s):
        out = []
        for q in s.traps:
            hh, vy = s.h(q, s.t)
            if hh > 3: base = s.w.TER.y(q['x']); out.append(('r', q['x'] - s.WD / 2, base - hh, q['x'] + s.WD / 2, base + 20, 0, vy, q['id']))
        return out
    def snap(s): return [(q['x'], s.t - q['t0'], s.h(q, s.t)[0]) for q in s.traps]
    def threats(s): return [('r', q['x'] - s.WD / 2, s.w.TER.y(q['x']) - s.HM, q['x'] + s.WD / 2, s.w.TER.y(q['x']) + 20, 0, 0, q['id']) for q in s.traps]
    def draw_mid(s, c, sn, t, A):
        for (x, age, hh) in sn:
            base = s.w.TER.y(x) + 4
            if age < s.TW:
                c.set_source_rgba(1, 0.35, 0.3, 0.5 + 0.4 * ((age * 8) % 1 < 0.5))
                for i in range(5): c.save(); c.translate(x - 56 + i * 28, base - 6); c.scale(10, 4); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
            if hh > 1:
                c.set_source_rgb(*rgb('#3a3e48')); c.rectangle(x - s.WD / 2, base - 10, s.WD, 14); c.fill()
                c.set_source_rgb(*rgb('#c8ced8'))
                for i in range(5):
                    xx = x - s.WD / 2 + i * s.WD / 5; c.move_to(xx + 3, base - 6); c.line_to(xx + s.WD / 10, base - 6 - hh); c.line_to(xx + s.WD / 5 - 3, base - 6); c.close_path(); c.fill()

class Crusher(Hz):
    """Shrinking walls: both side walls creep inward over the timer (Gloop bounces off them as normal walls),
    and spiked blocks shoot out of them in pulses (some on the side Gloop is on) and retract."""
    def __init__(s, w, rng, op):
        super().__init__(w, rng, op); s.p = {-1: [], 1: []}; b = w.ball; s.next = w.T_START + 0.2; s.id = {-1: s.nid(), 1: s.nid()}
        side = -1 if b.vx > 0 else 1   # opening pulse chases him from behind
        if op: s.p[side].append((-0.4, s.amp(side, b.x, 0.0, rng.uniform(8, 70))))
        s.cur = {-1: 0.0, 1: 0.0}; s.vel = {-1: 0.0, 1: 0.0}; s.cr = 0.0; s.t = 0.0
    def creep(s, t): return 150 * clamp((t - s.w.T_START) / s.w.TL, 0, 1)
    def amp(s, side, bx, cr, margin=None):
        w = s.w; dist = (bx - w.WL - cr) if side < 0 else (w.WR - cr - bx)
        if margin is None: margin = s.rng.uniform(-10, 95)
        return clamp(dist - R - margin, 90, 330)
    def off(s, side, t):
        o = 0.0
        for (t0, a) in s.p[side]:
            u = t - t0
            if 0 <= u < 0.35: o = max(o, a * ease(u / 0.35))
            elif 0.35 <= u < 0.6: o = max(o, a)
            elif 0.6 <= u < 1.2: o = max(o, a * (1 - ease((u - 0.6) / 0.6)))
        return o
    def step(s, t, dt, k, live):
        w = s.w; b = w.ball
        if live and t >= s.next:
            side = (-1 if b.x < (w.WL + w.WR) / 2 else 1) if s.rng.random() < 0.8 else s.rng.choice((-1, 1))
            s.p[side].append((t, s.amp(side, b.x, s.cr))); s.ev(t, 'creak'); s.ev(t + 0.35, 'slam', 0.7)
            s.next = t + 1.2 / (k * s.D) + s.rng.uniform(0, 0.4)
        if not live and getattr(s, 'stop', None) is None: s.stop = t
        if getattr(s, 'stop', None) is None: s.cr = s.creep(t)
        b.xmin = w.WL + s.cr + R; b.xmax = w.WR - s.cr - R
        for sd in (-1, 1):
            o = s.off(sd, t) if getattr(s, 'stop', None) is None else max(0.0, s.cur[sd] - 500 * dt)
            s.vel[sd] = (o - s.cur[sd]) / dt; s.cur[sd] = o
        s.t = t
    def face(s, sd): return (s.w.WL + s.cr + s.cur[-1]) if sd < 0 else (s.w.WR - s.cr - s.cur[1])
    def shapes(s):
        out = []
        if s.cur[-1] > 10: out.append(('r', 0, HEAD, s.face(-1), H, s.vel[-1], 0, s.id[-1]))
        if s.cur[1] > 10: out.append(('r', s.face(1), HEAD, W, H, -s.vel[1], 0, s.id[1]))
        return out
    def snap(s): return (s.cr, s.cur[-1], s.cur[1])
    def draw_front(s, c, sn, t, A):
        w = s.w; cr = sn[0]
        for sd, o in ((-1, sn[1]), (1, sn[2])):
            wx = w.WL + cr if sd < 0 else w.WR - cr   # the moving wall face
            c.set_source_rgb(*rgb(w.A['wall'])); c.rectangle(0 if sd < 0 else wx, HEAD, wx if sd < 0 else W - wx, H - HEAD); c.fill()
            c.set_source_rgb(*rgb('#d8a020'))
            for yy in range(HEAD + 30, H, 140): c.rectangle(wx - 14 if sd < 0 else wx, yy, 14, 60); c.fill()
            if o > 1:
                x = wx + sd * -1 * -o if False else (wx + o if sd < 0 else wx - o)
                c.set_source_rgb(*rgb('#6a6e7a'))
                for yy in (HEAD + 300, GROUND - 300): c.rectangle(min(x, wx), yy - 12, abs(x - wx), 24); c.fill()
                c.set_source_rgb(*rgb('#4a4e5a')); c.rectangle(x - 26 if sd < 0 else x, HEAD, 26, GROUND + 60 - HEAD); c.fill()
                c.set_source_rgb(*rgb('#c8ced8'))
                for yy in range(HEAD + 10, GROUND + 40, 44):
                    if sd < 0: c.move_to(x, yy); c.line_to(x + 22, yy + 22); c.line_to(x, yy + 44)
                    else: c.move_to(x, yy); c.line_to(x - 22, yy + 22); c.line_to(x, yy + 44)
                    c.close_path(); c.fill()

class Blocks(Hz):
    """Heavy crates drop from above (some above where Gloop is heading) and smash on the floor. Faster rate."""
    G = 2400.0
    def __init__(s, w, rng, op):
        super().__init__(w, rng, op); s.bl = []; s.deb = []; b = w.ball; s.next = w.T_START - 0.3
        if op: s.add(clamp(b.x + b.vx * 0.45 + ring(rng, R + 60, R + 150), w.WL + 60, w.WR - 60), b.y - rng.uniform(220, 320), 350)
        else: s.add(rng.uniform(w.WL + 60, w.WR - 60), HEAD - 60, 300)
    def add(s, x, y, vy): s.bl.append(dict(x=x, y=y, vy=vy, s=100, id=s.nid(), rot=s.rng.uniform(-0.15, 0.15)))
    def step(s, t, dt, k, live):
        w = s.w; b = w.ball
        if live and t >= s.next:
            x = b.x + b.vx * 0.75 + ring(s.rng, R + 55, R + 150) if s.rng.random() < 0.75 else s.rng.uniform(w.WL + 60, w.WR - 60)
            s.add(clamp(x, w.WL + 58, w.WR - 58), HEAD - 70, 500 * k); s.ev(t, 'whoosh')
            s.next = t + 1.05 / (k * s.D) + s.rng.uniform(0, 0.3)
        if not live and getattr(s, 'stop', None) is None: s.stop = t
        keep = []
        for q in s.bl:
            q['vy'] += s.G * dt; q['y'] += q['vy'] * dt
            gy = min(w.TER.y(q['x'] - 50), w.TER.y(q['x'] + 50), w.TER.y(q['x']))
            if q['y'] + q['s'] / 2 >= gy: s.deb.append((t, q['x'], gy)); s.ev(t, 'crash')
            else: keep.append(q)
        s.bl = keep; s.deb = [d for d in s.deb if t - d[0] < 0.7]; s.t = t
    def shapes(s): return [('r', q['x'] - q['s'] / 2, q['y'] - q['s'] / 2, q['x'] + q['s'] / 2, q['y'] + q['s'] / 2, 0, q['vy'], q['id']) for q in s.bl if q['y'] > HEAD - 40]
    def snap(s): return ([(q['x'], q['y'], q['s'], q['rot']) for q in s.bl], [(s.t - d[0], d[1], d[2]) for d in s.deb])
    def draw_mid(s, c, sn, t, A):
        for (x, y, sz, rot) in sn[0]:   # landing shadow grows as it comes down
            gy = s.w.TER.y(x); k = clamp(1 - (gy - y) / 1200, 0.15, 1)
            c.set_source_rgba(0, 0, 0, 0.3 * k); c.save(); c.translate(x, gy + 3); c.scale(sz * 0.6 * k + 6, 8); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    def draw_front(s, c, sn, t, A):
        for (x, y, sz, rot) in sn[0]:
            c.save(); c.translate(x, y); c.rotate(rot); h = sz / 2
            c.set_source_rgb(*rgb('#8a6440')); c.rectangle(-h, -h, sz, sz); c.fill()
            c.set_source_rgb(*rgb('#5e4028')); c.set_line_width(12); c.rectangle(-h + 6, -h + 6, sz - 12, sz - 12); c.stroke()
            c.move_to(-h + 8, -h + 8); c.line_to(h - 8, h - 8); c.stroke()
            c.restore()
        for (age, x, gy) in sn[1]:
            k = age / 0.7
            for i in range(6):
                a = -math.pi * (0.1 + 0.8 * i / 5); d = 160 * k
                c.set_source_rgba(0.55, 0.4, 0.25, 1 - k); c.save(); c.translate(x + math.cos(a) * d, gy - 20 + math.sin(a) * d * 0.8 + 500 * k * k); c.rotate(i + 6 * k); c.rectangle(-16, -8, 32, 16); c.restore(); c.fill()

class Lava(Hz):
    """Lava waves: lava wells up from one side and rolls in across the floor to a seeded-random reach (sometimes
    toward Gloop), holds, then drains back. Reach, height and frequency grow over the timer."""
    def __init__(s, w, rng, op):
        super().__init__(w, rng, op); s.base = GROUND + 180; s.wv = []; s.next = w.T_START + 0.2; b = w.ball
        if op:
            sd = -1 if b.vx > 0 else 1
            s.wv.append(dict(t0=-0.35, sd=sd, reach=s._reach(sd, b.x, 0.0), pk=rng.uniform(45, 75)))
        s.t = 0.0; s.fr = {}; s.v = 0.0
    def _reach(s, sd, bx, extra):
        w = s.w; d = (bx - w.WL) if sd < 0 else (w.WR - bx)
        return clamp(d - R - s.rng.uniform(5, 75) + extra, 140, (w.WR - w.WL) * 0.85)
    def prof(s, q, t):
        u = t - q['t0']
        if u < 0: return 0.0, 0.0
        if u < 0.5: return ease(u / 0.5), 1.0
        if u < 0.85: return 1.0, 0.0
        if u < 1.5: return 1 - ease((u - 0.85) / 0.65), -1.0
        return 0.0, 0.0
    def step(s, t, dt, k, live):
        w = s.w; b = w.ball
        if live and t >= s.next:
            sd = (-1 if b.x < (w.WL + w.WR) / 2 else 1) if s.rng.random() < 0.75 else s.rng.choice((-1, 1))
            s.wv.append(dict(t0=t, sd=sd, reach=s._reach(sd, b.x, 40 * (k - 1)), pk=s.rng.uniform(40, 80) * min(1.5, 0.8 + 0.3 * k)))
            s.ev(t, 'rumble', 0.8); s.ev(t + 0.2, 'sizzle')
            s.next = t + 1.35 / (k * s.D) + s.rng.uniform(0, 0.4)
        if not live and getattr(s, 'stop', None) is None:
            s.stop = t
            for q in s.wv: q['t0'] = min(q['t0'], t - 0.85) if t - q['t0'] < 1.5 else q['t0']   # everything drains now
        s.wv = [q for q in s.wv if t - q['t0'] < 1.5]; s.t = t
    def fronts(s, t):
        out = []
        for q in s.wv:
            p, d = s.prof(q, t)
            if p > 0.01:
                fx = (s.w.WL + q['reach'] * p) if q['sd'] < 0 else (s.w.WR - q['reach'] * p)
                out.append((q['sd'], fx, GROUND - q['pk'] * min(1, p * 1.6), q['reach'] / 0.5 * d, id(q)))
        return out
    def shapes(s):
        out = []
        for (sd, fx, top, v, i) in s.fronts(s.t):
            if sd < 0: out.append(('r', 0, top, fx, H, v, 0, f'lava{i}'))
            else: out.append(('r', fx, top, W, H, -v, 0, f'lava{i}'))
        return out
    def snap(s): return s.fronts(s.t)
    def draw_mid(s, c, sn, t, A):
        for (sd, fx, top, v, i) in sn:
            x0 = 0 if sd < 0 else fx; x1 = fx if sd < 0 else W
            c.move_to(x0, H)
            for x in np.linspace(x0, x1, 30): c.line_to(x, top + 8 * math.sin(x * 0.03 + t * 5))
            c.line_to(x1, H); c.close_path(); c.set_source_rgb(*rgb('#e2562a')); c.fill()
            c.set_source_rgb(*rgb('#ffb347')); c.set_line_width(7)
            for j, x in enumerate(np.linspace(x0, x1, 30)): (c.move_to if j == 0 else c.line_to)(x, top + 8 * math.sin(x * 0.03 + t * 5))
            c.stroke()
            c.set_source_rgb(*rgb('#e2562a')); c.arc(fx, top + 40, 40, 0, 2 * math.pi); c.fill()   # rounded rolling front
            c.set_source_rgb(*rgb('#ff8a3a'))
            for k in range(4):
                u = (t * 0.9 + k / 4) % 1; x = lerp(x0, x1, (k + 0.5) / 4); c.arc(x, top + 30 + 80 * (1 - u), 5 + 7 * u, 0, 2 * math.pi); c.fill()

class SpikeBalls(Hz):
    """Other bouncing balls (spiky, real Ball physics: gravity, floor/walls, elastic ball-ball collisions).
    More of them + bouncier over time."""
    RB = 38
    def __init__(s, w, rng, op):
        super().__init__(w, rng, op); s.bs = []; b = w.ball
        if op:
            sd = 1 if b.x < (w.WL + w.WR) / 2 else -1; x = clamp(b.x + sd * rng.uniform(260, 340), w.WL + 60, w.WR - 60)
            s.add(x, b.y - rng.uniform(200, 380), -sd * rng.uniform(260, 360))
        else: s.add(rng.uniform(w.WL + 80, w.WR - 80), HEAD + 120, rng.choice((-1, 1)) * rng.uniform(150, 300), far=True)
        s.more = [w.T_START + w.TL * 0.5]
    def add(s, x, y, vx, far=False):
        w = s.w
        if far:
            for _ in range(40):
                if abs(x - w.ball.x) > 380: break
                x = s.rng.uniform(w.WL + 80, w.WR - 80)
        q = Ball(x, w.TER, R=s.RB, seed=s.rng.randrange(10 ** 6), vx=vx, hop=s.rng.uniform(380, 620), xmin=w.WL + s.RB, xmax=w.WR - s.RB, dent=0)
        q.y = y; q.vy = 0.0; q.id = s.nid(); q.h0 = q.base_h; q.a = 1.0; s.bs.append(q)
    def step(s, t, dt, k, live):
        w = s.w
        if live and s.more and t >= s.more[0]: s.more.pop(0); s.add(s.rng.uniform(w.WL + 80, w.WR - 80), HEAD - 40, s.rng.choice((-1, 1)) * 250, far=True); s.ev(t, 'pop')
        if not live and getattr(s, 'stop', None) is None: s.stop = t
        for q in s.bs:
            q.vmin = math.sqrt(2 * Ball.G * q.h0 * min(1.6, 0.85 + 0.25 * k * s.D)); q.vxmax = 330 * min(1.6, k * s.D)
            nl = len(q.landings); q.step(t, dt=dt, sub=1)
            if len(q.landings) > nl and t < getattr(s, 'stop', 1e9): s.ev(t, 'thump', 0.35)
            if getattr(s, 'stop', None) is not None: q.a = max(0.0, 1 - (t - s.stop) / 0.5)
        for i in range(len(s.bs)):   # equal-mass elastic collisions between the spike balls
            for j in range(i + 1, len(s.bs)):
                a, b2 = s.bs[i], s.bs[j]; dx, dy = b2.x - a.x, b2.y - a.y; d = math.hypot(dx, dy)
                if 0 < d < 2 * s.RB:
                    nx, ny = dx / d, dy / d; rel = (a.vx - b2.vx) * nx + (a.vy - b2.vy) * ny
                    if rel > 0: a.vx -= rel * nx; a.vy -= rel * ny; b2.vx += rel * nx; b2.vy += rel * ny; a._pushed = b2._pushed = True
                    o = (2 * s.RB - d) / 2; a.x -= nx * o; a.y -= ny * o; b2.x += nx * o; b2.y += ny * o
        s.t = t
    def shapes(s): return [('c', q.x, q.y, s.RB + 8, q.vx, q.vy, q.id) for q in s.bs if q.a > 0.5]
    def recoil(s, _id, vx, vy):
        for q in s.bs:
            if q.id == _id: q.vx += vx; q.vy += vy; q._pushed = True
    def snap(s): return [(q.x, q.y, q.a) for q in s.bs]
    def draw_front(s, c, sn, t, A):
        for (x, y, a) in sn:
            if a <= 0.01: continue
            c.push_group(); c.save(); c.translate(x, y); c.rotate(x / s.RB)
            c.set_source_rgb(*rgb('#e8e0e4'))
            for i in range(12):
                b = i * math.pi / 6; c.move_to(math.cos(b - 0.2) * s.RB, math.sin(b - 0.2) * s.RB); c.line_to(math.cos(b) * (s.RB + 16), math.sin(b) * (s.RB + 16)); c.line_to(math.cos(b + 0.2) * s.RB, math.sin(b + 0.2) * s.RB); c.close_path(); c.fill()
            c.set_source_rgb(*rgb('#c8364a')); c.arc(0, 0, s.RB, 0, 2 * math.pi); c.fill()
            c.set_source_rgb(*rgb('#e05a6a')); c.arc(-12, -12, s.RB * 0.42, 0, 2 * math.pi); c.fill()
            c.restore(); c.pop_group_to_source(); c.paint_with_alpha(a)

class Cannons(Hz):
    """Wall cannons lob cannonballs at where Gloop is right now (gravity arc, he keeps moving). Faster fire."""
    G = 1000.0; RC = 32
    def __init__(s, w, rng, op):
        super().__init__(w, rng, op); s.pr = []; b = w.ball
        s.cn = [(w.WL - 4, rng.uniform(GROUND - 520, GROUND - 200), 1), (w.WR + 4, rng.uniform(GROUND - 520, GROUND - 200), -1)]
        if rng.random() < 0.5: s.cn.append((w.WL - 4, rng.uniform(HEAD + 200, GROUND - 600), 1))
        s.next = w.T_START - 0.2; s.i = 0
        if op:
            sd = 1 if b.x < (w.WL + w.WR) / 2 else -1; x0 = clamp(b.x + sd * rng.uniform(320, 420), w.WL + 40, w.WR - 40)
            s.fire(x0, clamp(b.y + rng.uniform(-40, 160), HEAD + 120, GROUND - 120), b.x + b.vx * 0.5 + ring(rng, R + 60, R + 160), b.y + 260, 800, -0.0)
    def fire(s, x, y, tx, ty, v, t):
        d = math.hypot(tx - x, ty - y) or 1; T = d / v
        s.pr.append(dict(x=x, y=y, vx=(tx - x) / T, vy=(ty - y) / T - 0.5 * s.G * T, id=s.nid(), a=1.0, t0=t))
    def aim(s, i):
        b = s.w.ball; x, y, sd = s.cn[i]; return math.atan2(b.y - y, (b.x - x))
    def step(s, t, dt, k, live):
        w = s.w; b = w.ball
        if live and t >= s.next:
            i = s.i % len(s.cn); s.i += 1; x, y, sd = s.cn[i]
            s.fire(x + sd * 60, y, b.x + b.vx * abs(b.x - x) / 800 + ring(s.rng, R + 36, R + 130), b.y + s.rng.uniform(-60, 60), 720 * min(1.6, 0.8 + 0.25 * k * s.D), t)
            s.ev(t, 'thump', 0.9); s.ev(t, 'whoosh'); s.next = t + 1.5 / (k * s.D) + s.rng.uniform(0, 0.4)
        if not live and getattr(s, 'stop', None) is None: s.stop = t
        keep = []
        for q in s.pr:
            q['vy'] += s.G * dt; q['x'] += q['vx'] * dt; q['y'] += q['vy'] * dt
            if getattr(s, 'stop', None) is not None: q['a'] = max(0.0, q['a'] - dt / 0.4)
            if q['x'] < w.WL - 60 or q['x'] > w.WR + 60 or q['y'] > w.TER.y(clamp(q['x'], 0, W)) - s.RC * 0.4 or q['a'] <= 0:
                if q['a'] > 0 and w.WL < q['x'] < w.WR: s.ev(t, 'thump', 0.5)
                continue
            keep.append(q)
        s.pr = keep; s.t = t
    def shapes(s): return [('c', q['x'], q['y'], s.RC, q['vx'], q['vy'], q['id']) for q in s.pr if q['a'] > 0.5]
    def snap(s): return ([(q['x'], q['y'], q['a']) for q in s.pr], [s.aim(i) for i in range(len(s.cn))])
    def draw_walls(s, c, sn, t, A):
        for (x, y, sd), ang in zip(s.cn, sn[1]):
            ang = clamp(ang, -1.2, 1.2) if sd > 0 else (ang if abs(ang) > 1.9 else math.copysign(1.95, ang))
            c.save(); c.translate(x, y); c.rotate(ang)
            c.set_source_rgb(*rgb('#2a2c34')); rrect(c, 0, -24, 92, 48, 14); c.fill(); c.rectangle(80, -28, 14, 56); c.fill()
            c.restore()
            c.set_source_rgb(*rgb('#3a3e48')); c.arc(x, y, 34, 0, 2 * math.pi); c.fill()
    def draw_front(s, c, sn, t, A):
        for (x, y, a) in sn[0]:
            c.set_source_rgba(*rgb('#4a4e5c'), a); c.arc(x, y, s.RC, 0, 2 * math.pi); c.fill()
            c.set_source_rgba(*rgb('#c8ced8'), a); c.set_line_width(4); c.arc(x, y, s.RC - 2, 0, 2 * math.pi); c.stroke()
            c.set_source_rgba(1, 1, 1, 0.45 * a); c.arc(x - 9, y - 9, 8, 0, 2 * math.pi); c.fill()

HZ_CLS = {'saws': Saws, 'lasers': Lasers, 'spikes': Spikes, 'crusher': Crusher, 'blocks': Blocks, 'lava': Lava, 'spikeballs': SpikeBalls, 'cannons': Cannons}

# ------------------------------------------------------------------------------------------------ ending
class LoopEnding(Ending):
    """Same claw (art, timing, sounds) as every Gloop video, but instead of flying off it carries Gloop back
    up to the exact spot where frame 0 drops him, and the video ends on the claw holding him there -> the
    0.4 s crossfade into frame 0 reads as the claw dropping him into the next run (seamless loop)."""
    def __init__(s, S, home):
        super().__init__(S); s.home = home; s.T_HOME = s.T_LIFT + 1.1
    def claw_pos(s, t):
        gx, gy = s.S.GRAB; ry = gy - 150
        if t < s.T_CLAW_IN: return None
        if t < s.T_GRAB:
            k = ease((t - s.T_CLAW_IN) / (s.T_GRAB - s.T_CLAW_IN)); return lerp(W + 250, gx, k), lerp(380, ry, k)
        if t < s.T_LIFT: return gx, ry
        hx, hy = s.home; k = ease((t - s.T_LIFT) / (s.T_HOME - s.T_LIFT))
        return lerp(gx, hx, k), lerp(ry, hy - 150, k) - 140 * math.sin(math.pi * k)

# ------------------------------------------------------------------------------------------------ world
class World:
    def __init__(s, cfg):
        s.cfg = cfg; seed = cfg['seed']; s.rng = rng = random.Random(seed * 9973 + 17)
        A = s.A = ARENAS[cfg['arena']]; s.WL, s.WR = A['WL'], A['WR']; s.D = cfg.get('D', 1.0)
        s.T_START = HOOK_T; s.TL = cfg['TL']; s.T_END = s.T_START + s.TL
        s.TER = Terrain(GROUND, seed=seed, bumps=0, amp=0, soft=True); s.TER.h = _prof(A['shape'], s.WL, s.WR)
        x0 = rng.uniform(s.WL + 170, s.WR - 170)
        s.ball = Ball(x0, s.TER, R=R, seed=seed, xmin=s.WL + R, xmax=s.WR - R, dent=0.0025, hop=rng.uniform(220, 290))
        if cfg['arena'] == 'ice_cave': s.ball.e_wall = 0.95
        s.ball.y = s.TER.y(x0) - R - rng.uniform(380, 520); s.ball.vy = 0.0
        s.home = (s.ball.x, s.ball.y)
        s.events = [[0.0, 'whoosh']]
        s.WGT = (1.0, 1.0) if len(cfg['hazards']) == 1 else (0.7, 0.5)   # two hazards share the difficulty budget
        s.hz = [HZ_CLS[h](s, random.Random(seed * 31 + i * 7 + 3), i == 0) for i, h in enumerate(cfg['hazards'])]

    def gap(s, sh, bx, by):
        k = sh[0]
        if k == 'c':
            _, x, y, r, vx, vy, _id = sh; d = math.hypot(bx - x, by - y)
            return d - r - R, ((bx - x) / (d or 1), (by - y) / (d or 1)), (vx, vy), _id
        if k == 'r':
            _, x0, y0, x1, y1, vx, vy, _id = sh; g, n = _rect_gap(bx, by, x0, y0, x1, y1); return g, n, (vx, vy), _id
        if k == 's':
            _, x1, y1, x2, y2, hw, vx, vy, _id = sh; g, n = _seg_gap(bx, by, x1, y1, x2, y2, hw); return g, n, (vx, vy), _id
        if k == 'L':
            _, L, vL, _id = sh; return L - (by + R), (0.0, -1.0), (0.0, min(0.0, vL)), _id

    def simulate(s):
        b = s.ball; T_FAIL = None; S_ = {}; NEARS = []; pre_contact = False; fail_by = None
        hp = HEARTS; HITS = []; last_hit = -9.0; s.HP = []
        N0 = int((s.T_END + 7.0) * FPS); h = 1 / (FPS * SUB)
        s.GX, s.GY, s.MG, s.SN, s.TS, s.KK = [], [], [], [], [], []
        hook_min = 1e9; gap0 = None
        for f in range(N0):
            for sub in range(SUB):
                t = f / FPS + sub * h
                live = T_FAIL is None and t < s.T_END
                prog = clamp((t - s.T_START) / s.TL, 0, 1); k = 1 + RAMP * prog
                for z in s.hz: z.step(t, h, k, live)
                b.step(t, dt=h, sub=1)
                if T_FAIL is not None: b.vx *= 0.995
                if not live: continue
                for z in s.hz:
                    for sh in z.shapes():
                        g, n, hv, _id = s.gap(sh, b.x, b.y)
                        if t < 1.0: hook_min = min(hook_min, g)
                        st = S_.setdefault(_id, {'in': False, 'min': 1e9, 't': 0, 'hit': False})
                        if g < NEAR:
                            st['in'] = True
                            if g < st['min']: st['min'] = g; st['t'] = t
                        elif st['in'] and g > NEAR * 2:
                            if not st['hit'] and s.T_START <= st['t'] < s.T_END: NEARS.append((st['t'], st['min'], _id))
                            S_[_id] = {'in': False, 'min': 1e9, 't': 0, 'hit': False}
                        if g > NEAR: st['lock'] = False
                        if g < 0:
                            st['hit'] = True
                            if t < s.T_START: pre_contact = True; continue
                            if st.get('lock'): continue
                            st['lock'] = True
                            nx, ny = n; rel = (hv[0] - b.vx) * nx + (hv[1] - b.vy) * ny   # real knock along the contact normal
                            j = clamp(max(rel, 0) + 380, 380, 1000); b.vx += j * nx; b.vy += j * ny; b._pushed = True
                            if hasattr(z, 'recoil'): z.recoil(_id, -nx * j, -ny * j)
                            if t - last_hit < GRACE: continue
                            last_hit = t; hp -= 1; HITS.append((t, b.x, b.y)); s.events += [[t, 'heart'], [t, 'thump', 1.0]]
                            if hp == 0:
                                T_FAIL = t; fail_by = _id; b.vmin = 0.0; b.e = 0.45; s.events += [[t, 'crash']]
                                break
                    if T_FAIL is not None: break
            if f == 0:   # how close the visible danger is on frame 1 (armed warnings count: they are on screen)
                gs = [s.gap(sh, b.x, b.y)[0] for z in s.hz for sh in (z.threats() if hasattr(z, 'threats') else z.shapes())]
                gap0 = min(gs) if gs else 1e9
            s.GX.append(b.x); s.GY.append(b.y); s.TS.append(s.TER.snapshot())
            s.KK.append(clamp((f / FPS - s.T_START) / s.TL, 0, 1))
            mg = 1e9
            for z in s.hz:
                for sh in z.shapes(): mg = min(mg, s.gap(sh, b.x, b.y)[0])
            s.MG.append(mg); s.SN.append([z.snap() for z in s.hz]); s.HP.append(hp)
        for _id, st in S_.items():
            if st['in'] and not st['hit'] and s.T_START <= st['t'] < (T_FAIL or s.T_END): NEARS.append((st['t'], st['min'], _id))
        NEARS.sort()
        if T_FAIL is not None: NEARS = [n for n in NEARS if n[0] < T_FAIL - 0.05]
        NEARS = [n for n in NEARS if all(abs(n[0] - hh[0]) > 0.6 for hh in HITS)]   # a miss right next to a hit doesn't read as a close call
        s.T_FAIL, s.NEARS, s.pre_contact, s.hook_min, s.gap0, s.fail_by = T_FAIL, NEARS, pre_contact, hook_min, gap0, fail_by
        s.HITS = HITS
        for (tl, xl, imp) in b.landings:
            s.events.append([tl, 'hop'])
        for tw in b.walls: s.events.append([tw, 'thump', 0.35])
        for (tn, g, _id) in NEARS: s.events.append([tn, 'whoosh'])
        return s

    def stats(s):
        return dict(outcome='fail' if s.T_FAIL else 'win', t_fail=None if s.T_FAIL is None else round(s.T_FAIL - s.T_START, 2),
                    left=None if s.T_FAIL is None else round(s.T_END - s.T_FAIL, 2), nears=len(s.NEARS),
                    near_t=[round(n[0] - s.T_START, 2) for n in s.NEARS], near_px=[round(n[1]) for n in s.NEARS],
                    pre_contact=s.pre_contact, hook_min=round(s.hook_min), gap0=round(s.gap0), seed=s.cfg['seed'], D=s.D,
                    hits=[round(h[0] - s.T_START, 2) for h in s.HITS], hearts=HEARTS - len(s.HITS))

def score(st, want, TL):
    """None = reject. Higher = better. Hook in frame 1, 3-4 near-misses spread out, outcome open until the
    last ~3 s: fails lose the last heart in the last 3 s of the timer; wins are down to their last heart or
    have a near-miss / hit in the last 3 s."""
    if st['pre_contact'] or st['outcome'] != want: return None
    if st['gap0'] > 300 or st['hook_min'] > 160: return None
    n = st['nears']; nt = st['near_t']
    if n < 3: return None
    if want == 'fail':
        if not (0.5 <= st['left'] <= 3.0): return None
    else:
        late = [x for x in nt + st['hits'] if x >= TL - 3.0]
        if not late: return None
    if nt[0] > TL * 0.5: return None
    sc = 10 - 3 * abs(n - 3.5) + (2 if want == 'win' or st['left'] >= 0.8 else 0) - 0.02 * st['hook_min'] - 0.006 * st['gap0']
    gaps = [b - a for a, b in zip(nt, nt[1:])]
    if gaps and min(gaps) < 0.5: sc -= 2
    return sc

# ------------------------------------------------------------------------------------------------ scene
def build(cfg):
    w = World(cfg).simulate()
    class S: pass
    S.T_START, S.TL, S.T_END = w.T_START, w.TL, w.T_END
    S.OUTCOME = 'fail' if w.T_FAIL else 'win'; S.T_RES = w.T_FAIL or w.T_END
    words = ' AND '.join(HAZ[h][1].upper() for h in cfg['hazards'])
    S.HOOK1 = 'WILL GLOOP SURVIVE'; S.HOOK2 = f'THE {words}?'
    S.HOOK2_SIZE = 92 if len(S.HOOK2) <= 14 else (78 if len(S.HOOK2) <= 20 else (62 if len(S.HOOK2) <= 27 else 50))
    fb = w.fail_by or ''
    fw = next((HAZ[h][2] for h, z in zip(cfg['hazards'], w.hz) if fb.startswith(z.__class__.__name__) or (fb.startswith('lava') and h == 'lava')), 'OUCH!')
    S.FAIL_WORD = fw; S.FAIL_SIZE = 140
    S.GRAB = (540, GROUND - R)
    END = S.END = LoopEnding(S, w.home)
    gi = min(int(END.T_GRAB * FPS), len(w.GX) - 1); S.GRAB = (w.GX[gi], w.GY[gi])
    S.events = [e for e in w.events if e[0] < S.DUR]
    if w.T_FAIL is None: S.events = [e for e in S.events if not (e[1] in ('crash',) and e[0] > S.T_RES)]
    S.AMB = {'drone': 50, 'rumble': 0.03 if 'lava' in cfg['hazards'] else 0.0}
    A = w.A
    HT = [h[0] for h in w.HITS]
    def draw_bar(c, t, f):   # same 3-heart row as the DODGE videos
        hp = w.HP[min(f, len(w.HP) - 1)]; lost = [h for h in HT if h <= t]
        pop = max(0, 1 - (t - lost[-1]) / 0.35) if lost else 0
        for i in range(HEARTS):
            x = W / 2 - 150 + i * 150; y = 235; full = i < hp
            sc = 1.0 + (0.35 * pop if i == hp and pop > 0 else 0)
            c.save(); c.translate(x, y); c.scale(sc, sc); heart_path(c, 0, 0, 40)
            c.set_source_rgb(0, 0, 0); c.set_line_width(10); c.stroke_preserve()
            c.set_source_rgb(*(rgb('#ff3b5c') if full else rgb('#3a3446'))); c.fill()
            if full: c.set_source_rgba(1, 1, 1, 0.5); c.arc(-14, -10, 8, 0, 2 * math.pi); c.fill()
            c.restore()
    S.draw_bar = draw_bar
    PS = Particles(cfg['seed'] % 97 + 3)
    hits = [e[0] for e in w.events if e[1] == 'crash' and abs(e[0] - S.T_RES) < 0.01 and w.T_FAIL]

    def backdrop(c, t):
        c.set_source_rgb(*rgb(A['bg'])); c.rectangle(0, HEAD, W, H - HEAD); c.fill()
        m = cfg['arena']; acc = rgb(A['acc'])
        if m == 'neon_lab':
            c.set_source_rgba(*acc, 0.08); c.set_line_width(2)
            for x in range(A['WL'], A['WR'], 90): c.move_to(x, HEAD); c.line_to(x, GROUND); c.stroke()
            for y in range(HEAD + 60, GROUND, 90): c.move_to(A['WL'], y); c.line_to(A['WR'], y); c.stroke()
        elif m == 'lava_forge':
            c.set_source_rgb(*rgb(A['bg2']))
            for i, x in enumerate(range(A['WL'], A['WR'], 110)): c.move_to(x, HEAD); c.line_to(x + 55, HEAD + 90 + 60 * (i % 3)); c.line_to(x + 110, HEAD); c.close_path(); c.fill()
            c.set_source_rgba(1, 0.55, 0.2, 0.25); c.set_line_width(4)
            for (x, y) in ((250, 900), (700, 1100), (520, 760)): c.move_to(x, y); c.line_to(x + 40, y + 60); c.line_to(x + 10, y + 120); c.stroke()
        elif m == 'ice_cave':
            c.set_source_rgb(*rgb(A['bg2']))
            for i, x in enumerate(range(A['WL'], A['WR'], 80)): c.move_to(x, HEAD); c.line_to(x + 40, HEAD + 70 + 50 * ((i * 7) % 3)); c.line_to(x + 80, HEAD); c.close_path(); c.fill()
            c.set_source_rgba(*acc, 0.18)
            for (x, y, r) in ((300, 1000, 50), (780, 860, 40), (520, 1200, 30)): c.move_to(x, y - r * 2); c.line_to(x + r * 0.6, y); c.line_to(x, y + r); c.line_to(x - r * 0.6, y); c.close_path(); c.fill()
        elif m == 'jungle_temple':
            c.set_source_rgb(*rgb(A['bg2']))
            for j, y in enumerate(range(HEAD + 100, GROUND, 120)):
                for x in range(A['WL'] + (60 if j % 2 else 0), A['WR'], 180): rrect(c, x + 6, y + 6, 168, 108, 8); c.fill()
            c.set_source_rgb(*rgb('#2e5a32')); c.set_line_width(7)
            for vx in (260, 610, 880): c.move_to(vx, HEAD); c.curve_to(vx + 20 * math.sin(t), HEAD + 200, vx - 20, HEAD + 320, vx + 10 * math.sin(t * 1.3), HEAD + 430); c.stroke()
        elif m == 'space_dock':
            rr = random.Random(4)
            for _ in range(60): c.set_source_rgba(1, 1, 1, rr.uniform(0.2, 0.7)); c.arc(rr.uniform(0, W), rr.uniform(HEAD, GROUND - 100), rr.uniform(1, 2.5), 0, 2 * math.pi); c.fill()
            c.set_source_rgb(*rgb('#3a2e5e')); c.arc(780, 700, 120, 0, 2 * math.pi); c.fill()
            c.set_source_rgb(*rgb('#4a3c76')); c.arc(740, 670, 46, 0, 2 * math.pi); c.fill()
        elif m == 'factory':
            c.set_source_rgb(*rgb(A['bg2'])); c.rectangle(A['WL'], HEAD + 150, A['WR'] - A['WL'], 50); c.fill(); c.rectangle(300, HEAD + 150, 44, 900); c.fill(); c.rectangle(760, HEAD + 200, 36, 700); c.fill()
            c.set_source_rgba(*acc, 0.12)
            for x in range(A['WL'], A['WR'], 60): c.move_to(x, GROUND - 30); c.line_to(x + 30, GROUND - 30); c.line_to(x + 60, GROUND - 60); c.line_to(x + 30, GROUND - 60); c.close_path(); c.fill()
        elif m == 'candy_box':
            c.set_source_rgb(*rgb(A['bg2']))
            for x in range(-H, W, 140): c.move_to(x, HEAD); c.line_to(x + 70, HEAD); c.line_to(x + 70 + (GROUND - HEAD), GROUND); c.line_to(x + (GROUND - HEAD), GROUND); c.close_path(); c.fill()
            for (x, y, col) in ((260, 1000, '#7ae0c0'), (820, 900, '#ffd36b')):
                c.set_source_rgb(*rgb('#d8c8d0')); c.rectangle(x - 5, y, 10, 300); c.fill(); c.set_source_rgba(*rgb(col), 0.6); c.arc(x, y, 50, 0, 2 * math.pi); c.fill()
        elif m == 'desert_ruins':
            c.set_source_rgb(*rgb('#e6dfc4')); c.arc(800, 560, 50, 0, 2 * math.pi); c.fill()
            c.set_source_rgb(*rgb(A['bg2'])); c.move_to(150, 1300); c.line_to(400, 950); c.line_to(650, 1300); c.close_path(); c.fill()
            c.move_to(560, 1300); c.line_to(760, 1020); c.line_to(960, 1300); c.close_path(); c.fill()
    def walls(c):
        for (x0, x1) in ((0, A['WL']), (A['WR'], W)):
            c.set_source_rgb(*rgb(A['wall'])); c.rectangle(x0, HEAD, x1 - x0, H - HEAD); c.fill()
            c.set_source_rgb(*rgb(A['wall2'])); c.rectangle(x1 - 10 if x0 == 0 else x0, HEAD, 10, H - HEAD); c.fill()
            c.set_source_rgba(0, 0, 0, 0.18)
            for y in range(HEAD + 80, H, 160): c.rectangle(x0, y, x1 - x0, 6); c.fill()

    def render(f, c):
        t = f / FPS; fi = min(f, len(w.GX) - 1); sn = w.SN[fi]
        shake = (0, 0)
        if any(th <= t < th + 0.2 for th in HT): shake = (random.uniform(-6, 6), random.uniform(-6, 6))
        c.save(); c.translate(*shake)
        backdrop(c, t)
        for z, s_ in zip(w.hz, sn):
            if hasattr(z, 'draw_back'): z.draw_back(c, s_, t, 1)
        w.TER.fill(c, w.TS[fi], A['top'], A['deep'], A['rim'])
        for z, s_ in zip(w.hz, sn):
            if hasattr(z, 'draw_mid'): z.draw_mid(c, s_, t, 1)
        walls(c)
        for z, s_ in zip(w.hz, sn):
            if hasattr(z, 'draw_walls'): z.draw_walls(c, s_, t, 1)
        failed = w.T_FAIL is not None and t >= w.T_FAIL
        if END.carried(t) or t >= END.T_GRAB: gx, gy = (END.carry_xy(t) if END.carried(t) else S.GRAB)
        else:
            gx, gy = w.GX[fi], w.GY[fi]
            hh = max(0, w.TER.y(gx) - R - gy); kk = 1 / (1 + hh / 220)
            c.set_source_rgba(0, 0, 0, 0.25 * kk); c.save(); c.translate(gx, w.TER.y(gx) + 3); c.scale(R * (0.5 + 0.4 * kk), 9); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
        mood = 'happy' if (t >= S.T_END and S.OUTCOME == 'win') else ('scared' if failed or w.MG[fi] < 170 or t < S.T_START else 'worried')
        draw_blob(c, t, gx, gy, mood, 0, R=R, dizzy=failed and t > w.T_FAIL + 0.35)
        for z, s_ in zip(w.hz, sn):
            if hasattr(z, 'draw_front'): z.draw_front(c, s_, t, 1)
        shown = -9.0
        for (tn, g, _id) in w.NEARS:   # small 'CLOSE!' tag at each real near-miss (one at a time)
            if tn - shown < 0.75: continue
            shown = tn
            if tn <= t < tn + 0.7:
                k = (t - tn) / 0.7; text_at(c, 'CLOSE!', clamp(w.GX[int(tn * FPS)], 200, 880), w.GY[int(tn * FPS)] - R - 70 - 60 * k, 50, rgb('#ffd36b'), 1.0, lw=8)
        for (th, hx, hy) in w.HITS:
            if abs(t - th) < 0.5 / FPS: PS.spawn(hx, hy, 14, (1.0, 0.85, 0.5), 420, 0.45, grav=900, r=7)
        PS.draw(c)
        END.draw_claw(c, t)
        c.restore()
        END.header(c, t, fi)
    return S, render, w

def main(cfg):
    S, render, w = build(cfg)
    if sys.argv[1] == 'sim':
        st = w.stats(); st['dur'] = S.DUR; print(json.dumps(st)); sys.exit()
    run(S, render)
