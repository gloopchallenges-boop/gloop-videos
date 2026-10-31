"""Gloop Halloween engine (2026-10-31). One themed scene engine, configured per video.
cfg keys: seed, threat (pumpkin|cauldron|hands|ghost|bats|spider), support (rope|web|branch|broom|bubble),
bg (pumpkin_patch|witch_hut|graveyard|haunted_house|crypt|swamp), skin (pumpkin|witch|ghost|vampire|mummy|cat),
time (timer seconds), fail (bool), fail_left (seconds left on timer when the support breaks), hook (2nd hook line).
Usage: python3 scenario.py out.mp4 events.json [stills t1,t2,...]
"""
import cairo, math, random, subprocess, sys, json
from types import SimpleNamespace

W, H, FPS = 1080, 1920, 30
HEAD = 330
G = 1730            # ground line
S = SimpleNamespace()


def ease(x): x = max(0, min(1, x)); return x * x * (3 - 2 * x)
def lerp(a, b, k): return a + (b - a) * k
def hexc(h, a=1):
    h = h.lstrip('#'); return (int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255, a)
def rgb(h): return hexc(h)[:3]

def rrect(c, x, y, w, h, r):
    c.new_sub_path()
    c.arc(x + w - r, y + r, r, -math.pi / 2, 0); c.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    c.arc(x + r, y + h - r, r, math.pi / 2, math.pi); c.arc(x + r, y + r, r, math.pi, 1.5 * math.pi)
    c.close_path()

def star_path(c, x, y, r):
    for i in range(10):
        a = -math.pi / 2 + i * math.pi / 5; rr = r if i % 2 == 0 else r * 0.45
        (c.move_to if i == 0 else c.line_to)(x + math.cos(a) * rr, y + math.sin(a) * rr)
    c.close_path()

SUPPORT_LABEL = {'rope': 'ROPE', 'web': 'WEB', 'branch': 'BRANCH', 'broom': 'BROOM', 'bubble': 'BUBBLE'}
BREAK_WORD = {'rope': 'SNAP!', 'web': 'SNAP!', 'branch': 'CRACK!', 'broom': 'SNAP!', 'bubble': 'POP!'}
BASE = {'rope': (540, 960), 'web': (540, 900), 'branch': (630, 955), 'broom': (580, 930), 'bubble': (540, 940)}
ACTION = {'rope': 'hop', 'web': 'wiggle', 'branch': 'hop', 'broom': 'wiggle', 'bubble': 'hop'}
HOPR = {'rope': (70, 170), 'branch': (120, 230), 'bubble': (35, 70)}


# ======================================================================= timeline
def setup(cfg):
    S.cfg = cfg; S.rng = random.Random(cfg.get('seed', 1)); rng = S.rng
    S.threat, S.support, S.skin, S.bg = cfg['threat'], cfg['support'], cfg['skin'], cfg['bg']
    S.T_START = 2.6; S.TL = cfg['time']; S.T_END = S.T_START + S.TL
    S.fail = cfg.get('fail', False)
    if S.fail:
        S.T_FAIL = S.T_END - cfg.get('fail_left', 2.3); stop = S.T_FAIL
    else:
        S.T_FAIL = None; stop = S.T_END - 0.75
    acts = []; t = 3.1; iv = 1.1
    while t < stop - 0.35:
        acts.append(t); t += iv; iv = max(0.55, iv * 0.93)
    if S.fail: acts.append(S.T_FAIL)
    S.acts = acts
    if ACTION[S.support] == 'hop':
        lo, hi = HOPR[S.support]; S.HOP = [rng.uniform(lo, hi) for _ in acts]
        wts = [h * rng.uniform(0.8, 1.2) for h in S.HOP]
    else:
        S.HOP = [0] * len(acts); wts = [rng.uniform(0.7, 1.3) for _ in acts]
    total = 100.0 if S.fail else rng.uniform(93, 96)
    dm = [w * total / sum(wts) for w in wts]
    S.pcts = []; acc = 100.0
    for d in dm:
        acc -= d; S.pcts.append(max(0, round(acc)))
    if S.fail: S.pcts[-1] = 0
    else: S.pcts = [max(3, p) for p in S.pcts]
    S.DMG_SHOW = [max(1, round(d)) for d in dm]
    fr = [0.40, 0.63, 0.85]
    if S.fail:
        S.attacks = [S.T_START + S.TL * f for f in fr if S.T_START + S.TL * f < S.T_FAIL - 0.7]
        S.T_BREAK = S.T_FAIL
        S.T_CATCH = S.T_FAIL + 0.5
        S.attacks.append(S.T_CATCH)
        if S.threat in ('pumpkin', 'cauldron'):
            S.T_SPIT = S.T_CATCH + 0.75; S.T_REST = S.T_SPIT + 0.55
        elif S.threat == 'spider':
            S.T_SPIT = None; S.T_REST = S.T_CATCH + 0.6
        else:
            S.T_SPIT = None; S.T_REST = S.T_CATCH
        S.T_CLAW_IN = S.T_REST + 0.1
        S.T_GRAB = S.T_REST + 1.1
        S.T_DART = S.T_GRAB - 0.3
        S.T_LIFT = S.T_GRAB + 0.25
        S.T_GONE = S.T_LIFT + 1.9
        S.T_RES = S.T_FAIL + 0.6       # result header
        S.T_OUTRO = S.T_GRAB + 1.5
        S.T_RECEDE = S.T_GRAB + 0.3 if S.threat == 'spider' else S.T_REST + 0.6
    else:
        S.attacks = [S.T_START + S.TL * f for f in fr] + [S.T_END + 0.45]
        S.T_CLAW_IN = S.T_END - 1.4; S.T_DART = S.T_END - 0.15; S.T_GRAB = S.T_END
        S.T_BREAK = S.T_END + 0.15; S.T_LIFT = S.T_END + 0.35; S.T_GONE = S.T_END + 2.2
        S.T_RES = S.T_END + 0.7; S.T_OUTRO = S.T_END + 2.0; S.T_RECEDE = S.T_END + 1.2
    S.DUR = S.T_OUTRO + 2.7
    S.N = int(S.DUR * FPS)
    S.particles = []
    S.web_order = list(range(8)); rng.shuffle(S.web_order)
    S.stars = [(rng.uniform(0, W), rng.uniform(HEAD, 1200), rng.uniform(1, 3), rng.uniform(0, 6)) for _ in range(70)]
    S.bats = [(rng.uniform(0, 6.28), rng.uniform(0.6, 1.4), rng.uniform(-1, 1), rng.uniform(-90, 90), rng.uniform(0.7, 1.2)) for _ in range(16)]
    S.fog = [(rng.uniform(0, W), rng.uniform(G - 120, G + 60), rng.uniform(120, 260), rng.uniform(0.2, 0.6)) for _ in range(9)]
    S.fireflies = [(rng.uniform(0, W), rng.uniform(900, 1650), rng.uniform(0, 6)) for _ in range(18)]
    if not S.fail: S.GP = pre_pos(S.T_GRAB)
    elif S.threat == 'spider': S.GP = threat_center(S.T_GRAB)
    else: S.GP = rest_pos()


def pct_at(t):
    if t >= S.T_BREAK: return 0
    v = 100
    for st, sp in zip(S.acts, S.pcts):
        if t >= st: v = v + (sp - v) * min(1, (t - st) / 0.15)
    return v

def timer_at(t):
    if S.fail: t = min(t, S.T_FAIL)
    return max(0.0, S.TL - max(0, t - S.T_START))

def last_hit(t):
    ls = None
    for st in S.acts + [S.T_BREAK]:
        if t >= st: ls = st
    return ls

def rise(t):
    full = S.T_START + S.TL * 0.36
    if t < 3.2: r = 0.0
    elif t < 6.0: r = 0.25 * ease((t - 3.2) / 2.8)
    elif t < full: r = 0.25 + 0.75 * ease((t - 6.0) / max(0.5, full - 6.0))
    else: r = 1.0
    if t > S.T_RECEDE: r *= 1 - 0.85 * ease((t - S.T_RECEDE) / 1.5)
    return r

def lunge(t, extra=0.0):
    v = 0.0
    for a in S.attacks:
        a = a + extra
        if a - 0.6 <= t < a: v = max(v, ease((t - (a - 0.6)) / 0.6))
        elif a <= t < a + 0.12: v = max(v, 1.0)
        elif a + 0.12 <= t < a + 0.62: v = max(v, 1 - ease((t - a - 0.12) / 0.5))
    if S.fail and S.threat == 'spider' and t >= S.T_CATCH: v = max(v, 1 - ease((t - S.T_CATCH - 0.12) / 0.5))
    return v

def attack_idx(t):
    best = 0
    for i, a in enumerate(S.attacks):
        if t >= a - 0.7: best = i
    return best


# ======================================================================= motion
def anchor(t):
    """support anchor position (where the blob rests without action offset)"""
    bx, by = BASE[S.support]
    if S.support == 'rope': bx += 30 * math.sin(t * 1.7)
    elif S.support == 'broom': bx += 18 * math.sin(t * 1.1); by += 26 * math.sin(t * 2.2)
    elif S.support == 'bubble': bx += 16 * math.sin(t * 1.1); by += 20 * math.sin(t * 1.8)
    return bx, by

def action_off(t):
    dx = dy = 0.0
    B = [1.7] + S.acts; HOP = [0] + S.HOP
    if ACTION[S.support] == 'hop':
        for j in range(len(B)):
            if B[j] <= t and (j == len(B) - 1 or t < B[j + 1]):
                if j < len(B) - 1:
                    k = (t - B[j]) / (B[j + 1] - B[j]); dy = -HOP[j + 1] * 4 * k * (1 - k)
                if j > 0:
                    d = t - B[j]; dy += HOP[j] * 0.25 * math.exp(-d * 9) * math.sin(d * 28)
    else:
        for a in S.acts:
            if t >= a:
                d = t - a; dx += 42 * math.sin(d * 26) * math.exp(-d * 5)
    return dx, dy

def squash_at(t):
    ls = None
    for a in S.acts:
        if t >= a: ls = a
    if ls is None: return 0.03 * math.sin(t * 6)
    d = t - ls
    return 0.03 * math.sin(t * 6) + 0.16 * math.exp(-d * 10) * math.cos(d * 30)

def pre_pos(t):
    ax, ay = anchor(t); dx, dy = action_off(t)
    return ax + dx, ay + dy

def threat_center(t):
    """the point a gulping/catching threat holds Gloop at"""
    if S.threat == 'pumpkin':
        cx, cy = pumpkin_geom(t); return cx, cy + 50
    if S.threat == 'cauldron': return 540, 1450
    if S.threat == 'spider':
        cx, cy = spider_geom(t); return cx, cy - 245
    return pre_pos(S.T_FAIL)[0], G - 80

def rest_pos():
    if S.threat == 'pumpkin': return 190, G - 80
    if S.threat == 'cauldron': return 935, G - 80
    if S.threat == 'spider': return threat_center(S.T_REST)
    return pre_pos(S.T_FAIL)[0], G - 80

