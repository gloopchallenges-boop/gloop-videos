"""Shared Gloop helpers (2026-11-01). Scenario scripts import this, define a Scene object with
   setup()/sim done at import, then call run(scene).
Scene must provide: DUR, T_START, T_END, T_RES (time challenge resolved), OUTCOME ('win'|'fail'),
   HOOK2 (2nd hook line), GRAB (x, y) where the claw grabs Gloop, draw_world(c, t, f),
   draw_bar(c, t, f) (header bar under the timer), events (list of [t, kind, extra]) for sfx,
   optional FAIL_WORD (big word shown at failure, e.g. 'SPOTTED!'), gloop_carry(c, t) to draw
   Gloop hanging from the claw after the lift (default: blob under claw).
"""
import cairo, math, random, subprocess, sys, json, os, re
import numpy as np

W, H, FPS, HEAD = 1080, 1920, 30, 330
HOOK_T = 1.5      # hook length: use S.T_START = HOOK_T (hazard must already be in motion from frame 0)
MIN_DUR = 18.0    # every video >= 18 s (YouTube job contract)
LOOP_T = 0.4      # last 0.4 s crossfade back into frame 0 so the Short loops seamlessly
GUESS_AT, GUESS_LEN = 2.2, 1.8   # 'SURVIVE OR FAIL?' prompt, seconds after T_START

def gloop_record():
    """Gloop's W-L record before this video: env RECORD='W-L' or counted from history.md
    (rows whose Outcome starts with Survived/Failed). Append each video's history row right after
    building it so the next video's record includes it."""
    if os.environ.get('RECORD'):
        w, l = os.environ['RECORD'].split('-'); return int(w), int(l)
    hp = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'history.md')
    w = l = 0
    try:
        for line in open(hp):
            cells = [x.strip() for x in line.strip().strip('|').split('|')]
            if len(cells) >= 6 and re.match(r'\d{4}-\d\d-\d\d', cells[0]):
                if cells[-1].lower().startswith('survived'): w += 1
                elif cells[-1].lower().startswith('failed'): l += 1
    except OSError: pass
    return w, l

def ease(x): x = max(0, min(1, x)); return x * x * (3 - 2 * x)
def lerp(a, b, k): return a + (b - a) * k
def clamp(x, a, b): return max(a, min(b, x))
def hexc(h, a=1):
    h = h.lstrip('#'); return (int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255, a)
def rgb(h): return hexc(h)[:3]

def rrect(c, x, y, w, h, r):
    r = min(r, w / 2, h / 2)
    c.new_sub_path()
    c.arc(x + w - r, y + r, r, -math.pi / 2, 0); c.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    c.arc(x + r, y + h - r, r, math.pi / 2, math.pi); c.arc(x + r, y + r, r, math.pi, 1.5 * math.pi)
    c.close_path()

def font(c, size):
    c.select_font_face('Poppins', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD); c.set_font_size(size)

def text_at(c, s, x, y, size, col, scale=1.0, lw=10):
    font(c, size); ext = c.text_extents(s)
    c.save(); c.translate(x, y); c.scale(scale, scale)
    c.move_to(-ext.width / 2 - ext.x_bearing, ext.height / 2); c.text_path(s)
    c.set_line_join(cairo.LINE_JOIN_ROUND)
    c.set_source_rgb(0, 0, 0); c.set_line_width(lw); c.stroke_preserve()
    c.set_source_rgb(*col); c.fill(); c.restore()

def text_center(c, s, y, size, col, scale=1.0, shake=(0, 0)):
    text_at(c, s, W / 2 + shake[0], y + shake[1], size, col, scale)

