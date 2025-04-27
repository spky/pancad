"""A modules providing a TurtleWindow class that can draw PanCAD geometry. 
Intended primarily for developing and testing PanCAD, but can also be 
used to view the quality of CAD sketch imports.
"""

import math
import turtle

import numpy as np

from PanCAD.geometry.point import Point
from PanCAD.geometry.line import Line
from PanCAD.geometry.line_segment import LineSegment

class TurtleWindow:
    """A class representing the window that python's turtle library creates. 
    This class extends turtle's functionality so that it can also draw 
    PanCAD objects.
    
    :param screen_title: The turtle window's title
    :param screen_size: The turtle window's screen size
    :param speed: The speed of turtle updates, defaults to 0 (fastest execution)
    :param pensize: The size of the turtle's pen
    :param pencolor: The pencolor and fill color of the turtle
    """
    def __init__(self, screen_title: str=None, *,
                 screen_size: tuple[int, int]=None, speed: int=0,
                 pensize: int=None, pencolor: tuple[int, int, int]=(0, 0, 0)):
        self.turtle = turtle.Turtle()
        turtle.colormode(255)
        self.pencolor = pencolor
        
        if screen_title is not None: self.screen_title = screen_title
        if screen_size is not None:
            self.screen_size = screen_size
        else:
            self.screen_size = self.turtle.screen.screensize()
        
        if pensize is not None:
            self.pensize = pensize
        else:
            self.pensize = self.turtle.pensize()
        
        self.turtle.speed(speed)
        self.turtle.hideturtle()
    
    # Getters #
    @property
    def pencolor(self) -> tuple[int, int, int]:
        """The pencolor and fill color of the turtle.
        
        :getter: Returns the current color of the turtle in rgb
        :setter: Sets the color of the turtle in rgb
        """
        return self._pencolor
    
    @property
    def pensize(self) -> int:
        """The pensize of the turtle.
        
        :getter: Returns the current pensize of the turtle
        :setter: Sets the pensize of the turtle in pixels
        """
        return self._pensize
    
    @property
    def screen_size(self) -> tuple[int, int]:
        """The turtle window's screen size.
        
        :getter: Returns the current turtle screen size as (width, height), 
                 where (0, 0) is in the center of the screen.
        :setter: Sets the screen size with a tuple (width, height)
        """
        return self._screen_size
    
    @property
    def screen_title(self) -> str:
        """The title of the turtle window.
        
        :getter: Returns the window's current title
        :setter: Sets the window's title
        """
        return self._screen_title
    
    # Setters #
    @pencolor.setter
    def pencolor(self, value: tuple[int, int, int]):
        self._pencolor = value
        self.turtle.color(value)
    
    @pensize.setter
    def pensize(self, value: int):
        self._pensize = value
        self.turtle.pensize(value)
    
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
    def coordinate_system(self,
                          horizontal_division: int, vertical_division: int=None,
                          *,
                          major_line_rgb: tuple=(0, 0, 0),
                          major_line_thickness: int=2,
                          minor_line_rgb: tuple=(220, 220, 220),
                          minor_line_thickness: int=1) -> None:
        """Generates a coordinate system image that fills the turtle screen.
        
        :param horizontal_division: The distance between minor horizontal lines
        :param vertical_division: The distance between minor vertical lines
        :param major_line_rgb: The color of the major lines (the axes) in (r, g, b)
        :param major_line_thickness: The thickness of the major lines in pixels
        :param minor_line_rgb: The color of the minor lines (the axes) in (r, g, b)
        :param minor_line_thickness: The thickness of the minor lines in pixels
        """
        # Setup
        if vertical_division is None: vertical_division = horizontal_division
        self.hide_updates()
        initial_pensize = self.pensize
        initial_color = self.pencolor
        
        # Minor Lines
        self.pensize = minor_line_thickness
        self.turtle.color(minor_line_rgb)
        width, height = self.screen_size
        
        no_horizontal_lines = math.floor(height / 2 / vertical_division)
        no_vertical_lines = math.floor(width / 2 / horizontal_division)
        
        # # Minor Horizontal Lines
        for i in range(1, no_horizontal_lines):
            y_value = i * vertical_division
            self.draw_line(Line.from_y_intercept(y_value))
            self.draw_line(Line.from_y_intercept(-y_value))
        
        # Minor Horizontal Lines
        for i in range(1, no_vertical_lines):
            x_value = i * horizontal_division
            self.draw_line(Line.from_x_intercept(x_value))
            self.draw_line(Line.from_x_intercept(-x_value))
        
        # Major Lines
        self.pensize = major_line_thickness
        self.turtle.color(major_line_rgb)
        self.draw_line(Line.from_x_intercept(0))
        self.draw_line(Line.from_y_intercept(0))
        
        # Clean Up
        self.update()
        self.pensize = initial_pensize
        self.pencolor = initial_color
    
    def draw_line(self, line: Line) -> None:
        """Draws an infinite line using a PanCAD Line object.
        
        :param line: An infinite line represented by a PanCAD Line
        """
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
    
    def draw_line_segment(self, line_segment: LineSegment) -> None:
        """Draws an line segment using a PanCAD LineSegment object.
        
        :param line_segment: An finite line represented by a PanCAD Line
        """
        initial_position = self.turtle.pos()
        self.turtle.penup()
        self.turtle.setposition(tuple(line_segment.point_a))
        self.turtle.pendown()
        self.turtle.setposition(tuple(line_segment.point_b))
        self.turtle.penup()
        self.turtle.setposition(initial_position)
    
    def hide_updates(self) -> None:
        """Hides updates drawn to the window to speed up execution time"""
        turtle.tracer(0, 0)
    
    def update(self):
        """Forces the window to update, even if updates have been hidden"""
        turtle.update()