#!/usr/bin/env python
# coding=utf-8
#
# Copyright (C) 2024 Mark Hubbart, marcus.erronius@gmail.com

"""
Generates living hinge patterns to be cut with a laser-cutter
To make it easier to understand, I've adopted this terminology:
slit: one single cut ----
gap: distance between consecutive slits
row:  one full row of slits, with gaps in between ----  ----  ----
strip: smallest possible hinge, two rows of slits, 1 strip width apart
    ----  ----
   --  ----  --
hinge: the full hinge, with the given number of strips and slits
   --  ----  --
    ----  ----
   --  ----  --
    ----  ----
   --  ----  --
    ----  ----
   --  ----  --
wide row: a row of slits that cut all the way to the edge
short row: a row of slits that stop short of the edge
start-cut row: a row that starts cut all the way to the edge, but ends short
end-cut row: a row that starts short of the edge, but cuts to the end

For wide rows, the two short end slits are treated as one slit for configuration
purposes. Thus, the following hinge is generated when calling for one slit:
--  --
 ----
--  --
I'll call this a symmetrical cut or symcut

For hinges made from start-cut/end-cut rows, there are no short slits. Thus, a
one-slit hinge looks like this:
 ----
----
 ----
This is an alternating cut, or altcut

"""

from types import SimpleNamespace

import inkex
from inkex import Path, PathElement, Transform
from inkex.paths import Move, move, Line, line, Curve, curve

