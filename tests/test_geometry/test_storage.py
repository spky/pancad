"""Tests for storing pancad geometry in sqlite databases"""

from contextlib import closing
import tomllib
from unittest import TestCase
from pathlib import Path
from sqlite3 import connect, PARSE_DECLTYPES

from pancad import geometry, config
from pancad.utils import sql_convert

class MemoryDatabase(TestCase):
    """Writing into a temporary database memory."""
    
    def setUp(self):
        with open(Path(config.__file__).parent / "sqlite.toml", "rb") as file:
            self.types = tomllib.load(file)["conform_type"]
        
        geometry_and_values = [
            (geometry.Point(0, 0), "0;0"),
            (geometry.Point(0, 0, 0), "0;0;0"),
            (geometry.Circle((0, 0), 1), "0;0;1"),
            (geometry.Line.from_two_points((0, 0), (1, 0)), "0.0;0.0;1.0;0.0"),
            (geometry.Line.from_two_points((0, 0, 0), (1, 0, 0)), "0.0;0.0;0.0;1.0;0.0;0.0"),
            (geometry.LineSegment((0, 0), (1, 0)), "0;0;1;0"),
            (geometry.LineSegment((0, 0, 0), (1, 0, 0)), "0;0;0;1;0;0"),
            (geometry.CircularArc((0, 0), 1, (1, 0), (0, 1), False), "0;0|1.0;0.0|0.0;1.0|0|1")
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
                    self.assertEqual(expected, result)