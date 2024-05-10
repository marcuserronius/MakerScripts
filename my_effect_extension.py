#!/usr/bin/env python
# coding=utf-8
#
# Copyright (C) [YEAR] [YOUR NAME], [YOUR EMAIL]
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
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

import inkex
from inkex import Path, PathElement, Line, Transform
from inkex.paths import Move, Horz, Vert, move, horz, vert

class MakeRedExt(inkex.EffectExtension):
  """Please rename this class, don't keep it unnamed"""
  def add_arguments(self, pars):
    pars.add_argument("-v", "--vertical", type=bool, default=False, help="vertical or horizontal")
    pars.add_argument("-s", "--segments", type=int, default=4, help="Number of segments along width")
    pars.add_argument("-t", "--strips", type=int, default=10, help="Strips")
    pars.add_argument("-g", "--gap", type=float, default=3, help="Gap between cuts")


  def _effect(self):
    s = self.svg.selection
    opt = self.options
    if( len(s)==1 and s[0].tag_name=='rect'):
      (l,t,w,h) = (s[0].left,s[0].top,s[0].width,s[0].height)
      p = Path()
      cutlen = h/opt.segments-opt.gap
      space = w/opt.strips/2
      for x in range(opt.strips*2+1):
        for y in range(opt.segments+1-x%2):
          if x%2==0:
            if y==0:
              p.append(Move(space*x+l,t))
              p.append(vert(cutlen/2))
            elif y==opt.segments:
              p.append(move(0,opt.gap))
              p.append(vert(cutlen/2))
            else:
              p.append(move(0,opt.gap))
              p.append(vert(cutlen))
          else:
            if y==0:
              p.append(Move(space*x+l,t+opt.gap/2))
              p.append(vert(cutlen))
            else:
              p.append(move(0,opt.gap))
              p.append(vert(cutlen))
            
      pe = PathElement.new(p)
      pe.style = s[0].style
      pe.transform = s[0].transform
      s[0].replace_with(pe)
  
  def hinge_standard(self, slitlen, slitcount, gaplen, stripwidth, rowcount, startshort=False, altcut=False):
    p = Path()
    for x in range(rowcount):
      # does the cut start at the leading edge?
      start = (x + (not startshort))%2
      # is it a wide row?
      wide = start * (not altcut)
      for y in range(slitcount+wide): # add one slit for wide rows
        # First move to position
        if y!=0: # if not first slit, relative move to gap length
          p.append(move(0,gaplen))
        elif start: # first slit cut to edge
          p.append(Move(stripwidth*x,0))
        elif altcut: # full gap at start for alternating cut
          p.append(Move(stripwidth*x,gaplen))
        else: # half gap at start for symetrical cut
          p.append(Move(stripwidth*x,gaplen/2))
        # then make the slit
        if not altcut and start and (y==0 or y==slitcount): # half-length slit
          p.append(vert(slitlen/2))
        else: # full-length slit
          p.append(vert(slitlen))
    return p
  
  def effect(self):
    opt = self.options
    s = self.svg.selection
    if len(s)==1 and s[0].tag_name=='rect':  
      rect = s[0]
      p = self.hinge_standard(
        rect.height/opt.segments-opt.gap, opt.segments,
        opt.gap, rect.width/opt.strips, opt.strips+1)
      pe = PathElement.new(p.transform(Transform(f"translate({rect.left},{rect.top})")))
      pe.style = rect.style
      pe.transform = rect.transform
      rect.replace_with(pe)
if __name__ == '__main__':
  MakeRedExt().run()

