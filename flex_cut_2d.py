
import inkex
from inkex import Path, PathElement, Transform
from inkex.paths import Move, move, Horz, horz, Vert, vert, Line, line


class MSFlexCut2D(inkex.EffectExtension):
  """Please rename this class, don't keep it unnamed"""
  def add_arguments(self, params):
    params.add_argument("-u", "--units",
      help="units to use for distances",
      type=str, default="mm")
    params.add_argument("-g", "--gap",
      help="gap between cuts",
      type=float, default=3)
    params.add_argument("-s", "--size",
      help="size of the spiral parts (bigger is more flexible)",
      type=int, default=3)
    params.add_argument("-w", "--width",
      help="number of sections across",
      type=int, default=5)
    params.add_argument("-j", "--height",
      help="number of sections tall",
      type=int, default=5)
    params.add_argument("-p", "--shape",
      help="shape of the spiral segments",
      type=str, default="square")

  
  # convert from the configured units to viewport units
  def deunit(self, value):
    return self.svg.viewport_to_unit(f"{value}{self.config.units}")
  
  def effect(self):
    p = Path()
    opt = self.options
    if opt.shape == 'square':
      p.append(self.flex_cut_2d_square())
    elif opt.shape == 'hex':
      p.append(self.flex_cut_2d_hex())
    else:
      self.msg("other shapes not yet implemented!")
    pe = PathElement.new(p)
    pe.style={"stroke-width":"0.02mm", "stroke": "black", "fill":"none"}
    self.svg.append(pe)
    
  def flex_cut_2d_square(self):
    opt = self.options
    p = Path()
    
    # make 1 segment
    seg=Path()
    seg.append(Move(1,1))
    for s in range(1, opt.size+1):
      dir = -1 if s%2 == 1 else 1
      seg.append(horz(dir*(4*s)))
      seg.append(vert(dir*(4*s)))
    seg.append(seg.transform(Transform('rotate(180)')))
    w = opt.size*2+1
    
    for x in range(opt.width):
      for y in range(opt.height):
        t = f"translate({w+w*x*2},{w+w*y*2})"
        t = t + " rotate(90)" if x%2^y%2 else t
        p.append(seg.transform(Transform(t)))
    return p

  def flex_cut_2d_hex(self):
    opt = self.options
    p = Path()
    
    # make 1 segment
    th = (3**0.5)*0.5
    seg_part=Path()
    seg_part.append(Move(0,-1))
    for s in range(1, opt.size+1):
      if s%3 == 1:
        seg_part.append(line(th*(s+1),0.5+0.5*s))
        seg_part.append(line(0,1*s))
      elif s%3 == 2:
        seg_part.append(line(-th*(s+1),0.5+0.5*s))
        seg_part.append(line(-th*s,-0.5*s))
      else:
        seg_part.append(line(0,-1-s))
        seg_part.append(line(th*s,-0.5*s))
    seg = Path()
    seg.append(seg_part)
    seg.append(seg_part.transform(Transform('rotate(120)')))
    seg.append(seg_part.transform(Transform('rotate(240)')))
    w = opt.size+1
    # 3, 4.5, 6
    for x in range(opt.width):
      for y in range(opt.height):
        
        t = f"translate({w*(x+0.5*(y%2))*th*2},{(opt.size+1)*1.5*y})"
        p.append(seg.transform(Transform(t)))
    return p
    
    
    
if __name__ == '__main__':
  MSFlexCut2D().run()