def draw_blob(c, t, x, y, mood, squash=0.0, R=86, skin=('#ffd36b', '#ff8a1f', '#c45a00'), sweat=True, dizzy=False):
    c.save(); c.translate(x, y); c.scale(R / 86, R / 86)
    c.scale(1 + squash, 1 - squash)
    c.set_source_rgba(1, 0.6, 0.2, 0.15); c.arc(0, 0, 110, 0, 2 * math.pi); c.fill()
    c.new_path()
    for i in range(61):
        a = i / 60 * 2 * math.pi
        r = 86 * (1 + 0.035 * math.sin(a * 3 + t * 5) + 0.02 * math.sin(a * 5 - t * 7))
        (c.move_to if i == 0 else c.line_to)(math.cos(a) * r, math.sin(a) * r)
    c.close_path()
    gr = cairo.RadialGradient(-25, -30, 10, 0, 0, 86)
    gr.add_color_stop_rgb(0, *rgb(skin[0])); gr.add_color_stop_rgb(1, *rgb(skin[1]))
    c.set_source(gr); c.fill_preserve(); c.set_line_width(5); c.set_source_rgb(*rgb(skin[2])); c.stroke()
    c.set_source_rgba(1, 0.35, 0.35, 0.45)
    c.arc(-44, 18, 13, 0, 2 * math.pi); c.fill(); c.arc(44, 18, 13, 0, 2 * math.pi); c.fill()
    blink = (t % 3.7) < 0.08 and mood == 'worried'
    look_y = 6 if mood in ('worried', 'scared') else -2
    c.set_line_cap(cairo.LINE_CAP_ROUND)
    for ex in (-24, 24):
        if dizzy:
            c.set_line_width(5); c.set_source_rgb(0.1, 0.06, 0.05)
            for k in range(14):
                a = k * 0.7 + t * 8; r = 3 + k * 1.1
                (c.move_to if k == 0 else c.line_to)(ex + math.cos(a) * r, -10 + math.sin(a) * r)
            c.stroke(); continue
        if mood == 'happy':
            c.set_line_width(7); c.set_source_rgb(0.1, 0.06, 0.05)
            c.arc(ex, -6, 13, math.pi * 1.1, math.pi * 1.9); c.stroke(); continue
        er = 21 if mood == 'scared' else 18
        if blink:
            c.set_line_width(6); c.set_source_rgb(0.1, 0.06, 0.05); c.move_to(ex - 14, -8); c.line_to(ex + 14, -8); c.stroke(); continue
        c.set_source_rgb(1, 1, 1); c.arc(ex, -10, er, 0, 2 * math.pi); c.fill()
        c.set_source_rgb(0.1, 0.06, 0.05); c.arc(ex + 2, -10 + look_y, er * 0.48, 0, 2 * math.pi); c.fill()
        c.set_source_rgb(1, 1, 1); c.arc(ex + 6, -14 + look_y, 4, 0, 2 * math.pi); c.fill()
    c.set_line_width(7); c.set_source_rgb(0.25, 0.12, 0.02)
    if mood == 'worried':
        c.move_to(-38, -38); c.line_to(-12, -46); c.stroke(); c.move_to(38, -38); c.line_to(12, -46); c.stroke()
    elif mood == 'scared':
        c.move_to(-40, -44); c.line_to(-12, -52); c.stroke(); c.move_to(40, -44); c.line_to(12, -52); c.stroke()
    c.set_source_rgb(0.25, 0.05, 0.05)
    if mood == 'scared' and not dizzy:
        c.save(); c.translate(0, 30); c.scale(1, 1.3); c.arc(0, 0, 14, 0, 2 * math.pi); c.restore(); c.fill()
    elif mood == 'worried' or dizzy:
        c.set_line_width(6); c.move_to(-16, 34)
        for i in range(5): c.line_to(-16 + (i + 1) * 8, 34 + (4 if i % 2 == 0 else 0))
        c.stroke()
    else:
        c.arc(0, 22, 22, 0.1, math.pi - 0.1); c.close_path(); c.fill()
        c.set_source_rgb(1, 0.45, 0.5); c.arc(0, 36, 9, 0, math.pi); c.fill()
    c.restore()
    if dizzy:
        for i in range(3):
            a = t * 4 + i * 2.1
            sx, sy = x + math.cos(a) * R * 0.9, y - R * 1.05 + math.sin(a) * 18
            c.set_source_rgb(1, 0.9, 0.3); star_path(c, sx, sy, 14); c.fill()
    elif sweat and mood in ('worried', 'scared'):
        k = (t * 0.8) % 1
        c.set_source_rgba(0.6, 0.85, 1, 0.9 * (1 - k))
        dx, dy = x + R * 0.72, y - R * 0.58 + k * 50
        c.move_to(dx, dy - 14); c.curve_to(dx + 10, dy, dx + 8, dy + 10, dx, dy + 10); c.curve_to(dx - 8, dy + 10, dx - 10, dy, dx, dy - 14); c.fill()

