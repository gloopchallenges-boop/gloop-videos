import cairo, math, random, subprocess, sys, json
W, H, FPS, DUR = 1080, 1920, 30, 22.0
N = int(DUR * FPS)
HEAD = 330
ANCH = (560, 440)
L0 = 560
SURF = 1580
rng = random.Random(7)

def ease(x): x = max(0, min(1, x)); return x * x * (3 - 2 * x)

# ---------------- timeline ----------------
T_START, TIME_LIMIT = 2.6, 15.0
T_END = T_START + TIME_LIMIT          # timer hits 0
T_CLAW_IN = T_END - 1.4               # claw appears & hovers
T_DART = T_END - 0.15
T_GRAB = T_END
T_BREAK = T_END + 0.15                # rope snaps right as claw holds him
T_LIFT = T_END + 0.35
T_GONE = T_END + 2.2
T_SURV = T_END + 0.7
T_OUTRO = T_END + 2.0
bounces = []; bt, iv = 2.6, 1.05
while bt < T_END - 0.75:
    bounces.append(bt); bt += iv; iv = max(0.55, iv * 0.94)
B = [1.7] + bounces
HOP = [0] + [rng.uniform(70, 170) for _ in bounces]
dmg = [HOP[j] * rng.uniform(0.8, 1.2) for j in range(1, len(B))]
sc = 97 / sum(dmg); dmg = [d * sc for d in dmg]
snap_t = bounces
snap_p = []; acc = 100
for d in dmg:
    acc -= d; snap_p.append(max(2, round(acc)))
DMG_SHOW = [max(1, round(d)) for d in dmg]
chomps = [10.0, 13.4, 16.1, T_END + 0.45]

def pct_at(t):
    if t >= T_BREAK: return 0
    v = 100
    for st, sp in zip(snap_t, snap_p):
        if t >= st: v = v + (sp - v) * min(1, (t - st) / 0.15)
    return v

def timer_at(t):
    return max(0.0, TIME_LIMIT - max(0, t - T_START))

def last_snap(t):
    ls = None
    for st in snap_t + [T_BREAK]:
        if t >= st: ls = st
    return ls

def croc_rise(t):
    if t < 3.5: return 0.0
    if t < 6.5: return 0.18 * ease((t - 3.5) / 3)
    if t < 9.5: return 0.18 + 0.82 * ease((t - 6.5) / 3)
    if t > T_END + 1.2: return 1 - 0.8 * ease((t - T_END - 1.2) / 1.5)
    return 1.0

def croc_jaw(t):
    j = 0.0
    for c in chomps:
        if c - 0.6 <= t < c: j = max(j, ease((t - (c - 0.6)) / 0.45))
        elif c <= t < c + 0.12: j = max(j, 1 - (t - c) / 0.12)
    return max(0, min(1, j))

def croc_geom(t):
    rise = croc_rise(t)
    lunge = 0
    lc = chomps[-1]
    if lc - 0.5 < t < lc + 0.4: lunge = 90 * math.sin(math.pi * (t - (lc - 0.5)) / 0.9)
    return SURF + 260 - rise * 390 - lunge, 8 * math.sin(t * 1.3)

# ---------------- hop model ----------------
def hang(t):
    th = 0.06 * math.sin(t * 1.7)
    yoff = 0.0
    for j in range(len(B)):
        if B[j] <= t and (j == len(B) - 1 or t < B[j + 1]):
            if j < len(B) - 1:
                k = (t - B[j]) / (B[j + 1] - B[j])
                yoff = -HOP[j + 1] * 4 * k * (1 - k)
            if j > 0:
                d = t - B[j]
                yoff += HOP[j] * 0.3 * math.exp(-d * 9) * math.sin(d * 28)
    return th, yoff

def rope_geom(t):
    th, yoff = hang(t)
    return ANCH[0] + L0 * math.sin(th), ANCH[1] + L0 * math.cos(th) + yoff, max(0, -yoff)

def bez(ax, ay, bx, by, slack):
    mx, my = (ax + bx) / 2, (ay + by) / 2
    L = math.hypot(bx - ax, by - ay) or 1
    nx, ny = -(by - ay) / L, (bx - ax) / L
    cx, cy = mx + nx * slack * 0.6, my + ny * slack * 0.6
    return lambda u: ((1 - u) ** 2 * ax + 2 * (1 - u) * u * cx + u * u * bx, (1 - u) ** 2 * ay + 2 * (1 - u) * u * cy + u * u * by)

GRAB_POS = rope_geom(T_GRAB)[:2]

