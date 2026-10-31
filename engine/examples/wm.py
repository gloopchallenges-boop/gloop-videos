import sys, math, cairo
sys.argv = ['x']
import gloop_croc as g
S = 300
surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, S, S); c = cairo.Context(surf)
c.set_source_rgba(*g.hexc('#140f2e', 0.85)); c.arc(S/2, S/2, 146, 0, 2*math.pi); c.fill()
c.set_source_rgb(*g.hexc('#ffb23a')[:3]); c.set_line_width(8); c.arc(S/2, S/2, 140, 0, 2*math.pi); c.stroke()
c.save(); c.translate(S/2, S/2 - 22); c.scale(0.95, 0.95); g.draw_blob(c, 0.3, 0, 0, 0, 'happy', 0.0); c.restore()
c.select_font_face('Poppins', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD); c.set_font_size(44)
e = c.text_extents('SUB!'); c.move_to(S/2 - e.width/2 - e.x_bearing, 268); c.text_path('SUB!')
c.set_source_rgb(0, 0, 0); c.set_line_width(8); c.stroke_preserve(); c.set_source_rgb(*g.hexc('#7dff8a')[:3]); c.fill()
surf.write_to_png('/mnt/user-data/outputs/gloop_watermark.png')
