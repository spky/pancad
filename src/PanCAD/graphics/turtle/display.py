import math
import turtle

import numpy as np

from PanCAD.geometry.point import Point
from PanCAD.geometry.line import Line


class TurtleWindow:
    
    def __init__(self, screen_title: str=None, *,
                 screen_size: tuple[int, int]=None, speed: int=0):
        self.turtle = turtle.Turtle()
        turtle.colormode(255)
        if screen_title is not None: self.screen_title = screen_title
        if screen_size is not None:
            self.screen_size = screen_size
        else:
            self.screen_size = self.turtle.screen.screensize()
        self.turtle.speed(speed)
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
    
    def coordinate_system(self, horizontal_division: int, vertical_division: int,
                          *,
                          major_line_rgb: tuple=(0, 0, 0),
                          major_line_thickness: float=0.5,
                          minor_line_rgb: tuple=(220, 220, 220),
                          minor_line_thickness: float=0.25):
        
        # Minor Lines
        self.turtle.pensize(minor_line_thickness)
        self.turtle.color(minor_line_rgb)
        width, height = self.screen_size
        
        print(width, height)
        no_horizontal_lines = math.floor(height / 2 / vertical_division)
        no_vertical_lines = math.floor(width / 2 / horizontal_division)
        print(no_horizontal_lines, no_vertical_lines)
        
        # if width % x_division == 0: no_horizontal_lines -= 1
        # if height % y_division == 0: no_vertical_lines -= 1
        
        # # Minor Horizontal Lines
        for i in range(1, no_horizontal_lines):
            y_value = i*vertical_division
            self.draw_line(Line.from_two_points((0, y_value), (1, y_value)))
            self.draw_line(Line.from_two_points((0, -y_value), (1, -y_value)))
        
        # Minor Horizontal Lines
        for i in range(1, no_vertical_lines):
            x_value = i*horizontal_division
            self.draw_line(Line.from_two_points((x_value, 0), (x_value, 1)))
            self.draw_line(Line.from_two_points((-x_value, 0), (-x_value, 1)))
        
        # Major Lines
        self.turtle.pensize(major_line_thickness)
        self.turtle.color(major_line_rgb)
        self.draw_line(Line.from_two_points((0, 0), (1, 0)))
        self.draw_line(Line.from_two_points((0, 0), (0, 1)))