def claw_pos(t):
    """claw head centre"""
    if t < T_CLAW_IN: return None
    if t < T_DART:
        bx, by, _ = rope_geom(t)
        hx, hy = bx + 190, by - 300
        k = ease((t - T_CLAW_IN) / 0.7)
        return 1250 + (hx - 1250) * k, 380 + (hy - 380) * k + 10 * math.sin(t * 5)
    if t < T_GRAB:
        bx, by, _ = rope_geom(T_DART)
        k = ease((t - T_DART) / (T_GRAB - T_DART))
        sx, sy = bx + 190, by - 300 + 10 * math.sin(T_DART * 5)
        return sx + (GRAB_POS[0] - sx) * k, sy + (GRAB_POS[1] - 125 - sy) * k
    if t < T_LIFT: return GRAB_POS[0], GRAB_POS[1] - 125
    k = ease((t - T_LIFT) / (T_GONE - T_LIFT))
    sx, sy = GRAB_POS[0], GRAB_POS[1] - 125
    return sx + (1250 - sx) * k, sy + (150 - sy) * k

def claw_close(t):
    return 0.0 if t < T_GRAB else ease((t - T_GRAB) / 0.12)

def blob_pos(t):
    if t < T_GRAB: return rope_geom(t)[:2]
    cx, cy = claw_pos(t)
    sw = 0
    if t > T_LIFT: sw = 18 * math.sin((t - T_LIFT) * 7) * math.exp(-(t - T_LIFT) * 1.2)
    return cx + sw, cy + 125
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

def draw_claw(c, t):
    p = claw_pos(t)
    if p is None: return
    x, y = p
    c.set_source_rgb(*hexc('#9aa3b5')[:3]); c.set_line_width(8)
    c.move_to(x + 520, HEAD - 20); c.line_to(x, y - 30); c.stroke()
    cl = claw_close(t)
    for side in (-1, 1):
        c.save(); c.translate(x + side * 40, y + 30); c.rotate(side * (-0.55 + 0.55 * cl))
        c.set_source_rgb(*hexc('#6f7891')[:3]); c.set_line_width(16); c.set_line_cap(cairo.LINE_CAP_ROUND)
        c.move_to(0, 0); c.line_to(side * 55, 80); c.line_to(side * 20, 150); c.stroke()
        c.restore()
    c.set_source_rgb(*hexc('#c9d0de')[:3]); rrect(c, x - 70, y - 40, 140, 80, 22); c.fill()
    c.set_source_rgb(*hexc('#6f7891')[:3]); rrect(c, x - 70, y + 10, 140, 30, 12); c.fill()
    on = (t * 6) % 1 < 0.5
    c.set_source_rgb(*(hexc('#ff4040')[:3] if on else hexc('#7a2020')[:3])); c.arc(x, y - 10, 13, 0, 2 * math.pi); c.fill()

def draw_rope(c, t, bx, by, pct):
    ax, ay = ANCH
    c.set_line_cap(cairo.LINE_CAP_ROUND); c.set_line_join(cairo.LINE_JOIN_ROUND)
    if t >= T_BREAK:
        k = min(1, (t - T_BREAK) / 0.6)
        P = bez(ax, ay, GRAB_POS[0], GRAB_POS[1] - 86, 0)
        mx, my = P(0.42)
        sw = 40 * math.sin((t - T_BREAK) * 7) * math.exp(-(t - T_BREAK) * 1.5)
        c.set_line_width(17); c.set_source_rgb(*hexc('#c79a5b')[:3])
        c.move_to(ax, ay); c.curve_to(ax, ay + 60, mx + sw, my - 60 - 40 * k, mx + sw, my - 40 * k); c.stroke()
        return
    _, _, slack = rope_geom(t)
    P = bez(ax, ay, bx, by - 86, slack)
    pts = [P(i / 40) for i in range(41)]
    c.set_line_width(17); c.set_source_rgb(*hexc('#c79a5b')[:3])
    c.move_to(*pts[0]); [c.line_to(*q) for q in pts[1:]]; c.stroke()
    c.set_line_width(3); c.set_source_rgb(*hexc('#8f6a37')[:3])
    for i in range(1, 40, 2):
        (x1, y1), (x2, y2) = pts[i], pts[i + 1]
        L = math.hypot(x2 - x1, y2 - y1) or 1; nx, ny = -(y2 - y1) / L, (x2 - x1) / L
        c.move_to(x1 - nx * 7, y1 - ny * 7); c.line_to(x2 + nx * 7, y2 + ny * 7); c.stroke()
    fx, fy = P(0.42); gx, gy = P(0.47)
    L = math.hypot(gx - fx, gy - fy) or 1; ux, uy = (gx - fx) / L, (gy - fy) / L; nx, ny = -uy, ux
    c.set_line_width(22); c.set_source_rgb(*hexc('#2a1d4a')[:3])
    c.move_to(fx - ux * 26, fy - uy * 26); c.line_to(fx + ux * 26, fy + uy * 26); c.stroke()
    c.set_line_width(4 + 13 * pct / 100); c.set_source_rgb(*hexc('#e2b877')[:3])
    c.move_to(fx - ux * 30, fy - uy * 30); c.line_to(fx + ux * 30, fy + uy * 30); c.stroke()
    r2 = random.Random(3); c.set_line_width(2.5)
    for i in range(int((100 - pct) / 6) + 2):
        side = 1 if i % 2 else -1
        off = r2.uniform(-24, 24); ln = r2.uniform(14, 34); wig = 4 * math.sin(t * 9 + i)
        px, py = fx + ux * off, fy + uy * off
        c.move_to(px, py); c.curve_to(px + nx * side * ln * 0.5, py + ny * side * ln * 0.5, px + nx * side * ln + wig, py + ny * side * ln, px + nx * side * ln + ux * 8 + wig, py + ny * side * ln + uy * 8); c.stroke()
    c.set_source_rgb(*hexc('#a97f45')[:3]); c.arc(bx, by - 86, 14, 0, 2 * math.pi); c.fill()
    c.arc(ax, ay + 6, 15, 0, 2 * math.pi); c.fill()