def star_path(c, x, y, r):
    for i in range(10):
        a = -math.pi / 2 + i * math.pi / 5; rr = r if i % 2 == 0 else r * 0.45
        (c.move_to if i == 0 else c.line_to)(x + math.cos(a) * rr, y + math.sin(a) * rr)
    c.close_path()

def heart_path(c, x, y, s):
    c.move_to(x, y + s * 0.9)
    c.curve_to(x - s * 1.3, y + s * 0.1, x - s * 0.9, y - s * 0.9, x, y - s * 0.35)
    c.curve_to(x + s * 0.9, y - s * 0.9, x + s * 1.3, y + s * 0.1, x, y + s * 0.9)
    c.close_path()

def bar(c, frac, label, col, pop=0.0, bw=700, by_=205, x_off=0):
    bx = (W - bw) / 2 + x_off
    c.set_source_rgb(0.2, 0.2, 0.25); rrect(c, bx, by_, bw, 52, 26); c.fill()
    if frac > 0.005:
        c.set_source_rgb(*col); rrect(c, bx, by_, max(52, bw * min(1, frac)), 52, 26); c.fill()
    font(c, 36 * (1 + 0.2 * pop)); e = c.text_extents(label)
    c.move_to(bx + bw / 2 - e.width / 2 - e.x_bearing, by_ + 26 + e.height / 2); c.text_path(label)
    c.set_source_rgb(0, 0, 0); c.set_line_width(7); c.stroke_preserve(); c.set_source_rgb(1, 1, 1); c.fill()
    return bx

def good_bad_col(p):  # p: 0..1 where 1 is good
    return rgb('#7dff8a') if p > 0.6 else (rgb('#ffd84a') if p > 0.3 else rgb('#ff4d4d'))
def bad_col(p):  # p: 0..1 where 1 is bad
    return rgb('#ffd84a') if p < 0.5 else (rgb('#ff8a3a') if p < 0.8 else rgb('#ff3b3b'))


class Particles:
    def __init__(self, seed=5): self.p = []; self.rng = random.Random(seed)
    def spawn(self, x, y, n, col, spd, life, grav=1400, r=9):
        for _ in range(n):
            a = self.rng.uniform(0, 2 * math.pi); s = self.rng.uniform(0.3, 1) * spd
            self.p.append([x, y, math.cos(a) * s, math.sin(a) * s - spd * 0.4, life, life, col, grav, r])
    def draw(self, c):
        for p in self.p[:]:
            p[0] += p[2] / FPS; p[1] += p[3] / FPS; p[3] += p[7] / FPS; p[4] -= 1 / FPS
            if p[4] <= 0: self.p.remove(p); continue
            c.set_source_rgba(*p[6], p[4] / p[5]); c.arc(p[0], p[1], p[8] * p[4] / p[5], 0, 2 * math.pi); c.fill()


