import sys, math, cairo
sys.argv = ['x']
import gloop_croc as g
S = 1024
surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, S, S); c = cairo.Context(surf)
gr = cairo.RadialGradient(S/2, S/2, 50, S/2, S/2, S*0.72)
gr.add_color_stop_rgb(0, *g.hexc('#4b2d8f')[:3]); gr.add_color_stop_rgb(1, *g.hexc('#140f2e')[:3])
c.set_source(gr); c.paint()
# sun rays
c.save(); c.translate(S/2, S/2)
for i in range(16):
    a = i * 2 * math.pi / 16
    c.move_to(0, 0); c.arc(0, 0, S, a, a + math.pi / 16); c.close_path()
c.set_source_rgba(1, 0.8, 0.4, 0.07); c.fill(); c.restore()
# slime at bottom
c.move_to(0, S)
for x in range(0, S + 20, 16): c.line_to(x, S*0.80 + 14*math.sin(x*0.025))
c.line_to(S, S); c.close_path(); c.set_source_rgb(*g.hexc('#4fe05c')[:3]); c.fill()
# Gloop big
c.save(); c.translate(S/2, S*0.50); c.scale(3.6, 3.6)
g.draw_blob(c, 0.7, 0, 0, 0, 'happy', 0.0)
c.restore()
surf.write_to_png(sys.argv[0] if False else '../out/gloop_pfp.png')