def blob_pos(t):
    """returns x, y, hidden"""
    if not S.fail:
        if t < S.T_GRAB: x, y = pre_pos(t); return x, y, False
        cx, cy = claw_pos(t); sw = 0
        if t > S.T_LIFT: sw = 18 * math.sin((t - S.T_LIFT) * 7) * math.exp(-(t - S.T_LIFT) * 1.2)
        return cx + sw, cy + 125, False
    if t < S.T_FAIL: x, y = pre_pos(t); return x, y, False
    if S.GP is not None and t >= S.T_GRAB:
        cx, cy = claw_pos(t); sw = 0
        if t > S.T_LIFT: sw = 18 * math.sin((t - S.T_LIFT) * 7) * math.exp(-(t - S.T_LIFT) * 1.2)
        return cx + sw, cy + 125, False
    p0 = pre_pos(S.T_FAIL)
    if t < S.T_CATCH:
        k = (t - S.T_FAIL) / (S.T_CATCH - S.T_FAIL); p1 = threat_center(S.T_CATCH)
        return lerp(p0[0], p1[0], k), p0[1] + (p1[1] - p0[1]) * k * k, False
    if S.threat == 'spider':
        x, y = threat_center(t); return x, y, False
    if S.T_SPIT is not None:
        p1 = threat_center(S.T_CATCH); rp = rest_pos()
        if t < S.T_SPIT: return p1[0], p1[1], True
        if t < S.T_REST:
            k = (t - S.T_SPIT) / (S.T_REST - S.T_SPIT)
            return lerp(p1[0], rp[0], k), lerp(p1[1], rp[1], k) - 330 * 4 * k * (1 - k), False
        return rp[0], rp[1], False
    rp = rest_pos(); return rp[0], rp[1], False


# ======================================================================= claw
def claw_pos(t):
    if t < S.T_CLAW_IN: return None
    gp = S.GP
    if S.fail:
        hov = lambda tt: (gp[0] + 40, gp[1] - 360 + 12 * math.sin(tt * 5))
    else:
        hov = lambda tt: (pre_pos(tt)[0] + 190, pre_pos(tt)[1] - 300 + 10 * math.sin(tt * 5))
    if t < S.T_DART:
        hx, hy = hov(t); k = ease((t - S.T_CLAW_IN) / 0.7)
        return 1250 + (hx - 1250) * k, 380 + (hy - 380) * k
    if t < S.T_GRAB:
        sx, sy = hov(S.T_DART); k = ease((t - S.T_DART) / (S.T_GRAB - S.T_DART))
        return sx + (gp[0] - sx) * k, sy + (gp[1] - 125 - sy) * k
    if t < S.T_LIFT: return gp[0], gp[1] - 125
    k = ease((t - S.T_LIFT) / (S.T_GONE - S.T_LIFT))
    sx, sy = gp[0], gp[1] - 125
    return sx + (1250 - sx) * k, sy + (150 - sy) * k

def claw_close(t): return 0.0 if t < S.T_GRAB else ease((t - S.T_GRAB) / 0.12)

def draw_claw(c, t):
    p = claw_pos(t)
    if p is None: return
    x, y = p
    c.set_source_rgb(*rgb('#9aa3b5')); c.set_line_width(8)
    c.move_to(x + 520, HEAD - 20); c.line_to(x, y - 30); c.stroke()
    cl = claw_close(t)
    for side in (-1, 1):
        c.save(); c.translate(x + side * 40, y + 30); c.rotate(side * (-0.55 + 0.55 * cl))
        c.set_source_rgb(*rgb('#6f7891')); c.set_line_width(16); c.set_line_cap(cairo.LINE_CAP_ROUND)
        c.move_to(0, 0); c.line_to(side * 55, 80); c.line_to(side * 20, 150); c.stroke()
        c.restore()
    c.set_source_rgb(*rgb('#c9d0de')); rrect(c, x - 70, y - 40, 140, 80, 22); c.fill()
    c.set_source_rgb(*rgb('#7b4bb7')); rrect(c, x - 70, y + 10, 140, 30, 12); c.fill()
    on = (t * 6) % 1 < 0.5
    c.set_source_rgb(*(rgb('#ff9a2e') if on else rgb('#7a3d10'))); c.arc(x - 25, y - 10, 13, 0, 2 * math.pi); c.fill()
    # tiny pumpkin sticker
    c.set_source_rgb(*rgb('#ff8c1a')); c.save(); c.translate(x + 30, y - 8); c.scale(1.25, 1); c.arc(0, 0, 13, 0, 2 * math.pi); c.restore(); c.fill()
    c.set_source_rgb(*rgb('#2f6b3a')); c.rectangle(x + 27, y - 26, 6, 8); c.fill()


