import sys, math, random, cairo
sys.argv = ['x']
import gloop_croc as g
W, H = 2560, 1440
SX, SY, SW, SH = (W-1546)/2, (H-423)/2, 1546, 423   # safe area
surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); c = cairo.Context(surf)
gr = cairo.LinearGradient(0, 0, 0, H)
gr.add_color_stop_rgb(0, *g.hexc('#0f0c26')[:3]); gr.add_color_stop_rgb(1, *g.hexc('#2e1f55')[:3])
c.set_source(gr); c.paint()
r = random.Random(4)
for _ in range(220):
    c.set_source_rgba(1, 1, .9, r.uniform(.3, .9)); c.arc(r.uniform(0, W), r.uniform(0, H*0.75), r.uniform(1.5, 4), 0, 2*math.pi); c.fill()
# tree silhouettes
c.set_source_rgb(*g.hexc('#1b1538')[:3])
for x in range(-60, W+120, 110):
    s = r.uniform(.7, 1.3); top = 900 - 280*s
    c.move_to(x-85*s, 1000); c.line_to(x, top); c.line_to(x+85*s, 1000); c.close_path(); c.fill()
sl = SY + SH + 40
# moon
c.set_source_rgba(*g.hexc('#fff3c4', .12)); c.arc(SX+SW-120, SY+60, 150, 0, 2*math.pi); c.fill()
c.set_source_rgb(*g.hexc('#fff3c4')[:3]); c.arc(SX+SW-120, SY+60, 85, 0, 2*math.pi); c.fill()
# croc eyes peeking (drawn before slime so slime covers bottom)
for ex in (SX+SW-300, SX+SW-180):
    ey = sl - 18
    c.set_source_rgb(*g.hexc('#3e9b4f')[:3]); c.arc(ex, ey+10, 58, 0, 2*math.pi); c.fill()
    c.set_source_rgb(*g.hexc('#ffe14d')[:3]); c.arc(ex, ey, 36, 0, 2*math.pi); c.fill()
    c.set_source_rgb(.05, .05, .05); c.save(); c.translate(ex-12, ey); c.scale(.45, 1); c.arc(0, 0, 26, 0, 2*math.pi); c.fill(); c.restore()
    c.save(); c.arc(ex, ey, 38, 0, 2*math.pi); c.clip(); c.set_source_rgb(*g.hexc('#3e9b4f')[:3]); c.rectangle(ex-40, ey-40, 80, 26); c.fill(); c.restore()
# slime
sl = SY + SH + 40
c.move_to(0, H)
for x in range(0, W+20, 20): c.line_to(x, sl + 14*math.sin(x*0.012))
c.line_to(W, H); c.close_path()
gg = cairo.LinearGradient(0, sl, 0, H); gg.add_color_stop_rgb(0, *g.hexc('#4fe05c')[:3]); gg.add_color_stop_rgb(1, *g.hexc('#16602a')[:3])
c.set_source(gg); c.fill()
c.set_line_width(8); c.set_source_rgba(*g.hexc('#b6ff9e', .8))
for x in range(0, W+20, 20): (c.move_to if x == 0 else c.line_to)(x, sl + 14*math.sin(x*0.012))
c.stroke()
# rope + gloop hanging at left of safe area
gx, gy = SX + 230, SY + 215
c.set_line_width(22); c.set_source_rgb(*g.hexc('#c79a5b')[:3]); c.set_line_cap(cairo.LINE_CAP_ROUND)
c.move_to(gx, 0); c.line_to(gx, gy-150); c.stroke()
c.set_line_width(4); c.set_source_rgb(*g.hexc('#8f6a37')[:3])
for y in range(10, int(gy-160), 22): c.move_to(gx-9, y); c.line_to(gx+9, y+10); c.stroke()
c.save(); c.translate(gx, gy); c.scale(1.75, 1.75); g.draw_blob(c, 0.3, 0, 0, 0, 'happy', 0.0); c.restore()
# text
def txt(s, x, y, size, rgb, stroke=14):
    c.select_font_face('Poppins', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD); c.set_font_size(size)
    c.move_to(x, y); c.text_path(s); c.set_line_join(cairo.LINE_JOIN_ROUND)
    c.set_source_rgb(0, 0, 0); c.set_line_width(stroke); c.stroke_preserve(); c.set_source_rgb(*rgb); c.fill()
tx = SX + 470
txt('GLOOP', tx, SY + 215, 210, g.hexc('#ffb23a')[:3], 18)
txt('CAN HE SURVIVE?', tx + 8, SY + 305, 74, (1, 1, 1), 10)
txt('NEW CHALLENGE EVERY DAY', tx + 8, SY + 385, 50, g.hexc('#7dff8a')[:3], 8)
surf.write_to_png('../out/gloop_banner.png')
# preview with safe-area box
c.set_source_rgba(1, 0, 0, .8); c.set_line_width(4); c.rectangle(SX, SY, SW, SH); c.stroke()
surf.write_to_png('../out/banner_check.png')
