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
    params.add_argument("-u", "--units",
      help="units to use for distances",
      type=str, default="mm")
    params.add_argument("-t", "--turns",
      help="number of turns the spiral cut makes",
      type=float, default=1.5)
    params.add_argument("-c", "--cuts",
      help="number of spiral cuts to make",
      type=int, default=3)
    params.add_argument("-g", "--gap",
      help="distance between cuts",
      type=float, default=3)
    params.add_argument("-p", "--shape",
      help="shape of the spiral",
      type=str, default="round")
    
  # convert from the configured units to viewport units
  def deunit(self, value):
    return self.svg.viewport_to_unit(f"{value}{self.config.units}")
  
  
  def effect(self):
    center = self.svg.selection[0]
    opt = self.options
    self.config = SimpleNamespace()
    conf = self.config
    du = self.deunit
    
    # direct copies:
    conf.units = opt.units
    conf.turns = opt.turns
    conf.cuts = opt.cuts
    conf.gap = du(opt.gap)
    conf.shape = opt.shape
    
    # calculations:
    conf.dimensions = (center.width,center.height)
    
    # generate the paths
    p = Path()
    if conf.shape == "round":
      p.append(self.flex_cut_button())
    else:
      self.msg("other shaped cuts not yet implemented!")
    
    t = (center.left+center.width/2, center.top+center.height/2)
    pe = PathElement.new(p.transform(Transform(f"translate{t[0],t[1]}")))
    pe.set_random_id(prefix:"flexbutton")
    pe.style = {"fill":"none","stroke":"black","stroke-width":conf.gap/4}
    
    g = GroupElement(pe)
    parent = center.ancestors[0]
    center.addnext(g)
    parent.remove(center)
    g.append(center)
  
  def flex_cut_button(self):
    p = Path()
    
    return p
    
if __name__ == '__main__':
  MSFlexCut1D().run()

