import turtle

from PanCAD.geometry.point import Point
from PanCAD.geometry.line import Line

def draw_line_segment(t: turtle.Turtle, point_1: Point, point_2: Point):
    initial_position = t.pos()
    t.penup()
    t.setposition(tuple(point_1))
    t.pendown()
    t.setposition(tuple(point_2))
    t.penup()
    t.setposition(initial_position)

def draw_line(t: turtle.Turtle, line: Line):
    pass