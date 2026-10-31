import cairo, math, random, subprocess, sys, json
W, H, FPS, DUR = 1080, 1920, 30, 23.0
N = int(DUR * FPS)
HEAD = 330
SURF = 99999
FLOOR = 1560
rng = random.Random(11)
T_BREAK = 999.0

def ease(x): x = max(0, min(1, x)); return x * x * (3 - 2 * x)
def lerp(a, b, k): return a + (b - a) * k

# ---------------- timeline ----------------
T_START, TIME_LIMIT = 2.6, 16.0
T_END = T_START + TIME_LIMIT
LIGHT = (205, 860)          # flashlight lens
HALF = math.radians(8.5)    # cone half angle
UP_RATE, DOWN_RATE = 42.0, 12.0

# beam angle keyframes (deg below horizontal)
BEAM = [(0, 48.2), (1.5, 71.8), (3.0, 50.5), (4.2, 74.7), (5.0, 64.7), (5.5, 59.3), (6.5, 45.9), (7.5, 55.4), (8.3, 61.9), (8.75, 56.0), (9.3, 66.1), (9.9, 49.4), (10.4, 43.8), (11.5, 34.7), (12.6, 44.8), (13.4, 51.7), (14.0, 41.6), (14.6, 38.6), (15.4, 47.1), (16.3, 39.1), (30, 39.1)]
def beam_angle(t):
    for (t0, a0), (t1, a1) in zip(BEAM, BEAM[1:]):
        if t0 <= t <= t1: return math.radians(lerp(a0, a1, ease((t - t0) / (t1 - t0))))
    return math.radians(BEAM[-1][1])

# hiding spots (drawn IN FRONT of Gloop): x0, x1, top, kind
COVERS = [(310, 490, FLOOR - 220, 'crate'), (565, 710, FLOOR - 190, 'barrel'), (785, 950, FLOOR - 400, 'crates'), (945, 1075, FLOOR - 185, 'can')]
R = 74
HIDE_Y = FLOOR - R * 0.75
PATH = [(0, 400), (5.0, 400), (5.8, 637), (9.6, 637), (10.4, 867), (13.6, 867), (14.6, 998), (30, 998)]
PEEKS = [(8.2, 8.95), (12.0, 12.5)]
T_TIP = 16.2      # trash can tips over
def gloop_pos(t):
    x = PATH[-1][1]; moving = False
    for (t0, x0), (t1, x1) in zip(PATH, PATH[1:]):
        if t0 <= t <= t1:
            x = lerp(x0, x1, ease((t - t0) / (t1 - t0))); moving = x0 != x1; break
    y = HIDE_Y
    if moving: y -= abs(math.sin(t * 7.0 * math.pi)) * 90 + 30
    peek = 0
    for p0, p1 in PEEKS:
        if p0 <= t <= p1: peek = math.sin(math.pi * (t - p0) / (p1 - p0))
    y -= peek * 125
    return x, y, moving, peek

def can_tip(t):
    return ease((t - T_TIP) / 0.35) if t > T_TIP else 0.0

def hidden(t):
    x, y, moving, peek = gloop_pos(t)
    if moving or peek > 0.35: return False
    if t > T_TIP + 0.2 and abs(x - 998) < 5: return False
    return any(x0 <= x <= x1 for x0, x1, top, k in COVERS)

def in_cone(px, py, t):
    a = beam_angle(t)
    ang = math.atan2(py - LIGHT[1], px - LIGHT[0])
    return abs(ang - a) < HALF + math.atan2(R * 0.6, math.hypot(px - LIGHT[0], py - LIGHT[1]))

def seen(t):
    x, y, _, _ = gloop_pos(t)
    return in_cone(x, y, t) and not hidden(t)

# simulate detection
DET, SEEN = [], []
d = 0.0; T_SPOT = None
for f in range(N):
    t = f / FPS
    s = T_START <= t < T_END and T_SPOT is None and seen(t)
    if T_SPOT is None and T_START <= t < T_END:
        d += (UP_RATE if s else -DOWN_RATE) / FPS
        d = max(0, min(100, d))
        if d >= 100: T_SPOT = t
    DET.append(d); SEEN.append(s)
OUTCOME = 'fail' if T_SPOT else 'win'
T_RESOLVE = T_SPOT if T_SPOT else T_END
T_CAGE = T_RESOLVE + 0.05
T_TEXT = T_RESOLVE + 0.7
T_CLAW_IN = T_RESOLVE + 1.1
T_GRAB = T_RESOLVE + 2.0
T_LIFT = T_RESOLVE + 2.3
T_GONE = T_RESOLVE + 4.0
T_OUTRO = T_RESOLVE + 3.0
def rrect(c, x, y, w, h, r):
    c.new_sub_path()
    c.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    c.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    c.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    c.arc(x + r, y + r, r, math.pi, 1.5 * math.pi)
    c.close_path()

def hexc(h, a=1):
    h = h.lstrip('#'); return (int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255, a)

