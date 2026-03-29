"""Tests for storing pancad geometry in sqlite databases"""

from contextlib import closing
import tomllib
from unittest import TestCase
from pathlib import Path
from importlib.util import find_spec
from sqlite3 import connect, PARSE_DECLTYPES

from pancad.geometry.point import Point
from pancad.geometry.circle import Circle
from pancad.geometry.line import Line
from pancad.geometry.line_segment import LineSegment
from pancad.geometry.circular_arc import CircularArc
from pancad import geometry
from pancad.utils import sql_convert

RESOURCES = Path(find_spec("pancad.resources").origin).parent

class MemoryDatabase(TestCase):
    """Writing into a temporary database memory."""
    
    def setUp(self):
        with open(RESOURCES / "sqlite.toml", "rb") as file:
            self.types = tomllib.load(file)["conform_type"]
        
        geometry_and_values = [
            (Point(0, 0), "0;0"),
            (Point(0, 0, 0), "0;0;0"),
            (Circle((0, 0), 1), "0;0;1"),
            (Line.from_two_points((0, 0), (1, 0)), "0.0;0.0;1.0;0.0"),
            (Line.from_two_points((0, 0, 0), (1, 0, 0)), "0.0;0.0;0.0;1.0;0.0;0.0"),
            (LineSegment((0, 0), (1, 0)), "0;0;1;0"),
            (LineSegment((0, 0, 0), (1, 0, 0)), "0;0;0;1;0;0"),
            (CircularArc((0, 0), 1, (1, 0), (0, 1), False), "0;0|1.0;0.0|0.0;1.0|0|1.0")
        ]
        self.tests = []
        for geo, value in geometry_and_values:
            self.tests.append((geo, value, self.types[geo.__class__.__name__]))
    
    def test_conform(self):
        with closing(connect(":memory:")) as con:
            con.row_factory = lambda cur, row: row[0]
            for geo, expected, *_ in self.tests:
                with self.subTest(f"Geometry: {geo}, Expected: {expected}"):
                    result = con.execute("SELECT ?", (geo,)).fetchone()
                    self.assertEqual(result, expected)
    
    def test_convert(self):
        TABLE_SQL = "CREATE TABLE IF NOT EXISTS %s(i INTEGER, v %s)"
        INSERT_SQL = "INSERT INTO %s VALUES(?, ?)"
        WHERE_SQL = "SELECT i, v FROM %s WHERE i = %s"
        with closing(connect(":memory:", detect_types=PARSE_DECLTYPES)) as con:
            con.row_factory = lambda cur, row: row[1]
            for i, (expected, sql_value, type_) in enumerate(self.tests):
                table = type_ + "_table"
                con.execute(TABLE_SQL % (table, type_))
                con.execute(INSERT_SQL % table, (i, sql_value))
                with self.subTest(f"Expected: {expected}, Value: {expected}"):
                    result = con.execute(WHERE_SQL % (table, i)).fetchone()
                    self.assertTrue(result.is_equal(expected))