def fray_point(t):
    t = min(t, T_BREAK)
    bx, by, slack = rope_geom(min(t, T_GRAB))
    return bez(ANCH[0], ANCH[1], bx, by - 86, slack)(0.42)

def draw_header(c, t):
    c.set_source_rgb(*hexc('#0d0b14')[:3]); c.rectangle(0, 0, W, HEAD); c.fill()
    if t < T_START:
        k = ease(t / 0.3)
        text_center(c, 'WILL GLOOP SURVIVE', 140, 72, (1, 1, 1), 0.6 + 0.4 * k)
        text_center(c, 'THE CROCODILE?', 235, 90, hexc('#ffd36b')[:3], 0.6 + 0.4 * k)
        return
    if t < T_END:
        tm = timer_at(t)
        tcol = (1, 1, 1) if tm > 5 else (hexc('#ffd84a')[:3] if tm > 2 else hexc('#ff4d4d')[:3])
        pulse = 0.12 * max(0, 1 - (tm % 1) / 0.25) if tm < 5 else 0
        text_center(c, f'SURVIVE: {tm:.1f}s', 105, 92, tcol, 1 + pulse)
        pct = pct_at(t); ls = last_snap(t)
        pop = max(0, 1 - (t - ls) / 0.25) if ls is not None else 0
        col = hexc('#7dff8a')[:3] if pct > 60 else (hexc('#ffd84a')[:3] if pct > 30 else hexc('#ff4d4d')[:3])
        bw, bx, by_ = 700, (W - 700) / 2, 205
        c.set_source_rgb(0.2, 0.2, 0.25); rrect(c, bx, by_, bw, 52, 26); c.fill()
        if pct > 0:
            c.set_source_rgb(*col); rrect(c, bx, by_, max(52, bw * pct / 100), 52, 26); c.fill()
        c.select_font_face('Poppins', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD); c.set_font_size(36 * (1 + 0.2 * pop))
        s = f'ROPE {int(round(pct))}%'; e = c.text_extents(s)
        c.move_to(W / 2 - e.width / 2 - e.x_bearing, by_ + 26 + e.height / 2); c.text_path(s)
        c.set_source_rgb(0, 0, 0); c.set_line_width(7); c.stroke_preserve(); c.set_source_rgb(1, 1, 1); c.fill()
        return
    if t < T_SURV:
        k = ease((t - T_END) / 0.15)
        text_center(c, 'TIME!', 175, 150, hexc('#7dff8a')[:3], 0.5 + 0.5 * k + 0.05 * math.sin(t * 25))
        return
    if t < T_OUTRO:
        k = ease((t - T_SURV) / 0.25)
        text_center(c, 'GLOOP SURVIVED!', 175, 92, hexc('#7dff8a')[:3], 0.6 + 0.4 * k)
        return
    k = ease((t - T_OUTRO) / 0.25)
    text_center(c, 'SEE YOU NEXT', 135, 84, (1, 1, 1), 0.6 + 0.4 * k)
    text_center(c, 'CHALLENGE!', 240, 100, hexc('#ffd36b')[:3], 0.6 + 0.4 * k)