# ======================================================================= text / header
def text_center(c, s, y, size, col, scale=1.0, maxw=1000, x=W / 2):
    c.select_font_face('Poppins', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    c.set_font_size(size); ext = c.text_extents(s)
    if ext.width > maxw: scale *= maxw / ext.width
    c.save(); c.translate(x, y); c.scale(scale, scale)
    c.move_to(-ext.width / 2 - ext.x_bearing, ext.height / 2)
    c.text_path(s); c.set_line_join(cairo.LINE_JOIN_ROUND)
    c.set_source_rgb(0, 0, 0); c.set_line_width(10); c.stroke_preserve()
    c.set_source_rgba(*col) if len(col) == 4 else c.set_source_rgb(*col); c.fill()
    c.restore()

def bat_shape(c, x, y, s, flap, col):
    c.save(); c.translate(x, y); c.scale(s, s)
    c.set_source_rgb(*col)
    wy = -18 * flap
    c.move_to(0, -6)
    c.curve_to(-20, -20 + wy, -45, -18 + wy, -60, -8 + wy); c.curve_to(-50, -4 + wy * 0.5, -45, 4, -36, 2)
    c.curve_to(-30, 8, -20, 2, -14, 8); c.curve_to(-8, 4, -4, 8, 0, 10)
    c.curve_to(4, 8, 8, 4, 14, 8); c.curve_to(20, 2, 30, 8, 36, 2)
    c.curve_to(45, 4, 50, -4 + wy * 0.5, 60, -8 + wy); c.curve_to(45, -18 + wy, 20, -20 + wy, 0, -6)
    c.close_path(); c.fill()
    c.arc(0, -2, 10, 0, 2 * math.pi); c.fill()
    c.move_to(-8, -8); c.line_to(-6, -20); c.line_to(-1, -10); c.fill()
    c.move_to(8, -8); c.line_to(6, -20); c.line_to(1, -10); c.fill()
    c.restore()

def draw_header(c, t):
    c.set_source_rgb(*rgb('#0d0b14')); c.rectangle(0, 0, W, HEAD); c.fill()
    c.set_source_rgb(*rgb('#6a2fa0')); c.rectangle(0, HEAD - 14, W, 6); c.fill()
    c.set_source_rgb(*rgb('#ff8c1a')); c.rectangle(0, HEAD - 8, W, 8); c.fill()
    for (bx, by, s) in ((70, 60, 0.7), (1010, 70, 0.6), (130, 285, 0.45), (950, 280, 0.5)):
        bat_shape(c, bx, by + 4 * math.sin(t * 3 + bx), s, math.sin(t * 9 + bx), rgb('#3b1d5a'))
    if t < S.T_START:
        k = ease(t / 0.3)
        text_center(c, 'HALLOWEEN SPECIAL', 48, 40, rgb('#ff9a2e'), 0.6 + 0.4 * k)
        text_center(c, 'WILL GLOOP SURVIVE', 140, 72, (1, 1, 1), 0.6 + 0.4 * k)
        text_center(c, S.cfg['hook'], 240, 90, rgb('#ff9a2e'), 0.6 + 0.4 * k, maxw=980)
        return
    res_t = S.T_RES
    if t < (res_t if S.fail else S.T_END):
        tm = timer_at(t)
        tcol = (1, 1, 1) if tm > 5 else (rgb('#ffd84a') if tm > 2 else rgb('#ff4d4d'))
        pulse = 0.12 * max(0, 1 - (tm % 1) / 0.25) if (tm < 5 and not (S.fail and t >= S.T_FAIL)) else 0
        text_center(c, f'SURVIVE: {tm:.1f}s', 105, 92, tcol, 1 + pulse)
        pct = pct_at(t); ls = last_hit(t)
        pop = max(0, 1 - (t - ls) / 0.25) if ls is not None else 0
        col = rgb('#7dff8a') if pct > 60 else (rgb('#ffd84a') if pct > 30 else rgb('#ff4d4d'))
        bw, bx, by_ = 700, (W - 700) / 2, 205
        c.set_source_rgb(0.2, 0.2, 0.25); rrect(c, bx, by_, bw, 52, 26); c.fill()
        if pct > 0:
            c.set_source_rgb(*col); rrect(c, bx, by_, max(52, bw * pct / 100), 52, 26); c.fill()
        c.select_font_face('Poppins', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD); c.set_font_size(36 * (1 + 0.2 * pop))
        s = f'{SUPPORT_LABEL[S.support]} {int(round(pct))}%'; e = c.text_extents(s)
        c.move_to(W / 2 - e.width / 2 - e.x_bearing, by_ + 26 + e.height / 2); c.text_path(s)
        c.set_source_rgb(0, 0, 0); c.set_line_width(7); c.stroke_preserve(); c.set_source_rgb(1, 1, 1); c.fill()
        return
    if not S.fail and t < res_t:
        k = ease((t - S.T_END) / 0.15)
        text_center(c, 'TIME!', 175, 150, rgb('#7dff8a'), 0.5 + 0.5 * k + 0.05 * math.sin(t * 25))
        return
    if t < S.T_OUTRO:
        k = ease((t - res_t) / 0.25)
        if S.fail: text_center(c, 'GLOOP FAILED!', 175, 100, rgb('#ff4d4d'), 0.6 + 0.4 * k + 0.03 * math.sin(t * 20))
        else: text_center(c, 'GLOOP SURVIVED!', 175, 92, rgb('#7dff8a'), 0.6 + 0.4 * k)
        return
    k = ease((t - S.T_OUTRO) / 0.25)
    text_center(c, 'SEE YOU NEXT', 135, 84, (1, 1, 1), 0.6 + 0.4 * k)
    text_center(c, 'CHALLENGE!', 240, 100, rgb('#ff9a2e'), 0.6 + 0.4 * k)


# ======================================================================= backgrounds
def sky(c, top, bot):
    gr = cairo.LinearGradient(0, HEAD, 0, H)
    gr.add_color_stop_rgb(0, *rgb(top)); gr.add_color_stop_rgb(1, *rgb(bot))
    c.set_source(gr); c.rectangle(0, HEAD, W, H - HEAD); c.fill()

def stars(c, t):
    for x, y, r, ph in S.stars:
        c.set_source_rgba(1, 1, 0.9, 0.35 + 0.35 * math.sin(t * 2 + ph)); c.arc(x, y, r, 0, 2 * math.pi); c.fill()

def moon(c, x, y, r, col):
    c.set_source_rgba(*hexc(col, 0.12)); c.arc(x, y, r * 1.7, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*rgb(col)); c.arc(x, y, r, 0, 2 * math.pi); c.fill()
    c.set_source_rgba(0, 0, 0, 0.08); c.arc(x - r * 0.3, y - r * 0.2, r * 0.18, 0, 2 * math.pi); c.fill(); c.arc(x + r * 0.3, y + r * 0.3, r * 0.12, 0, 2 * math.pi); c.fill()

def ground(c, col, top_col=None):
    c.set_source_rgb(*rgb(col)); c.rectangle(0, G, W, H - G); c.fill()
    if top_col:
        c.set_source_rgb(*rgb(top_col)); c.rectangle(0, G, W, 10); c.fill()

def fog(c, t, col=(0.8, 0.75, 1.0)):
    for x, y, r, a in S.fog:
        xx = (x + t * 25) % (W + 400) - 200
        c.set_source_rgba(*col, 0.06 + 0.05 * a); c.save(); c.translate(xx, y); c.scale(1.8, 0.45); c.arc(0, 0, r, 0, 2 * math.pi); c.restore(); c.fill()

def mini_pumpkin(c, x, y, s, lit=True):
    c.save(); c.translate(x, y); c.scale(s, s)
    c.set_source_rgb(*rgb('#d9620f'))
    for dx in (-18, 18): c.save(); c.translate(dx, 0); c.scale(0.7, 1); c.arc(0, 0, 30, 0, 2 * math.pi); c.restore(); c.fill()
    c.set_source_rgb(*rgb('#ff8c1a')); c.save(); c.scale(0.9, 1); c.arc(0, 0, 32, 0, 2 * math.pi); c.restore(); c.fill()
    c.set_source_rgb(*rgb('#3d5a1e')); c.rectangle(-4, -42, 8, 14); c.fill()
    if lit:
        c.set_source_rgb(*rgb('#ffe066'))
        for ex in (-12, 12): c.move_to(ex - 7, -2); c.line_to(ex, -14); c.line_to(ex + 7, -2); c.close_path(); c.fill()
        c.move_to(-16, 8); c.line_to(16, 8); c.line_to(10, 18); c.line_to(-10, 18); c.close_path(); c.fill()
    c.restore()

def bare_tree(c, x, base, s, col):
    c.set_source_rgb(*rgb(col)); c.set_line_cap(cairo.LINE_CAP_ROUND)
    def br(x0, y0, ang, ln, w, d):
        if d == 0 or ln < 12: return
        x1, y1 = x0 + math.cos(ang) * ln, y0 + math.sin(ang) * ln
        c.set_line_width(w); c.move_to(x0, y0); c.line_to(x1, y1); c.stroke()
        br(x1, y1, ang - 0.45, ln * 0.7, w * 0.65, d - 1); br(x1, y1, ang + 0.4, ln * 0.68, w * 0.65, d - 1)
    br(x, base, -math.pi / 2, 260 * s, 34 * s, 5)

def bg_pumpkin_patch(c, t):
    sky(c, '#1a1035', '#4a2350'); stars(c, t); moon(c, 820, 560, 95, '#ffb347')
    c.set_source_rgb(*rgb('#22132e'))
    c.move_to(0, 1500); c.curve_to(250, 1380, 520, 1460, 700, 1420); c.curve_to(860, 1390, 980, 1430, W, 1400); c.line_to(W, G); c.line_to(0, G); c.close_path(); c.fill()
    bare_tree(c, 930, 1460, 0.8, '#1a0f24')
    ground(c, '#2a1a1c', '#3a2a1c')
    for i, (x, s) in enumerate([(60, 1.0), (300, 0.8), (780, 0.9), (1010, 1.1), (520, 0.7)]):
        mini_pumpkin(c, x, G + 60 + (i % 2) * 70, s * 1.3, lit=i % 2 == 0)
    c.set_source_rgba(0.25, 0.4, 0.15, 0.9); c.set_line_width(5)
    c.move_to(0, G + 30); c.curve_to(200, G + 90, 400, G + 10, 600, G + 80); c.curve_to(800, G + 140, 950, G + 40, W, G + 90); c.stroke()
    fog(c, t, (1, 0.8, 0.6))

def bg_witch_hut(c, t):
    sky(c, '#241c33', '#2e2340')
    c.set_source_rgba(0, 0, 0, 0.25); c.set_line_width(3)
    for row, y in enumerate(range(HEAD + 20, G, 70)):
        c.move_to(0, y); c.line_to(W, y); c.stroke()
        for x in range(-60 + (row % 2) * 70, W, 140): c.move_to(x, y); c.line_to(x, y + 70); c.stroke()
    # window
    c.set_source_rgb(*rgb('#3a2a1e')); rrect(c, 760, 470, 240, 300, 20); c.fill()
    gr = cairo.LinearGradient(0, 480, 0, 760); gr.add_color_stop_rgb(0, *rgb('#1d1a4a')); gr.add_color_stop_rgb(1, *rgb('#4a2a6a'))
    c.set_source(gr); rrect(c, 775, 485, 210, 270, 14); c.fill()
    moon(c, 900, 560, 40, '#fff1b8')
    c.set_source_rgb(*rgb('#3a2a1e')); c.rectangle(873, 485, 14, 270); c.fill(); c.rectangle(775, 610, 210, 14); c.fill()
    # shelves with potions
    for sy in (820, 1080):
        c.set_source_rgb(*rgb('#4a3324')); c.rectangle(30, sy, 280, 18); c.fill()
        for i, col in enumerate(['#6bff5a', '#c74bff', '#ff5a7a', '#4bd6ff']):
            x = 60 + i * 65; h = 50 + (i * 17 + sy) % 40
            c.set_source_rgba(*hexc(col, 0.85)); rrect(c, x, sy - h, 40, h, 10); c.fill()
            c.set_source_rgb(*rgb('#8a6a4a')); c.rectangle(x + 12, sy - h - 14, 16, 14); c.fill()
            gl = 0.2 + 0.15 * math.sin(t * 3 + i)
            c.set_source_rgba(*hexc(col, gl)); c.arc(x + 20, sy - h / 2, 40, 0, 2 * math.pi); c.fill()
    # hanging herbs
    c.set_line_width(4)
    for hx in (420, 520, 640):
        c.set_source_rgb(*rgb('#5a4a3a')); c.move_to(hx, HEAD); c.line_to(hx, HEAD + 110); c.stroke()
        c.set_source_rgb(*rgb('#3f6b35'))
        for k in range(5): c.save(); c.translate(hx + (k - 2) * 8, HEAD + 120 + k % 2 * 10); c.scale(0.4, 1); c.arc(0, 0, 24, 0, 2 * math.pi); c.restore(); c.fill()
    ground(c, '#3b2a1e', '#4d3727')
    c.set_source_rgba(0, 0, 0, 0.3); c.set_line_width(3)
    for x in range(0, W, 120): c.move_to(x, G); c.line_to(x - 60, H); c.stroke()

def bg_graveyard(c, t):
    sky(c, '#0f1a2e', '#2a3352'); stars(c, t); moon(c, 300, 560, 85, '#e8f5d0')
    c.set_source_rgba(0.6, 0.6, 0.75, 0.15)
    for cx, cy, sp in ((200, 650, 12), (700, 480, 8)):
        xx = (cx + t * sp) % (W + 300) - 150
        c.save(); c.translate(xx, cy); c.scale(2.2, 0.5); c.arc(0, 0, 90, 0, 2 * math.pi); c.restore(); c.fill()
    bare_tree(c, 960, 1600, 0.9, '#141a28')
    # fence
    c.set_source_rgb(*rgb('#161b2a')); c.set_line_width(6)
    c.move_to(0, 1520); c.line_to(W, 1520); c.stroke(); c.move_to(0, 1600); c.line_to(W, 1600); c.stroke()
    for x in range(10, W, 50):
        c.move_to(x, G); c.line_to(x, 1490); c.stroke(); c.move_to(x - 8, 1494); c.line_to(x, 1474); c.line_to(x + 8, 1494); c.fill()
    ground(c, '#1c2619', '#2a3a22')
    for i, (x, w, h) in enumerate([(90, 130, 190), (330, 110, 150), (760, 140, 200), (990, 120, 160)]):
        y = G + 90 - h
        c.set_source_rgb(*rgb('#5a6070')); c.move_to(x - w / 2, G + 90); c.line_to(x - w / 2, y + w / 2); c.arc(x, y + w / 2, w / 2, math.pi, 2 * math.pi); c.line_to(x + w / 2, G + 90); c.close_path(); c.fill()
        c.set_source_rgb(*rgb('#3c4150'))
        text_center(c, 'RIP', y + w / 2 + 20, 38, rgb('#3c4150'), x=x)
    fog(c, t, (0.75, 0.85, 1.0))

def bg_haunted_house(c, t):
    sky(c, '#170f2b', '#3a2050'); stars(c, t); moon(c, 220, 520, 70, '#fff3c4')
    flash = 0
    for lt in (5.3, 11.7):
        if lt <= t < lt + 0.35: flash = max(flash, (1 - (t - lt) / 0.35) * (0.6 if (t - lt) % 0.12 < 0.06 else 0.3))
    # house
    c.set_source_rgb(*rgb('#120a1e'))
    c.move_to(560, G); c.line_to(560, 1050); c.line_to(700, 920); c.line_to(840, 1050); c.line_to(840, 980)
    c.line_to(900, 800); c.line_to(960, 980); c.line_to(960, 1150); c.line_to(1080, 1150); c.line_to(1080, G); c.close_path(); c.fill()
    for i, (wx, wy) in enumerate([(620, 1120), (720, 1120), (620, 1300), (880, 1010), (1000, 1250), (720, 1300)]):
        on = 0.6 + 0.4 * math.sin(t * 4 + i * 2.1) if i != 3 else 1
        c.set_source_rgba(1, 0.85, 0.3, 0.25 * on); c.arc(wx + 25, wy + 35, 70, 0, 2 * math.pi); c.fill()
        c.set_source_rgba(1, 0.8, 0.3, on); c.rectangle(wx, wy, 50, 70); c.fill()
        c.set_source_rgb(*rgb('#120a1e')); c.rectangle(wx + 22, wy, 6, 70); c.fill(); c.rectangle(wx, wy + 32, 50, 6); c.fill()
    bare_tree(c, 120, G, 1.05, '#100818')
    ground(c, '#161021', '#221833')
    fog(c, t, (0.8, 0.7, 1.0))
    if flash: c.set_source_rgba(0.85, 0.85, 1, flash * 0.5); c.rectangle(0, HEAD, W, H - HEAD); c.fill()

def bg_crypt(c, t):
    sky(c, '#1e1d26', '#2b2a36')
    c.set_source_rgba(0, 0, 0, 0.35); c.set_line_width(4)
    for row, y in enumerate(range(HEAD + 30, G, 90)):
        c.move_to(0, y); c.line_to(W, y); c.stroke()
        for x in range(-90 + (row % 2) * 90, W, 180): c.move_to(x, y); c.line_to(x, y + 90); c.stroke()
    for tx in (110, 970):
        fl = 1 + 0.12 * math.sin(t * 13 + tx) + 0.08 * math.sin(t * 21)
        rg = cairo.RadialGradient(tx, 640, 10, tx, 640, 200); rg.add_color_stop_rgba(0, 1, 0.6, 0.2, 0.35 * fl); rg.add_color_stop_rgba(1, 1, 0.6, 0.2, 0)
        c.set_source(rg); c.arc(tx, 640, 200, 0, 2 * math.pi); c.fill()
        c.set_source_rgb(*rgb('#4a3a2a')); c.rectangle(tx - 12, 680, 24, 90); c.fill()
        c.set_source_rgb(*rgb('#6a5a4a')); rrect(c, tx - 26, 665, 52, 22, 6); c.fill()
        c.set_source_rgb(*rgb('#ff8c1a')); c.save(); c.translate(tx, 640); c.scale(1, fl)
        c.move_to(0, -60); c.curve_to(28, -20, 30, 10, 0, 22); c.curve_to(-30, 10, -28, -20, 0, -60); c.restore(); c.fill()
        c.set_source_rgb(*rgb('#ffe066')); c.save(); c.translate(tx, 650); c.scale(1, fl)
        c.move_to(0, -32); c.curve_to(14, -10, 15, 6, 0, 12); c.curve_to(-15, 6, -14, -10, 0, -32); c.restore(); c.fill()
    # cobwebs in corners
    c.set_source_rgba(1, 1, 1, 0.35); c.set_line_width(2)
    for (cx, cy, sx) in ((0, HEAD, 1), (W, HEAD, -1)):
        for k in range(6):
            a = k / 5 * math.pi / 2; c.move_to(cx, cy); c.line_to(cx + sx * math.cos(a) * 220, cy + math.sin(a) * 220); c.stroke()
        for r in (60, 110, 165):
            for k in range(5):
                a0, a1 = k / 5 * math.pi / 2, (k + 1) / 5 * math.pi / 2
                c.move_to(cx + sx * math.cos(a0) * r, cy + math.sin(a0) * r); c.line_to(cx + sx * math.cos(a1) * r, cy + math.sin(a1) * r); c.stroke()
    ground(c, '#18171f', '#2a2934')
    c.set_source_rgba(0, 0, 0, 0.35); c.set_line_width(3)
    for x in range(0, W + 1, 135): c.move_to(x, G); c.line_to(x + (x - 540) * 0.3, H); c.stroke()
    fog(c, t, (0.6, 0.6, 0.7))

def bg_swamp(c, t):
    sky(c, '#0d1f1a', '#2c3b2e'); stars(c, t); moon(c, 820, 540, 80, '#d9ffb0')
    for x, s in ((80, 1.0), (300, 0.7), (1000, 0.9)): bare_tree(c, x, G, s, '#0f1a14')
    c.move_to(0, G - 20)
    for x in range(0, W + 20, 20): c.line_to(x, G - 20 + 6 * math.sin(x * 0.02 + t * 1.5))
    c.line_to(W, H); c.line_to(0, H); c.close_path()
    gr = cairo.LinearGradient(0, G, 0, H); gr.add_color_stop_rgb(0, *rgb('#2a4a35')); gr.add_color_stop_rgb(1, *rgb('#0f2219'))
    c.set_source(gr); c.fill()
    c.set_source_rgba(0.6, 0.9, 0.5, 0.3); c.set_line_width(3)
    for x in range(0, W + 20, 20): (c.move_to if x == 0 else c.line_to)(x, G - 20 + 6 * math.sin(x * 0.02 + t * 1.5))
    c.stroke()
    for x, y, ph in S.fireflies:
        a = max(0, math.sin(t * 2.5 + ph)); xx = x + 20 * math.sin(t + ph); yy = y + 15 * math.cos(t * 1.3 + ph)
        c.set_source_rgba(1, 1, 0.5, 0.25 * a); c.arc(xx, yy, 14, 0, 2 * math.pi); c.fill()
        c.set_source_rgba(1, 1, 0.6, 0.9 * a); c.arc(xx, yy, 4, 0, 2 * math.pi); c.fill()
    fog(c, t, (0.6, 1.0, 0.6))

BGS = {'pumpkin_patch': bg_pumpkin_patch, 'witch_hut': bg_witch_hut, 'graveyard': bg_graveyard,
       'haunted_house': bg_haunted_house, 'crypt': bg_crypt, 'swamp': bg_swamp}


# ======================================================================= threats
def pumpkin_geom(t):
    r = rise(t); l = lunge(t)
    return 540 + 12 * math.sin(t * 1.1), H + 330 - r * 640 - l * 250

def draw_pumpkin(c, t, look):
    cx, cy = pumpkin_geom(t)
    if cy - 300 > H: return
    l = lunge(t)
    chew = 0
    if S.fail and S.T_CATCH <= t < S.T_SPIT + 0.1: chew = math.sin((t - S.T_CATCH) * 22) * 0.04
    RX, RY = 330 * (1 + chew), 270 * (1 - chew)
    c.save(); c.translate(cx, cy)
    c.set_source_rgba(1, 0.55, 0.1, 0.18); c.save(); c.scale(RX + 60, RY + 60); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    for dx, sc, col in ((-170, 0.55, '#c8500a'), (170, 0.55, '#c8500a'), (-85, 0.7, '#e0650f'), (85, 0.7, '#e0650f'), (0, 0.6, '#ff8c1a')):
        c.save(); c.translate(dx * RX / 330, 0); c.scale(RX * sc, RY); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore()
        c.set_source_rgb(*rgb(col)); c.fill()
    c.set_source_rgb(*rgb('#4a6b1e')); c.move_to(-20, -RY + 10); c.curve_to(-25, -RY - 60, 10, -RY - 90, 40, -RY - 80); c.line_to(30, -RY - 55); c.curve_to(15, -RY - 50, 20, -RY - 20, 22, -RY + 10); c.close_path(); c.fill()
    # eyes (glowing triangles)
    glow = 0.8 + 0.2 * math.sin(t * 9)
    for ex in (-120, 120):
        c.set_source_rgba(1, 0.9, 0.3, 0.35 * glow); c.arc(ex, -70, 75, 0, 2 * math.pi); c.fill()
        c.set_source_rgb(*rgb('#3a1505'))
        c.move_to(ex - 65, -30); c.line_to(ex + (10 if ex < 0 else -10), -130); c.line_to(ex + 65, -30); c.close_path(); c.fill()
        c.set_source_rgba(1, 0.88, 0.3, glow)
        c.move_to(ex - 45, -42); c.line_to(ex + (8 if ex < 0 else -8), -110); c.line_to(ex + 45, -42); c.close_path(); c.fill()
    # brows angry
    c.set_source_rgb(*rgb('#8a3a08')); c.set_line_width(14); c.set_line_cap(cairo.LINE_CAP_ROUND)
    c.move_to(-190, -150); c.line_to(-70, -125); c.stroke(); c.move_to(190, -150); c.line_to(70, -125); c.stroke()
    # mouth
    op = 0.15 + 0.85 * l
    if S.fail and S.T_CATCH <= t < S.T_SPIT: op = 0.05
    if S.fail and S.T_SPIT <= t < S.T_SPIT + 0.3: op = 1.0
    mh = 30 + 150 * op; my = 70
    c.set_source_rgb(*rgb('#3a1505'))
    c.move_to(-200, my - mh / 2)
    for i in range(9):
        x = -200 + (i + 0.5) * 400 / 9; c.line_to(x, my - mh / 2 + (22 if i % 2 == 0 else 0))
    c.line_to(200, my - mh / 2); c.curve_to(190, my + mh / 2, -190, my + mh / 2, -200, my - mh / 2); c.close_path(); c.fill()
    c.set_source_rgba(1, 0.8, 0.25, 0.75 * glow)
    c.save(); c.translate(0, my + mh * 0.1); c.scale(150, max(4, mh * 0.3)); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    c.set_source_rgb(*rgb('#ff9a2e'))
    for x in (-90, 60):
        c.rectangle(x, my + mh / 2 - 30 - 10 * op, 34, 30); c.fill()
    c.restore()

def draw_cauldron(c, t, look):
    r = rise(t); l = lunge(t); RIM = 1450
    # fire
    for i in range(7):
        x = 330 + i * 70; fl = 1 + 0.25 * math.sin(t * 14 + i * 1.7)
        c.set_source_rgb(*rgb('#ff6a1a')); c.save(); c.translate(x, G + 10); c.scale(1, fl)
        c.move_to(0, -110); c.curve_to(40, -40, 40, 0, 0, 10); c.curve_to(-40, 0, -40, -40, 0, -110); c.restore(); c.fill()
        c.set_source_rgb(*rgb('#ffd84a')); c.save(); c.translate(x, G + 10); c.scale(1, fl)
        c.move_to(0, -60); c.curve_to(20, -25, 20, 0, 0, 6); c.curve_to(-20, 0, -20, -25, 0, -60); c.restore(); c.fill()
    # geyser behind rim front
    if l > 0.02 and not (S.fail and t >= S.T_CATCH):
        top = RIM - l * (RIM - (look[1] + 190))
        c.set_source_rgba(0.42, 1, 0.35, 0.95)
        c.move_to(470, RIM)
        for k in range(21):
            y = RIM + (top - RIM) * k / 20; c.line_to(470 + 12 * math.sin(k + t * 12), y)
        c.arc(540, top, 70, math.pi, 2 * math.pi)
        for k in range(20, -1, -1):
            y = RIM + (top - RIM) * k / 20; c.line_to(610 + 12 * math.sin(k * 1.3 - t * 12), y)
        c.close_path(); c.fill()
        c.set_source_rgba(0.75, 1, 0.65, 0.8)
        for k in range(8):
            a = k / 8 * 2 * math.pi + t * 3
            c.arc(540 + math.cos(a) * 110 * l, top - 20 + math.sin(a) * 50, 14, 0, 2 * math.pi); c.fill()
    # body
    gr = cairo.RadialGradient(470, 1520, 40, 540, 1580, 380)
    gr.add_color_stop_rgb(0, *rgb('#4a4458')); gr.add_color_stop_rgb(1, *rgb('#141119'))
    c.set_source(gr)
    c.move_to(220, RIM); c.curve_to(200, 1700, 880, 1700, 860, RIM); c.close_path(); c.fill()
    c.set_source_rgb(*rgb('#141119'))
    for lx in (330, 750): c.move_to(lx - 30, 1640); c.line_to(lx + 30, 1640); c.line_to(lx, G + 20); c.close_path(); c.fill()
    # rim
    c.set_source_rgb(*rgb('#2c2836')); c.save(); c.translate(540, RIM); c.scale(335, 58); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    glow = 0.5 + 0.5 * r
    rg = cairo.RadialGradient(540, RIM, 20, 540, RIM, 330); rg.add_color_stop_rgba(0, 0.42, 1, 0.35, 0.35 * glow); rg.add_color_stop_rgba(1, 0.42, 1, 0.35, 0)
    c.set_source(rg); c.save(); c.translate(540, RIM); c.scale(1, 0.6); c.translate(-540, -RIM); c.arc(540, RIM, 330, math.pi, 2 * math.pi); c.restore(); c.fill()
    c.set_source_rgb(*rgb('#55d94a')); c.save(); c.translate(540, RIM + 4); c.scale(300, 44); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
    for k in range(6):
        ph = (t * (0.8 + 0.6 * r) + k * 0.37) % 1
        x = 300 + k * 90 + 20 * math.sin(k * 3.1)
        c.set_source_rgba(0.75, 1, 0.65, 0.9 * (1 - ph)); c.set_line_width(4)
        c.arc(x, RIM + 4 - ph * 30, 10 + 18 * ph * glow, 0, 2 * math.pi); c.stroke()
    if S.fail and S.T_CATCH <= t < S.T_CATCH + 0.6:
        k = (t - S.T_CATCH) / 0.6
        c.set_source_rgba(0.42, 1, 0.35, 1 - k)
        for i in range(10):
            a = math.pi + i / 9 * math.pi
            c.arc(540 + math.cos(a) * 260 * k, RIM - 20 + math.sin(a) * 260 * k - 100 * k * (1 - k), 18, 0, 2 * math.pi); c.fill()

def draw_hands(c, t, look):
    r = rise(t); xs = (190, 400, 680, 890)
    if r < 0.01: return
    ai = attack_idx(t)
    for i, x0 in enumerate(xs):
        l = lunge(t, extra=i * 0.06)
        base = (x0, G + 40)
        idle = (x0 + 25 * math.sin(t * 2 + i), G - (120 + 90 * (i % 2)) * r + 15 * math.sin(t * 3 + i))
        side = -1 if x0 < 540 else 1
        tgt = (look[0] + side * (110 + 30 * (i % 2)), look[1] + 120)
        tip = (lerp(idle[0], tgt[0], l * 0.85), lerp(idle[1], tgt[1], l * 0.85))
        mid = (lerp(base[0], tip[0], 0.5) + side * 50, lerp(base[1], tip[1], 0.5))
        for (a, b) in ((base, mid), (mid, tip)):
            c.set_line_cap(cairo.LINE_CAP_ROUND)
            c.set_source_rgb(*rgb('#3a3528')); c.set_line_width(30); c.move_to(*a); c.line_to(*b); c.stroke()
            c.set_source_rgb(*rgb('#e8e0c8')); c.set_line_width(20); c.move_to(*a); c.line_to(*b); c.stroke()
        c.set_source_rgb(*rgb('#e8e0c8')); c.arc(mid[0], mid[1], 18, 0, 2 * math.pi); c.fill()
        ang = math.atan2(tip[1] - mid[1], tip[0] - mid[0])
        spread = 0.25 + 0.5 * l if l < 0.95 else 0.1
        c.save(); c.translate(*tip); c.rotate(ang)
        c.set_source_rgb(*rgb('#e8e0c8')); c.save(); c.scale(1.2, 1); c.arc(10, 0, 26, 0, 2 * math.pi); c.restore(); c.fill()
        c.set_line_width(9)
        for k in range(4):
            a = (k - 1.5) * spread
            c.set_source_rgb(*rgb('#e8e0c8'))
            x1, y1 = 30 + math.cos(a) * 30, math.sin(a) * 30 * 1.4
            x2, y2 = x1 + math.cos(a * 1.3) * 32, y1 + math.sin(a * 1.3) * 32
            c.move_to(25, (k - 1.5) * 9); c.line_to(x1, y1); c.line_to(x2, y2); c.stroke()
            c.set_source_rgb(*rgb('#b8ad90')); c.arc(x1, y1, 5, 0, 2 * math.pi); c.fill()
        c.set_source_rgb(*rgb('#e8e0c8')); c.move_to(10, -20); c.line_to(25, -48); c.stroke()
        c.restore()
        c.set_source_rgb(*rgb('#3a2a1c')); c.save(); c.translate(x0, G + 30); c.scale(90, 30); c.arc(0, 0, 1, math.pi, 2 * math.pi); c.restore(); c.fill()

def ghost_geom(t):
    r = rise(t); l = lunge(t)
    bx, by = 540 + 260 * math.sin(t * 0.7), 1480 + 40 * math.sin(t * 1.3)
    by = H + 300 - r * (H + 300 - by)
    side = -1 if attack_idx(t) % 2 == 0 else 1
    p = pre_pos(min(t, S.T_GRAB if not S.fail else S.T_FAIL))
    tx, ty = p[0] + side * 300, p[1] + 230
    return lerp(bx, tx, l), lerp(by, ty, l), l, side

def draw_ghost(c, t, look):
    x, y, l, side = ghost_geom(t)
    if y - 200 > H: return
    c.save(); c.translate(x, y); c.rotate(-side * 0.15 * l)
    rg = cairo.RadialGradient(0, 40, 60, 0, 40, 300); rg.add_color_stop_rgba(0, 0.85, 0.9, 1, 0.22); rg.add_color_stop_rgba(1, 0.85, 0.9, 1, 0)
    c.set_source(rg); c.arc(0, 40, 300, 0, 2 * math.pi); c.fill()
    c.move_to(-170, 0); c.arc(0, 0, 170, math.pi, 2 * math.pi); c.line_to(170, 230)
    for k in range(9):
        xx = 170 - (k + 1) * 340 / 9; yy = 230 + (30 if k % 2 == 0 else -10) + 12 * math.sin(t * 8 + k)
        c.line_to(xx, yy)
    c.close_path()
    gr = cairo.LinearGradient(0, -170, 0, 260); gr.add_color_stop_rgba(0, 1, 1, 1, 0.95); gr.add_color_stop_rgba(1, 0.85, 0.88, 1, 0.75)
    c.set_source(gr); c.fill()
    lx, ly = look[0] - x, look[1] - y; d = math.hypot(lx, ly) or 1
    for ex in (-60, 60):
        c.set_source_rgb(0.08, 0.06, 0.12); c.save(); c.translate(ex + lx / d * 8, -30 + ly / d * 8); c.scale(0.75, 1.15); c.arc(0, 0, 30, 0, 2 * math.pi); c.restore(); c.fill()
    mo = 0.3 + 0.9 * l
    c.save(); c.translate(0, 60); c.scale(0.8, mo); c.arc(0, 0, 40, 0, 2 * math.pi); c.restore(); c.fill()
    c.set_source_rgba(1, 0.6, 0.7, 0.5); c.arc(-100, 25, 18, 0, 2 * math.pi); c.fill(); c.arc(100, 25, 18, 0, 2 * math.pi); c.fill()
    c.restore()
    if l > 0.55: text_center(c, 'BOO!', y - 230, 80, (1, 1, 1, min(1, (l - 0.55) * 4)), 0.8 + 0.3 * l, x=max(170, min(W - 170, x)))

def draw_bats(c, t, look):
    r = rise(t)
    if r < 0.01: return
    ai = attack_idx(t); a = S.attacks[ai]; p = (t - (a - 0.7)) / 1.4
    w = math.sin(math.pi * p) if 0 <= p <= 1 else 0
    w = ease(w * 1.4)
    dirn = 1 if ai % 2 == 0 else -1
    pp = pre_pos(min(t, S.T_GRAB))
    for i, (ph, sp, ox, oy, sz) in enumerate(S.bats):
        ix = 540 + 360 * ox + 60 * math.sin(t * sp * 2 + ph)
        iy = 1430 + 160 * math.sin(t * sp + ph) + oy
        iy = H + 200 - r * (H + 200 - iy)
        q = max(0, min(1, p)) + (i % 5) * 0.03
        sx = -250 + 1580 * q if dirn > 0 else W + 250 - 1580 * q
        sy = pp[1] + 175 + oy * 0.8 + 30 * math.sin(q * 9 + ph)
        x, y = lerp(ix, sx, w), lerp(iy, sy, w)
        s2 = 2.1 * sz
        rg = cairo.RadialGradient(x, y, 5, x, y, 80 * s2 / 2); rg.add_color_stop_rgba(0, 0.75, 0.45, 1, 0.35); rg.add_color_stop_rgba(1, 0.75, 0.45, 1, 0)
        c.set_source(rg); c.arc(x, y, 80 * s2 / 2, 0, 2 * math.pi); c.fill()
        bat_shape(c, x, y, s2, math.sin(t * 22 + ph * 3), rgb('#120818'))
        c.set_source_rgb(*rgb('#ffd84a')); c.arc(x - 4 * s2, y - 3 * s2, 2.6 * s2, 0, 2 * math.pi); c.fill(); c.arc(x + 4 * s2, y - 3 * s2, 2.6 * s2, 0, 2 * math.pi); c.fill()

def spider_geom(t):
    r = rise(t); l = lunge(t)
    return 540 + 14 * math.sin(t * 1.2), H + 320 - r * (H + 320 - 1580) - l * 300

def draw_spider(c, t, look):
    cx, cy = spider_geom(t)
    if cy - 300 > H: return
    l = lunge(t)
    col = rgb('#2a1a33'); c.set_line_cap(cairo.LINE_CAP_ROUND)
    for side in (-1, 1):
        for i in range(4):
            jx, jy = cx + side * 50, cy - 40 + i * 30
            kx = cx + side * (200 + i * 25); ky = cy - 200 + i * 60 - 30 * math.sin(t * 6 + i + side)
            fx = cx + side * (290 + i * 30); fy = cy + 60 + i * 60 + 20 * math.sin(t * 6 + i * 2 + side)
            c.set_source_rgb(*col); c.set_line_width(20 - i * 2)
            c.move_to(jx, jy); c.line_to(kx, ky); c.line_to(fx, fy); c.stroke()
            c.set_source_rgb(*rgb('#4a2f5a')); c.arc(kx, ky, 10, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*col); c.save(); c.translate(cx, cy + 90); c.scale(1, 1.1); c.arc(0, 0, 160, 0, 2 * math.pi); c.restore(); c.fill()
    c.set_source_rgb(*rgb('#ff8c1a'))
    c.move_to(cx - 40, cy + 30); c.line_to(cx + 40, cy + 30); c.line_to(cx, cy + 90); c.close_path(); c.fill()
    c.move_to(cx - 40, cy + 150); c.line_to(cx + 40, cy + 150); c.line_to(cx, cy + 90); c.close_path(); c.fill()
    c.set_source_rgb(*col); c.arc(cx, cy - 90, 100, 0, 2 * math.pi); c.fill()
    for k, (ex, ey, er) in enumerate([(-40, -110, 22), (40, -110, 22), (-75, -80, 13), (75, -80, 13), (-18, -150, 10), (18, -150, 10)]):
        c.set_source_rgb(*rgb('#ff3a3a')); c.arc(cx + ex, cy + ey, er, 0, 2 * math.pi); c.fill()
        c.set_source_rgb(1, 0.85, 0.85); c.arc(cx + ex - er * 0.3, cy + ey - er * 0.3, er * 0.3, 0, 2 * math.pi); c.fill()
    op = 0.2 + 0.6 * l
    c.set_source_rgb(*rgb('#f2ecf5'))
    for side in (-1, 1):
        c.save(); c.translate(cx + side * 30, cy - 20); c.rotate(side * -op * 0.6)
        c.move_to(-8, 0); c.curve_to(-10, 30, side * 5, 50, side * 18, 60); c.curve_to(side * 4, 40, 6, 25, 8, 0); c.close_path(); c.fill()
        c.restore()

THREATS = {'pumpkin': draw_pumpkin, 'cauldron': draw_cauldron, 'hands': draw_hands, 'ghost': draw_ghost, 'bats': draw_bats, 'spider': draw_spider}
THREAT_FRONT = {'hands'}   # drawn after support (still behind gloop)


# ======================================================================= supports
def rope_pts(t, bx, by):
    ax, ay = 540, 440
    slack = max(0, -action_off(t)[1]) if t < S.T_BREAK else 0
    mx, my = (ax + bx) / 2, (ay + by - 86) / 2
    L = math.hypot(bx - ax, by - 86 - ay) or 1; nx, ny = -(by - 86 - ay) / L, (bx - ax) / L
    cx, cy = mx + nx * slack * 0.6, my + ny * slack * 0.6
    return lambda u: ((1 - u) ** 2 * ax + 2 * (1 - u) * u * cx + u * u * bx, (1 - u) ** 2 * ay + 2 * (1 - u) * u * cy + u * u * (by - 86))

def web_anchors():
    return [(40, 470), (540, 400), (1040, 470), (1040, 900), (1040, 1330), (540, 1420), (40, 1330), (40, 900)]

def branch_pivot(): return (240, 1062)

def weak_point(t):
    tb = min(t, S.T_BREAK - 0.01)
    bx, by = pre_pos(tb)
    if S.support == 'rope': return rope_pts(tb, bx, by)(0.4)
    if S.support == 'web':
        n = broken_count(pct_at(tb)); i = S.web_order[min(7, n)]
        ax, ay = web_anchors()[i]; return (ax + bx) / 2, (ay + by) / 2
    if S.support == 'branch': return branch_pivot()[0], 1045
    if S.support == 'broom': ax, ay = anchor(tb); return ax - 300, ay + 95
    ax, ay = anchor(tb); return ax + 110, ay - 120

def broken_count(pct):
    return min(7, int(round((100 - pct) / 100 * 7.4)))

def draw_support(c, t, bx, by, front):
    pct = pct_at(t); broken = t >= S.T_BREAK; tb = t - S.T_BREAK
    sp = S.support
    if sp == 'rope' and not front:
        # tree branch overhead
        c.set_source_rgb(*rgb('#2e2018'))
        c.move_to(W, 400); c.curve_to(850, 410, 600, 420, 380, 425); c.line_to(380, 452); c.curve_to(600, 450, 850, 450, W, 470); c.close_path(); c.fill()
        c.set_source_rgb(*rgb('#3a2a1e')); c.arc(540, 448, 16, 0, 2 * math.pi); c.fill()
        c.set_line_cap(cairo.LINE_CAP_ROUND)
        if broken:
            k = min(1, tb / 0.6); sw = 40 * math.sin(tb * 7) * math.exp(-tb * 1.5)
            P = rope_pts(S.T_BREAK - 0.01, *pre_pos(S.T_BREAK - 0.01)); mx, my = P(0.4)
            c.set_line_width(17); c.set_source_rgb(*rgb('#c79a5b'))
            c.move_to(540, 440); c.curve_to(540, 500, mx + sw, my - 60 - 40 * k, mx + sw, my - 40 * k); c.stroke(); return
        P = rope_pts(t, bx, by); pts = [P(i / 40) for i in range(41)]
        c.set_line_width(17); c.set_source_rgb(*rgb('#c79a5b')); c.move_to(*pts[0]); [c.line_to(*q) for q in pts[1:]]; c.stroke()
        c.set_line_width(3); c.set_source_rgb(*rgb('#8f6a37'))
        for i in range(1, 40, 2):
            (x1, y1), (x2, y2) = pts[i], pts[i + 1]
            L = math.hypot(x2 - x1, y2 - y1) or 1; nx, ny = -(y2 - y1) / L, (x2 - x1) / L
            c.move_to(x1 - nx * 7, y1 - ny * 7); c.line_to(x2 + nx * 7, y2 + ny * 7); c.stroke()
        fx, fy = P(0.4); gx, gy = P(0.45)
        L = math.hypot(gx - fx, gy - fy) or 1; ux, uy = (gx - fx) / L, (gy - fy) / L; nx, ny = -uy, ux
        c.set_line_width(22); c.set_source_rgb(*rgb('#1a1030')); c.move_to(fx - ux * 26, fy - uy * 26); c.line_to(fx + ux * 26, fy + uy * 26); c.stroke()
        c.set_line_width(4 + 13 * pct / 100); c.set_source_rgb(*rgb('#e2b877')); c.move_to(fx - ux * 30, fy - uy * 30); c.line_to(fx + ux * 30, fy + uy * 30); c.stroke()
        r2 = random.Random(3); c.set_line_width(2.5)
        for i in range(int((100 - pct) / 6) + 2):
            side = 1 if i % 2 else -1; off = r2.uniform(-24, 24); ln = r2.uniform(14, 34); wig = 4 * math.sin(t * 9 + i)
            px, py = fx + ux * off, fy + uy * off
            c.move_to(px, py); c.line_to(px + nx * side * ln + wig, py + ny * side * ln); c.stroke()
        c.set_source_rgb(*rgb('#a97f45')); c.arc(bx, by - 86, 14, 0, 2 * math.pi); c.fill()
    elif sp == 'web' and not front:
        A = web_anchors(); nb = 8 if broken else broken_count(pct)
        brk = set(S.web_order[:nb])
        c.set_line_cap(cairo.LINE_CAP_ROUND)
        for i, (ax, ay) in enumerate(A):
            if i in brk:
                c.set_source_rgba(1, 1, 1, 0.75); c.set_line_width(4)
                dx, dy = (bx - ax) * 0.35, (by - ay) * 0.35; sw = 10 * math.sin(t * 3 + i)
                c.move_to(ax, ay); c.curve_to(ax + dx * 0.5, ay + dy * 0.5, ax + dx + sw, ay + dy + 40, ax + dx * 0.8 + sw, ay + dy + 90); c.stroke()
            else:
                c.set_source_rgba(1, 1, 1, 0.85); c.set_line_width(5); c.move_to(ax, ay); c.line_to(bx, by); c.stroke()
        if not broken:
            angs = sorted([(math.atan2(A[i][1] - by, A[i][0] - bx), i) for i in range(8)])
            c.set_source_rgba(1, 1, 1, 0.55); c.set_line_width(2.5)
            for rr in (110, 180, 260, 350):
                for j in range(8):
                    a0, i0 = angs[j]; a1, i1 = angs[(j + 1) % 8]
                    if i0 in brk or i1 in brk: continue
                    d0 = math.hypot(A[i0][0] - bx, A[i0][1] - by); d1 = math.hypot(A[i1][0] - bx, A[i1][1] - by)
                    if rr > min(d0, d1) - 20: continue
                    p0 = (bx + (A[i0][0] - bx) * rr / d0, by + (A[i0][1] - by) * rr / d0)
                    p1 = (bx + (A[i1][0] - bx) * rr / d1, by + (A[i1][1] - by) * rr / d1)
                    m = ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2); mm = (lerp(m[0], bx, 0.12), lerp(m[1], by, 0.12))
                    c.move_to(*p0); c.curve_to(mm[0], mm[1], mm[0], mm[1], *p1); c.stroke()
        for ax, ay in A:
            c.set_source_rgb(*rgb('#4a3a30')); c.arc(ax, ay, 12, 0, 2 * math.pi); c.fill()
    elif sp == 'branch' and not front:
        c.set_source_rgb(*rgb('#2e2018')); c.rectangle(0, HEAD, 150, G - HEAD); c.fill()
        c.set_source_rgb(*rgb('#3d2c20'))
        for yy in range(HEAD + 40, G, 90): c.rectangle(40, yy, 9, 50); c.fill()
        px, py = branch_pivot()
        ls = last_hit(t); bend = 0
        if ls is not None and not broken: d = t - ls; bend = 0.035 * math.exp(-d * 6) * math.cos(d * 22)
        ang = bend; dy = 0
        if broken: ang = 0.9 * ease(tb / 0.5) + 2.5 * max(0, tb - 0.4) ** 2; dy = 1400 * max(0, tb - 0.25) ** 2
        c.set_source_rgb(*rgb('#4a3424'))
        c.move_to(140, 1030); c.line_to(px, 1036); c.line_to(px, 1088); c.line_to(140, 1100); c.close_path(); c.fill()
        c.save(); c.translate(px, py + dy); c.rotate(ang)
        c.set_source_rgb(*rgb('#4a3424'))
        c.move_to(0, -26); c.curve_to(250, -30, 450, -22, 660, -14); c.line_to(660, 6); c.curve_to(450, 14, 250, 22, 0, 26); c.close_path(); c.fill()
        c.set_source_rgb(*rgb('#5e4430')); c.set_line_width(4)
        for x in (120, 300, 480): c.move_to(x, -10); c.line_to(x + 60, -8); c.stroke()
        c.set_source_rgb(*rgb('#2a4a22'))
        for lx, ly in ((560, -40), (620, -30), (660, -18)): c.save(); c.translate(lx, ly); c.scale(1, 0.55); c.arc(0, 0, 26, 0, 2 * math.pi); c.restore(); c.fill()
        c.restore()
        if not broken:
            dmg = (100 - pct) / 100
            c.set_source_rgb(*rgb('#120a06')); c.set_line_width(5)
            c.move_to(px, py - 26)
            for k in range(1, 7):
                yy = py - 26 + k * 52 * dmg / 6; c.line_to(px + (10 if k % 2 else -10), yy)
            c.stroke()
    elif sp == 'broom' and front:
        if broken:
            ax, ay = anchor(S.T_BREAK); g = 1500
            for side, sx in ((-1, ax - 80), (1, ax + 90)):
                c.save(); c.translate(sx + side * 160 * tb, ay + 80 - 400 * tb + g * tb * tb); c.rotate(side * tb * 5)
                c.set_source_rgb(*rgb('#8a5a2b')); rrect(c, -110, -9, 220, 18, 9); c.fill()
                if side < 0:
                    c.set_source_rgb(*rgb('#d9b25a'))
                    for k in range(8): c.set_line_width(5); c.move_to(-100, 0); c.line_to(-220, -50 + k * 14); c.stroke()
                c.restore()
            return
        ax, ay = anchor(t); tilt = -0.08 + 0.02 * math.sin(t * 2.2)
        c.save(); c.translate(ax, ay + 85); c.rotate(tilt)
        n = 6 + int(pct / 100 * 22)
        c.set_line_width(6); c.set_line_cap(cairo.LINE_CAP_ROUND)
        for k in range(n):
            f = k / max(1, n - 1)
            c.set_source_rgb(*(rgb('#d9b25a') if k % 3 else rgb('#b08a3a')))
            c.move_to(-270, 0); c.line_to(-420 - 30 * math.sin(f * 3.1), -70 + f * 140 + 8 * math.sin(t * 10 + k)); c.stroke()
        c.set_source_rgb(*rgb('#6a2fa0')); rrect(c, -290, -22, 40, 44, 10); c.fill()
        c.set_source_rgb(*rgb('#8a5a2b')); rrect(c, -260, -11, 460, 22, 11); c.fill()
        c.set_source_rgb(*rgb('#6e4520')); c.set_line_width(3)
        for x in (-150, 0, 120): c.move_to(x, -6); c.line_to(x + 40, -6); c.stroke()
        c.restore()
        # sparkle trail
        for k in range(6):
            ph = (t * 1.5 + k / 6) % 1
            c.set_source_rgba(1, 0.75, 0.3, 0.8 * (1 - ph)); star_path(c, ax - 430 - ph * 300, ay + 80 + 40 * math.sin(k * 2.3 + t), 10 * (1 - ph) + 3); c.fill()
    elif sp == 'bubble' and front:
        if broken:
            if tb < 0.4:
                ax, ay = anchor(S.T_BREAK); k = tb / 0.4
                c.set_source_rgba(0.75, 0.95, 1, 1 - k); c.set_line_width(8 * (1 - k)); c.arc(ax, ay, 165 + 120 * k, 0, 2 * math.pi); c.stroke()
            return
        ax, ay = anchor(t); ls = last_hit(t); wob = 0
        if ls is not None: d = t - ls; wob = 0.1 * math.exp(-d * 6) * math.sin(d * 25)
        c.save(); c.translate(ax, ay); c.scale(1 + wob, 1 - wob)
        c.set_source_rgba(0.7, 0.9, 1, 0.10); c.arc(0, 0, 165, 0, 2 * math.pi); c.fill()
        gr = cairo.LinearGradient(-165, -165, 165, 165)
        a = 0.35 + 0.55 * pct / 100
        gr.add_color_stop_rgba(0, 0.6, 0.9, 1, a); gr.add_color_stop_rgba(0.5, 1, 0.6, 1, a); gr.add_color_stop_rgba(1, 0.6, 1, 0.7, a)
        c.set_source(gr); c.set_line_width(2 + 8 * pct / 100); c.arc(0, 0, 165, 0, 2 * math.pi); c.stroke()
        c.set_source_rgba(1, 1, 1, 0.6); c.set_line_width(8); c.arc(0, 0, 135, math.pi * 1.15, math.pi * 1.45); c.stroke()
        c.arc(-75, -95, 6, 0, 2 * math.pi); c.fill()
        r3 = random.Random(5)
        for i in range(int((100 - pct) / 12)):
            a0 = r3.uniform(0, 6.28); c.set_source_rgba(0.2, 0.2, 0.35, 0.35); c.set_line_width(3)
            c.move_to(math.cos(a0) * 165, math.sin(a0) * 165); c.line_to(math.cos(a0 + 0.08) * 145, math.sin(a0 + 0.08) * 145); c.line_to(math.cos(a0 + 0.02) * 128, math.sin(a0 + 0.02) * 128); c.stroke()
        c.restore()