stars = [(rng.uniform(0, W), rng.uniform(HEAD, 1100), rng.uniform(1, 3), rng.uniform(0, 6)) for _ in range(70)]
trees = [(x, rng.uniform(0.7, 1.2)) for x in range(-40, W + 80, 95)]
bubbles = [(rng.uniform(40, W - 40), rng.uniform(0, 3), rng.uniform(6, 16)) for _ in range(22)]

def draw_bg(c, t):
    gr = cairo.LinearGradient(0, HEAD, 0, H)
    gr.add_color_stop_rgb(0, *hexc('#120f2e')[:3]); gr.add_color_stop_rgb(1, *hexc('#2a1d4a')[:3])
    c.set_source(gr); c.rectangle(0, HEAD, W, H - HEAD); c.fill()
    for x, y, r, ph in stars:
        a = 0.4 + 0.4 * math.sin(t * 2 + ph)
        c.set_source_rgba(1, 1, 0.9, a); c.arc(x, y, r, 0, 2 * math.pi); c.fill()
    # moon
    c.set_source_rgba(*hexc('#fff3c4', 0.12)); c.arc(860, 560, 120, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*hexc('#fff3c4')[:3]); c.arc(860, 560, 70, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*hexc('#e9dca8')[:3]); c.arc(840, 545, 12, 0, 2 * math.pi); c.fill(); c.arc(885, 585, 8, 0, 2 * math.pi); c.fill()
    # far tree silhouettes
    c.set_source_rgb(*hexc('#1b1538')[:3])
    for x, s in trees:
        top = 1250 - 260 * s
        c.move_to(x - 70 * s, SURF); c.line_to(x, top); c.line_to(x + 70 * s, SURF); c.close_path(); c.fill()
    c.set_source_rgb(*hexc('#15102c')[:3])
    for x, s in trees[::2]:
        top = 1380 - 200 * s
        c.move_to(x + 30 - 80 * s, SURF); c.line_to(x + 30, top); c.line_to(x + 30 + 80 * s, SURF); c.close_path(); c.fill()
    # big tree left + branch
    c.set_source_rgb(*hexc('#3a2a20')[:3])
    c.rectangle(0, HEAD, 120, SURF - HEAD); c.fill()
    c.move_to(100, 470); c.curve_to(300, 430, 480, 420, 640, 430); c.line_to(640, 455); c.curve_to(480, 450, 300, 470, 100, 520); c.close_path(); c.fill()
    c.set_source_rgb(*hexc('#4b382b')[:3])
    for yy in range(HEAD + 40, SURF, 90):
        c.rectangle(30, yy, 8, 50); c.fill()
    # leaves
    for (lx, ly, r) in [(60, 400, 110), (200, 380, 80), (640, 420, 40), (40, 600, 70)]:
        c.set_source_rgb(*hexc('#1f4a2c')[:3]); c.arc(lx, ly, r, 0, 2 * math.pi); c.fill()
    # hanging vines
    c.set_line_width(5); c.set_source_rgb(*hexc('#2f6b3a')[:3])
    for vx, vl in [(260, 220), (330, 140), (470, 260)]:
        sw = 10 * math.sin(t * 1.5 + vx)
        c.move_to(vx, 455); c.curve_to(vx + sw, 455 + vl / 2, vx - sw, 455 + vl * 0.8, vx + sw, 455 + vl); c.stroke()

def draw_slime_back(c, t):
    c.set_source_rgba(*hexc('#5cff7a', 0.10)); c.rectangle(0, SURF - 60, W, 80); c.fill()

def draw_slime(c, t):
    c.move_to(0, H)
    for x in range(0, W + 20, 20):
        y = SURF + 10 * math.sin(x * 0.02 + t * 2.2) + 6 * math.sin(x * 0.05 - t * 3)
        c.line_to(x, y)
    c.line_to(W, H); c.close_path()
    gr = cairo.LinearGradient(0, SURF, 0, H)
    gr.add_color_stop_rgb(0, *hexc('#4fe05c')[:3]); gr.add_color_stop_rgb(1, *hexc('#16602a')[:3])
    c.set_source(gr); c.fill()
    c.set_line_width(6); c.set_source_rgba(*hexc('#b6ff9e', 0.8))
    for x in range(0, W + 20, 20):
        y = SURF + 10 * math.sin(x * 0.02 + t * 2.2) + 6 * math.sin(x * 0.05 - t * 3)
        (c.move_to if x == 0 else c.line_to)(x, y)
    c.stroke()
    for bx, ph, r in bubbles:
        k = (t * 0.5 + ph) % 1
        y = H - 40 - k * (H - SURF - 40)
        c.set_source_rgba(0.75, 1, 0.7, 0.55 * (1 - k)); c.set_line_width(3)
        c.arc(bx + 6 * math.sin(t * 3 + ph * 5), y, r * (0.6 + 0.4 * k), 0, 2 * math.pi); c.stroke()

