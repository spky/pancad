import math
import turtle

import numpy as np

from PanCAD.geometry.point import Point
from PanCAD.geometry.line import Line


class TurtleWindow:
    
    def __init__(self, screen_title: str=None, *,
                 screen_size: tuple[int, int]=None):
        self.turtle = turtle.Turtle()
        if screen_title is not None: self.screen_title = screen_title
        
        if screen_size is not None:
            self.screen_size = screen_size
        else:
            self.screen_size = self.turtle.screen.screensize()
        self.turtle.hideturtle()
    
    # Getters #
    @property
    def screen_size(self) -> tuple:
        return self._screen_size
    
    @property
    def screen_title(self) -> str:
        return self._screen_title
    
    # Setters #
    @screen_size.setter
    def screen_size(self, value: tuple):
        if len(value) != 2:
            raise ValueError("screen_size can only be 2 elements long, "
                             f"given {len(value)}")
        self._screen_size = value
        self.turtle.screen.screensize(*value)
        max_x = round(value[0]/2)
        max_y = round(value[1]/2)
        
        top_left = Point(-max_x, max_y)
        top_right = Point(max_x, max_y)
        bot_left = Point(-max_x, -max_y)
        bot_right = Point(max_x, -max_y)
        
        self._boundaries = {
            "top": Line.from_two_points(top_left, top_right),
            "bottom": Line.from_two_points(bot_left, bot_right),
            "left": Line.from_two_points(bot_left, top_left),
            "right": Line.from_two_points(bot_right, top_right),
        }
    
    @screen_title.setter
    def screen_title(self, value: str):
        self._screen_title = value
        self.turtle.screen.title(value)
    
    # Public Methods #
    def draw_line(self, line: Line):
        intersections = []
        norms = []
        for b in self._boundaries:
            pt = line.get_intersection(self._boundaries[b])
            if pt is None:
                intersections.append(pt)
                norms.append(math.inf)
            else:
                intersections.append(pt)
                norms.append(pt.r)
        
        pt_1 = intersections[norms.index(min(norms))]
        norms.pop(norms.index(min(norms)))
        intersections.pop(norms.index(min(norms)))
        pt_2 = intersections[norms.index(min(norms))]
        
        initial_position = self.turtle.pos()
        self.turtle.penup()
        self.turtle.setposition(tuple(pt_1))
        self.turtle.pendown()
        self.turtle.setposition(tuple(pt_2))
        self.turtle.penup()
        self.turtle.setposition(initial_position)