# ======================================================================= gloop
SKIN_GRAD = {'pumpkin': ('#ffb347', '#e8650a', '#a84400'), None: ('#ffd36b', '#ff8a1f', '#c45a00')}

def body_path(c, t, R):
    c.new_path()
    for i in range(61):
        a = i / 60 * 2 * math.pi
        r = R * (1 + 0.035 * math.sin(a * 3 + t * 5) + 0.02 * math.sin(a * 5 - t * 7))
        (c.move_to if i == 0 else c.line_to)(math.cos(a) * r, math.sin(a) * r)
    c.close_path()

def draw_gloop(c, t, x, y, mood, squash, tint=None, cocoon=0.0):
    R = 86; skin = S.skin
    c.save(); c.translate(x, y); c.scale(1 + squash, 1 - squash)
    if skin == 'vampire':   # cape collar behind
        c.set_source_rgb(*rgb('#1a0a12'))
        c.move_to(-60, -20); c.line_to(-150, -120); c.line_to(-110, 40); c.line_to(110, 40); c.line_to(150, -120); c.line_to(60, -20); c.close_path(); c.fill()
        c.set_source_rgb(*rgb('#8a1028')); c.move_to(-60, -10); c.line_to(-130, -100); c.line_to(-100, 30); c.close_path(); c.fill()
        c.move_to(60, -10); c.line_to(130, -100); c.line_to(100, 30); c.close_path(); c.fill()
    c.set_source_rgba(1, 0.6, 0.2, 0.15); c.arc(0, 0, R + 24, 0, 2 * math.pi); c.fill()
    g0, g1, g2 = SKIN_GRAD.get(skin, SKIN_GRAD[None])
    if tint == 'green': g0, g1, g2 = '#d4ff9a', '#5fd94a', '#2f8a22'
    body_path(c, t, R)
    gr = cairo.RadialGradient(-25, -30, 10, 0, 0, R); gr.add_color_stop_rgb(0, *rgb(g0)); gr.add_color_stop_rgb(1, *rgb(g1))
    c.set_source(gr); c.fill_preserve(); c.set_line_width(5); c.set_source_rgb(*rgb(g2)); c.stroke()
    # body overlays
    if skin == 'pumpkin':
        c.save(); body_path(c, t, R); c.clip()
        c.set_source_rgba(*hexc('#b84a00', 0.45)); c.set_line_width(5)
        for sx in (-0.45, 0.45):
            c.save(); c.scale(sx, 1); c.arc(0, 0, R, -math.pi / 2, math.pi / 2); c.restore(); c.stroke()
        c.restore()
    if skin == 'mummy':
        c.save(); body_path(c, t, R); c.clip()
        c.set_source_rgba(*hexc('#efe6cf', 0.92))
        for (yy, a, h) in ((-62, 0.15, 22), (24, -0.12, 20), (52, 0.1, 22), (78, -0.05, 20)):
            c.save(); c.translate(0, yy); c.rotate(a); c.rectangle(-120, -h / 2, 240, h); c.restore(); c.fill()
        c.set_source_rgba(*hexc('#c9bfa5', 0.8)); c.set_line_width(2)
        for (yy, a) in ((-62, 0.15), (24, -0.12), (52, 0.1)):
            c.save(); c.translate(0, yy); c.rotate(a); c.move_to(-120, 0); c.line_to(120, 0); c.restore(); c.stroke()
        c.restore()
        c.set_source_rgba(*hexc('#efe6cf', 0.92)); c.save(); c.translate(70, 60); c.rotate(0.6 + 0.2 * math.sin(t * 4)); c.rectangle(0, -9, 60, 18); c.restore(); c.fill()
    if skin == 'ghost':
        c.move_to(-R - 8, 0); c.arc(0, 0, R + 8, math.pi, 2 * math.pi); c.line_to(R + 8, R + 20)
        for k in range(7):
            xx = R + 8 - (k + 1) * (2 * R + 16) / 7; c.line_to(xx, R + 20 + (16 if k % 2 == 0 else -4) + 5 * math.sin(t * 7 + k))
        c.close_path(); c.set_source_rgba(1, 1, 1, 0.78); c.fill()
    # cheeks
    if skin != 'mummy' or True:
        c.set_source_rgba(1, 0.35, 0.35, 0.45); c.arc(-44, 18, 13, 0, 2 * math.pi); c.fill(); c.arc(44, 18, 13, 0, 2 * math.pi); c.fill()
    # eyes
    look_y = 6 if mood in ('worried', 'scared') else -2
    blink = (t % 3.7) < 0.08 and mood == 'worried'
    for ex in (-24, 24):
        if mood == 'happy':
            c.set_line_width(7); c.set_source_rgb(0.1, 0.06, 0.05); c.arc(ex, -6, 13, math.pi * 1.1, math.pi * 1.9); c.stroke(); continue
        if mood == 'dizzy':
            c.set_source_rgb(1, 1, 1); c.arc(ex, -10, 18, 0, 2 * math.pi); c.fill()
            c.set_line_width(3.5); c.set_source_rgb(0.1, 0.06, 0.05)
            for k in range(30):
                a = k * 0.45 + t * 8 * (1 if ex < 0 else -1); rr = 2 + k * 0.5
                (c.move_to if k == 0 else c.line_to)(ex + math.cos(a) * rr, -10 + math.sin(a) * rr)
            c.stroke(); continue
        er = 21 if mood == 'scared' else 18
        if blink:
            c.set_line_width(6); c.set_source_rgb(0.1, 0.06, 0.05); c.move_to(ex - 14, -8); c.line_to(ex + 14, -8); c.stroke(); continue
        c.set_source_rgb(1, 1, 1); c.arc(ex, -10, er, 0, 2 * math.pi); c.fill()
        c.set_source_rgb(0.1, 0.06, 0.05); c.arc(ex + 2, -10 + look_y, er * 0.48, 0, 2 * math.pi); c.fill()
        c.set_source_rgb(1, 1, 1); c.arc(ex + 6, -14 + look_y, 4, 0, 2 * math.pi); c.fill()
    c.set_line_width(7); c.set_source_rgb(0.25, 0.12, 0.02); c.set_line_cap(cairo.LINE_CAP_ROUND)
    if mood == 'worried':
        c.move_to(-38, -38); c.line_to(-12, -46); c.stroke(); c.move_to(38, -38); c.line_to(12, -46); c.stroke()
    elif mood == 'scared':
        c.move_to(-40, -44); c.line_to(-12, -52); c.stroke(); c.move_to(40, -44); c.line_to(12, -52); c.stroke()
    c.set_source_rgb(0.25, 0.05, 0.05)
    if mood == 'scared':
        c.save(); c.translate(0, 30); c.scale(1, 1.3); c.arc(0, 0, 14, 0, 2 * math.pi); c.restore(); c.fill()
    elif mood in ('worried', 'dizzy'):
        c.set_line_width(6); c.move_to(-16, 34)
        for i in range(5): c.line_to(-16 + (i + 1) * 8, 34 + (4 if i % 2 == 0 else 0))
        c.stroke()
    else:
        c.arc(0, 22, 22, 0.1, math.pi - 0.1); c.close_path(); c.fill()
        c.set_source_rgb(1, 0.45, 0.5); c.arc(0, 36, 9, 0, math.pi); c.fill()
    # accessories on top
    if skin == 'vampire':
        c.set_source_rgb(1, 1, 1)
        my = 22 if mood == 'happy' else 30
        for fx in (-10, 10): c.move_to(fx - 5, my); c.line_to(fx + 5, my); c.line_to(fx, my + 14); c.close_path(); c.fill()
        c.set_source_rgb(*rgb('#1a0a12'))
        c.move_to(-80, -30); c.arc(0, 0, 86, math.pi * 1.12, math.pi * 1.88); c.line_to(40, -58); c.line_to(0, -48); c.line_to(-40, -58); c.close_path(); c.fill()
    if skin == 'witch':
        c.set_source_rgb(*rgb('#4a1f75')); c.save(); c.translate(0, -74); c.scale(100, 20); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); c.fill()
        c.set_source_rgb(*rgb('#6a2fa0'))
        c.move_to(-55, -80); c.curve_to(-30, -150, -10, -200, 30, -225 + 6 * math.sin(t * 3)); c.curve_to(15, -190, 30, -140, 55, -80); c.close_path(); c.fill()
        c.set_source_rgb(*rgb('#ff8c1a')); c.move_to(-55, -82); c.line_to(55, -82); c.line_to(48, -104); c.line_to(-48, -104); c.close_path(); c.fill()
        c.set_source_rgb(*rgb('#ffd84a')); c.set_line_width(4); c.rectangle(-12, -100, 24, 16); c.stroke()
    if skin == 'pumpkin':
        c.set_source_rgb(*rgb('#4a6b1e')); c.move_to(-10, -82); c.curve_to(-14, -110, 4, -125, 18, -122); c.line_to(14, -108); c.curve_to(6, -104, 8, -94, 10, -82); c.close_path(); c.fill()
        c.set_source_rgb(*rgb('#5fa83a')); c.save(); c.translate(36, -100); c.rotate(-0.4 + 0.1 * math.sin(t * 4)); c.scale(1, 0.5); c.arc(0, 0, 24, 0, 2 * math.pi); c.restore(); c.fill()
    if skin == 'cat':
        for sx in (-1, 1):
            c.set_source_rgb(*rgb('#15101a')); c.move_to(sx * 30, -78); c.line_to(sx * 70, -140); c.line_to(sx * 76, -50); c.close_path(); c.fill()
            c.set_source_rgb(*rgb('#ff8fb0')); c.move_to(sx * 42, -76); c.line_to(sx * 66, -118); c.line_to(sx * 68, -64); c.close_path(); c.fill()
        c.set_source_rgb(*rgb('#15101a')); c.set_line_width(3)
        for sx in (-1, 1):
            for k in (-1, 0, 1): c.move_to(sx * 58, 22 + k * 8); c.line_to(sx * 108, 16 + k * 16); c.stroke()
        c.set_source_rgb(*rgb('#ff6f9a')); c.move_to(-7, 10); c.line_to(7, 10); c.line_to(0, 18); c.close_path(); c.fill()
    if cocoon > 0:
        c.set_source_rgba(0.96, 0.95, 1, 0.85 * cocoon); c.set_line_width(7)
        for k in range(9):
            if k / 9 > cocoon: break
            yy = -70 + k * 19; a = 0.25 * (1 if k % 2 else -1)
            if -30 < yy < 0: continue
            c.save(); c.translate(0, yy); c.rotate(a); c.move_to(-100, 0); c.curve_to(-40, 14, 40, 14, 100, 0); c.restore(); c.stroke()
    c.restore()
    if mood == 'dizzy':
        for k in range(3):
            a = t * 4 + k * 2.09
            c.set_source_rgb(*rgb('#ffd84a')); star_path(c, x + math.cos(a) * 85, y - 120 + math.sin(a) * 22, 15); c.fill()
    elif mood in ('worried', 'scared'):
        k = (t * 0.8) % 1
        c.set_source_rgba(0.6, 0.85, 1, 0.9 * (1 - k)); dx, dy = x + 62, y - 50 + k * 50
        c.move_to(dx, dy - 14); c.curve_to(dx + 10, dy, dx + 8, dy + 10, dx, dy + 10); c.curve_to(dx - 8, dy + 10, dx - 10, dy, dx, dy - 14); c.fill()