def draw_croc(c, t, look):
    by, sw = croc_geom(t)
    if by > H + 50: return
    jaw = croc_jaw(t)
    hx = 640 + sw  # hinge
    green, dark, belly = hexc('#3e9b4f')[:3], hexc('#2b7039')[:3], hexc('#b9d98a')[:3]
    # lower jaw
    c.save(); c.translate(hx, by)
    c.rotate(-0.0 + jaw * 0.25)
    c.set_source_rgb(*dark); rrect(c, -300, 0, 330, 70, 30); c.fill()
    c.set_source_rgb(*belly); rrect(c, -290, 0, 300, 26, 12); c.fill()
    c.set_source_rgb(1, 1, 1)
    for i in range(6):
        x = -270 + i * 45
        c.move_to(x, 2); c.line_to(x + 14, -24); c.line_to(x + 28, 2); c.close_path(); c.fill()
    c.restore()
    # body behind hinge
    c.set_source_rgb(*green); rrect(c, hx - 40, by - 110, 380, 240, 90); c.fill()
    # bumps
    c.set_source_rgb(*dark)
    for i in range(4):
        c.arc(hx + 40 + i * 70, by - 110, 20, math.pi, 2 * math.pi); c.fill()
    # upper jaw
    c.save(); c.translate(hx, by)
    c.rotate(jaw * 0.75)
    c.set_source_rgb(*green); rrect(c, -330, -100, 380, 105, 45); c.fill()
    c.set_source_rgb(1, 1, 1)
    for i in range(7):
        x = -300 + i * 42
        c.move_to(x, -2); c.line_to(x + 13, 26); c.line_to(x + 26, -2); c.close_path(); c.fill()
    c.set_source_rgb(*dark)
    c.arc(-300, -70, 9, 0, 2 * math.pi); c.fill(); c.arc(-270, -76, 9, 0, 2 * math.pi); c.fill()
    c.restore()
    # eyes
    for ex in (hx + 10, hx + 110):
        ey = by - 150
        c.set_source_rgb(*green); c.arc(ex, ey + 10, 48, math.pi, 2 * math.pi); c.fill()
        c.arc(ex, ey + 10, 48, 0, math.pi); c.fill()
        c.set_source_rgb(*hexc('#ffe14d')[:3]); c.arc(ex, ey, 32, 0, 2 * math.pi); c.fill()
        dx, dy = look[0] - ex, look[1] - ey; d = math.hypot(dx, dy) or 1
        c.set_source_rgb(0.05, 0.05, 0.05); c.save(); c.translate(ex + dx / d * 12, ey + dy / d * 12); c.scale(0.45, 1); c.arc(0, 0, 22, 0, 2 * math.pi); c.fill(); c.restore()
        c.set_source_rgb(*green); c.rectangle(ex - 50, ey - 46, 100, 22); c.fill()  # heavy lid
    # water occlusion line drawn by slime after

def draw_blob(c, t, x, y, vel, mood, squash):
    R = 86
    c.save(); c.translate(x, y)
    sx, sy = 1 + squash, 1 - squash
    c.scale(sx, sy)
    # glow
    c.set_source_rgba(1, 0.6, 0.2, 0.15); c.arc(0, 0, R + 24, 0, 2 * math.pi); c.fill()
    # wobbly body
    c.new_path()
    for i in range(0, 61):
        a = i / 60 * 2 * math.pi
        r = R * (1 + 0.035 * math.sin(a * 3 + t * 5) + 0.02 * math.sin(a * 5 - t * 7))
        px, py = math.cos(a) * r, math.sin(a) * r
        (c.move_to if i == 0 else c.line_to)(px, py)
    c.close_path()
    gr = cairo.RadialGradient(-25, -30, 10, 0, 0, R)
    gr.add_color_stop_rgb(0, *hexc('#ffd36b')[:3]); gr.add_color_stop_rgb(1, *hexc('#ff8a1f')[:3])
    c.set_source(gr); c.fill_preserve()
    c.set_line_width(5); c.set_source_rgb(*hexc('#c45a00')[:3]); c.stroke()
    # cheeks
    c.set_source_rgba(1, 0.35, 0.35, 0.45)
    c.arc(-44, 18, 13, 0, 2 * math.pi); c.fill(); c.arc(44, 18, 13, 0, 2 * math.pi); c.fill()
    # eyes
    blink = (t % 3.7) < 0.08 and mood == 'worried'
    look_y = 6 if mood in ('worried', 'scared') else -2
    for ex in (-24, 24):
        if mood == 'happy':
            c.set_line_width(7); c.set_source_rgb(0.1, 0.06, 0.05)
            c.arc(ex, -6, 13, math.pi * 1.1, math.pi * 1.9); c.stroke()
            continue
        er = 21 if mood == 'scared' else 18
        if blink:
            c.set_line_width(6); c.set_source_rgb(0.1, 0.06, 0.05); c.move_to(ex - 14, -8); c.line_to(ex + 14, -8); c.stroke(); continue
        c.set_source_rgb(1, 1, 1); c.arc(ex, -10, er, 0, 2 * math.pi); c.fill()
        c.set_source_rgb(0.1, 0.06, 0.05); c.arc(ex + 2, -10 + look_y, er * 0.48, 0, 2 * math.pi); c.fill()
        c.set_source_rgb(1, 1, 1); c.arc(ex + 6, -14 + look_y, 4, 0, 2 * math.pi); c.fill()
    # brows
    c.set_line_width(7); c.set_source_rgb(0.25, 0.12, 0.02); c.set_line_cap(cairo.LINE_CAP_ROUND)
    if mood == 'worried':
        c.move_to(-38, -38); c.line_to(-12, -46); c.stroke(); c.move_to(38, -38); c.line_to(12, -46); c.stroke()
    elif mood == 'scared':
        c.move_to(-40, -44); c.line_to(-12, -52); c.stroke(); c.move_to(40, -44); c.line_to(12, -52); c.stroke()
    # mouth
    c.set_source_rgb(0.25, 0.05, 0.05)
    if mood == 'scared':
        c.save(); c.translate(0, 30); c.scale(1, 1.3); c.arc(0, 0, 14, 0, 2 * math.pi); c.restore(); c.fill()
    elif mood == 'worried':
        c.set_line_width(6); c.move_to(-16, 34)
        for i in range(5): c.line_to(-16 + (i + 1) * 8, 34 + (4 if i % 2 == 0 else 0))
        c.stroke()
    else:
        c.arc(0, 22, 22, 0.1, math.pi - 0.1); c.close_path(); c.fill()
        c.set_source_rgb(1, 0.45, 0.5); c.arc(0, 36, 9, 0, math.pi); c.fill()
    c.restore()
    # sweat drop
    if mood in ('worried', 'scared') and t < T_BREAK:
        k = (t * 0.8) % 1
        c.set_source_rgba(0.6, 0.85, 1, 0.9 * (1 - k))
        dx, dy = x + 62, y - 50 + k * 50
        c.move_to(dx, dy - 14); c.curve_to(dx + 10, dy, dx + 8, dy + 10, dx, dy + 10); c.curve_to(dx - 8, dy + 10, dx - 10, dy, dx, dy - 14); c.fill()