class MSFlexCut1D(inkex.EffectExtension):
  """Please rename this class, don't keep it unnamed"""
  def add_arguments(self, params):
    params.add_argument("-o", "--orientation",
      help="orient [v]ertically or [h]orizontally",
      type=str, default="h")
    params.add_argument("-u", "--units",
      help="units to use for distances",
      type=str, default="mm")
    params.add_argument("-s", "--slitcount",
      help="minimum slits per row",
      type=int, default=4)
    params.add_argument("-w", "--stripwidth",
      help="minimum strip width",
      type=float, default=3)
    params.add_argument("-g", "--gaplen",
      help="gap between slits",
      type=float, default=3)
    params.add_argument("-f", "--offset",
      help="sideways deviation for shaped slits",
      type=float, default=3)
    params.add_argument("-p", "--shape",
      help="shape of the slit (if offset != 0)",
      type=str, default="angle")
    params.add_argument("-e", "--cutedge",
      help="first cut hits the edge",
      type=inkex.Boolean, default=True)
    params.add_argument("-y", "--symmetrical",
      help="cuts are symmetrical",
      type=inkex.Boolean, default=True)
  
  # swap x and y based on orientation configured
  def reorient(self, x, y):
    return (x,y) if self.config.orient == "h" else (y,x)
  
  # convert from the configured units to viewport units
  def deunit(self, value):
    return self.svg.viewport_to_unit(f"{value}{self.config.units}")
  
  
  def effect(self):
    rect = self.svg.selection[0]
    opt = self.options
    self.config = SimpleNamespace()
    conf = self.config
    du = self.deunit
    
    # direct copies:
    conf.units = opt.units
    conf.slitgap = du(opt.gaplen)
    conf.slitcount = opt.slitcount
    conf.symmetrical = opt.symmetrical
    conf.startwide = opt.cutedge
    conf.orient = opt.orientation
    conf.shape = opt.shape
    conf.offset = 0 if conf.shape == "plain" else du(opt.offset)
    
    # calculations:
    conf.dimensions = self.reorient(rect.width,rect.height)
    conf.slitlen = (conf.dimensions[0]-conf.slitgap*(conf.slitcount+1))/conf.slitcount
    conf.rowcount = int((conf.dimensions[1]-conf.offset)/du(opt.stripwidth))+1
    conf.rowgap = (conf.dimensions[1]-conf.offset)/(conf.rowcount-1)
    
    # generate the path and replace the rectangle with it
    p = Path()
    if conf.shape == "plain":
      p.append(self.flex_cut_1d_plain())
    elif conf.shape == "angle":
      p.append(self.flex_cut_1d_angle())
    elif conf.shape == "wave":
      p.append(self.flex_cut_1d_curve())
    else:
      self.msg("other shaped cuts not yet implemented!")
    
    pe = PathElement.new(p.transform(Transform(f"translate({rect.left},{rect.top})")))
    
    pe.style = rect.style
    pe.transform = rect.transform
    rect.replace_with(pe)
    
    
  
  def flex_cut_1d_plain(self):
    c = self.config
    ro = self.reorient
    p = Path()
    for r in range(c.rowcount):
      if c.symmetrical:
        if c.startwide ^ r%2: # wide row
          for s in range(c.slitcount+1):
            if s == 0:
              p.append(Move(*ro(0,r*c.rowgap)))
              p.append(line(*ro((c.slitlen+c.slitgap)/2,0)))
            elif s == c.slitcount:
              p.append(move(*ro(c.slitgap,0)))
              p.append(line(*ro((c.slitlen+c.slitgap)/2,0)))
            else:
              p.append(move(*ro(c.slitgap,0)))
              p.append(line(*ro(c.slitlen,0)))
        else: # narrow row
          for s in range(c.slitcount):
            if s == 0:
              p.append(Move(*ro(c.slitgap,r*c.rowgap)))
            else:
              p.append(move(*ro(c.slitgap,0)))
            p.append(line(*ro(c.slitlen,0)))
      else: # not symmetrical
        if c.startwide ^ r%2: # flagged for first cut to edge
          p.append(Move(*ro(0,r*c.rowgap)))
        else: # first slit but not cut to edge
          p.append(Move(*ro(c.slitgap, r*c.rowgap)))
        for s in range(c.slitcount):
          p.append(move(*ro(c.slitgap,0))) if s!=0 else None # relative move on subsequent slits
          p.append(line(*ro(c.slitlen,0))) # cut the slit
    return p
                            
  def flex_cut_1d_angle(self):
    c = self.config
    # calculate how much we move sideways for the gap and slit
    c.oslitgap = (c.offset*c.slitgap)/(c.slitgap+c.slitlen)
    c.oslitlen = (c.offset*c.slitlen)/(c.slitgap+c.slitlen)
    ro = self.reorient
    p = Path()
    for r in range(c.rowcount):
      if c.symmetrical:
        if c.startwide ^ r%2: # wide row
          for s in range(c.slitcount+1):
            if s == 0:
              p.append(Move(*ro(0,r*c.rowgap-c.oslitgap)))
              p.append(line(*ro((c.slitlen+c.slitgap)/2,c.oslitlen+c.oslitgap)))
            elif s == c.slitcount:
              p.append(move(*ro(c.slitgap,0)))
              p.append(line(*ro((c.slitlen+c.slitgap)/2,-c.oslitlen-c.oslitgap)))
            else:
              p.append(move(*ro(c.slitgap,0)))
              p.append(line(*ro(c.slitlen/2,-c.oslitlen)))
              p.append(line(*ro(c.slitlen/2,c.oslitlen)))
        else: # narrow row
          for s in range(c.slitcount):
            if s == 0:
              p.append(Move(*ro(c.slitgap,r*c.rowgap+c.oslitgap)))
            else:
              p.append(move(*ro(c.slitgap,0)))
            p.append(line(*ro(c.slitlen/2,c.oslitlen)))
            p.append(line(*ro(c.slitlen/2,-c.oslitlen)))
      else: # not symmetrical
        self.msg("asymmetrical angle cuts not implemented!")
        return
        if c.startwide ^ r%2: # flagged for first cut to edge
          p.append(Move(*ro(0,r*c.rowgap)))
        else: # first slit but not cut to edge
          p.append(Move(*ro(c.slitgap, r*c.rowgap)))
        for s in range(c.slitcount):
          p.append(move(*ro(c.slitgap,0))) if s!=0 else None # relative move on subsequent slits
          p.append(line(*ro(c.slitlen,0))) # cut the slit
    return p
    
  def flex_cut_1d_curve(self):
    c = self.config
    ro = self.reorient
    p = Path()
    for r in range(c.rowcount):
      if c.symmetrical:
        if c.startwide ^ r%2: # wide row
          for s in range(c.slitcount+1):
            if s == 0:
              p.append(Move(*ro(0,r*c.rowgap)))
              p.append(line(*ro(c.slitgap/2,0)))
              p.append(curve(
                *ro(c.slitlen/6,0),
                *ro(c.slitlen/3,c.offset),
                *ro(c.slitlen/2,c.offset)
              ))
            elif s == c.slitcount:
              p.append(move(*ro(c.slitgap,0)))
              p.append(curve(
                *ro(c.slitlen/6,0),
                *ro(c.slitlen/3,-c.offset),
                *ro(c.slitlen/2,-c.offset)
              ))
              p.append(line(*ro(c.slitgap/2,0)))
            else:
              p.append(move(*ro(c.slitgap,0)))
              p.append(curve(
                *ro(c.slitlen/6,0),
                *ro(c.slitlen/3,-c.offset),
                *ro(c.slitlen/2,-c.offset)
              ))
              #p.append(line(*ro(c.slitgap,0)))
              p.append(curve(
                *ro(c.slitlen/6,0),
                *ro(c.slitlen/3,c.offset),
                *ro(c.slitlen/2,c.offset)
              ))
        else: # narrow row
          for s in range(c.slitcount):
            if s == 0:
              p.append(Move(*ro(c.slitgap,r*c.rowgap)))
            else:
              p.append(move(*ro(c.slitgap,0)))
            p.append(curve(
              *ro(c.slitlen/6,0),
              *ro(c.slitlen/3,c.offset),
              *ro(c.slitlen/2,c.offset)
            ))
            #p.append(line(*ro(c.slitgap,0)))
            p.append(curve(
              *ro(c.slitlen/6,0),
              *ro(c.slitlen/3,-c.offset),
              *ro(c.slitlen/2,-c.offset)
            ))
      else: # not symmetrical
        self.msg("asymmetrical curve cuts not implemented!")
        return
        if c.startwide ^ r%2: # flagged for first cut to edge
          p.append(Move(*ro(0,r*c.rowgap)))
        else: # first slit but not cut to edge
          p.append(Move(*ro(c.slitgap, r*c.rowgap)))
        for s in range(c.slitcount):
          p.append(move(*ro(c.slitgap,0))) if s!=0 else None # relative move on subsequent slits
          p.append(line(*ro(c.slitlen,0))) # cut the slit
    return p
    
if __name__ == '__main__':
  MSFlexCut1D().run()