# ======================================================================= particles / render
PCOL = {'rope': ('#e2b877', 'fiber'), 'web': ('#ffffff', 'fiber'), 'branch': ('#7a5636', 'fiber'), 'broom': ('#d9b25a', 'fiber'), 'bubble': ('#bfefff', 'dot')}

def spawn(x, y, n, col, spd, life, kind='dot'):
    rng = S.rng
    for _ in range(n):
        a = rng.uniform(0, 2 * math.pi); s = rng.uniform(0.3, 1) * spd
        S.particles.append([x, y, math.cos(a) * s, math.sin(a) * s - spd * 0.3, life, life, col, kind])

def render(f, c):
    t = f / FPS; rng = S.rng
    ls = last_hit(t); shake = (0, 0)
    if ls is not None and t - ls < 0.2:
        a = (1 - (t - ls) / 0.2) * (14 if ls == S.T_BREAK else 6); shake = (rng.uniform(-a, a), rng.uniform(-a, a))
    if S.fail and S.T_CATCH <= t < S.T_CATCH + 0.25:
        a = 12 * (1 - (t - S.T_CATCH) / 0.25); shake = (rng.uniform(-a, a), rng.uniform(-a, a))
    pc, kind = PCOL[S.support]
    for st in S.acts:
        if f == int(st * FPS) and st != S.T_BREAK: x, y = weak_point(st); spawn(x, y, 10, rgb(pc), 450, 0.8, kind)
    if f == int(S.T_BREAK * FPS): x, y = weak_point(S.T_BREAK); spawn(x, y, 30, rgb(pc), 900, 0.8, kind)
    if f == int(S.T_GRAB * FPS): spawn(S.GP[0], S.GP[1] - 60, 20, (1, 1, 0.7), 650, 0.6, 'star')
    if S.fail and S.T_SPIT and f == int(S.T_SPIT * FPS):
        p = threat_center(S.T_CATCH); spawn(p[0], p[1], 18, (0.45, 1, 0.4) if S.threat == 'cauldron' else (1, 0.7, 0.2), 600, 0.7)
    c.save(); c.translate(*shake)
    BGS[S.bg](c, t)
    bx, by, hidden = blob_pos(t)
    if S.threat not in THREAT_FRONT: THREATS[S.threat](c, t, (bx, by))
    draw_support(c, t, bx, by, False)
    if S.threat in THREAT_FRONT: THREATS[S.threat](c, t, (bx, by))
    # mood
    tint = None; cocoon = 0.0
    if not S.fail:
        if t < S.T_GRAB:
            scared = (ls is not None and t - ls < 0.5) or lunge(t) > 0.35 or t > S.T_CLAW_IN
            mood = 'scared' if scared else 'worried'; sq = squash_at(t)
        elif t < S.T_RES: mood = 'scared'; sq = -0.05
        else: mood = 'happy'; sq = 0.03 * math.sin(t * 8)
    else:
        if t < S.T_FAIL:
            scared = (ls is not None and t - ls < 0.5) or lunge(t) > 0.35
            mood = 'scared' if scared else 'worried'; sq = squash_at(t)
        elif t < S.T_CATCH: mood = 'scared'; sq = -0.08
        elif t < S.T_OUTRO: mood = 'dizzy'; sq = 0.05 * math.sin(t * 6)
        else: mood = 'happy'; sq = 0.03 * math.sin(t * 8)
        if S.threat == 'cauldron' and t >= S.T_SPIT: tint = 'green'
        if S.threat == 'spider' and t >= S.T_CATCH: cocoon = ease((t - S.T_CATCH) / 0.6)
        if S.T_SPIT is not None and S.T_REST <= t < S.T_REST + 0.25:
            sq = 0.2 * math.cos((t - S.T_REST) * 25) * math.exp(-(t - S.T_REST) * 8)
    if not hidden:
        draw_gloop(c, t, bx, by, mood, sq, tint, cocoon)
    draw_support(c, t, bx, by, True)
    if S.threat == 'cauldron' and S.fail and t >= S.T_CATCH - 0.1 and hidden:
        pass
    draw_claw(c, t)
    for j, st in enumerate(S.acts):
        if st <= t < st + 0.9:
            k = (t - st) / 0.9; fx, fy = weak_point(st)
            fx = max(60, min(W - 230, fx + 50))
            c.save(); c.translate(fx, fy - 10 - 70 * k)
            c.select_font_face('Poppins', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD); c.set_font_size(56 * (1 + 0.3 * max(0, 1 - k * 5)))
            c.move_to(0, 0); c.text_path(f'-{S.DMG_SHOW[j]}%')
            c.set_source_rgba(0, 0, 0, 1 - k); c.set_line_width(8); c.stroke_preserve()
            c.set_source_rgba(1, 0.3, 0.3, 1 - k); c.fill(); c.restore()
    for p in S.particles[:]:
        p[0] += p[2] / FPS; p[1] += p[3] / FPS; p[3] += 1600 / FPS; p[4] -= 1 / FPS
        if p[4] <= 0: S.particles.remove(p); continue
        a = p[4] / p[5]; c.set_source_rgba(*p[6], a)
        if p[7] == 'fiber':
            c.set_line_width(3); c.move_to(p[0], p[1]); c.line_to(p[0] - p[2] * 0.03, p[1] - p[3] * 0.03); c.stroke()
        elif p[7] == 'star':
            star_path(c, p[0], p[1], 14 * a); c.fill()
        else:
            c.arc(p[0], p[1], 8 * a, 0, 2 * math.pi); c.fill()
    if S.T_BREAK <= t < S.T_BREAK + 0.6:
        k = (t - S.T_BREAK) / 0.6; wx, wy = weak_point(S.T_BREAK)
        text_center(c, BREAK_WORD[S.support], max(HEAD + 120, wy - 60 * k - 40), 110, rgb('#ff4d4d'), 0.7 + 0.5 * ease(k * 3), x=max(220, min(W - 220, wx)))
    if S.fail and S.threat == 'pumpkin' and S.T_CATCH <= t < S.T_SPIT:
        text_center(c, 'GULP!', 1180, 110, rgb('#ff9a2e'), 0.8 + 0.2 * math.sin(t * 20))
    if S.fail and S.threat == 'cauldron' and S.T_CATCH <= t < S.T_SPIT:
        text_center(c, 'SPLOOSH!', 1230, 100, rgb('#7dff8a'), 0.8 + 0.2 * math.sin(t * 20))
    if S.fail and S.threat == 'spider' and S.T_CATCH + 0.2 <= t < S.T_CATCH + 1.2:
        text_center(c, 'WRAPPED!', 880, 100, (1, 1, 1), 0.9 + 0.1 * math.sin(t * 20))
    c.restore()
    draw_header(c, t)


def events():
    return {'acts': S.acts, 'break': S.T_BREAK, 'end': S.T_END, 'claw_in': S.T_CLAW_IN, 'grab': S.T_GRAB, 'lift': S.T_LIFT,
            'attacks': S.attacks, 'outro': S.T_OUTRO, 'start': S.T_START, 'dur': S.DUR, 'fail': S.fail,
            'fail_t': S.T_FAIL, 'catch': getattr(S, 'T_CATCH', None), 'spit': getattr(S, 'T_SPIT', None),
            'res': S.T_RES, 'threat': S.threat, 'support': S.support}

def main(cfg):
    setup(cfg)
    out = sys.argv[1]
    json.dump(events(), open(sys.argv[2], 'w'))
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    if len(sys.argv) > 3:
        want = {int(round(x * FPS)) for x in map(float, sys.argv[3].split(','))}
        for f in range(S.N):
            c = cairo.Context(surf); render(f, c)
            if f in want: surf.write_to_png(f'{out}_{f:04d}.png')
        return
    ff = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgra', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                           '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    for f in range(S.N):
        c = cairo.Context(surf); render(f, c); surf.flush(); ff.stdin.write(bytes(surf.get_data()))
    ff.stdin.close(); sys.exit(ff.wait())