particles = []
def spawn(x, y, n, col, spd, life, kind='dot'):
    for _ in range(n):
        a = rng.uniform(0, 2 * math.pi); s = rng.uniform(0.3, 1) * spd
        particles.append([x, y, math.cos(a) * s, math.sin(a) * s - spd * 0.3, life, life, col, kind])

def render(f, c):
    t = f / FPS
    ls = last_snap(t); shake = (0, 0)
    if ls is not None and t - ls < 0.2:
        a = (1 - (t - ls) / 0.2) * (14 if ls == T_BREAK else 6)
        shake = (rng.uniform(-a, a), rng.uniform(-a, a))
    if f in {int(s * FPS) for s in snap_t}:
        fx, fy = fray_point(t); spawn(fx, fy, 10, hexc('#e2b877')[:3], 450, 0.8, 'fiber')
    if f == int(T_BREAK * FPS):
        fx, fy = fray_point(t); spawn(fx, fy, 30, hexc('#e2b877')[:3], 900, 0.8, 'fiber')
    if f == int(T_GRAB * FPS):
        spawn(GRAB_POS[0], GRAB_POS[1] - 60, 20, (1, 1, 0.7), 650, 0.6, 'star')
    for cc in chomps:
        if f == int(cc * FPS):
            by, sw = croc_geom(cc); spawn(640 - 330 + sw, by - 20, 14, (0.6, 1, 0.6), 500, 0.6)
    c.save(); c.translate(*shake)
    draw_bg(c, t); draw_slime_back(c, t)
    bx, by = blob_pos(t)
    pct = pct_at(t)
    draw_rope(c, t, bx, by, pct)
    draw_croc(c, t, (bx, by))
    draw_slime(c, t)
    if t < T_GRAB:
        scared = (ls is not None and t - ls < 0.5) or (t > 9.4 and any(cc - 0.6 < t < cc + 0.4 for cc in chomps)) or t > T_CLAW_IN
        mood = 'scared' if scared else 'worried'
        squash = 0.04 * math.sin(t * 6)
    elif t < T_SURV:
        mood = 'scared'; squash = -0.05
    else:
        mood = 'happy'; squash = 0.03 * math.sin(t * 8)
    draw_blob(c, t, bx, by, 0, mood, squash)
    draw_claw(c, t)
    for j, bt_ in enumerate(snap_t):
        if bt_ <= t < bt_ + 0.9:
            k = (t - bt_) / 0.9
            fx, fy = fray_point(bt_)
            c.save(); c.translate(fx + 60, fy - 10 - 70 * k)
            c.select_font_face('Poppins', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD); c.set_font_size(56 * (1 + 0.3 * max(0, 1 - k * 5)))
            c.move_to(0, 0); c.text_path(f'-{DMG_SHOW[j]}%')
            c.set_source_rgba(0, 0, 0, 1 - k); c.set_line_width(8); c.stroke_preserve()
            c.set_source_rgba(1, 0.3, 0.3, 1 - k); c.fill(); c.restore()
    for p in particles[:]:
        p[0] += p[2] / FPS; p[1] += p[3] / FPS; p[3] += 1600 / FPS; p[4] -= 1 / FPS
        if p[4] <= 0: particles.remove(p); continue
        a = p[4] / p[5]; c.set_source_rgba(*p[6], a)
        if p[7] == 'fiber':
            c.set_line_width(3); c.move_to(p[0], p[1]); c.line_to(p[0] - p[2] * 0.03, p[1] - p[3] * 0.03); c.stroke()
        elif p[7] == 'star':
            s = 10 * a; c.move_to(p[0], p[1] - s * 2); c.line_to(p[0] + s * 0.6, p[1]); c.line_to(p[0], p[1] + s * 2); c.line_to(p[0] - s * 0.6, p[1]); c.close_path(); c.fill()
        else:
            c.arc(p[0], p[1], 8 * a, 0, 2 * math.pi); c.fill()
    if T_BREAK <= t < T_BREAK + 0.6:
        k = (t - T_BREAK) / 0.6
        text_center(c, 'SNAP!', 640 - 60 * k, 110, hexc('#ff4d4d')[:3], 0.7 + 0.5 * ease(k * 3))
    c.restore()
    draw_header(c, t)

if __name__ == '__main__':
    out = sys.argv[1]
    json.dump({'bounces': snap_t, 'break': T_BREAK, 'end': T_END, 'claw_in': T_CLAW_IN, 'grab': T_GRAB, 'lift': T_LIFT,
               'chomps': chomps, 'outro': T_OUTRO, 'start': T_START, 'dur': DUR}, open(sys.argv[2], 'w'))
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