class Ending:
    """Claw + header timing after the challenge resolves at T_RES."""
    def __init__(self, S):
        self.S = S; r = S.T_RES
        pad = max(0.0, MIN_DUR - (r + 3.8))   # short ending; hold the result longer only if needed for MIN_DUR
        self.T_TEXT = r + 0.7
        self.T_CLAW_IN = r + 0.6 + pad * 0.5
        self.T_GRAB = r + 1.3 + pad * 0.5
        self.T_LIFT = r + 1.5 + pad
        self.T_GONE = r + 2.9 + pad
        self.T_OUTRO = r + 2.3 + pad
        S.DUR = round(r + 3.8 + pad, 2)
        self.REC = gloop_record()
        g0 = S.T_START + GUESS_AT
        self.T_GUESS = g0 if S.T_RES > g0 + GUESS_LEN + 0.6 else None
    def overlay(self, c, t):
        """Drawn on top of every frame: record badge + mid-video guess prompt."""
        S = self.S; w, l = self.REC; pop = 0.0
        if t >= self.T_TEXT:
            if S.OUTCOME == 'win': w += 1
            else: l += 1
            pop = max(0.0, 1 - (t - self.T_TEXT) / 0.4)
        font(c, 34); s1 = 'GLOOP RECORD'; s2 = f'{w}W - {l}L'
        e1 = c.text_extents(s1); font(c, 44); e2 = c.text_extents(s2)
        bw = max(e1.x_advance, e2.x_advance) + 40
        c.save(); c.translate(24, HEAD + 22); c.scale(1 + 0.25 * pop, 1 + 0.25 * pop)
        c.set_source_rgba(0.05, 0.04, 0.08, 0.72); rrect(c, 0, 0, bw, 104, 22); c.fill()
        c.set_source_rgb(*(rgb('#7dff8a') if pop and S.OUTCOME == 'win' else rgb('#ff4d4d') if pop else rgb('#ffd36b'))); c.set_line_width(4); rrect(c, 0, 0, bw, 104, 22); c.stroke()
        c.restore()
        text_at(c, s1, 24 + bw / 2, HEAD + 22 + 30, 30, (0.85, 0.85, 0.9), 1 + 0.25 * pop, lw=6)
        text_at(c, s2, 24 + bw / 2, HEAD + 22 + 72, 44, (1, 1, 1), 1 + 0.25 * pop, lw=7)
        if self.T_GUESS is not None and self.T_GUESS <= t < self.T_GUESS + GUESS_LEN:
            k = (t - self.T_GUESS) / GUESS_LEN
            a = min(1, k / 0.12, (1 - k) / 0.12); sc = 0.7 + 0.3 * ease(k / 0.15)
            y = HEAD + 250
            c.save(); c.translate(W / 2, y); c.scale(sc, sc)
            c.set_source_rgba(0.05, 0.04, 0.08, 0.75 * a); rrect(c, -400, -95, 800, 190, 36); c.fill()
            c.restore()
            if a > 0.3:
                text_at(c, 'SURVIVE OR FAIL?', W / 2, y - 35, 72 * sc, rgb('#ffd36b'), lw=9)
                text_at(c, 'COMMENT YOUR GUESS!', W / 2, y + 45, 50 * sc, (1, 1, 1), lw=8)
    def claw_pos(self, t):
        gx, gy = self.S.GRAB; ry = gy - 150
        if t < self.T_CLAW_IN: return None
        if t < self.T_GRAB:
            k = ease((t - self.T_CLAW_IN) / (self.T_GRAB - self.T_CLAW_IN)); return lerp(W + 250, gx, k), lerp(380, ry, k)
        if t < self.T_LIFT: return gx, ry
        k = ease((t - self.T_LIFT) / (self.T_GONE - self.T_LIFT)); return lerp(gx, W + 250, k), lerp(ry, 40, k)
    def carried(self, t): return t >= self.T_LIFT
    def carry_xy(self, t):
        x, y = self.claw_pos(t); return x, y + 150
    def draw_claw(self, c, t):
        p = self.claw_pos(t)
        if p is None: return
        x, y = p
        c.set_source_rgb(*rgb('#9aa3b5')); c.set_line_width(8)
        c.move_to(x + 520, HEAD - 20); c.line_to(x, y - 30); c.stroke()
        cl = 0.0 if t < self.T_GRAB else ease((t - self.T_GRAB) / 0.15)
        for side in (-1, 1):
            c.save(); c.translate(x + side * 40, y + 30); c.rotate(side * (-0.55 + 0.55 * cl))
            c.set_source_rgb(*rgb('#6f7891')); c.set_line_width(16); c.set_line_cap(cairo.LINE_CAP_ROUND)
            c.move_to(0, 0); c.line_to(side * 55, 80); c.line_to(side * 20, 150); c.stroke()
            c.restore()
        c.set_source_rgb(*rgb('#c9d0de')); rrect(c, x - 70, y - 40, 140, 80, 22); c.fill()
        c.set_source_rgb(*rgb('#6f7891')); rrect(c, x - 70, y + 10, 140, 30, 12); c.fill()
        on = (t * 6) % 1 < 0.5
        c.set_source_rgb(*(rgb('#ff4040') if on else rgb('#7a2020'))); c.arc(x, y - 10, 13, 0, 2 * math.pi); c.fill()
    def header(self, c, t, f):
        S = self.S
        c.set_source_rgb(*rgb('#0d0b14')); c.rectangle(0, 0, W, HEAD); c.fill()
        if t < S.T_START:
            k = ease(t / 0.3)
            text_center(c, getattr(S, 'HOOK1', 'WILL GLOOP SURVIVE'), 135, 76, (1, 1, 1), 0.6 + 0.4 * k)
            text_center(c, S.HOOK2, 240, getattr(S, 'HOOK2_SIZE', 92), rgb('#ffd36b'), 0.6 + 0.4 * k)
            return
        if t >= self.T_OUTRO:
            k = ease((t - self.T_OUTRO) / 0.25)
            text_center(c, 'SEE YOU NEXT', 135, 84, (1, 1, 1), 0.6 + 0.4 * k)
            text_center(c, 'CHALLENGE!', 240, 100, rgb('#ffd36b'), 0.6 + 0.4 * k); return
        if t >= S.T_RES:
            if t < self.T_TEXT:
                k = ease((t - S.T_RES) / 0.15)
                if S.OUTCOME == 'win':
                    text_center(c, 'TIME!', 175, 150, rgb('#7dff8a'), 0.5 + 0.5 * k + 0.05 * math.sin(t * 25))
                else:
                    sh = (math.sin(t * 91) * 7, math.cos(t * 77) * 7)
                    text_center(c, getattr(S, 'FAIL_WORD', 'OH NO!'), 175, getattr(S, 'FAIL_SIZE', 140), rgb('#ff4d4d'), 0.5 + 0.5 * k, sh)
                return
            k = ease((t - self.T_TEXT) / 0.25)
            if S.OUTCOME == 'win': text_center(c, 'GLOOP SURVIVED!', 175, 92, rgb('#7dff8a'), 0.6 + 0.4 * k)
            else: text_center(c, 'GLOOP FAILED!', 175, 96, rgb('#ff4d4d'), 0.6 + 0.4 * k)
            return
        tm = max(0, S.T_END - t)
        tcol = (1, 1, 1) if tm > 5 else (rgb('#ffd84a') if tm > 2 else rgb('#ff4d4d'))
        pulse = 0.12 * max(0, 1 - (tm % 1) / 0.25) if tm < 5 else 0
        text_center(c, f'SURVIVE: {tm:.1f}s', 105, 92, tcol, 1 + pulse)
        S.draw_bar(c, t, f)
    def std_events(self):
        S = self.S; ev = []
        for k in range(5, 0, -1):
            at = S.T_END - k
            if at < S.T_RES: ev.append([at, 'tick', 1 if k <= 2 else 0])
        ev.append([S.T_RES, 'win' if S.OUTCOME == 'win' else 'fail'])
        ev.append([self.T_TEXT, 'wah' if S.OUTCOME == 'fail' else 'none'])
        ev.append([self.T_CLAW_IN, 'claw_in', self.T_GRAB - self.T_CLAW_IN])
        ev.append([self.T_GRAB, 'grab']); ev.append([self.T_LIFT, 'claw_lift', 1.6])
        ev.append([self.T_OUTRO, 'outro'])
        return ev