def text_center(c, s, y, size, rgb, scale=1.0, shake=(0, 0)):
    c.select_font_face('Poppins', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    c.set_font_size(size)
    ext = c.text_extents(s)
    c.save(); c.translate(W / 2 + shake[0], y + shake[1]); c.scale(scale, scale)
    c.move_to(-ext.width / 2 - ext.x_bearing, ext.height / 2)
    c.text_path(s)
    c.set_line_join(cairo.LINE_JOIN_ROUND)
    c.set_source_rgb(0, 0, 0); c.set_line_width(10); c.stroke_preserve()
    c.set_source_rgb(*rgb); c.fill()
    c.restore()


# ---------------- scene drawing ----------------
bricks = [(x, y) for y in range(HEAD + 20, FLOOR, 46) for x in range(-60 + (30 if (y // 46) % 2 else 0), W, 120)]
dust = [(rng.uniform(0, W), rng.uniform(HEAD, FLOOR), rng.uniform(1.5, 3.5), rng.uniform(0, 6)) for _ in range(60)]

def draw_room(c, t):
    gr = cairo.LinearGradient(0, HEAD, 0, FLOOR)
    gr.add_color_stop_rgb(0, *hexc('#14122a')[:3]); gr.add_color_stop_rgb(1, *hexc('#221c3d')[:3])
    c.set_source(gr); c.rectangle(0, HEAD, W, FLOOR - HEAD); c.fill()
    c.set_line_width(3); c.set_source_rgba(1, 1, 1, 0.035)
    for x, y in bricks:
        rrect(c, x, y, 112, 40, 6); c.stroke()
    # window with moon
    c.set_source_rgb(*hexc('#0b0a1a')[:3]); rrect(c, 640, 470, 260, 200, 14); c.fill()
    c.set_source_rgba(*hexc('#fff3c4', 0.9)); c.arc(820, 535, 34, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*hexc('#3b3358')[:3]); c.set_line_width(10)
    c.rectangle(640, 470, 260, 200); c.stroke(); c.move_to(770, 470); c.line_to(770, 670); c.stroke(); c.move_to(640, 570); c.line_to(900, 570); c.stroke()
    # moonlight shaft on wall
    c.set_source_rgba(0.8, 0.8, 1, 0.04); c.move_to(640, 670); c.line_to(900, 670); c.line_to(980, 1100); c.line_to(560, 1100); c.close_path(); c.fill()
    # catwalk for guard
    c.set_source_rgb(*hexc('#3d3a52')[:3]); c.rectangle(0, LIGHT[1] + 100, 330, 26); c.fill()
    c.set_line_width(6); c.set_source_rgb(*hexc('#2c2a3e')[:3])
    for x in range(20, 330, 50):
        c.move_to(x, LIGHT[1] + 126); c.line_to(x + 25, LIGHT[1] + 200); c.stroke()
    c.move_to(0, LIGHT[1] + 40); c.line_to(330, LIGHT[1] + 40); c.stroke()
    for x in range(10, 330, 40): c.move_to(x, LIGHT[1] + 40); c.line_to(x, LIGHT[1] + 100); c.stroke()
    # floor
    c.set_source_rgb(*hexc('#2e2640')[:3]); c.rectangle(0, FLOOR, W, H - FLOOR); c.fill()
    c.set_source_rgb(*hexc('#3d3354')[:3]); c.rectangle(0, FLOOR, W, 10); c.fill()
    c.set_line_width(3); c.set_source_rgba(0, 0, 0, 0.25)
    for x in range(-200, W, 140): c.move_to(x, FLOOR + 10); c.line_to(x + 160, H); c.stroke()
    for x, y, r, ph in dust:
        c.set_source_rgba(1, 1, 1, 0.05 + 0.04 * math.sin(t + ph)); c.arc(x + 10 * math.sin(t * 0.3 + ph), y, r, 0, 2 * math.pi); c.fill()

def wood_box(c, x0, y0, x1, y1):
    c.set_source_rgb(*hexc('#8a5a2b')[:3]); rrect(c, x0, y0, x1 - x0, y1 - y0, 8); c.fill()
    c.set_source_rgb(*hexc('#6b4220')[:3]); c.set_line_width(10)
    c.rectangle(x0 + 5, y0 + 5, x1 - x0 - 10, y1 - y0 - 10); c.stroke()
    c.move_to(x0 + 10, y0 + 10); c.line_to(x1 - 10, y1 - 10); c.stroke()
    c.set_line_width(3); c.set_source_rgba(0, 0, 0, 0.25)
    for yy in range(int(y0) + 30, int(y1) - 10, 30): c.move_to(x0 + 10, yy); c.line_to(x1 - 10, yy); c.stroke()

def draw_covers(c, t):
    for x0, x1, top, kind in COVERS:
        if kind == 'crate':
            wood_box(c, x0, top, x1, FLOOR)
        elif kind == 'barrel':
            c.set_source_rgb(*hexc('#6e3b1f')[:3]); rrect(c, x0, top, x1 - x0, FLOOR - top, 30); c.fill()
            c.set_source_rgb(*hexc('#8c4d29')[:3]); rrect(c, x0 + 14, top, x1 - x0 - 28, FLOOR - top, 24); c.fill()
            c.set_source_rgb(*hexc('#5a5f6e')[:3])
            for yy in (top + 30, (top + FLOOR) / 2, FLOOR - 40): c.rectangle(x0 - 2, yy, x1 - x0 + 4, 12); c.fill()
        elif kind == 'crates':
            wood_box(c, x0, FLOOR - 200, x1, FLOOR)
            wood_box(c, x0 + 12, top, x1 - 8, FLOOR - 200)
        elif kind == 'can':
            tip = can_tip(t)
            c.save(); c.translate(x1, FLOOR); c.rotate(tip * math.radians(84)); c.translate(-x1, -FLOOR)
            c.set_source_rgb(*hexc('#7d8596')[:3])
            c.move_to(x0, top + 20); c.line_to(x1, top + 20); c.line_to(x1 - 10, FLOOR); c.line_to(x0 + 10, FLOOR); c.close_path(); c.fill()
            c.set_source_rgba(0, 0, 0, 0.18); c.set_line_width(5)
            for xx in range(int(x0) + 25, int(x1) - 10, 24): c.move_to(xx, top + 30); c.line_to(xx, FLOOR - 10); c.stroke()
            c.restore()
            # lid (flies off when tipping)
            lx, ly, la = x0 - 6, top, 0
            if t > T_TIP:
                k = min(1, (t - T_TIP) / 0.7)
                lx += 160 * k; ly += -120 * k + 300 * k * k; la = 2.5 * k
                ly = min(ly, FLOOR - 14)
            c.save(); c.translate(lx + (x1 - x0 + 12) / 2, ly + 12); c.rotate(la)
            c.set_source_rgb(*hexc('#9aa1b0')[:3]); rrect(c, -(x1 - x0 + 12) / 2, -12, x1 - x0 + 12, 24, 10); c.fill()
            c.set_source_rgb(*hexc('#5a5f6e')[:3]); rrect(c, -18, -26, 36, 16, 6); c.fill()
            c.restore()

def beam_poly(t, L=2600):
    a = beam_angle(t)
    return [LIGHT, (LIGHT[0] + math.cos(a - HALF) * L, LIGHT[1] + math.sin(a - HALF) * L),
            (LIGHT[0] + math.cos(a + HALF) * L, LIGHT[1] + math.sin(a + HALF) * L)]

def alarm_on(t): return T_SPOT is not None and t >= T_SPOT

def draw_beam(c, t):
    p = beam_poly(t)
    c.save(); c.rectangle(0, HEAD, W, H - HEAD); c.clip()
    a = beam_angle(t)
    gr = cairo.LinearGradient(LIGHT[0], LIGHT[1], LIGHT[0] + math.cos(a) * 1300, LIGHT[1] + math.sin(a) * 1300)
    col = (1, 0.25, 0.2) if alarm_on(t) else (1, 0.95, 0.6)
    gr.add_color_stop_rgba(0, *col, 0.55); gr.add_color_stop_rgba(1, *col, 0.12)
    c.move_to(*p[0]); c.line_to(*p[1]); c.line_to(*p[2]); c.close_path()
    c.set_source(gr); c.set_operator(cairo.OPERATOR_ADD); c.fill()
    c.set_operator(cairo.OPERATOR_OVER)
    c.restore()

def draw_guard(c, t):
    a = beam_angle(t)
    bx, by = 125, LIGHT[1] - 40
    # legs
    c.set_source_rgb(*hexc('#545b70')[:3]); c.set_line_width(14); c.set_line_cap(cairo.LINE_CAP_ROUND)
    c.move_to(bx - 22, by + 70); c.line_to(bx - 26, LIGHT[1] + 100); c.stroke(); c.move_to(bx + 22, by + 70); c.line_to(bx + 26, LIGHT[1] + 100); c.stroke()
    # body
    c.set_source_rgb(*hexc('#8e97ad')[:3]); rrect(c, bx - 55, by - 20, 110, 100, 26); c.fill()
    c.set_source_rgb(*hexc('#6a7288')[:3]); rrect(c, bx - 35, by + 10, 70, 40, 10); c.fill()
    # head
    c.set_source_rgb(*hexc('#aab3c8')[:3]); rrect(c, bx - 48, by - 110, 96, 80, 24); c.fill()
    c.set_source_rgb(*hexc('#22243a')[:3]); rrect(c, bx - 38, by - 92, 76, 40, 16); c.fill()
    ex, ey = bx + math.cos(a) * 12, by - 72 + math.sin(a) * 6
    eye = (1, 0.15, 0.15) if alarm_on(t) else (0.4, 0.9, 1)
    c.set_source_rgba(*eye, 0.35); c.arc(ex, ey, 22, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*eye); c.arc(ex, ey, 11, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(*hexc('#aab3c8')[:3]); c.set_line_width(5); c.move_to(bx, by - 110); c.line_to(bx, by - 140); c.stroke()
    blink = (t * 2) % 1 < 0.5
    c.set_source_rgb(*((1, 0.2, 0.2) if (blink or alarm_on(t)) else (0.4, 0.2, 0.2))); c.arc(bx, by - 145, 8, 0, 2 * math.pi); c.fill()
    # arm + flashlight
    c.save(); c.translate(LIGHT[0], LIGHT[1]); c.rotate(a)
    c.set_source_rgb(*hexc('#3a3f52')[:3]); rrect(c, -70, -15, 75, 30, 10); c.fill()
    c.set_source_rgb(*hexc('#d8dce6')[:3]); rrect(c, -8, -20, 16, 40, 5); c.fill()
    c.restore()
    c.set_source_rgb(*hexc('#8e97ad')[:3]); c.set_line_width(16)
    c.move_to(bx + 40, by + 20); c.line_to(LIGHT[0] - math.cos(a) * 55, LIGHT[1] - math.sin(a) * 55); c.stroke()

def cage_top(t):
    if T_SPOT is None or t < T_CAGE: return None
    tgt = FLOOR - 210
    k = (t - T_CAGE) / 0.35
    if k < 1: return lerp(HEAD - 260, tgt, k * k)
    if t < T_LIFT: return tgt - 18 * math.exp(-(t - T_CAGE - 0.35) * 9) * abs(math.sin((t - T_CAGE - 0.35) * 20))
    return claw_pos(t)[1] + 150

def draw_cage(c, t, front):
    ct = cage_top(t)
    if ct is None: return
    cx = claw_pos(t)[0] if t >= T_LIFT else 998
    x0, x1 = cx - 95, cx + 95
    c.set_source_rgb(*hexc('#b9c0d0')[:3]); c.set_line_width(8)
    if front:
        for i in range(7):
            x = x0 + i * (x1 - x0) / 6
            c.move_to(x, ct); c.line_to(x, ct + 210); c.stroke()
        c.set_source_rgb(*hexc('#7d8596')[:3]); rrect(c, x0 - 10, ct - 16, x1 - x0 + 20, 22, 8); c.fill()
        rrect(c, x0 - 10, ct + 196, x1 - x0 + 20, 16, 6); c.fill()
        c.set_line_width(9); c.set_source_rgb(*hexc('#c9d0de')[:3]); c.arc(cx, ct - 34, 20, math.pi, 2 * math.pi); c.stroke()

def claw_pos(t):
    if t < T_CLAW_IN: return (1300, 300)
    rx, ry = 998, FLOOR - 210 - 34 - 120
    if t < T_GRAB:
        k = ease((t - T_CLAW_IN) / (T_GRAB - T_CLAW_IN)); return lerp(1300, rx, k), lerp(380, ry, k)
    if t < T_LIFT: return rx, ry
    k = ease((t - T_LIFT) / (T_GONE - T_LIFT)); return lerp(rx, 1300, k), lerp(ry, 60, k)

def draw_claw(c, t):
    if t < T_CLAW_IN: return
    x, y = claw_pos(t)
    c.set_source_rgb(*hexc('#9aa3b5')[:3]); c.set_line_width(8)
    c.move_to(x + 520, HEAD - 20); c.line_to(x, y - 30); c.stroke()
    cl = 0.0 if t < T_GRAB else ease((t - T_GRAB) / 0.15)
    for side in (-1, 1):
        c.save(); c.translate(x + side * 40, y + 30); c.rotate(side * (-0.55 + 0.55 * cl))
        c.set_source_rgb(*hexc('#6f7891')[:3]); c.set_line_width(16); c.set_line_cap(cairo.LINE_CAP_ROUND)
        c.move_to(0, 0); c.line_to(side * 55, 80); c.line_to(side * 20, 150); c.stroke()
        c.restore()
    c.set_source_rgb(*hexc('#c9d0de')[:3]); rrect(c, x - 70, y - 40, 140, 80, 22); c.fill()
    c.set_source_rgb(*hexc('#6f7891')[:3]); rrect(c, x - 70, y + 10, 140, 30, 12); c.fill()
    on = (t * 6) % 1 < 0.5
    c.set_source_rgb(*(hexc('#ff4040')[:3] if on else hexc('#7a2020')[:3])); c.arc(x, y - 10, 13, 0, 2 * math.pi); c.fill()

def draw_eye_icon(c, x, y, open_):
    c.save(); c.translate(x, y)
    col = hexc('#ff4d4d')[:3] if open_ else (0.55, 0.55, 0.6)
    c.set_line_width(6); c.set_source_rgb(*col)
    c.move_to(-34, 0); c.curve_to(-14, -26 if open_ else -4, 14, -26 if open_ else -4, 34, 0)
    if open_:
        c.curve_to(14, 26, -14, 26, -34, 0); c.close_path(); c.stroke()
        c.arc(0, 0, 11, 0, 2 * math.pi); c.fill()
    else:
        c.stroke()
        for dx in (-18, 0, 18): c.move_to(dx, 2); c.line_to(dx * 1.2, 14); c.stroke()
    c.restore()

def draw_header(c, t, f):
    c.set_source_rgb(*hexc('#0d0b14')[:3]); c.rectangle(0, 0, W, HEAD); c.fill()
    if t < T_START:
        k = ease(t / 0.3)
        text_center(c, 'WILL GLOOP', 135, 84, (1, 1, 1), 0.6 + 0.4 * k)
        text_center(c, 'STAY UNSEEN?', 238, 100, hexc('#ffd36b')[:3], 0.6 + 0.4 * k)
        return
    if T_SPOT is None and t >= T_END:
        if t < T_OUTRO:
            text_center(c, 'GLOOP SURVIVED!', 175, 92, hexc('#7dff8a')[:3]); return
    elif T_SPOT is not None and t >= T_SPOT:
        if t < T_TEXT:
            sh = (rng.uniform(-8, 8), rng.uniform(-8, 8))
            text_center(c, 'SPOTTED!', 175, 150, hexc('#ff4d4d')[:3], 1 + 0.05 * math.sin(t * 30), sh); return
        if t < T_OUTRO:
            k = ease((t - T_TEXT) / 0.25)
            text_center(c, 'GLOOP FAILED!', 175, 96, hexc('#ff4d4d')[:3], 0.6 + 0.4 * k); return
    if t >= T_OUTRO:
        k = ease((t - T_OUTRO) / 0.25)
        text_center(c, 'SEE YOU NEXT', 135, 84, (1, 1, 1), 0.6 + 0.4 * k)
        text_center(c, 'CHALLENGE!', 240, 100, hexc('#ffd36b')[:3], 0.6 + 0.4 * k); return
    tm = max(0, T_END - t)
    tcol = (1, 1, 1) if tm > 5 else (hexc('#ffd84a')[:3] if tm > 2 else hexc('#ff4d4d')[:3])
    pulse = 0.12 * max(0, 1 - (tm % 1) / 0.25) if tm < 5 else 0
    text_center(c, f'SURVIVE: {tm:.1f}s', 105, 92, tcol, 1 + pulse)
    d = DET[f]; s = SEEN[f]
    bw, bx, by_ = 620, (W - 620) / 2 + 40, 205
    draw_eye_icon(c, bx - 60, by_ + 26, s)
    c.set_source_rgb(0.2, 0.2, 0.25); rrect(c, bx, by_, bw, 52, 26); c.fill()
    if d > 0.5:
        col = hexc('#ffd84a')[:3] if d < 50 else (hexc('#ff8a3a')[:3] if d < 80 else hexc('#ff3b3b')[:3])
        c.set_source_rgb(*col); rrect(c, bx, by_, max(52, bw * d / 100), 52, 26); c.fill()
    c.select_font_face('Poppins', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD); c.set_font_size(36 * (1.15 if s else 1))
    st = f'DETECTED {int(round(d))}%'; e = c.text_extents(st)
    c.move_to(bx + bw / 2 - e.width / 2 - e.x_bearing, by_ + 26 + e.height / 2); c.text_path(st)
    c.set_source_rgb(0, 0, 0); c.set_line_width(7); c.stroke_preserve(); c.set_source_rgb(1, 1, 1); c.fill()

particles = []
def spawn(x, y, n, col, spd, life):
    for _ in range(n):
        a = rng.uniform(0, 2 * math.pi); s = rng.uniform(0.3, 1) * spd
        particles.append([x, y, math.cos(a) * s, math.sin(a) * s - spd * 0.4, life, life, col])

seen_starts = [i / FPS for i in range(1, N) if SEEN[i] and not SEEN[i - 1]]

def render(f, c):
    t = f / FPS
    shake = (0, 0)
    if T_SPOT and T_SPOT <= t < T_SPOT + 0.3: a = 12; shake = (rng.uniform(-a, a), rng.uniform(-a, a))
    if T_SPOT and T_CAGE + 0.35 <= t < T_CAGE + 0.55: a = 16; shake = (rng.uniform(-a, a), rng.uniform(-a, a))
    if T_TIP + 0.3 <= t < T_TIP + 0.45: a = 7; shake = (rng.uniform(-a, a), rng.uniform(-a, a))
    if T_SPOT and f == int((T_CAGE + 0.35) * FPS): spawn(998, FLOOR - 5, 26, (0.75, 0.7, 0.8), 500, 0.7)
    if f == int((T_TIP + 0.35) * FPS): spawn(1072, FLOOR - 20, 16, (0.75, 0.75, 0.8), 450, 0.6)
    c.save(); c.translate(*shake)
    draw_room(c, t)
    # gloop (behind covers)
    if t >= T_LIFT and T_SPOT:
        gx, gy = claw_pos(t)[0], cage_top(t) + 210 - R * 0.95
        moving = False; peek = 0
    else:
        gx, gy, moving, peek = gloop_pos(t)
    s = SEEN[min(f, N - 1)]
    near = in_cone(gx, gy - 120, t) or in_cone(gx, gy, t)
    if T_SPOT and t >= T_SPOT: mood = 'scared'
    elif s or t > T_TIP or (peek > 0 and near): mood = 'scared'
    elif T_SPOT is None and t >= T_END: mood = 'happy'
    else: mood = 'worried'
    sq = 0.04 * math.sin(t * 6) + (0.12 if not moving and peek == 0 else -0.05)
    c.save(); c.translate(gx, gy); c.scale(R / 86, R / 86); draw_blob(c, t, 0, 0, 0, mood, sq); c.restore()
    draw_covers(c, t)
    draw_cage(c, t, True)
    draw_beam(c, t)
    draw_guard(c, t)
    draw_claw(c, t)
    # "!" popups
    for st in seen_starts:
        if st <= t < st + 0.6 and (T_SPOT is None or st <= T_SPOT):
            k = (t - st) / 0.6
            text_center(c, '!', 0, 1, (1, 1, 1))  # no-op to set font
            c.save(); c.translate(gx - W / 2, gy - 120 - 30 * k)
            text_center(c, '!', 0, 110 * (1 + 0.4 * max(0, 1 - k * 4)), hexc('#ff4d4d')[:3])
            c.restore()
    for p in particles[:]:
        p[0] += p[2] / FPS; p[1] += p[3] / FPS; p[3] += 1400 / FPS; p[4] -= 1 / FPS
        if p[4] <= 0: particles.remove(p); continue
        c.set_source_rgba(*p[6], p[4] / p[5]); c.arc(p[0], p[1], 9 * p[4] / p[5], 0, 2 * math.pi); c.fill()
    # alarm flash
    if alarm_on(t) and t < T_OUTRO:
        c.set_source_rgba(1, 0, 0, 0.16 * (0.5 + 0.5 * math.sin(t * 14))); c.rectangle(0, HEAD, W, H - HEAD); c.fill()
    c.restore()
    draw_header(c, t, f)

if __name__ == '__main__':
    out = sys.argv[1]
    json.dump({'start': T_START, 'end': T_END, 'spot': T_SPOT, 'seen_starts': seen_starts, 'seen': SEEN,
               'hops': [(5.0, 5.8), (9.6, 10.4), (13.6, 14.6)], 'peeks': PEEKS, 'tip': T_TIP, 'cage': T_CAGE,
               'text': T_TEXT, 'claw_in': T_CLAW_IN, 'grab': T_GRAB, 'lift': T_LIFT, 'outro': T_OUTRO,
               'fps': FPS, 'dur': DUR}, open(sys.argv[2], 'w'))
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    if len(sys.argv) > 3:
        want = {int(x * FPS) for x in map(float, sys.argv[3].split(','))}
        for f in range(N):
            c = cairo.Context(surf); render(f, c)
            if f in want: surf.write_to_png(f'{out}_{f:04d}.png')
        sys.exit()
    ff = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgra', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                           '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    for f in range(N):
        c = cairo.Context(surf); render(f, c); surf.flush(); ff.stdin.write(bytes(surf.get_data()))
    ff.stdin.close(); sys.exit(ff.wait())