def run(S, render):
    out = sys.argv[1]; N = int(S.DUR * FPS)
    events = sorted(S.events + S.END.std_events(), key=lambda e: e[0])
    json.dump({'dur': S.DUR, 'fps': FPS, 'start': S.T_START, 'end': S.T_END, 'res': S.T_RES, 'outcome': S.OUTCOME,
               'outro': S.END.T_OUTRO, 'events': events, 'amb': getattr(S, 'AMB', {})}, open(sys.argv[2], 'w'))
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    if len(sys.argv) > 3:
        want = {int(x * FPS) for x in map(float, sys.argv[3].split(','))}
        for f in range(min(N, max(want) + 1)):
            c = cairo.Context(surf); render(f, c); S.END.overlay(c, f / FPS)
            if f in want: surf.write_to_png(f'{out}_{f:04d}.png')
        return
    ff = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgra', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                           '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    first = None; NL = int(LOOP_T * FPS)
    for f in range(N):
        c = cairo.Context(surf); render(f, c); S.END.overlay(c, f / FPS); surf.flush()
        buf = bytes(surf.get_data())
        if f == 0: first = np.frombuffer(buf, np.uint8).astype(np.float32)
        if f >= N - NL:   # crossfade into frame 0 -> seamless loop
            a = (f - (N - NL) + 1) / NL
            cur = np.frombuffer(buf, np.uint8).astype(np.float32)
            buf = (cur * (1 - a) + first * a).astype(np.uint8).tobytes()
        ff.stdin.write(buf)
    ff.stdin.close(); sys.exit(ff.wait())
